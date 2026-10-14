#!/usr/bin/env python3
"""Safely reconcile the create_all-created workshop table before Alembic 0003/0004.

The command is intentionally read-only unless ``--apply`` and the explicit
confirmation token are supplied.  It is designed for the diagnosed state only.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

TOKEN = "RECONCILE-PARTICIPANT-REGISTRATION"
EXPECTED_REVISION = "0002_p0a_recording_sync"
REQUIRED_MIGRATIONS = ("0003_take_sequences.py", "0004_participant_self_registration.py")
LEGACY_TABLES = ("recording_take_counters", "recording_submissions")
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def qident(value: str) -> str:
    if not IDENTIFIER.fullmatch(value):
        raise RuntimeError(f"Unsafe database identifier encountered: {value!r}")
    return '"' + value.replace('"', '""') + '"'


def database_url() -> str:
    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    missing = [name for name in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD") if not os.getenv(name)]
    if missing:
        raise RuntimeError("Database configuration is incomplete: " + ", ".join(missing))
    user = quote(os.environ["POSTGRES_USER"], safe="")
    password = quote(os.environ["POSTGRES_PASSWORD"], safe="")
    db = quote(os.environ["POSTGRES_DB"], safe="")
    host = os.getenv("POSTGRES_HOST", "mobile-money-corpus-db")
    port = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


def backup_is_readable(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        return False
    try:
        result = subprocess.run(["pg_restore", "--list", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except OSError:
        return False
    return result.returncode == 0


def inspect_state(conn, root: Path) -> dict:
    revision = conn.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num")).scalars().all()
    table = conn.execute(text("SELECT to_regclass('public.workshop_codes')")).scalar_one()
    sequence = conn.execute(text("SELECT to_regclass('public.participant_login_number_seq')")).scalar_one()
    unique_constraint = conn.execute(text("""
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_users_participant_id'
    """)).scalar_one_or_none()
    active_index = conn.execute(text("""
        SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='ix_workshop_codes_active_window'
    """)).scalar_one_or_none()
    participants = conn.execute(text("SELECT count(*) FROM participants")).scalar_one()
    workshops = conn.execute(text("SELECT count(*) FROM workshop_codes")).scalar_one() if table else 0
    backup_table = conn.execute(text("SELECT to_regclass('public.workshop_codes_reconcile_backup')")).scalar_one()
    deps = conn.execute(text("""
        SELECT count(*) FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.confrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname='public' AND t.relname='workshop_codes'
    """)).scalar_one()
    legacy_counts = {
        name: int(conn.execute(text(f"SELECT count(*) FROM public.{name}")).scalar_one())
        if conn.execute(text("SELECT to_regclass(:name)"), {"name": f"public.{name}"}).scalar_one() else None
        for name in LEGACY_TABLES
    }
    return {"revision": tuple(str(x) for x in revision), "table": bool(table), "sequence": bool(sequence),
            "unique_constraint": bool(unique_constraint), "active_index": bool(active_index),
            "participants": int(participants), "workshops": int(workshops), "backup_table": bool(backup_table),
            "dependent_fks": int(deps), "migrations": all((root / "migrations" / "versions" / f).is_file() for f in REQUIRED_MIGRATIONS),
            "legacy_counts": legacy_counts}


def print_state(state: dict, backup: Path) -> None:
    print("Réconciliation participant-registration (lecture seule par défaut)")
    for key in ("revision", "migrations", "table", "sequence", "unique_constraint", "active_index", "participants", "workshops", "backup_table", "dependent_fks", "legacy_counts"):
        print(f"  {key}: {state[key]}")
    print(f"  sauvegarde fournie: {backup} (contenu non affiché)")


def require_preconditions(state: dict, backup: Path) -> None:
    if state["revision"] != (EXPECTED_REVISION,):
        raise RuntimeError(f"Précondition refusée: révision active attendue {EXPECTED_REVISION}, observée {state['revision']}")
    if not state["migrations"]:
        raise RuntimeError("Précondition refusée: les migrations 0003 et 0004 sont absentes")
    if not state["table"] or state["sequence"] or state["unique_constraint"] or state["active_index"]:
        raise RuntimeError("Précondition refusée: le schéma ne correspond pas exactement à la dérive diagnostiquée")
    if state["participants"] != 0 or state["backup_table"] or state["dependent_fks"]:
        raise RuntimeError("Précondition refusée: participants, table de reprise ou dépendances inattendus")
    if any(count not in (None, 0) for count in state["legacy_counts"].values()):
        raise RuntimeError("Précondition refusée: une table 0003 prématurée contient des lignes")
    if not backup_is_readable(backup):
        raise RuntimeError("Précondition refusée: sauvegarde absente, vide ou illisible par pg_restore")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup", type=Path, required=True, help="dump PostgreSQL custom vérifié")
    parser.add_argument("--dry-run", action="store_true", help="inspecter sans modifier (comportement par défaut)")
    parser.add_argument("--apply", action="store_true", help="effectuer la réconciliation et les migrations")
    parser.add_argument("--confirm", default="", help="confirmation exacte requise avec --apply")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    # Running the file by absolute path sets sys.path to /app/scripts; Alembic's
    # env.py imports the application package from the repository root.
    sys.path.insert(0, str(root))
    backup = args.backup.resolve()
    engine = create_engine(database_url(), future=True)
    with engine.connect() as conn:
        state = inspect_state(conn, root)
        print_state(state, backup)
        if not backup_is_readable(backup):
            raise RuntimeError("Précondition refusée: sauvegarde absente, vide ou illisible par pg_restore")
        if not args.apply:
            print("DRY-RUN: aucune modification exécutée.")
            return 0
        require_preconditions(state, backup)
        if args.confirm != TOKEN:
            raise RuntimeError(f"Confirmation requise: --confirm {TOKEN}")
        indexes = list(conn.execute(text("SELECT indexname FROM pg_indexes WHERE schemaname='public' AND tablename='workshop_codes'" )).scalars())
        constraints = list(conn.execute(text("SELECT conname FROM pg_constraint WHERE conrelid='public.workshop_codes'::regclass")).scalars())
        serial = conn.execute(text("SELECT pg_get_serial_sequence('public.workshop_codes','id')")).scalar_one_or_none()
        legacy_objects = {}
        for table_name in LEGACY_TABLES:
            exists = conn.execute(text("SELECT to_regclass(:name)"), {"name": f"public.{table_name}"}).scalar_one()
            if exists:
                legacy_objects[table_name] = {
                    "indexes": list(conn.execute(text("SELECT indexname FROM pg_indexes WHERE schemaname='public' AND tablename=:table"), {"table": table_name}).scalars()),
                    "constraints": list(conn.execute(text("SELECT conname FROM pg_constraint WHERE conrelid=(:table)::regclass"), {"table": f"public.{table_name}"}).scalars()),
                }
        conn.commit()
        with conn.begin():
            conn.execute(text("LOCK TABLE workshop_codes, users, participants IN ACCESS EXCLUSIVE MODE"))
            for table_name in legacy_objects:
                conn.execute(text(f"ALTER TABLE public.{qident(table_name)} RENAME TO {qident(table_name + '_reconcile_backup')}"))
                for name in legacy_objects[table_name]["constraints"]:
                    conn.execute(text(f"ALTER TABLE public.{qident(table_name + '_reconcile_backup')} RENAME CONSTRAINT {qident(name)} TO {qident('reconcile_' + name[:50])}"))
                for name in legacy_objects[table_name]["indexes"]:
                    if name in legacy_objects[table_name]["constraints"]:
                        continue
                    conn.execute(text(f"ALTER INDEX public.{qident(name)} RENAME TO {qident('reconcile_' + name[:50])}"))
            conn.execute(text("ALTER TABLE public.workshop_codes RENAME TO workshop_codes_reconcile_backup"))
            for name in constraints:
                conn.execute(text(f"ALTER TABLE public.workshop_codes_reconcile_backup RENAME CONSTRAINT {qident(name)} TO {qident('reconcile_wc_c_' + name[:43])}"))
            for name in indexes:
                # PostgreSQL renames an index backing a primary/unique constraint
                # when that constraint is renamed above; renaming it again by its
                # old name would fail with UndefinedTable.
                if name in constraints:
                    continue
                conn.execute(text(f"ALTER INDEX public.{qident(name)} RENAME TO {qident('reconcile_wc_i_' + name[:43])}"))
            if serial and "." in serial:
                serial_name = serial.split(".")[-1].strip('"')
                conn.execute(text(f"ALTER SEQUENCE public.{qident(serial_name)} RENAME TO {qident('reconcile_wc_' + serial_name[:45])}"))
        cfg = Config(str(root / "alembic.ini"))
        cfg.set_main_option("script_location", str(root / "migrations"))
        command.upgrade(cfg, "head")
        with engine.begin() as write:
            columns = "id,label,code_hash,is_active,starts_at,expires_at,max_registrations,use_count,created_by_user_id,created_at,disabled_at"
            write.execute(text(f"INSERT INTO public.workshop_codes ({columns}) SELECT {columns} FROM public.workshop_codes_reconcile_backup"))
            old_count = write.execute(text("SELECT count(*) FROM public.workshop_codes_reconcile_backup")).scalar_one()
            new_count = write.execute(text("SELECT count(*) FROM public.workshop_codes")).scalar_one()
            if old_count != new_count:
                raise RuntimeError("La vérification de restauration de workshop_codes a échoué")
            workshop_sequence = write.execute(text("SELECT pg_get_serial_sequence('public.workshop_codes','id')")).scalar_one_or_none()
            if workshop_sequence:
                write.execute(text("SELECT setval(CAST(:sequence_name AS regclass), COALESCE((SELECT max(id) FROM public.workshop_codes), 1), true)"), {"sequence_name": workshop_sequence})
            if "recording_take_counters" in legacy_objects:
                write.execute(text("INSERT INTO public.recording_take_counters SELECT * FROM public.recording_take_counters_reconcile_backup"))
            if "recording_submissions" in legacy_objects:
                write.execute(text("INSERT INTO public.recording_submissions SELECT * FROM public.recording_submissions_reconcile_backup"))
        print(f"Réconciliation terminée; table de reprise conservée: workshop_codes_reconcile_backup ({state['workshops']} ligne(s)).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        raise SystemExit(2)
