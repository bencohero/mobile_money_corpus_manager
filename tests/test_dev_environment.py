import json
import shutil
import subprocess
from pathlib import Path

import pytest

from alembic.script import ScriptDirectory


ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "docker-compose.dev.yml"
ENV_EXAMPLE = ROOT / ".env.dev.example"


def compose_config():
    if shutil.which("docker") is None:
        pytest.skip("Docker CLI absent: Compose validation is run by the host CI job")
    result = subprocess.run(
        ["docker", "compose", "--env-file", str(ENV_EXAMPLE), "-f", str(COMPOSE), "config", "--format", "json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def published_ports(service):
    return [f"{port['host_ip']}:{port['published']}:{port['target']}" for port in service.get("ports", [])]


def test_dev_compose_is_valid_and_isolated():
    config = compose_config()
    services = config["services"]
    assert set(services) == {"app", "db", "minio"}
    assert config["name"] == "mobile_money_corpus_manager_dev"
    assert set(config["networks"]) == {"dev_internal"}
    assert config["networks"]["dev_internal"].get("external", False) is False
    assert set(config["volumes"]) == {"postgres_dev_data", "minio_dev_data"}

    for service in services.values():
        assert not service.get("labels")
        assert "frontend" not in str(service.get("networks", {}))
        assert "traefik" not in json.dumps(service).lower()

    assert services["app"]["environment"]["APP_ENV"] == "development"
    assert services["app"]["environment"]["POSTGRES_HOST"] == "db"
    assert services["app"]["environment"]["MINIO_ENDPOINT"] == "minio:9000"
    assert all("healthcheck" in services[name] for name in ("app", "db", "minio"))
    assert published_ports(services["app"]) == ["127.0.0.1:8081:8000"]
    assert published_ports(services["minio"]) == ["127.0.0.1:9100:9000", "127.0.0.1:9101:9001"]
    assert "ports" not in services["db"]

    assert config["volumes"]["postgres_dev_data"]["name"] == "mobile_money_corpus_dev_postgres_data"
    assert config["volumes"]["minio_dev_data"]["name"] == "mobile_money_corpus_dev_minio_data"
    assert all(volume.get("external", False) is False for volume in config["volumes"].values())
    assert not {"pgdata", "miniodata"} & {volume["name"] for volume in config["volumes"].values()}


def test_dev_env_example_is_fake_and_ignored():
    env_text = ENV_EXAMPLE.read_text()
    assert "APP_ENV=development" in env_text
    assert "MINIO_BUCKET=mobile-money-corpus-dev" in env_text
    assert ".env.dev" in (ROOT / ".gitignore").read_text()
    assert "CHANGE_ME" in env_text
    assert "replace_with_" not in env_text
    assert "production" not in env_text.lower()


def test_alembic_head_and_runtime_files_exist():
    migrations = ROOT / "migrations"
    assert (ROOT / "alembic.ini").is_file()
    assert (migrations / "env.py").is_file()
    heads = ScriptDirectory(str(migrations)).get_heads()
    assert tuple(heads) == ("0006_multilingual_participant_identity",)
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "COPY migrations ./migrations" in dockerfile
    assert "COPY alembic.ini ./alembic.ini" in dockerfile
    assert "ffmpeg" in dockerfile
