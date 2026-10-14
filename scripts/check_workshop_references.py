"""Read-only integrity diagnostic for workshop foreign-key references.

This intentionally does not repair or delete anything and is safe to run
before an upgrade against a copy or a read-only operational connection.
"""
from sqlalchemy import create_engine, text
from app.config import settings


CHECKS = {
    "orphan_participants": """SELECT count(*) FROM participants p LEFT JOIN workshops w ON w.id=p.workshop_id WHERE w.id IS NULL""",
    "orphan_recordings": """SELECT count(*) FROM recordings r LEFT JOIN workshops w ON w.id=r.workshop_id WHERE w.id IS NULL""",
    "orphan_workshop_codes": """SELECT count(*) FROM workshop_codes c LEFT JOIN workshops w ON w.id=c.workshop_id WHERE w.id IS NULL""",
    "orphan_submissions": """SELECT count(*) FROM recording_submissions s LEFT JOIN workshops w ON w.id=s.workshop_id WHERE w.id IS NULL""",
    "participant_recording_mismatch": """SELECT count(*) FROM recordings r JOIN participants p ON p.id=r.participant_id WHERE r.workshop_id IS DISTINCT FROM p.workshop_id""",
}


def main() -> int:
    with create_engine(settings.effective_database_url).connect() as conn:
        revision = conn.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num")).scalars().all()
        print("revision=" + ",".join(map(str, revision)))
        findings = {}
        for name, query in CHECKS.items():
            value = int(conn.execute(text(query)).scalar_one())
            findings[name] = value
            print(f"{name}={value}")
    return 1 if any(findings.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
