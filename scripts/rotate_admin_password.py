#!/usr/bin/env python3
"""Controlled, one-target admin password rotation.

This command is intentionally inert unless --apply and --confirm-target benco
are both supplied. The new password is read from stdin and is never printed.
It uses the application's bcrypt helper and ORM transaction, not ad-hoc SQL.
"""

from __future__ import annotations

import argparse
import getpass
import sys

from sqlalchemy import select

from app.auth import hash_password
from app.config import settings
from app.db import SessionLocal
from app.models import User


TARGET_USERNAME = "benco"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rotate only the benco ADMIN password")
    parser.add_argument("--apply", action="store_true", help="commit the rotation")
    parser.add_argument(
        "--confirm-target",
        help="must be exactly benco when --apply is used",
    )
    parser.add_argument(
        "--password-stdin",
        action="store_true",
        help="read the new password from stdin; otherwise prompt without echo",
    )
    return parser.parse_args()


def read_password(use_stdin: bool) -> str:
    if use_stdin:
        value = sys.stdin.readline().rstrip("\r\n")
    else:
        value = getpass.getpass("New benco password: ")
    if not 12 <= len(value) <= 64 or len(value.encode("utf-8")) > 72:
        raise SystemExit("password rejected: length must be 12..64 bytes (bcrypt limit)")
    return value


def admin_snapshot(session):
    rows = session.execute(select(User).where(User.role == "ADMIN").order_by(User.id)).scalars().all()
    return {
        row.id: {
            "username": row.username,
            "role": row.role,
            "is_active": row.is_active,
            "participant_id": row.participant_id,
            "password_hash": row.password_hash,
        }
        for row in rows
    }


def main() -> int:
    args = parse_args()
    if args.apply and args.confirm_target != TARGET_USERNAME:
        raise SystemExit("refusing: --apply requires --confirm-target benco")
    if not args.apply:
        print("DRY RUN: no password was read and no database change was made")
        return 0
    if settings.app_env != "production":
        raise SystemExit("refusing: production APP_ENV is required")

    new_password = read_password(args.password_stdin)
    with SessionLocal() as session:
        before = admin_snapshot(session)
        target = session.execute(
            select(User).where(User.username == TARGET_USERNAME, User.role == "ADMIN").with_for_update()
        ).scalar_one_or_none()
        if target is None:
            raise SystemExit("refusing: benco ADMIN account not found")
        if not target.is_active:
            raise SystemExit("refusing: benco ADMIN account is inactive")
        if len(before) != 3:
            raise SystemExit("refusing: expected exactly three ADMIN accounts")

        target.password_hash = hash_password(new_password)
        session.flush()

        after = admin_snapshot(session)
        if set(after) != set(before):
            session.rollback()
            raise SystemExit("refusing: ADMIN identity set changed")
        for user_id, old in before.items():
            current = after[user_id]
            for field in ("username", "role", "is_active", "participant_id"):
                if current[field] != old[field]:
                    session.rollback()
                    raise SystemExit(f"refusing: protected ADMIN field changed for id {user_id}")
            if user_id != target.id and current["password_hash"] != old["password_hash"]:
                session.rollback()
                raise SystemExit(f"refusing: non-target ADMIN hash changed for id {user_id}")
        if after[target.id]["password_hash"] == before[target.id]["password_hash"]:
            session.rollback()
            raise SystemExit("refusing: target hash did not change")
        session.commit()

    print("ROTATED: benco password hash updated; no other ADMIN account was changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
