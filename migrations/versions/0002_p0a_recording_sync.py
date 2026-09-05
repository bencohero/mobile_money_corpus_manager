from alembic import op
import sqlalchemy as sa
revision = "0002_p0a_recording_sync"
down_revision = "0001_initial"
branch_labels = None
depends_on = None
def upgrade():
    op.add_column("recordings", sa.Column("sync_status", sa.String(length=30), nullable=False, server_default="READY"))
    op.add_column("recordings", sa.Column("raw_size_bytes", sa.Integer(), nullable=True))
    op.add_column("recordings", sa.Column("wav_size_bytes", sa.Integer(), nullable=True))
    op.add_column("recordings", sa.Column("raw_sha256", sa.String(length=64), nullable=True))
    op.add_column("recordings", sa.Column("wav_sha256", sa.String(length=64), nullable=True))
    op.add_column("recordings", sa.Column("sync_error", sa.Text(), nullable=True))
    op.add_column("recordings", sa.Column("finalized_at", sa.DateTime(), nullable=True))
    op.create_index("ix_recordings_sync_status", "recordings", ["sync_status"])
def downgrade():
    op.drop_index("ix_recordings_sync_status", table_name="recordings")
    op.drop_column("recordings", "finalized_at")
    op.drop_column("recordings", "sync_error")
    op.drop_column("recordings", "wav_sha256")
    op.drop_column("recordings", "raw_sha256")
    op.drop_column("recordings", "wav_size_bytes")
    op.drop_column("recordings", "raw_size_bytes")
    op.drop_column("recordings", "sync_status")
