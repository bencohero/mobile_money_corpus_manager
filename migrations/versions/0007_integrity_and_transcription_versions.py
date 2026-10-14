"""Enforce canonical languages and add optimistic transcription history."""
from alembic import op
import sqlalchemy as sa

revision = "0007_integrity_and_transcription_versions"
down_revision = "0006_multilingual_participant_identity"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    diagnostics = {}
    diagnostics["unknown_workshop_languages"] = bind.execute(sa.text("""
        SELECT count(*) FROM workshops w
        WHERE w.language_code IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM languages l WHERE l.code = upper(w.language_code))
    """)).scalar_one()
    diagnostics["unknown_participant_languages"] = bind.execute(sa.text("""
        SELECT count(*) FROM participants p
        WHERE p.language IS NULL
           OR NOT EXISTS (SELECT 1 FROM languages l WHERE l.code = upper(p.language))
    """)).scalar_one()
    diagnostics["orphan_participant_workshops"] = bind.execute(sa.text("""
        SELECT count(*) FROM participants p
        LEFT JOIN workshops w ON w.id = p.workshop_id
        WHERE w.id IS NULL
    """)).scalar_one()
    diagnostics["orphan_recording_workshops"] = bind.execute(sa.text("""
        SELECT count(*) FROM recordings r
        LEFT JOIN workshops w ON w.id = r.workshop_id
        WHERE w.id IS NULL
    """)).scalar_one()
    diagnostics["orphan_workshop_code_workshops"] = bind.execute(sa.text("""
        SELECT count(*) FROM workshop_codes c
        LEFT JOIN workshops w ON w.id = c.workshop_id
        WHERE w.id IS NULL
    """)).scalar_one()
    diagnostics["orphan_submission_workshops"] = bind.execute(sa.text("""
        SELECT count(*) FROM recording_submissions s
        LEFT JOIN workshops w ON w.id = s.workshop_id
        WHERE w.id IS NULL
    """)).scalar_one()
    diagnostics["workshop_participant_language_mismatch"] = bind.execute(sa.text("""
        SELECT count(*) FROM participants p JOIN workshops w ON w.id = p.workshop_id
        WHERE w.language_code IS NOT NULL AND upper(p.language) <> upper(w.language_code)
    """)).scalar_one()
    incompatible = {name: count for name, count in diagnostics.items() if count}
    if incompatible:
        rendered = "; ".join(f"{name}={count}" for name, count in incompatible.items())
        raise RuntimeError("Integrity migration blocked; human review required: " + rendered)

    if "language_code" not in {c["name"] for c in inspector.get_columns("participants")}:
        op.add_column("participants", sa.Column("language_code", sa.String(10), nullable=True, server_default="MOS"))
    bind.execute(sa.text("UPDATE participants SET language_code = upper(language) WHERE language_code IS NULL"))
    op.create_foreign_key("fk_participants_language_code", "participants", "languages", ["language_code"], ["code"], ondelete="RESTRICT")
    op.alter_column("participants", "language_code", nullable=False, existing_type=sa.String(10), server_default="MOS")

    workshop_fks = {fk["name"] for fk in inspector.get_foreign_keys("workshops")}
    if "fk_workshops_language_code" not in workshop_fks:
        op.create_foreign_key("fk_workshops_language_code", "workshops", "languages", ["language_code"], ["code"], ondelete="RESTRICT")

    if "version" not in {c["name"] for c in inspector.get_columns("transcriptions")}:
        op.add_column("transcriptions", sa.Column("version", sa.Integer(), nullable=True, server_default="1"))
        bind.execute(sa.text("UPDATE transcriptions SET version = 1 WHERE version IS NULL"))
        op.alter_column("transcriptions", "version", nullable=False, existing_type=sa.Integer(), server_default="1")

    transcription_fks = [fk for fk in inspector.get_foreign_keys("transcriptions")
                         if fk.get("constrained_columns") == ["recording_id"]]
    for fk in transcription_fks:
        op.drop_constraint(fk["name"], "transcriptions", type_="foreignkey")
    op.alter_column("transcriptions", "recording_id", nullable=True, existing_type=sa.Integer())
    op.create_foreign_key("fk_transcriptions_recording", "transcriptions", "recordings",
                          ["recording_id"], ["id"], ondelete="SET NULL")

    if "transcription_history" not in tables:
        op.create_table(
            "transcription_history",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("transcription_id", sa.Integer(), sa.ForeignKey("transcriptions.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("action", sa.String(40), nullable=False, server_default="EDIT"),
            sa.Column("old_reference_transcription", sa.Text()),
            sa.Column("new_reference_transcription", sa.Text()),
            sa.Column("old_normalized_transcription", sa.Text()),
            sa.Column("new_normalized_transcription", sa.Text()),
            sa.Column("old_verification_status", sa.String(30)),
            sa.Column("new_verification_status", sa.String(30)),
            sa.Column("previous_version", sa.Integer(), nullable=False),
            sa.Column("new_version", sa.Integer(), nullable=False),
            sa.Column("changed_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_transcription_history_transcription_id", "transcription_history", ["transcription_id"])
        bind.execute(sa.text("""
            INSERT INTO transcription_history
                (transcription_id, author_id, action, new_reference_transcription,
                 new_normalized_transcription, new_verification_status,
                 previous_version, new_version, changed_at)
            SELECT t.id, t.transcriber_id, 'BASELINE', t.reference_transcription,
                   t.normalized_transcription, t.verification_status,
                   0, 1, COALESCE(t.created_at, CURRENT_TIMESTAMP)
            FROM transcriptions t
        """))


def downgrade():
    raise RuntimeError("Integrity and transcription history are retained; restore a backup with writes disabled")
