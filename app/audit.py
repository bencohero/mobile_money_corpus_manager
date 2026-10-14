"""Security and audit helpers shared by HTTP handlers."""

import secrets

from fastapi import HTTPException, Request, Response

from .config import settings
from .models import AuditLog


def audit(db, user, action, entity_type=None, entity_id=None, detail=None):
    db.add(
        AuditLog(
            user_id=user.id if user else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            detail=detail,
        )
    )
    db.commit()


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def check_csrf(request: Request, token: str | None = None):
    supplied = token or request.headers.get("x-csrf-token")
    expected = request.cookies.get("csrf_token")
    if not supplied or not expected or not secrets.compare_digest(supplied, expected):
        raise HTTPException(403, "Requête expirée ou invalide. Rechargez la page.")


def set_csrf_cookie(response: Response, token: str):
    response.set_cookie(
        "csrf_token",
        token,
        httponly=False,
        samesite="strict",
        secure=settings.cookie_secure,
        max_age=settings.access_token_minutes * 60,
    )
