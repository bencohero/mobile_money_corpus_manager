import hashlib
import hmac
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import hash_password
from .config import settings
from .models import AuditLog, Participant, ParticipantLanguageSequence, ParticipantRegistrationRequest, Role, User, Workshop, WorkshopCode
from .languages import LANGUAGE_BY_CODE
from .time_utils import utc_now


LOGIN_RE = re.compile(r"^[A-Z][A-Z0-9]{1,9}_[0-9]{3,}$")
FORBIDDEN_PUBLIC_FIELDS = {
    "login_id", "username", "participant_code", "sequence_number", "role",
    "is_active", "is_superuser", "permissions", "id", "user_id", "participant_id",
}
ALLOWED_TOP_LEVEL_FIELDS = {"workshop_code", "password", "password_confirmation", "participant", "idempotency_key"}
ALLOWED_PARTICIPANT_FIELDS = {"language", "age_group", "gender", "region", "consent_obtained"}
ALLOWED_AGE_GROUPS = {"", "18-24", "25-34", "35-44", "45-54", "55+"}
ALLOWED_GENDERS = {"", "F", "M", "OTHER", "UNDISCLOSED"}


class RegistrationError(ValueError):
    pass


@dataclass(frozen=True)
class RegistrationResult:
    login_id: str
    user_id: int
    participant_id: int


def workshop_code_hash(code: str) -> str:
    normalized = code.strip().encode("utf-8")
    secret = settings.workshop_code_secret or settings.jwt_secret
    return hmac.new(secret.encode("utf-8"), normalized, hashlib.sha256).hexdigest()


def format_login_id(number: int, language_code: str = "MOS") -> str:
    if number < 1:
        raise ValueError("participant number must be positive")
    code = language_code.upper()
    if code not in LANGUAGE_BY_CODE:
        raise ValueError("unknown participant language")
    return f"{code}_{number:03d}"


def next_participant_number(db: Session, language_code: str = "MOS") -> int:
    code = language_code.upper()
    counter = db.query(ParticipantLanguageSequence).filter_by(language_code=code).with_for_update().one_or_none()
    if counter is None:
        counter = ParticipantLanguageSequence(language_code=code, last_number=0)
        db.add(counter)
        db.flush()
    counter.last_number += 1
    db.flush()
    return counter.last_number


def validate_password(password: object, confirmation: object) -> str:
    if not isinstance(password, str) or not isinstance(confirmation, str):
        raise RegistrationError("Le mot de passe et sa confirmation sont obligatoires.")
    if password != confirmation:
        raise RegistrationError("Les mots de passe ne correspondent pas.")
    if len(password) < 12:
        raise RegistrationError("Le mot de passe doit contenir au moins 12 caractères.")
    if len(password) > 64 or len(password.encode("utf-8")) > 72:
        raise RegistrationError("Le mot de passe est trop long.")
    return password


def validate_payload(payload: object) -> tuple[str, str, dict]:
    if not isinstance(payload, dict):
        raise RegistrationError("Requête d'inscription invalide.")
    keys = set(payload)
    if keys - ALLOWED_TOP_LEVEL_FIELDS or keys & FORBIDDEN_PUBLIC_FIELDS:
        raise RegistrationError("La requête contient des champs interdits.")
    participant = payload.get("participant")
    if not isinstance(participant, dict):
        raise RegistrationError("La fiche participant est obligatoire.")
    participant_keys = set(participant)
    if participant_keys - ALLOWED_PARTICIPANT_FIELDS or participant_keys & FORBIDDEN_PUBLIC_FIELDS:
        raise RegistrationError("La fiche participant contient des champs interdits.")
    code = payload.get("workshop_code")
    if not isinstance(code, str) or not code.strip() or len(code) > 128:
        raise RegistrationError("Inscription impossible avec ce code d'atelier.")
    password = validate_password(payload.get("password"), payload.get("password_confirmation"))
    age_group = participant.get("age_group", "")
    gender = participant.get("gender", "")
    region = participant.get("region", "")
    if age_group not in ALLOWED_AGE_GROUPS or gender not in ALLOWED_GENDERS:
        raise RegistrationError("La fiche participant contient une valeur invalide.")
    if not isinstance(region, str) or len(region.strip()) > 120:
        raise RegistrationError("La région est invalide.")
    if participant.get("consent_obtained") is not True:
        raise RegistrationError("Le consentement est obligatoire.")
    idempotency_key = payload.get("idempotency_key")
    if idempotency_key is not None and (not isinstance(idempotency_key, str) or not idempotency_key.strip() or len(idempotency_key) > 128):
        raise RegistrationError("La clé d’idempotence est invalide.")
    return code.strip(), password, {
        "age_group": age_group or None,
        "gender": gender or None,
        "region": region.strip() or None,
        "consent_obtained": True,
        "idempotency_key": idempotency_key.strip() if idempotency_key else None,
    }


