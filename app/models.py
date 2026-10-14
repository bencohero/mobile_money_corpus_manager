import enum
from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base
from .time_utils import utc_now

class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    PARTICIPANT = "PARTICIPANT"
    TRANSCRIBER = "TRANSCRIBER"
    VALIDATOR = "VALIDATOR"

class RecordingStatus(str, enum.Enum):
    RECORDED = "RECORDED"
    TRANSCRIBED = "TRANSCRIBED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class Language(Base):
    __tablename__ = "languages"
    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default=Role.PARTICIPANT.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    participant_id: Mapped[int | None] = mapped_column(ForeignKey("participants.id"), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    participant = relationship("Participant", back_populates="user", uselist=False)

class Participant(Base):
    __tablename__ = "participants"
    id: Mapped[int] = mapped_column(primary_key=True)
    workshop_id: Mapped[int] = mapped_column(ForeignKey("workshops.id", ondelete="RESTRICT"), index=True, nullable=False)
    participant_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    language: Mapped[str] = mapped_column(String(10), default="mos")
    # Canonical, FK-backed language code. ``language`` is retained verbatim for
    # historical exports and backwards compatibility with the original schema.
    language_code: Mapped[str] = mapped_column(String(10), ForeignKey("languages.code", ondelete="RESTRICT"), nullable=False, default="MOS", server_default="MOS")
    age_group: Mapped[str | None] = mapped_column(String(30), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(30), nullable=True)
    region: Mapped[str | None] = mapped_column(String(120), nullable=True)
    consent_obtained: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    user = relationship("User", back_populates="participant", uselist=False)
    recordings = relationship("Recording", back_populates="participant")
    workshop = relationship("Workshop", back_populates="participants")


class Workshop(Base):
    __tablename__ = "workshops"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    # Nullable is intentional: historical workshops require explicit admin attribution.
    language_code: Mapped[str | None] = mapped_column(ForeignKey("languages.code", ondelete="RESTRICT"), nullable=True, index=True, default="MOS")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    disabled_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    participants = relationship("Participant", back_populates="workshop")
    recordings = relationship("Recording", back_populates="workshop")
    codes = relationship("WorkshopCode", back_populates="workshop")
    language = relationship("Language")


class WorkshopCode(Base):
    __tablename__ = "workshop_codes"
    __table_args__ = (
        CheckConstraint("max_registrations IS NULL OR max_registrations > 0", name="ck_workshop_max_positive"),
        CheckConstraint("use_count >= 0", name="ck_workshop_use_count_nonnegative"),
        CheckConstraint("max_registrations IS NULL OR use_count <= max_registrations", name="ck_workshop_limit"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    workshop_id: Mapped[int] = mapped_column(ForeignKey("workshops.id", ondelete="RESTRICT"), index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(120))
    code_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    max_registrations: Mapped[int | None] = mapped_column(Integer, nullable=True)
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    workshop = relationship("Workshop", back_populates="codes")


class ParticipantLanguageSequence(Base):
    __tablename__ = "participant_language_sequences"
    language_code: Mapped[str] = mapped_column(ForeignKey("languages.code", ondelete="RESTRICT"), primary_key=True)
    last_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class ParticipantRegistrationRequest(Base):
    """Durable idempotency receipt for participant account creation."""
    __tablename__ = "participant_registration_requests"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_registration_request_key"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id", ondelete="RESTRICT"), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), unique=True)
    login_id: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class Utterance(Base):
    __tablename__ = "utterances"
    id: Mapped[int] = mapped_column(primary_key=True)
    utterance_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    language: Mapped[str] = mapped_column(String(10), default="mos")
    intent: Mapped[str] = mapped_column(String(60))
    scenario_fr: Mapped[str] = mapped_column(Text)
    reference_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    period: Mapped[str | None] = mapped_column(String(30), nullable=True)
    amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    counterparty: Mapped[str | None] = mapped_column(String(120), nullable=True)
    transaction_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    operator: Mapped[str | None] = mapped_column(String(50), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Recording(Base):
    __tablename__ = "recordings"
    __table_args__ = (
        UniqueConstraint("participant_id", "utterance_id", "condition", "take_number", name="uq_recording_take"),
        CheckConstraint("take_number BETWEEN 1 AND 999", name="ck_recordings_take_range"),
        Index("ix_recordings_workshop_created_at", "workshop_id", "created_at"),
        Index("ix_recordings_workshop_validation", "workshop_id", "status"),
        Index("ix_recordings_workshop_participant", "workshop_id", "participant_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    workshop_id: Mapped[int] = mapped_column(ForeignKey("workshops.id", ondelete="RESTRICT"), index=True, nullable=False)
    audio_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"), index=True)
    utterance_id: Mapped[int] = mapped_column(ForeignKey("utterances.id"), index=True)
    take_number: Mapped[int] = mapped_column(Integer, default=1)
    condition: Mapped[str] = mapped_column(String(20), default="CLEAN")
    raw_object: Mapped[str] = mapped_column(String(255))
    wav_object: Mapped[str] = mapped_column(String(255))
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default=RecordingStatus.RECORDED.value)
    sync_status: Mapped[str] = mapped_column(String(30), default="READY", index=True)
    raw_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    wav_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    wav_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    participant = relationship("Participant", back_populates="recordings")
    workshop = relationship("Workshop", back_populates="recordings")
    utterance = relationship("Utterance")
    transcription = relationship("Transcription", back_populates="recording", uselist=False)

class RecordingTakeCounter(Base):
    __tablename__ = "recording_take_counters"
    __table_args__ = (CheckConstraint("last_take_number BETWEEN 1 AND 999", name="ck_take_counter_range"),)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id", ondelete="RESTRICT"), primary_key=True)
    utterance_id: Mapped[int] = mapped_column(ForeignKey("utterances.id", ondelete="RESTRICT"), primary_key=True)
    condition: Mapped[str] = mapped_column(String(20), primary_key=True)
    last_take_number: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class RecordingSubmission(Base):
    """Durable receipt, retained even after the recording is deleted."""
    __tablename__ = "recording_submissions"
    __table_args__ = (UniqueConstraint("user_id", "idempotency_key", name="uq_submission_user_key"),)
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id", ondelete="RESTRICT"))
    workshop_id: Mapped[int] = mapped_column(ForeignKey("workshops.id", ondelete="RESTRICT"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    fingerprint: Mapped[str] = mapped_column(String(64))
    recording_id: Mapped[int | None] = mapped_column(ForeignKey("recordings.id", ondelete="SET NULL"), nullable=True, unique=True)
    take_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    audio_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str] = mapped_column(String(20), default="PENDING")
    error_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_detail: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class Transcription(Base):
    __tablename__ = "transcriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    recording_id: Mapped[int | None] = mapped_column(ForeignKey("recordings.id", ondelete="SET NULL"), unique=True, nullable=True)
    reference_transcription: Mapped[str] = mapped_column(Text)
    normalized_transcription: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcriber_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    verification_status: Mapped[str] = mapped_column(String(30), default="PENDING")
    verifier_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    verifier_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    recording = relationship("Recording", back_populates="transcription")
    transcriber = relationship("User", foreign_keys=[transcriber_id])
    verifier = relationship("User", foreign_keys=[verifier_id])
    history = relationship("TranscriptionHistory", back_populates="transcription", order_by="TranscriptionHistory.id")


class TranscriptionHistory(Base):
    __tablename__ = "transcription_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    transcription_id: Mapped[int] = mapped_column(ForeignKey("transcriptions.id", ondelete="RESTRICT"), nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    action: Mapped[str] = mapped_column(String(40), nullable=False, default="EDIT")
    old_reference_transcription: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_reference_transcription: Mapped[str | None] = mapped_column(Text, nullable=True)
    old_normalized_transcription: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_normalized_transcription: Mapped[str | None] = mapped_column(Text, nullable=True)
    old_verification_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_verification_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    previous_version: Mapped[int] = mapped_column(Integer, nullable=False)
    new_version: Mapped[int] = mapped_column(Integer, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    transcription = relationship("Transcription", back_populates="history")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(120))
    entity_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
