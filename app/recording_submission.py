"""Short PostgreSQL transactions for durable, user-scoped upload receipts."""
from datetime import datetime
import uuid

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from .models import Recording, RecordingSubmission, AuditLog
from .take_sequence import allocate_next_take
from .time_utils import utc_now


def result(receipt):
    if receipt.recording_id is None or receipt.state == "DELETED":
        raise HTTPException(410, "Cette prise a été supprimée ; son numéro reste consommé.")
    payload = {"ok": receipt.state == "READY", "recording_id": receipt.recording_id,
               "audio_id": receipt.audio_id, "take_number": receipt.take_number, "status": receipt.state}
    if receipt.state == "ERROR":
        payload["detail"] = receipt.error_detail
        return JSONResponse(payload, status_code=receipt.error_status or 502)
    if receipt.state == "PENDING":
        return JSONResponse(payload, status_code=202, headers={"Retry-After": "2"})
    return payload


def detach(db, receipt):
    db.refresh(receipt)
    db.expunge(receipt)
    db.rollback()  # release the refresh transaction before conversion/storage I/O
    return receipt


def reserve(db, user_id, participant, utterance, condition, key, fingerprint, suffix):
    operation = uuid.uuid4().hex
    now = utc_now()
    inserted = db.execute(insert(RecordingSubmission).values(
        id=operation, user_id=user_id, participant_id=participant.id, workshop_id=participant.workshop_id,
        idempotency_key=key, fingerprint=fingerprint, state="PENDING",
        created_at=now, updated_at=now,
    ).on_conflict_do_nothing(constraint="uq_submission_user_key").returning(RecordingSubmission.id)).scalar_one_or_none()
    if inserted is None:
        receipt = db.scalar(select(RecordingSubmission).filter_by(user_id=user_id, idempotency_key=key))
        if (receipt.fingerprint != fingerprint or receipt.participant_id != participant.id
                or receipt.workshop_id != participant.workshop_id):
            db.rollback()
            raise HTTPException(409, "Clé d’idempotence déjà utilisée pour un autre audio ou contexte.")
        return detach(db, receipt), False
    number = allocate_next_take(db, participant.id, utterance.id, condition)
    audio_id = f"{participant.participant_code}_{utterance.utterance_code}_{condition}_T{number:02d}"
    # Numeric participant ID avoids user-supplied path fragments. UUID isolates operations.
    rec = Recording(audio_id=audio_id, participant_id=participant.id, workshop_id=participant.workshop_id, utterance_id=utterance.id,
                    take_number=number, condition=condition, sync_status="PENDING",
                    raw_object=f"raw/{participant.id}/{operation}/source{suffix}",
                    wav_object=f"normalized/{participant.id}/{operation}/audio.wav")
    db.add(rec); db.flush()
    receipt = db.get(RecordingSubmission, operation)
    receipt.recording_id, receipt.take_number, receipt.audio_id = rec.id, number, audio_id
    db.add(AuditLog(user_id=user_id, action="RESERVE_RECORDING", entity_type="recording", entity_id=str(rec.id), detail=operation))
    db.commit()
    return detach(db, receipt), True


def finish(db, receipt_id, metadata):
    receipt = db.get(RecordingSubmission, receipt_id)
    rec = db.get(Recording, receipt.recording_id)
    for name, value in metadata.items(): setattr(rec, name, value)
    rec.sync_status, rec.sync_error, rec.finalized_at = "READY", None, utc_now()
    receipt.state, receipt.updated_at = "READY", utc_now()
    db.add(AuditLog(user_id=receipt.user_id, action="CREATE_RECORDING", entity_type="recording", entity_id=str(rec.id), detail=rec.audio_id))
    db.commit()
    return detach(db, receipt)


def mark_error(db, receipt_id, status, detail):
    """Resolve ambiguous commit outcomes before any compensating delete."""
    db.rollback()
    receipt = db.get(RecordingSubmission, receipt_id)
    if receipt.state == "READY":
        return detach(db, receipt)
    rec = db.get(Recording, receipt.recording_id)
    rec.sync_status, rec.sync_error = "ERROR", "upload_failed"
    receipt.state, receipt.error_status, receipt.error_detail = "ERROR", status, detail
    receipt.updated_at = utc_now()
    db.commit()
    return detach(db, receipt)
