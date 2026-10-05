"""Durable take counters and idempotent recording reservations."""
from alembic import op
import sqlalchemy as sa

revision = "0003_take_sequences"
down_revision = "0002_p0a_recording_sync"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    # Maintenance window required: block concurrent legacy uploads during backfill.
    bind.execute(sa.text("LOCK TABLE recordings IN ACCESS EXCLUSIVE MODE"))
    invalid = bind.execute(sa.text("SELECT count(*) FROM recordings WHERE take_number IS NULL OR take_number NOT BETWEEN 1 AND 999")).scalar()
    duplicates = bind.execute(sa.text("SELECT count(*) FROM (SELECT 1 FROM recordings GROUP BY participant_id,utterance_id,condition,take_number HAVING count(*)>1) d")).scalar()
    if invalid or duplicates:
        raise RuntimeError("Take migration blocked: invalid numbers or duplicate business keys; manual review required")
    op.create_table("recording_take_counters",
        sa.Column("participant_id", sa.Integer(), sa.ForeignKey("participants.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("utterance_id", sa.Integer(), sa.ForeignKey("utterances.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("condition", sa.String(20), primary_key=True),
        sa.Column("last_take_number", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("last_take_number BETWEEN 1 AND 999", name="ck_take_counter_range"))
    bind.execute(sa.text("INSERT INTO recording_take_counters SELECT participant_id,utterance_id,condition,max(take_number),CURRENT_TIMESTAMP,CURRENT_TIMESTAMP FROM recordings GROUP BY participant_id,utterance_id,condition"))
    constraints = sa.inspect(bind).get_unique_constraints("recordings")
    expected = ["participant_id", "utterance_id", "condition", "take_number"]
    existing = next((c for c in constraints if c["name"] == "uq_recording_take"), None)
    if existing and existing["column_names"] != expected:
        op.drop_constraint("uq_recording_take", "recordings", type_="unique")
        existing = None
    if existing is None:
        op.create_unique_constraint("uq_recording_take", "recordings", expected)
    op.create_check_constraint("ck_recordings_take_range", "recordings", "take_number BETWEEN 1 AND 999")
    op.create_table("recording_submissions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("participant_id", sa.Integer(), sa.ForeignKey("participants.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("recording_id", sa.Integer(), sa.ForeignKey("recordings.id", ondelete="SET NULL"), unique=True),
        sa.Column("take_number", sa.Integer()),
        sa.Column("audio_id", sa.String(120)),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("error_status", sa.Integer()),
        sa.Column("error_detail", sa.String(255)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_submission_user_key"))


def downgrade():
    # Dropping this ledger would silently permit reuse of consumed numbers.
    raise RuntimeError("Irreversible take ledger: roll back application with writes disabled; preserve counters and submissions")
