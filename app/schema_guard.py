from pathlib import Path

from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


class SchemaRevisionError(RuntimeError):
    """Raised when the database is not at the migrations embedded in the image."""


def migration_heads() -> tuple[str, ...]:
    migrations_dir = Path(__file__).resolve().parent.parent / "migrations"
    if not migrations_dir.is_dir():
        raise SchemaRevisionError("Migration directory is missing from the application image.")
    try:
        return tuple(sorted(ScriptDirectory(str(migrations_dir)).get_heads()))
    except Exception as exc:  # pragma: no cover - exercised by broken images
        raise SchemaRevisionError("Unable to inspect embedded migration heads.") from exc


def database_revisions(db: Session) -> tuple[str, ...]:
    try:
        rows = db.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num")).scalars().all()
    except SQLAlchemyError as exc:
        raise SchemaRevisionError("Database schema revision cannot be read.") from exc
    return tuple(sorted(str(row) for row in rows))


def assert_schema_current(db: Session) -> None:
    current = database_revisions(db)
    expected = migration_heads()
    if current != expected:
        current_text = ", ".join(current) if current else "<none>"
        expected_text = ", ".join(expected) if expected else "<none>"
        raise SchemaRevisionError(
            "Database schema is not up to date. "
            f"Current revision: {current_text}. Expected revision: {expected_text}. "
            "Run the approved migration procedure before starting the application."
        )
