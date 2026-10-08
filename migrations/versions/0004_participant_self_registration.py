"""Secure participant self-registration and workshop codes.

The downgrade is intentionally blocked: dropping the global identity sequence or
workshop ledger could permit reuse of participant identities and erase access
history.
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_participant_registration"
down_revision = "0003_take_sequences"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    bind.execute(sa.text("LOCK TABLE users, participants IN SHARE ROW EXCLUSIVE MODE"))

    duplicate_links = bind.execute(sa.text("""
        SELECT count(*) FROM (
            SELECT participant_id FROM users
            WHERE participant_id IS NOT NULL
            GROUP BY participant_id HAVING count(*) > 1
        ) duplicated
    """)).scalar_one()
    if duplicate_links:
        raise RuntimeError("Participant registration migration blocked: several users reference the same participant")

    mismatched_pairs = bind.execute(sa.text("""
        SELECT count(*) FROM users u
        JOIN participants p ON p.id = u.participant_id
        WHERE u.username ~ '^MOS_[0-9]{3,}$'
          AND p.participant_code ~ '^MOS_[0-9]{3,}$'
          AND u.username <> p.participant_code
    """)).scalar_one()
    if mismatched_pairs:
        raise RuntimeError("Participant registration migration blocked: linked MOS identities disagree")

    numeric_aliases = bind.execute(sa.text("""
        SELECT count(*) FROM (
            SELECT substring(identifier from 5)::bigint
            FROM (
                SELECT username AS identifier FROM users WHERE username ~ '^MOS_[0-9]{3,}$'
                UNION
                SELECT participant_code FROM participants WHERE participant_code ~ '^MOS_[0-9]{3,}$'
            ) identities
            GROUP BY substring(identifier from 5)::bigint
            HAVING count(*) > 1
        ) aliases
    """)).scalar_one()
    if numeric_aliases:
        raise RuntimeError("Participant registration migration blocked: MOS identifiers have ambiguous numeric aliases")

    op.create_unique_constraint("uq_users_participant_id", "users", ["participant_id"])
    op.execute("CREATE SEQUENCE participant_login_number_seq START WITH 1 INCREMENT BY 1 NO CYCLE")
    maximum = bind.execute(sa.text("""
        SELECT max(substring(identifier from 5)::bigint)
        FROM (
            SELECT username AS identifier FROM users WHERE username ~ '^MOS_[0-9]{3,}$'
            UNION
            SELECT participant_code FROM participants WHERE participant_code ~ '^MOS_[0-9]{3,}$'
        ) identities
    """)).scalar_one()
    if maximum is None:
        bind.execute(sa.text("SELECT setval('participant_login_number_seq', 1, false)"))
    else:
        bind.execute(sa.text("SELECT setval('participant_login_number_seq', :maximum, true)"), {"maximum": maximum})

    op.create_table(
        "workshop_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("starts_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("max_registrations", sa.Integer(), nullable=True),
        sa.Column("use_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("disabled_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("max_registrations IS NULL OR max_registrations > 0", name="ck_workshop_max_positive"),
        sa.CheckConstraint("use_count >= 0", name="ck_workshop_use_count_nonnegative"),
        sa.CheckConstraint("max_registrations IS NULL OR use_count <= max_registrations", name="ck_workshop_limit"),
        sa.UniqueConstraint("code_hash", name="uq_workshop_codes_code_hash"),
    )
    op.create_index("ix_workshop_codes_code_hash", "workshop_codes", ["code_hash"], unique=True)
    op.create_index("ix_workshop_codes_active_window", "workshop_codes", ["is_active", "starts_at", "expires_at"])


def downgrade():
    raise RuntimeError(
        "Irreversible participant identity/workshop ledger: restore a pre-upgrade backup only with writes disabled"
    )
