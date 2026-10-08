import os
import re
import uuid

import httpx

from app.db import SessionLocal
from app.models import AuditLog, Participant, User, WorkshopCode


BASE = "http://app-test:8000"


def client():
    return httpx.Client(base_url=BASE, follow_redirects=False, timeout=20)


def login(session, username, password):
    session.get("/login")
    csrf = session.cookies.get("csrf_token")
    return session.post("/login", data={"username": username, "password": password, "csrf_token": csrf})


def registration_payload(code):
    return {
        "workshop_code": code,
        "password": "http-participant-password",
        "password_confirmation": "http-participant-password",
        "participant": {"language": "mos", "age_group": "25-34", "gender": "F", "region": "Centre", "consent_obtained": True},
    }


def test_public_registration_api_permissions_csrf_and_login():
    admin = client()
    assert login(admin, "admin", os.environ["ADMIN_PASSWORD"]).status_code == 303
    label = "HTTP " + uuid.uuid4().hex
    created = admin.post("/admin/workshop-codes", data={
        "label": label, "max_registrations": "2", "starts_at": "", "expires_at": "",
        "workshop_id": "",
        "csrf_token": admin.cookies.get("csrf_token"),
    })
    assert created.status_code == 201
    code = re.search(r'<p class="login-id">([^<]+)</p>', created.text).group(1)

    participant = client()
    page = participant.get("/participant/register")
    assert page.status_code == 200 and "Créer mon compte" in page.text
    body = registration_payload(code)
    assert participant.post("/api/auth/participant-registration", json=body).status_code == 403
    headers = {"X-CSRF-Token": participant.cookies.get("csrf_token")}
    privileged = participant.post("/api/auth/participant-registration", json={**body, "role": "admin"}, headers=headers)
    assert privileged.status_code == 400
    response = participant.post("/api/auth/participant-registration", json=body, headers=headers)
    assert response.status_code == 200
    result = response.json()
    assert re.fullmatch(r"MOS_[0-9]{3,}", result["login_id"])
    assert result["role"] == "participant"
    serialized = response.text.lower()
    assert "password" not in serialized and code.lower() not in serialized

    signed_in = client()
    assert login(signed_in, result["login_id"], "http-participant-password").status_code == 303
    assert signed_in.get("/record").status_code == 200
    assert signed_in.get("/admin/workshop-codes").status_code == 403
    assert signed_in.get("/users").status_code == 403
    assert signed_in.post("/users", data={"username": "forbidden", "password": "not-created-password", "role": "ADMIN", "csrf_token": signed_in.cookies.get("csrf_token")}).status_code == 403

    with SessionLocal() as db:
        user = db.query(User).filter_by(username=result["login_id"]).one()
        participant_row = db.get(Participant, user.participant_id)
        workshop = db.query(WorkshopCode).filter_by(label=label).one()
        db.query(AuditLog).filter_by(user_id=user.id).delete()
        db.delete(user); db.flush()
        db.delete(participant_row); db.delete(workshop); db.commit()
    admin.close(); participant.close(); signed_in.close()
