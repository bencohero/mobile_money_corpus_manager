"""Read-only, bounded-resource corpus ZIP export."""
import csv
import hashlib
import io
import json
import logging
import socket
import tempfile
import uuid
import wave
import zipfile
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import storage
from .models import Recording, Workshop

logger = logging.getLogger("mobile_money_corpus_manager.export")
EXPORT_SCHEMA = "1.0"
BLOCK_SIZE = 1024 * 1024
MAX_EXPORT_RECORDINGS = 10000
MAX_EXPORT_BYTES = 20 * 1024 * 1024 * 1024

RECORDING_COLUMNS = [
    "audio_id", "workshop_id", "workshop_name", "file_name", "relative_audio_path", "participant_code", "utterance_code",
    "intent", "condition", "take_number", "duration_ms", "duration_sec", "status",
    "reference_transcription", "normalized_transcription", "verification_status",
    "sample_rate_hz", "channels", "sample_width_bits", "wav_size_bytes", "wav_sha256",
]
BENCHMARK_COLUMNS = [
    "audio_id", "file_name", "split", "language", "speaker_id", "gender", "environment",
    "snr_db", "sample_rate_hz", "channels", "duration_sec", "reference_text",
    "intent_expected", "amount_expected", "person_expected", "date_expected",
    "validation_status", "notes",
]


class ExportFailure(Exception):
    def __init__(self, classification, message, status_code=502):
        super().__init__(message)
        self.classification = classification
        self.message = message
        self.status_code = status_code


def classify_storage_error(exc):
    from minio.error import S3Error
    code = getattr(exc, "code", None)
    if code in {"NoSuchKey", "NoSuchObject", "NotFound"}:
        return "object_not_found"
    if code in {"AccessDenied", "InvalidAccessKeyId", "SignatureDoesNotMatch"}:
        return "storage_permission_denied"
    if isinstance(exc, (TimeoutError, socket.timeout)) or "timeout" in type(exc).__name__.lower():
        return "storage_timeout"
    if isinstance(exc, PermissionError):
        return "storage_permission_denied"
    if isinstance(exc, (ConnectionError, ConnectionRefusedError, OSError, S3Error)):
        return "storage_unavailable"
    return "storage_unavailable"


def parse_filters(mode, status, verification_status, condition, participant, intent,
                  has_transcription, date_min, date_max, strict, workshop_id=""):
    if mode not in {"work", "benchmark"}:
        raise HTTPException(400, "mode invalide")
    if status and status not in {"RECORDED", "TRANSCRIBED", "NEEDS_REVIEW", "VERIFIED", "REJECTED"}:
        raise HTTPException(400, "statut invalide")
    if verification_status and verification_status not in {"PENDING", "VERIFIED", "NEEDS_REVIEW", "REJECTED"}:
        raise HTTPException(400, "statut de vérification invalide")
    if condition and condition not in {"CLEAN", "NOISY"}:
        raise HTTPException(400, "condition invalide")
    if has_transcription not in {"", "true", "false"}:
        raise HTTPException(400, "présence de transcription invalide")
    try:
        start = date.fromisoformat(date_min) if date_min else None
        end = date.fromisoformat(date_max) if date_max else None
    except ValueError:
        raise HTTPException(400, "date invalide, attendu YYYY-MM-DD")
    if start and end and start > end:
        raise HTTPException(400, "intervalle de dates invalide")
    if strict not in {"true", "false"}:
        raise HTTPException(400, "strict doit valoir true ou false")
    if workshop_id:
        try: workshop_id = int(workshop_id)
        except (TypeError, ValueError): raise HTTPException(400, "atelier invalide")
        if workshop_id < 1: raise HTTPException(400, "atelier invalide")
    return {"mode": mode, "status": status or None, "verification_status": verification_status or None,
            "condition": condition or None, "participant": participant or None, "intent": intent or None,
            "has_transcription": None if not has_transcription else has_transcription == "true",
            "date_min": date_min or None, "date_max": date_max or None, "workshop_id": workshop_id or None,
            "strict": strict == "true"}


def _csv_value(value, raw=False):
    value = "" if value is None else str(value)
    # Keep exact linguistic text in JSONL; CSV is explicitly safe for spreadsheet opening.
    if not raw and value.startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def _safe_audio_path(audio_id, condition, used):
    if not audio_id or any(x in audio_id for x in ("..", "/", "\\")) or any(ord(c) < 32 for c in audio_id):
        raise ExportFailure("duplicate_archive_path", "identifiant audio non sûr", 500)
    if not all(c.isalnum() or c in "._-" for c in audio_id):
        raise ExportFailure("duplicate_archive_path", "identifiant audio non sûr", 500)
    bucket = condition.lower() if condition in {"CLEAN", "NOISY"} else "unknown"
    path = f"audio/{bucket}/{audio_id}.wav"
    if path in used:
        raise ExportFailure("duplicate_archive_path", "collision de chemin audio", 500)
    used.add(path)
    return path


