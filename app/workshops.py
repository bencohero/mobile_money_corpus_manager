from datetime import datetime

from fastapi import HTTPException

from .models import Participant, Role, User, Workshop
from .time_utils import as_utc_naive, utc_now


def workshop_is_open(workshop: Workshop, now: datetime | None = None) -> bool:
    now = as_utc_naive(now) if now else utc_now()
    return (
        workshop.is_active
        and (workshop.starts_at is None or now >= workshop.starts_at)
        and (workshop.ends_at is None or now < workshop.ends_at)
    )


def require_active_participant_workshop(db, user: User) -> Participant | None:
    """Server-side authorization guard for participant data-producing actions."""
    if user.role != Role.PARTICIPANT.value:
        return None
    participant = db.get(Participant, user.participant_id) if user.participant_id else None
    if not participant or not participant.workshop_id or not participant.workshop:
        raise HTTPException(403, "Votre atelier n’est pas disponible.")
    if not workshop_is_open(participant.workshop):
        raise HTTPException(403, "Votre atelier est désactivé ou fermé.")
    return participant
