import enum
from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

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

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default=Role.PARTICIPANT.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    participant_id: Mapped[int | None] = mapped_column(ForeignKey("participants.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    participant = relationship("Participant", back_populates="user", uselist=False)

class Participant(Base):
    __tablename__ = "participants"
    id: Mapped[int] = mapped_column(primary_key=True)
    participant_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    language: Mapped[str] = mapped_column(String(10), default="mos")
    age_group: Mapped[str | None] = mapped_column(String(30), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(30), nullable=True)
    region: Mapped[str | None] = mapped_column(String(120), nullable=True)
    consent_obtained: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="participant", uselist=False)
    recordings = relationship("Recording", back_populates="participant")

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
    )
    id: Mapped[int] = mapped_column(primary_key=True)
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    participant = relationship("Participant", back_populates="recordings")
    utterance = relationship("Utterance")
    transcription = relationship("Transcription", back_populates="recording", uselist=False)

class Transcription(Base):
    __tablename__ = "transcriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    recording_id: Mapped[int] = mapped_column(ForeignKey("recordings.id"), unique=True)
    reference_transcription: Mapped[str] = mapped_column(Text)
    normalized_transcription: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcriber_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    verification_status: Mapped[str] = mapped_column(String(30), default="PENDING")
    verifier_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    verifier_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    recording = relationship("Recording", back_populates="transcription")
    transcriber = relationship("User", foreign_keys=[transcriber_id])
    verifier = relationship("User", foreign_keys=[verifier_id])

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(120))
    entity_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