def _read_validate_object(rec, path):
    if not rec.wav_object:
        raise ExportFailure("db_without_object", "objet WAV absent en base")
    try:
        info = storage.stat_file(rec.wav_object)
    except Exception as exc:
        raise ExportFailure(classify_storage_error(exc), "objet WAV indisponible")
    if info.size == 0:
        raise ExportFailure("invalid_wav", "objet WAV vide")
    if rec.wav_size_bytes is not None and info.size != rec.wav_size_bytes:
        raise ExportFailure("checksum_mismatch", "taille WAV divergente")
    digest = hashlib.sha256()
    size = 0
    try:
        response = storage.client.get_object(storage.settings.minio_bucket, rec.wav_object)
        try:
            with path.open("wb") as target:
                while True:
                    block = response.read(BLOCK_SIZE)
                    if not block:
                        break
                    target.write(block)
                    digest.update(block)
                    size += len(block)
                    if size > MAX_EXPORT_BYTES:
                        raise ExportFailure("storage_unavailable", "export trop volumineux", 413)
        finally:
            response.close()
            response.release_conn()
    except ExportFailure:
        raise
    except Exception as exc:
        raise ExportFailure(classify_storage_error(exc), "lecture MinIO impossible")
    actual_digest = digest.hexdigest()
    if rec.wav_sha256 and actual_digest != rec.wav_sha256:
        raise ExportFailure("checksum_mismatch", "checksum WAV divergent")
    try:
        with wave.open(str(path), "rb") as wav:
            channels, width, rate, frames = wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()
            if (channels, width, rate) != (1, 2, 16000) or frames <= 0:
                raise ExportFailure("invalid_wav", "WAV non conforme au format PCM16 mono 16 kHz")
            duration_sec = frames / rate
    except ExportFailure:
        raise
    except (wave.Error, OSError, EOFError):
        raise ExportFailure("invalid_wav", "WAV illisible")
    return {"size": size, "sha256": actual_digest, "channels": channels, "width_bits": width * 8,
            "rate": rate, "frames": frames, "duration_sec": duration_sec}


def _query(db, filters):
    query = db.query(Recording).filter(Recording.sync_status == "READY").order_by(Recording.id)
    if filters["status"]: query = query.filter(Recording.status == filters["status"])
    if filters["condition"]: query = query.filter(Recording.condition == filters["condition"])
    if filters.get("workshop_id"): query = query.filter(Recording.workshop_id == filters["workshop_id"])
    if filters["participant"]: query = query.join(Recording.participant).filter_by(participant_code=filters["participant"])
    if filters["intent"]: query = query.join(Recording.utterance).filter_by(intent=filters["intent"])
    records = query.all()
    start = datetime.fromisoformat(filters["date_min"]).date() if filters["date_min"] else None
    end = datetime.fromisoformat(filters["date_max"]).date() if filters["date_max"] else None
    result = []
    for rec in records:
        tr = rec.transcription
        if filters["verification_status"] and (not tr or tr.verification_status != filters["verification_status"]): continue
        if filters["has_transcription"] is True and not tr: continue
        if filters["has_transcription"] is False and tr: continue
        created = rec.created_at.date() if rec.created_at else None
        if start and (not created or created < start): continue
        if end and (not created or created > end): continue
        result.append(rec)
    return result


