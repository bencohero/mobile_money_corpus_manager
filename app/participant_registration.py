import hashlib
import hmac
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import hash_password
from .config import settings
from .models import AuditLog, Participant, Role, User, Workshop, WorkshopCode


LOGIN_RE = re.compile(r"^MOS_[0-9]{3,}$")
FORBIDDEN_PUBLIC_FIELDS = {
    "login_id", "username", "participant_code", "sequence_number", "role",
    "is_active", "is_superuser", "permissions", "id", "user_id", "participant_id",
}
ALLOWED_TOP_LEVEL_FIELDS = {"workshop_code", "password", "password_confirmation", "participant"}
ALLOWED_PARTICIPANT_FIELDS = {"language", "age_group", "gender", "region", "consent_obtained"}
ALLOWED_LANGUAGES = {"mos"}
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


def format_login_id(number: int) -> str:
    if number < 1:
        raise ValueError("participant number must be positive")
    return f"MOS_{number:03d}"


def next_participant_number(db: Session) -> int:
    return int(db.execute(text("SELECT nextval('participant_login_number_seq')")).scalar_one())


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
    language = participant.get("language", "mos")
    age_group = participant.get("age_group", "")
    gender = participant.get("gender", "")
    region = participant.get("region", "")
    if language not in ALLOWED_LANGUAGES or age_group not in ALLOWED_AGE_GROUPS or gender not in ALLOWED_GENDERS:
        raise RegistrationError("La fiche participant contient une valeur invalide.")
    if not isinstance(region, str) or len(region.strip()) > 120:
        raise RegistrationError("La région est invalide.")
    if participant.get("consent_obtained") is not True:
        raise RegistrationError("Le consentement est obligatoire.")
    return code.strip(), password, {
        "language": language,
        "age_group": age_group or None,
        "gender": gender or None,
        "region": region.strip() or None,
        "consent_obtained": True,
    }


def register_participant(
    db: Session,
    payload: object,
    *,
    now: datetime | None = None,
    number_allocator: Callable[[Session], int] = next_participant_number,
) -> RegistrationResult:
    code, password, fields = validate_payload(payload)
    current_time = now or datetime.utcnow()
    try:
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

        login_id = format_login_id(number_allocator(db))
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
        db.commit()
        return RegistrationResult(login_id, user.id, participant.id)
    except RegistrationError:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise RegistrationError("Inscription impossible. Veuillez réessayer.") from exc
    except Exception:
        db.rollback()
        raise
