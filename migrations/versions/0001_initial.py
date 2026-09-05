from alembic import op
import sqlalchemy as sa
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None
def upgrade():
    op.create_table("participants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("participant_code", sa.String(length=30), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="mos"),
        sa.Column("age_group", sa.String(length=30)),
        sa.Column("gender", sa.String(length=30)),
        sa.Column("region", sa.String(length=120)),
        sa.Column("consent_obtained", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("participant_code", name="uq_participants_participant_code"))
    op.create_index("ix_participants_participant_code", "participants", ["participant_code"], unique=True)
    op.create_table("users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False, server_default="PARTICIPANT"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("participant_id", sa.Integer(), sa.ForeignKey("participants.id")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("username", name="uq_users_username"))
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_table("utterances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("utterance_code", sa.String(length=40), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="mos"),
        sa.Column("intent", sa.String(length=60), nullable=False),
        sa.Column("scenario_fr", sa.Text(), nullable=False),
        sa.Column("reference_text", sa.Text()),
        sa.Column("period", sa.String(length=30)),
        sa.Column("amount", sa.Integer()),
        sa.Column("counterparty", sa.String(length=120)),
        sa.Column("transaction_type", sa.String(length=50)),
        sa.Column("operator", sa.String(length=50)),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("utterance_code", name="uq_utterances_utterance_code"))
    op.create_index("ix_utterances_utterance_code", "utterances", ["utterance_code"], unique=True)
    op.create_table("recordings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("audio_id", sa.String(length=120), nullable=False),
        sa.Column("participant_id", sa.Integer(), sa.ForeignKey("participants.id"), nullable=False),
        sa.Column("utterance_id", sa.Integer(), sa.ForeignKey("utterances.id"), nullable=False),
        sa.Column("take_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("condition", sa.String(length=20), nullable=False, server_default="CLEAN"),
        sa.Column("raw_object", sa.String(length=255), nullable=False),
        sa.Column("wav_object", sa.String(length=255), nullable=False),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="RECORDED"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("audio_id", name="uq_recordings_audio_id"),
        sa.UniqueConstraint("participant_id","utterance_id","condition","take_number", name="uq_recording_take"))
    op.create_index("ix_recordings_audio_id", "recordings", ["audio_id"], unique=True)
    op.create_index("ix_recordings_participant_id", "recordings", ["participant_id"])
    op.create_index("ix_recordings_utterance_id", "recordings", ["utterance_id"])
    op.create_table("transcriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("recording_id", sa.Integer(), sa.ForeignKey("recordings.id"), nullable=False),
        sa.Column("reference_transcription", sa.Text(), nullable=False),
        sa.Column("normalized_transcription", sa.Text()),
        sa.Column("transcriber_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("verification_status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("verifier_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("verifier_comment", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("recording_id", name="uq_transcriptions_recording_id"))
    op.create_table("audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80)),
        sa.Column("entity_id", sa.String(length=80)),
        sa.Column("detail", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False))
def downgrade():
    op.drop_table("audit_logs")
    op.drop_table("transcriptions")
    op.drop_index("ix_recordings_utterance_id", table_name="recordings")
    op.drop_index("ix_recordings_participant_id", table_name="recordings")
    op.drop_index("ix_recordings_audio_id", table_name="recordings")
    op.drop_table("recordings")
    op.drop_index("ix_utterances_utterance_code", table_name="utterances")
    op.drop_table("utterances")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_participants_participant_code", table_name="participants")
    op.drop_table("participants")