def register_participant(
    db: Session,
    payload: object,
    *,
    now: datetime | None = None,
    number_allocator: Callable[[Session], int] = next_participant_number,
) -> RegistrationResult:
    code, password, fields = validate_payload(payload)
    request_key = fields.pop("idempotency_key") or uuid.uuid4().hex
    fingerprint = hashlib.sha256(json.dumps({"workshop_code": code, "password": password, "participant": fields}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    current_time = now or utc_now()
    try:
        existing_request = db.query(ParticipantRegistrationRequest).filter_by(idempotency_key=request_key).one_or_none()
        if existing_request:
            if existing_request.fingerprint != fingerprint:
                raise RegistrationError("Cette requête d’inscription a déjà été utilisée avec d’autres données.")
            db.rollback()
            return RegistrationResult(existing_request.login_id, existing_request.user_id, existing_request.participant_id)
        code_record = (
            db.query(WorkshopCode)
            .filter(WorkshopCode.code_hash == workshop_code_hash(code))
            .with_for_update()
            .one_or_none()
        )
        if code_record is not None and code_record.workshop is None:
            code_record.workshop = Workshop(name=f"Atelier — {code_record.label}")
            db.flush()
        workshop = code_record.workshop if code_record else None
        unavailable = (
            code_record is None or workshop is None
            or not code_record.is_active or not workshop.is_active
            or (workshop.starts_at is not None and current_time < workshop.starts_at)
            or (workshop.ends_at is not None and current_time >= workshop.ends_at)
            or (code_record.starts_at is not None and current_time < code_record.starts_at)
            or (code_record.expires_at is not None and current_time >= code_record.expires_at)
            or (code_record.max_registrations is not None and code_record.use_count >= code_record.max_registrations)
            or (workshop.capacity is not None and len(workshop.participants) >= workshop.capacity)
        )
        if unavailable:
            raise RegistrationError("Inscription impossible avec ce code d'atelier.")

        language_code = (workshop.language_code or "").upper()
        if language_code not in LANGUAGE_BY_CODE:
            raise RegistrationError("La langue de cet atelier doit être attribuée par un administrateur avant l’inscription.")
        try:
            allocated_number = number_allocator(db, language_code)
        except TypeError:
            allocated_number = number_allocator(db)
        login_id = format_login_id(allocated_number, language_code)
        fields["language"] = language_code.lower()
        fields["language_code"] = language_code
        participant = Participant(participant_code=login_id, workshop_id=workshop.id, **fields)
        db.add(participant)
        db.flush()
        user = User(
            username=login_id,
            password_hash=hash_password(password),
            role=Role.PARTICIPANT.value,
            is_active=True,
            participant_id=participant.id,
        )
        db.add(user)
        db.flush()
        code_record.use_count += 1
        db.add(AuditLog(
            user_id=user.id,
            action="REGISTER_PARTICIPANT",
            entity_type="participant",
            entity_id=str(participant.id),
            detail=f"workshop_id={workshop.id};code_id={code_record.id}",
        ))
        db.add(ParticipantRegistrationRequest(
            idempotency_key=request_key, fingerprint=fingerprint,
            participant_id=participant.id, user_id=user.id, login_id=login_id,
        ))
        db.commit()
        return RegistrationResult(login_id, user.id, participant.id)
    except RegistrationError:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        # A concurrent retry may have committed the same idempotency receipt
        # between the initial lookup and our insert.
        existing_request = db.query(ParticipantRegistrationRequest).filter_by(idempotency_key=request_key).one_or_none()
        if existing_request and existing_request.fingerprint == fingerprint:
            return RegistrationResult(existing_request.login_id, existing_request.user_id, existing_request.participant_id)
        raise RegistrationError("Inscription impossible. Veuillez réessayer.") from exc
    except Exception:
        db.rollback()
        raise
