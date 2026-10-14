"""Add the extensible language catalog and per-language identity counters.

Historical workshops remain unassigned. The migration only derives counter
high-water marks from already allocated public identifiers; it never renames
participants or invents a language for a workshop.
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_multilingual_participant_identity"
down_revision = "0005_workshop_attribution"
branch_labels = None
depends_on = None


LANGUAGES = (("FR", "Français"), ("MOS", "Mooré"), ("DYU", "Dioula"), ("FUL", "Fulfuldé"))


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    # The legacy Alembic bootstrap used VARCHAR(32), which is shorter than
    # this revision identifier. Alembic updates this row after upgrade() has
    # returned, so widen it before the version-table write occurs.
    version_columns = {c["name"]: c for c in inspector.get_columns("alembic_version")}
    if version_columns.get("version_num", {}).get("type") is not None:
        op.alter_column(
            "alembic_version",
            "version_num",
            existing_type=sa.String(length=32),
            type_=sa.String(length=255),
            existing_nullable=False,
        )
    conflicting_links = bind.execute(sa.text("""
        SELECT count(*) FROM users u JOIN participants p ON p.participant_code = u.username
        WHERE u.participant_id IS NULL OR u.participant_id <> p.id
    """)).scalar_one()
    if conflicting_links:
        raise RuntimeError("Multilingual identity migration blocked: user and participant public identifiers collide")
    workshop_columns = {c["name"] for c in inspector.get_columns("workshops")}
    if "language_code" not in workshop_columns:
        op.add_column("workshops", sa.Column("language_code", sa.String(10), nullable=True))
        op.create_index("ix_workshops_language_code", "workshops", ["language_code"])

    if "languages" not in inspector.get_table_names():
        op.create_table(
            "languages",
            sa.Column("code", sa.String(10), primary_key=True),
            sa.Column("name", sa.String(80), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        )
    for code, name in LANGUAGES:
        bind.execute(sa.text("INSERT INTO languages (code, name, is_active) VALUES (:code, :name, true) ON CONFLICT (code) DO NOTHING"), {"code": code, "name": name})

    if "participant_language_sequences" not in inspector.get_table_names():
        op.create_table(
            "participant_language_sequences",
            sa.Column("language_code", sa.String(10), primary_key=True),
            sa.Column("last_number", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["language_code"], ["languages.code"], ondelete="RESTRICT"),
            sa.CheckConstraint("last_number >= 0", name="ck_participant_language_sequence_nonnegative"),
        )
    for code, _ in LANGUAGES:
        bind.execute(sa.text("INSERT INTO participant_language_sequences (language_code, last_number) VALUES (:code, 0) ON CONFLICT (language_code) DO NOTHING"), {"code": code})
        prefix_position = len(code) + 2
        if bind.dialect.name == "postgresql":
            query = f"SELECT max(CAST(substring(identifier FROM {prefix_position}) AS BIGINT)) FROM (SELECT participant_code AS identifier FROM participants WHERE participant_code ~ '^{code}_[0-9]{{3,}}$' UNION ALL SELECT username AS identifier FROM users WHERE username ~ '^{code}_[0-9]{{3,}}$') identities"
        else:
            query = f"SELECT max(CAST(substr(identifier, {prefix_position}) AS INTEGER)) FROM (SELECT participant_code AS identifier FROM participants WHERE participant_code GLOB '{code}_[0-9][0-9][0-9]*' UNION ALL SELECT username AS identifier FROM users WHERE username GLOB '{code}_[0-9][0-9][0-9]*') identities"
        maximum = bind.execute(sa.text(query)).scalar()
        if maximum is not None:
            bind.execute(sa.text("UPDATE participant_language_sequences SET last_number = CASE WHEN last_number < :maximum THEN :maximum ELSE last_number END WHERE language_code = :code"), {"maximum": maximum, "code": code})

    if "participant_registration_requests" not in inspector.get_table_names():
        op.create_table(
            "participant_registration_requests",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("idempotency_key", sa.String(128), nullable=False),
            sa.Column("fingerprint", sa.String(64), nullable=False),
            sa.Column("participant_id", sa.Integer(), sa.ForeignKey("participants.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("login_id", sa.String(30), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("idempotency_key", name="uq_registration_request_key"),
            sa.UniqueConstraint("participant_id", name="uq_registration_request_participant"),
            sa.UniqueConstraint("user_id", name="uq_registration_request_user"),
        )


def downgrade():
    raise RuntimeError("Identity counters and receipts are retained to prevent identifier reuse; restore a backup instead")
