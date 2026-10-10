"""Add shared, expiring PostgreSQL rate-limit buckets."""
from alembic import op
import sqlalchemy as sa

revision = "0008_rate_limit_buckets"
down_revision = "0007_integrity_and_transcription_versions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "rate_limit_buckets",
        sa.Column("bucket_key", sa.String(64), nullable=False),
        sa.Column("scope", sa.String(80), nullable=False),
        sa.Column("window_started_at", sa.DateTime(), nullable=False),
        sa.Column("event_count", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("bucket_key", "scope", name="pk_rate_limit_buckets"),
        sa.CheckConstraint("event_count >= 0", name="ck_rate_limit_event_count_nonnegative"),
    )
    op.create_index("ix_rate_limit_buckets_expires_at", "rate_limit_buckets", ["expires_at"])


def downgrade():
    raise RuntimeError("Rate-limit state is operational data; restore a backup instead")
