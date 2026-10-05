"""PostgreSQL allocation. Caller commits the reservation before external I/O."""
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from .models import RecordingTakeCounter


class TakeLimitReached(Exception):
    pass


def allocate_next_take(db, participant_id, utterance_id, condition):
    table = RecordingTakeCounter.__table__
    now = datetime.utcnow()
    statement = insert(table).values(
        participant_id=participant_id, utterance_id=utterance_id,
        condition=condition, last_take_number=1, created_at=now, updated_at=now,
    ).on_conflict_do_update(
        index_elements=[table.c.participant_id, table.c.utterance_id, table.c.condition],
        set_={"last_take_number": table.c.last_take_number + 1, "updated_at": now},
        where=table.c.last_take_number < 999,
    ).returning(table.c.last_take_number)
    number = db.execute(statement).scalar_one_or_none()
    if number is None:
        raise TakeLimitReached("Limite de 999 prises atteinte pour cette combinaison.")
    return number


def next_take_estimate(db, participant_id, utterance_id, condition):
    value = db.scalar(select(RecordingTakeCounter.last_take_number).filter_by(
        participant_id=participant_id, utterance_id=utterance_id, condition=condition))
    if value is not None and value >= 999:
        raise TakeLimitReached("Limite de 999 prises atteinte pour cette combinaison.")
    return (value or 0) + 1