def build_export(db: Session, filters):
    records = _query(db, filters)
    if len(records) > MAX_EXPORT_RECORDINGS:
        raise HTTPException(413, f"export limité à {MAX_EXPORT_RECORDINGS} enregistrements")
    excluded = Counter()
    included = []
    used = set()
    archive_tmp = tempfile.NamedTemporaryFile(prefix="corpus-export-", suffix=".zip", delete=False)
    archive_tmp.close()
    archive_path = Path(archive_tmp.name)
    try:
      with tempfile.TemporaryDirectory(prefix="corpus-export-audio-") as td:
        tempdir = Path(td)
        for rec in records:
            tr = rec.transcription
            reason = None
            if filters["mode"] == "benchmark":
                if rec.status != "VERIFIED":
                    excluded["not_verified"] += 1
                    continue
                if not tr or tr.verification_status != "VERIFIED":
                    excluded["not_verified"] += 1
                    continue
                if not tr.reference_transcription or not tr.reference_transcription.strip():
                    excluded["missing_transcription"] += 1
                    continue
            if not rec.wav_object and not reason: reason = "db_without_object"
            if reason:
                excluded[reason] += 1
                if filters["strict"]:
                    raise ExportFailure(reason, "enregistrement non exploitable en mode strict")
                continue
            try:
                rel = _safe_audio_path(rec.audio_id, rec.condition, used)
                audio = _read_validate_object(rec, tempdir / f"{len(included)}.wav")
            except ExportFailure as exc:
                excluded[exc.classification] += 1
                if filters["strict"]:
                    raise
                continue
            included.append((rec, tr, rel, audio, tempdir / f"{len(included)}.wav"))
        if not included:
            raise HTTPException(404, "Aucun enregistrement exploitable ne correspond aux filtres")

        export_id = uuid.uuid4().hex
        generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        prefix = f"mobile_money_corpus_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        zip_path = archive_path
        file_hashes = {}
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            rows = []
            benchmark_rows = []
            raw_rows = []
            for rec, tr, rel, audio, local in included:
                archive.write(local, prefix + "/" + rel)
                row = {
                    "audio_id": rec.audio_id, "workshop_id": getattr(rec, "workshop_id", "") or "", "workshop_name": getattr(getattr(rec, "workshop", None), "name", "") or "",
                    "file_name": Path(rel).name, "relative_audio_path": rel,
                    "participant_code": rec.participant.participant_code, "utterance_code": rec.utterance.utterance_code,
                    "intent": rec.utterance.intent, "condition": rec.condition, "take_number": rec.take_number,
                    "duration_ms": round(audio["duration_sec"] * 1000), "duration_sec": round(audio["duration_sec"], 6),
                    "status": rec.status, "reference_transcription": tr.reference_transcription if tr else "",
                    "normalized_transcription": tr.normalized_transcription if tr else "",
                    "verification_status": tr.verification_status if tr else "", "sample_rate_hz": audio["rate"],
                    "channels": audio["channels"], "sample_width_bits": audio["width_bits"], "wav_size_bytes": audio["size"],
                    "wav_sha256": audio["sha256"],
                }
                rows.append(row)
                raw_rows.append(row.copy())
                benchmark_rows.append({"audio_id": rec.audio_id, "file_name": Path(rel).name, "split": "",
                    "language": rec.participant.language, "speaker_id": rec.participant.participant_code,
                    "gender": rec.participant.gender or "", "environment": (rec.condition or "").lower(), "snr_db": "",
                    "sample_rate_hz": audio["rate"], "channels": audio["channels"], "duration_sec": round(audio["duration_sec"], 6),
                    "reference_text": tr.reference_transcription if tr else "", "intent_expected": rec.utterance.intent,
                    "amount_expected": rec.utterance.amount or "", "person_expected": rec.utterance.counterparty or "",
                    "date_expected": rec.utterance.period or "", "validation_status": tr.verification_status if tr else "",
                    "notes": ""})
            def csv_bytes(fields, data):
                out = io.StringIO(newline="")
                writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                for row in data: writer.writerow({k: _csv_value(row.get(k)) for k in fields})
                return out.getvalue().encode("utf-8")
            recordings_csv = csv_bytes(RECORDING_COLUMNS, rows)
            metadata_csv = csv_bytes(BENCHMARK_COLUMNS, benchmark_rows)
            manifest = {"schema_version": EXPORT_SCHEMA, "export_id": export_id, "generated_at": generated_at,
                "mode": filters["mode"], "filters": filters, "recording_count": len(rows),
                "participant_count": len({r["participant_code"] for r in rows}),
                "workshops": [{"id": workshop_id, "name": workshop_name}
                    for workshop_id, workshop_name in {tuple((x["workshop_id"], x["workshop_name"])) for x in rows}],
                "total_duration_sec": round(sum(r["duration_sec"] for r in rows), 6),
                "conditions": dict(Counter(r["condition"] or "UNKNOWN" for r in rows)),
                "statuses": dict(Counter(r["status"] for r in rows)),
                "audio_format": {"container": "WAV", "codec": "PCM_S16LE", "sample_rate_hz": 16000, "channels": 1, "sample_width_bits": 16},
                "excluded_count": sum(excluded.values()), "exclusions": dict(excluded), "max_recordings": MAX_EXPORT_RECORDINGS,
                "max_estimated_bytes": MAX_EXPORT_BYTES, "git_revision": None}
            manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
            raw_bytes = b"\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True).encode("utf-8") for r in raw_rows) + b"\n"
            entries = {"metadata/recordings.csv": recordings_csv, "metadata/metadata.csv": metadata_csv,
                       "metadata/manifest.json": manifest_bytes, "metadata/recordings.jsonl": raw_bytes}
            for name, data in entries.items(): archive.writestr(prefix + "/" + name, data)
            for rec, tr, rel, audio, local in included:
                data = local.read_bytes()
                file_hashes[rel] = hashlib.sha256(data).hexdigest()
            for name, data in entries.items(): file_hashes[name] = hashlib.sha256(data).hexdigest()
            sums = "".join(f"{digest}  {name}\n" for name, digest in sorted(file_hashes.items()))
            archive.writestr(prefix + "/SHA256SUMS", sums.encode("utf-8"))
        return zip_path, prefix
    except Exception:
        archive_path.unlink(missing_ok=True)
        raise


def stream_file(path):
    try:
        with path.open("rb") as source:
            while block := source.read(BLOCK_SIZE):
                yield block
    finally:
        path.unlink(missing_ok=True)
