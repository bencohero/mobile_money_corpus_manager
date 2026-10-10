from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from fastapi import HTTPException

from app.auth import ALGO, create_token, get_current_user
from app.config import settings


class FakeDB:
    def __init__(self, user=None):
        self.user = user

    def get(self, model, user_id):
        return self.user if self.user and self.user.id == user_id else None


def request_for(token):
    return SimpleNamespace(cookies={"session": token})


def test_jwt_contract_accepts_signed_expiring_session():
    user = SimpleNamespace(id=42, role="TRANSCRIBER", is_active=True)
    token = create_token(user)
    assert get_current_user(request_for(token), FakeDB(user)) is user


@pytest.mark.parametrize("mutator", [
    lambda payload: {**payload, "sub": "not-an-integer"},
    lambda payload: {k: v for k, v in payload.items() if k != "role"},
])
def test_jwt_contract_rejects_malformed_claims(mutator):
    payload = {"sub": "42", "role": "TRANSCRIBER", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    token = jwt.encode(mutator(payload), settings.jwt_secret, algorithm=ALGO)
    with pytest.raises(HTTPException) as exc:
        get_current_user(request_for(token), FakeDB(SimpleNamespace(id=42, is_active=True)))
    assert exc.value.status_code == 401


def test_jwt_contract_rejects_expired_bad_signature_and_algorithm():
    base = {"sub": "42", "role": "TRANSCRIBER"}
    expired = jwt.encode({**base, "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}, settings.jwt_secret, algorithm=ALGO)
    bad_signature = jwt.encode({**base, "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}, "w" * 32, algorithm=ALGO)
    wrong_algorithm = jwt.encode({**base, "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}, "w" * 48, algorithm="HS384")
    for token in (expired, bad_signature, wrong_algorithm):
        with pytest.raises(HTTPException) as exc:
            get_current_user(request_for(token), FakeDB(SimpleNamespace(id=42, is_active=True)))
        assert exc.value.status_code == 401


def test_jwt_permissions_reject_unknown_or_inactive_users():
    token = create_token(SimpleNamespace(id=42, role="PARTICIPANT"))
    for user in (None, SimpleNamespace(id=42, role="PARTICIPANT", is_active=False)):
        with pytest.raises(HTTPException) as exc:
            get_current_user(request_for(token), FakeDB(user))
        assert exc.value.status_code == 401
