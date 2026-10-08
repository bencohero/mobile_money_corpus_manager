"""Persist workshop ownership for participants and recordings.

Existing rows are deliberately attached to one explicit historical workshop.
The migration refuses to continue if the historical data is structurally corrupt.
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_workshop_attribution"
down_revision = "0004_participant_registration"
branch_labels = None
depends_on = None

HISTORICAL_NAME = "Atelier historique — à confirmer"


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {c["name"] for c in inspector.get_columns("participants")}
    if "workshop_id" not in existing:
        op.create_table(
            "workshops",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(160), nullable=False, unique=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("starts_at", sa.DateTime()), sa.Column("ends_at", sa.DateTime()),
            sa.Column("capacity", sa.Integer()),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("disabled_at", sa.DateTime()),
            sa.Column("disabled_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        )
        op.add_column("workshop_codes", sa.Column("workshop_id", sa.Integer(), nullable=True))
        op.create_index("ix_workshop_codes_workshop_id", "workshop_codes", ["workshop_id"])
        op.add_column("participants", sa.Column("workshop_id", sa.Integer(), nullable=True))
        op.create_index("ix_participants_workshop_id", "participants", ["workshop_id"])
        op.add_column("recordings", sa.Column("workshop_id", sa.Integer(), nullable=True))
        op.create_index("ix_recordings_workshop_id", "recordings", ["workshop_id"])
        op.add_column("recording_submissions", sa.Column("workshop_id", sa.Integer(), nullable=True))

    duplicate_participant_links = bind.execute(sa.text("""
        SELECT count(*) FROM recordings r
        JOIN participants p ON p.id = r.participant_id
        WHERE r.participant_id IS NULL
    """)).scalar_one()
    if duplicate_participant_links:
        raise RuntimeError("Workshop migration blocked: recording without participant")

    workshop_id = bind.execute(sa.text("SELECT id FROM workshops WHERE name=:name"), {"name": HISTORICAL_NAME}).scalar()
    if workshop_id is None:
        workshop_id = bind.execute(sa.text("""
            INSERT INTO workshops (name, is_active, created_at, updated_at)
            VALUES (:name, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id
        """), {"name": HISTORICAL_NAME}).scalar_one()

    bind.execute(sa.text("UPDATE workshop_codes SET workshop_id=:wid WHERE workshop_id IS NULL"), {"wid": workshop_id})
    bind.execute(sa.text("UPDATE participants SET workshop_id=:wid WHERE workshop_id IS NULL"), {"wid": workshop_id})
    bind.execute(sa.text("""
        UPDATE recordings r SET workshop_id=p.workshop_id
        FROM participants p WHERE p.id=r.participant_id AND r.workshop_id IS NULL
    """), {"wid": workshop_id})
    bind.execute(sa.text("""
        UPDATE recording_submissions s SET workshop_id=p.workshop_id
        FROM participants p WHERE p.id=s.participant_id AND s.workshop_id IS NULL
    """))

    ambiguous = bind.execute(sa.text("""
        SELECT (SELECT count(*) FROM participants WHERE workshop_id IS NULL)
             + (SELECT count(*) FROM recordings WHERE workshop_id IS NULL)
             + (SELECT count(*) FROM workshop_codes WHERE workshop_id IS NULL)
             + (SELECT count(*) FROM recording_submissions WHERE workshop_id IS NULL)
    """)).scalar_one()
    if ambiguous:
        raise RuntimeError("Workshop migration blocked: historical rows could not be attributed")

    op.create_foreign_key("fk_workshop_codes_workshop", "workshop_codes", "workshops", ["workshop_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_participants_workshop", "participants", "workshops", ["workshop_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_recordings_workshop", "recordings", "workshops", ["workshop_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_recording_submissions_workshop", "recording_submissions", "workshops", ["workshop_id"], ["id"], ondelete="RESTRICT")
    op.alter_column("workshop_codes", "workshop_id", nullable=False)
    op.alter_column("participants", "workshop_id", nullable=False)
    op.alter_column("recordings", "workshop_id", nullable=False)
    op.alter_column("recording_submissions", "workshop_id", nullable=False)
    op.create_index("ix_recordings_workshop_created_at", "recordings", ["workshop_id", "created_at"])
    op.create_index("ix_recordings_workshop_validation", "recordings", ["workshop_id", "status"])
    op.create_index("ix_recordings_workshop_participant", "recordings", ["workshop_id", "participant_id"])


def downgrade():
    raise RuntimeError("Workshop attribution is historical; restore a backup with writes disabled instead of dropping it")
