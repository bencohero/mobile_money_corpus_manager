import csv, io, logging, secrets, subprocess, tempfile, time, hashlib, uuid, wave
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .config import settings
from .db import Base, engine, get_db, SessionLocal
from .models import User, Participant, Utterance, Recording, Transcription, TranscriptionHistory, AuditLog, RecordingSubmission, Workshop, WorkshopCode
from .take_sequence import next_take_estimate, TakeLimitReached
from .recording_submission import reserve as reserve_recording, finish as finish_recording, mark_error as mark_recording_error, result as submission_result
from .auth import verify_password, hash_password, create_token, get_current_user
from .storage import ensure_bucket, check_ready, put_file, get_bytes, delete_file, stat_file, list_files, verify_file, stream_file as stream_storage_file
from .seed import seed
from .corpus_export import build_export, parse_filters, stream_file
from .participant_registration import RegistrationError, next_participant_number, register_participant, validate_password, workshop_code_hash, format_login_id
from .languages import LANGUAGE_BY_CODE, LANGUAGES, language_name
from .rate_limit import login_limiter, registration_limiter, workshop_language_limiter
from .time_utils import as_utc_naive, utc_now
from .schema_guard import SchemaRevisionError, assert_schema_current
from .workshops import require_active_participant_workshop, workshop_is_open
from .audio_processing import (
    ConversionSaturated,
    run_audio_command as _run_audio_command,
    operation_id,
    audio_error,
    compensate_uploaded as _compensate_uploaded,
    CONVERSION_SLOTS as _default_conversion_slots,
)
from .audit import audit, new_csrf_token, check_csrf, set_csrf_cookie
from .write_freeze import WriteFreezeMiddleware

logger = logging.getLogger("mobile_money_corpus_manager")
ALLOWED_AUDIO_TYPES = {"audio/webm", "audio/ogg", "audio/wav", "audio/x-wav", "audio/mp4", "audio/mpeg"}
ALLOWED_CONDITIONS = {"CLEAN", "NOISY"}
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100
CONVERSION_SLOTS = _default_conversion_slots


def run_audio_command(args, **kwargs):
    """Compatibility seam for route tests while delegating to the audio service."""
    return _run_audio_command(args, slots=CONVERSION_SLOTS, **kwargs)


def compensate_uploaded(uploaded, request):
    """Delegate compensation while retaining the main-module storage seam."""
    return _compensate_uploaded(uploaded, request, delete=delete_file)


app = FastAPI(title="Mobile Money Corpus Manager")
app.add_middleware(WriteFreezeMiddleware)


class SecurityHeadersMiddleware:
    async def __call__(self, scope, receive, send):
        nonce = secrets.token_urlsafe(16)
        scope.setdefault("state", {})["csp_nonce"] = nonce

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                security = {
                    "content-security-policy": f"default-src 'self'; script-src 'self' 'nonce-{nonce}'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'",
                    "x-content-type-options": "nosniff",
                    "referrer-policy": "strict-origin-when-cross-origin",
                    "permissions-policy": "microphone=(self)",
                    "x-frame-options": "DENY",
                }
                if settings.cookie_secure:
                    security["strict-transport-security"] = "max-age=31536000; includeSubDomains"
                existing = {key.decode().lower() for key, _ in headers}
                headers.extend((key.encode(), value.encode()) for key, value in security.items() if key not in existing)
                message = {**message, "headers": headers}
            await send(message)
        await self.app(scope, receive, send_with_headers)

    def __init__(self, app):
        self.app = app


app.add_middleware(SecurityHeadersMiddleware)
_trusted_hosts = [host.strip() for host in settings.trusted_hosts.split(",") if host.strip()]
if settings.app_env == "production" and _trusted_hosts == ["*"]:
    _trusted_hosts = [settings.app_host]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=_trusted_hosts or [settings.app_host])
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def render_template(name, context, **kwargs):
    """Render templates using Starlette's keyword-only request contract."""
    return templates.TemplateResponse(
        request=context["request"], name=name, context=context, **kwargs
    )

@app.on_event("startup")
def startup():
    for _ in range(20):
        try:

            with SessionLocal() as db:
                assert_schema_current(db)
            ensure_bucket()
            with SessionLocal() as db:
                seed(db)
            return
        except SchemaRevisionError:
            logger.error("Startup refused: database schema revision is not current")
            raise
        except Exception as exc:
            logger.exception("Startup initialization attempt %s/20 failed: %s", _ + 1, exc)
            time.sleep(2)
    raise RuntimeError("Initialization failed")

def current(request: Request, db: Session):
    try:
        return get_current_user(request, db)
    except HTTPException:
        return None

def require(request: Request, db: Session, roles=None):
    user = get_current_user(request, db)
    if roles and user.role not in roles:
        raise HTTPException(403)
    return user

@app.get("/health")
def health():
    """Liveness probe: the process is serving requests."""
    return {"status": "ok"}


@app.get("/ready")
def readiness(db: Session = Depends(get_db)):
    """Readiness probe: all mandatory persistence dependencies are reachable."""
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        if not check_ready():
            raise RuntimeError("MinIO bucket is not ready")
        return {"status": "ready"}
    except Exception:
        logger.exception("Readiness check failed")
        raise HTTPException(503, "Service indisponible")

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    token = new_csrf_token()
    response = render_template("login.html", {"request":request, "csrf_token":token})
    set_csrf_cookie(response, token)
    return response

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), csrf_token: str = Form(""), db: Session = Depends(get_db)):
    check_csrf(request, csrf_token)
    login_scope = f"login:{username.casefold()}"
    login_limiter.check(request, login_scope, db=db, record=False)
    user = db.query(User).filter_by(username=username).first()
    if not user:
        participant = db.query(Participant).filter_by(participant_code=username).one_or_none()
        user = participant.user if participant else None
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        login_limiter.record(request, login_scope, db=db)
        return render_template("login.html", {"request":request,"error":"Identifiants incorrects", "csrf_token":csrf_token}, status_code=401)
    token = create_token(user)
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie("session", token, httponly=True, samesite="strict", secure=settings.cookie_secure, max_age=settings.access_token_minutes * 60)
    set_csrf_cookie(resp, csrf_token)
    audit(db,user,"LOGIN","user",user.id)
    return resp


@app.get("/participant/register", response_class=HTMLResponse)
def participant_registration_page(request: Request):
    token = new_csrf_token()
    response = render_template("participant_register.html", {"request": request, "csrf_token": token})
    set_csrf_cookie(response, token)
    return response


@app.get("/api/auth/workshop-language")
def public_workshop_language(request: Request, code: str, db: Session = Depends(get_db)):
    """Expose only the registration-relevant language for a valid workshop code."""
    normalized_code = code.strip() if isinstance(code, str) else ""
    workshop_language_limiter.check(request, "workshop-language", db=db)
    if not normalized_code or len(normalized_code) > 128:
        raise HTTPException(400, "Code d’atelier incorrect ou indisponible.")
    code_record = db.query(WorkshopCode).filter(
        WorkshopCode.code_hash == workshop_code_hash(normalized_code)
    ).one_or_none()
    now = utc_now()
    workshop = code_record.workshop if code_record else None
    unavailable = (
        code_record is None or workshop is None
        or not code_record.is_active or not workshop.is_active
        or (workshop.starts_at is not None and now < workshop.starts_at)
        or (workshop.ends_at is not None and now >= workshop.ends_at)
        or (code_record.starts_at is not None and now < code_record.starts_at)
        or (code_record.expires_at is not None and now >= code_record.expires_at)
        or (code_record.max_registrations is not None and code_record.use_count >= code_record.max_registrations)
        or (workshop.capacity is not None and len(workshop.participants) >= workshop.capacity)
    )
    if unavailable:
        raise HTTPException(400, "Code d’atelier incorrect ou indisponible.")
    language_code = (workshop.language_code or "").upper()
    if language_code not in LANGUAGE_BY_CODE:
        raise HTTPException(400, "Code d’atelier incorrect ou indisponible.")
    return {"language_code": language_code, "language_name": language_name(language_code)}


@app.post("/api/auth/participant-registration")
async def participant_registration_api(request: Request, db: Session = Depends(get_db)):
    check_csrf(request)
    registration_limiter.check(request, "participant-registration", db=db)
    try:
        if int(request.headers.get("content-length", "0")) > 8192:
            raise HTTPException(413, "Requête d'inscription trop volumineuse.")
    except ValueError:
        raise HTTPException(400, "Requête d'inscription invalide.")
    try:
        content_length = request.headers.get("content-length")
        if content_length is not None and int(content_length) > 8192:
            raise HTTPException(413, "Requête d'inscription trop volumineuse.")
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 8192:
                raise HTTPException(413, "Requête d'inscription trop volumineuse.")
        import json
        payload = json.loads(bytes(body))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(400, "Requête d'inscription invalide.")
    try:
        result = register_participant(db, payload)
    except RegistrationError as exc:
        raise HTTPException(400, str(exc))
    except SQLAlchemyError:
        correlation_id = operation_id(request)
        logger.exception("Participant registration infrastructure failure", extra={"operation_id": correlation_id})
        db.rollback()
        return JSONResponse(
            {"detail": "Le service d’inscription est temporairement indisponible.", "operation_id": correlation_id},
            status_code=503,
            headers={"X-Operation-ID": correlation_id},
        )
    return {
        "login_id": result.login_id,
        "role": "participant",
        "message": "Compte participant créé avec succès.",
    }

@app.post("/logout")
def logout(request: Request, csrf_token: str = Form("")):
    check_csrf(request, csrf_token)
    resp=RedirectResponse("/login",303)
    resp.delete_cookie("session")
    return resp

@app.get("/help", response_class=HTMLResponse)
def participant_help(request: Request, db: Session = Depends(get_db)):
    user = require(request, db, ["PARTICIPANT"])
    return render_template("participant_help.html", {"request": request, "user": user})

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = current(request,db)
    if not user: return RedirectResponse("/login",303)
    if user.role == "PARTICIPANT":
        participant = db.get(Participant, user.participant_id)
        if not participant:
            return render_template("message.html", {"request": request, "user": user,
                "message": "Votre compte participant n’est pas disponible. Contactez l’équipe."}, status_code=403)
        recordings_count = db.query(Recording).filter(
            Recording.participant_id == participant.id, Recording.sync_status == "READY"
        ).count()
        workshop_open = bool(participant.workshop and workshop_is_open(participant.workshop))
        return render_template("dashboard.html", {"request": request, "user": user,
            "participant": participant, "participant_recordings": recordings_count,
            "workshop_open": workshop_open})
    qrec = db.query(Recording).filter(Recording.sync_status == "READY")
    if user.role=="PARTICIPANT" and user.participant_id:
        qrec=qrec.filter(Recording.participant_id==user.participant_id)
    stats = {
        "participants": db.query(Participant).count(),
        "recordings": qrec.count(),
        "transcribed": qrec.filter(Recording.status.in_(["TRANSCRIBED","VERIFIED"])).count(),
        "verified": qrec.filter(Recording.status=="VERIFIED").count(),
    }
    latest=qrec.order_by(Recording.created_at.desc()).limit(10).all()
    return render_template("dashboard.html", {"request":request,"user":user,"stats":stats,"latest":latest})

@app.get("/participants", response_class=HTMLResponse)
def participants(request: Request, db: Session = Depends(get_db)):
    user=require(request,db,["ADMIN"])
    workshop_id = request.query_params.get("workshop_id")
    query = db.query(Participant).order_by(Participant.participant_code)
    if workshop_id:
        try: query = query.filter(Participant.workshop_id == int(workshop_id))
        except ValueError: raise HTTPException(400, "Atelier invalide")
    items=query.all()
    workshops=db.query(Workshop).order_by(Workshop.name).all()
    return render_template("participants.html", {"request":request,"user":user,"items":items,"workshops":workshops,"selected_workshop_id":workshop_id})

@app.post("/participants")
def create_participant(
    request: Request,
    participant_code: str=Form(""), username: str=Form(""), password: str=Form(...), csrf_token: str=Form(...),
    language: str=Form("mos"), age_group: str=Form(""), gender: str=Form(""),
    region: str=Form(""), consent_obtained: bool=Form(False), workshop_id: int | None=Form(None),
    db: Session=Depends(get_db)
):
    admin=require(request,db,["ADMIN"])
    check_csrf(request, csrf_token)
    workshop = db.get(Workshop, workshop_id) if workshop_id else db.query(Workshop).filter(
        Workshop.is_active.is_(True), Workshop.language_code.in_(tuple(LANGUAGE_BY_CODE))
    ).order_by(Workshop.id).first()
    if not workshop or not workshop_is_open(workshop): raise HTTPException(400,"Atelier invalide ou fermé")
    if not workshop.language_code or workshop.language_code not in LANGUAGE_BY_CODE:
        raise HTTPException(400, "La langue de l’atelier doit être attribuée avant de créer un participant")
    generated_code = format_login_id(next_participant_number(db, workshop.language_code), workshop.language_code)
    p=Participant(workshop_id=workshop.id, participant_code=generated_code,language=workshop.language_code.lower(),language_code=workshop.language_code,age_group=age_group or None,
                  gender=gender or None,region=region or None,consent_obtained=consent_obtained)
    db.add(p); db.flush()
    login_username = username.strip() or generated_code
    if db.query(User).filter_by(username=login_username).first():
        db.rollback()
        raise HTTPException(400, "Identifiant déjà utilisé")
    u=User(username=login_username,password_hash=hash_password(password),role="PARTICIPANT",participant_id=p.id)
    db.add(u); db.commit()
    audit(db,admin,"CREATE_PARTICIPANT","participant",p.id,generated_code)
    return RedirectResponse("/participants",303)


@app.post("/participants/{participant_id}/account-status")
def set_participant_account_status(participant_id: int, request: Request, active: bool = Form(...), csrf_token: str = Form(...), db: Session = Depends(get_db)):
    admin = require(request, db, ["ADMIN"])
    check_csrf(request, csrf_token)
    participant = db.get(Participant, participant_id)
    if not participant or not participant.user:
        raise HTTPException(404)
    participant.user.is_active = active
    db.commit()
    audit(db, admin, "SET_PARTICIPANT_ACCOUNT_STATUS", "user", participant.user.id, f"active={active}")
    return RedirectResponse("/participants", 303)


@app.post("/participants/{participant_id}/reset-password")
def reset_participant_password(participant_id: int, request: Request, password: str = Form(...), password_confirmation: str = Form(...), csrf_token: str = Form(...), db: Session = Depends(get_db)):
    admin = require(request, db, ["ADMIN"])
    check_csrf(request, csrf_token)
    participant = db.get(Participant, participant_id)
    if not participant or not participant.user:
        raise HTTPException(404)
    try:
        new_password = validate_password(password, password_confirmation)
    except RegistrationError as exc:
        raise HTTPException(400, str(exc))
    participant.user.password_hash = hash_password(new_password)
    db.commit()
    audit(db, admin, "RESET_PARTICIPANT_PASSWORD", "user", participant.user.id)
    return RedirectResponse("/participants", 303)

@app.get("/record", response_class=HTMLResponse)
def record_page(request: Request, db: Session=Depends(get_db)):
    user=require(request,db,["PARTICIPANT","ADMIN"])
    if user.role=="PARTICIPANT":
        participant=db.get(Participant,user.participant_id)
        if not participant or not participant.consent_obtained:
            return render_template("message.html",{"request":request,"user":user,"message":"Consentement non enregistré. Contactez l'administrateur."},status_code=403)
        if not participant.workshop or not workshop_is_open(participant.workshop):
            return render_template("message.html",{"request":request,"user":user,"message":"Cet atelier est terminé. Aucun nouvel enregistrement n’est possible."},status_code=403)
    else:
        participant=None
    utterances=db.query(Utterance).filter_by(active=True).order_by(Utterance.utterance_code).all()
    participants=db.query(Participant).order_by(Participant.participant_code).all() if user.role=="ADMIN" else []
    template = "participant_record.html" if user.role == "PARTICIPANT" else "record.html"
    requested_utterance_id = request.query_params.get("utterance_id")
    selected_utterance_id = utterances[0].id if utterances else None
    phrase_number = 1
    if participant and utterances:
        requested_id = int(requested_utterance_id) if requested_utterance_id and requested_utterance_id.isdigit() else None
        if requested_id in {u.id for u in utterances}:
            selected_utterance_id = requested_id
        phrase_number = next((i + 1 for i, u in enumerate(utterances) if u.id == selected_utterance_id), 1)
    next_utterance_id = None
    if utterances:
        current_index = next((i for i, u in enumerate(utterances) if u.id == selected_utterance_id), 0)
        next_utterance_id = utterances[(current_index + 1) % len(utterances)].id
    return render_template(template,{"request":request,"user":user,"participant":participant,"participants":participants,
        "utterances":utterances,"selected_utterance_id":selected_utterance_id,"phrase_number":phrase_number,
        "next_utterance_id":next_utterance_id})

def recording_context(db, user, participant_id, utterance_id, condition):
    if user.role == "PARTICIPANT":
        require_active_participant_workshop(db, user)
    pid = user.participant_id if user.role == "PARTICIPANT" else participant_id
    if user.role == "PARTICIPANT" and participant_id is not None and participant_id != pid:
        raise HTTPException(403, "Participant non autorisé")
    if not pid: raise HTTPException(400, "participant requis")
    participant, utterance = db.get(Participant, pid), db.get(Utterance, utterance_id)
    if not participant or not utterance: raise HTTPException(404)
    if not participant.consent_obtained: raise HTTPException(403, "consentement absent")
    if not utterance.active: raise HTTPException(400, "scénario inactif")
    if condition not in ALLOWED_CONDITIONS: raise HTTPException(400, "condition invalide")
    return participant, utterance


@app.get("/api/recordings/next-take")
def preview_take(request: Request, utterance_id: int, condition: str = "CLEAN",
                 participant_id: int | None = None, db: Session = Depends(get_db)):
    user = require(request, db, ["PARTICIPANT", "ADMIN"])
    participant, utterance = recording_context(db, user, participant_id, utterance_id, condition)
    try:
        return {"next_take_number": next_take_estimate(db, participant.id, utterance.id, condition), "reserved": False}
    except TakeLimitReached as exc:
        raise HTTPException(409, str(exc))


@app.post("/api/recordings")
def upload_recording(
    request: Request, utterance_id: int = Form(...), condition: str = Form("CLEAN"),
    participant_id: int | None = Form(None), idempotency_key: str = Form(...),
    take_number: str | None = Form(None), audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = require(request, db, ["PARTICIPANT", "ADMIN"])
    check_csrf(request)
    if take_number is not None:
        raise HTTPException(400, "take_number est attribué par le serveur ; retirez ce champ.")
    if not 16 <= len(idempotency_key) <= 128 or not all(c.isascii() and (c.isalnum() or c in "-_") for c in idempotency_key):
        raise HTTPException(400, "Clé d’idempotence invalide")
    participant, utterance = recording_context(db, user, participant_id, utterance_id, condition)
    content_type = (audio.content_type or "").split(";", 1)[0].lower()
    if content_type not in ALLOWED_AUDIO_TYPES: raise HTTPException(415, "format audio non accepté")
    suffix = {"audio/webm": ".webm", "audio/ogg": ".ogg", "audio/wav": ".wav",
              "audio/x-wav": ".wav", "audio/mp4": ".mp4", "audio/mpeg": ".mp3"}[content_type]
    # Snapshot authorization data; no transaction spans reading/converting/uploading.
    uid = user.id
    db.expunge(participant); db.expunge(utterance); db.rollback()
    with tempfile.TemporaryDirectory() as td:
        raw, wav = Path(td) / ("source" + suffix), Path(td) / "audio.wav"
        size, digest = 0, hashlib.sha256()
        with raw.open("wb") as target:
            while chunk := audio.file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.max_audio_mb * 1024 * 1024:
                    raise HTTPException(413, "Fichier audio trop volumineux")
                digest.update(chunk); target.write(chunk)
        if not size: raise HTTPException(400, "fichier audio vide")
        raw_sha = digest.hexdigest()
        fingerprint = hashlib.sha256(f"{participant.id}:{participant.workshop_id}:{utterance.id}:{condition}:{content_type}:{raw_sha}".encode()).hexdigest()
        try:
            receipt, created = reserve_recording(db, uid, participant, utterance, condition, idempotency_key, fingerprint, suffix)
        except TakeLimitReached as exc:
            db.rollback()
            raise HTTPException(409, str(exc))
        except HTTPException:
            raise
        except Exception:
            db.rollback()
            logger.error("Recording reservation failed")
            raise HTTPException(503, "Réservation indisponible ; réessayez avec la même clé.")
        if not created:
            return submission_result(receipt)
        rec = db.get(Recording, receipt.recording_id)
        raw_obj, wav_obj = rec.raw_object, rec.wav_object
        db.rollback()
        attempted = []
        try:
            try:
                run_audio_command(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)], check=True, timeout=settings.ffmpeg_timeout_seconds, capture_output=True)
                with wave.open(str(wav), "rb") as normalized:
                    if (normalized.getnchannels(), normalized.getsampwidth(), normalized.getframerate()) != (1, 2, 16000) or normalized.getnframes() <= 0:
                        raise ValueError("invalid normalized WAV")
                probe = run_audio_command(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(wav)], capture_output=True, text=True, check=True, timeout=settings.ffprobe_timeout_seconds)
                duration_ms = int(float(probe.stdout.strip()) * 1000)
                if not settings.min_audio_duration_seconds * 1000 <= duration_ms <= settings.max_audio_duration_seconds * 1000:
                    raise ValueError("invalid duration")
            except ConversionSaturated:
                raise HTTPException(429, "Le traitement audio est saturé ; cette réservation est en erreur.")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, wave.Error, OSError, EOFError, ValueError):
                raise HTTPException(422, "audio illisible, durée invalide ou conversion trop longue")
            wav_data = wav.read_bytes()
            wav_sha, wav_size = hashlib.sha256(wav_data).hexdigest(), len(wav_data)
            # Record attempted keys BEFORE PUT: a timeout may occur after the server stored it.
            attempted.append(raw_obj); put_file(raw_obj, str(raw), content_type)
            attempted.append(wav_obj); put_file(wav_obj, str(wav), "audio/wav")
            verify_file(raw_obj, size, raw_sha)
            verify_file(wav_obj, wav_size, wav_sha)
            receipt = finish_recording(db, receipt.id, {
                "duration_ms": duration_ms, "raw_size_bytes": size, "wav_size_bytes": wav_size,
                "raw_sha256": raw_sha, "wav_sha256": wav_sha,
            })
            return submission_result(receipt)
        except Exception as exc:
            status = exc.status_code if isinstance(exc, HTTPException) else 502
            detail = exc.detail if isinstance(exc, HTTPException) else "Enregistrement audio temporairement indisponible"
            try:
                receipt = mark_recording_error(db, receipt.id, status, detail)
            except Exception:
                db.rollback()
                # Outcome unknown: never delete objects that a committed READY row may own.
                logger.error("Recording outcome unknown; reconciliation required", extra={"operation_id": receipt.id})
                raise HTTPException(503, "État de finalisation indéterminé ; réessayez avec la même clé.")
            if receipt.state == "READY":
                return submission_result(receipt)
            compensate_uploaded(attempted, request)
            return submission_result(receipt)

@app.get("/recordings", response_class=HTMLResponse)
def recordings_page(request: Request, db: Session=Depends(get_db)):
    user=require(request,db,["ADMIN","PARTICIPANT","TRANSCRIBER","VALIDATOR"])
    q=db.query(Recording).filter(Recording.sync_status == "READY")
    try:
        page = max(1, int(request.query_params.get("page", "1")))
        page_size = min(MAX_PAGE_SIZE, max(1, int(request.query_params.get("page_size", str(DEFAULT_PAGE_SIZE)))))
    except ValueError:
        raise HTTPException(400, "Pagination invalide")
    if user.role == "TRANSCRIBER":
        active_filter = request.query_params.get("filter", "todo")
        if active_filter not in {"todo", "transcribed", "all"}:
            active_filter = "todo"
        if active_filter == "todo":
            q = q.filter(~db.query(Transcription.id).filter(Transcription.recording_id == Recording.id).exists())
        elif active_filter == "transcribed":
            q = q.filter(db.query(Transcription.id).filter(Transcription.recording_id == Recording.id).exists())
        counts = {
            "todo": db.query(Recording).filter(Recording.sync_status == "READY").filter(~db.query(Transcription.id).filter(Transcription.recording_id == Recording.id).exists()).count(),
            "transcribed": db.query(Recording).filter(Recording.sync_status == "READY").filter(db.query(Transcription.id).filter(Transcription.recording_id == Recording.id).exists()).count(),
            "all": db.query(Recording).filter(Recording.sync_status == "READY").count(),
        }
        total = counts[active_filter]
        items = q.options(
            joinedload(Recording.participant), joinedload(Recording.utterance),
            joinedload(Recording.transcription)
        ).order_by(Recording.created_at.desc(), Recording.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        visible = items
        selected_raw = request.query_params.get("selected")
        selected_id = int(selected_raw) if selected_raw and selected_raw.isdigit() else None
        selected = next((r for r in visible if r.id == selected_id), visible[0] if visible else None)
        payload = [{
            "id": r.id, "audio_id": r.audio_id, "participant": r.participant.participant_code,
            "intent": r.utterance.intent, "utterance_code": r.utterance.utterance_code,
            "scenario": r.utterance.scenario_fr, "condition": r.condition,
            "take_number": r.take_number, "duration_ms": r.duration_ms or 0,
            "created_at": r.created_at.strftime("%d/%m/%Y à %H:%M"),
            "status": r.status, "has_transcription": r.transcription is not None,
            "verification_status": r.transcription.verification_status if r.transcription else "",
            "reference_transcription": r.transcription.reference_transcription if r.transcription else "",
            "normalized_transcription": r.transcription.normalized_transcription if r.transcription else "",
            "version": r.transcription.version if r.transcription else 0,
            "can_edit": r.status != "VERIFIED",
        } for r in visible]
        return render_template("transcriber_workspace.html", {
            "request": request, "user": user, "items": items, "visible": visible,
            "selected": selected, "payload": payload, "counts": {
            }, "active_filter": active_filter, "saved": request.query_params.get("saved") == "1",
            "page": page, "page_size": page_size, "total": total,
        })
    if user.role=="PARTICIPANT":
        q=q.filter(Recording.participant_id==user.participant_id)
    workshop_id = request.query_params.get("workshop_id")
    if user.role=="ADMIN" and workshop_id:
        try: q=q.filter(Recording.workshop_id == int(workshop_id))
        except ValueError: raise HTTPException(400,"Atelier invalide")
    total = q.count()
    items=q.options(joinedload(Recording.participant), joinedload(Recording.utterance)).order_by(Recording.created_at.desc(), Recording.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    workshops=db.query(Workshop).order_by(Workshop.name).all() if user.role=="ADMIN" else []
    template = "participant_recordings.html" if user.role == "PARTICIPANT" else "recordings.html"
    return render_template(template,{"request":request,"user":user,"items":items,"workshops":workshops,"selected_workshop_id":workshop_id,"page":page,"page_size":page_size,"total":total})

@app.get("/audio/{recording_id}")
def audio(recording_id:int, request:Request, db:Session=Depends(get_db)):
    user=require(request,db,["ADMIN","PARTICIPANT","TRANSCRIBER","VALIDATOR"])
    rec=db.get(Recording,recording_id)
    if not rec: raise HTTPException(404)
    if rec.sync_status != "READY": raise HTTPException(409, "Audio non finalisé")
    if user.role=="PARTICIPANT" and rec.participant_id!=user.participant_id:
        raise HTTPException(403)
    try:
        info = stat_file(rec.wav_object)
    except Exception:
        raise HTTPException(502, "Audio temporairement indisponible")
    size = int(info.size)
    content_type = getattr(info, "content_type", None) or "audio/wav"
    headers = {"Accept-Ranges": "bytes", "Content-Length": str(size)}
    range_header = request.headers.get("range")
    if not range_header:
        return StreamingResponse(stream_storage_file(rec.wav_object), media_type=content_type, headers=headers)
    if not range_header.startswith("bytes=") or "," in range_header:
        return Response(status_code=416, headers={"Accept-Ranges": "bytes", "Content-Range": f"bytes */{size}"})
    value = range_header[6:].strip()
    try:
        start_text, end_text = value.split("-", 1)
        if not start_text:
            suffix = int(end_text)
            if suffix <= 0: raise ValueError
            start, end = max(0, size - suffix), size - 1
        else:
            start = int(start_text)
            end = int(end_text) if end_text else size - 1
            end = min(end, size - 1)
        if start < 0 or start >= size or end < start:
            raise ValueError
    except ValueError:
        return Response(status_code=416, headers={"Accept-Ranges": "bytes", "Content-Range": f"bytes */{size}"})
    length = end - start + 1
    headers.update({"Content-Length": str(length), "Content-Range": f"bytes {start}-{end}/{size}"})
    return StreamingResponse(stream_storage_file(rec.wav_object, offset=start, length=length), status_code=206, media_type=content_type, headers=headers)

@app.get("/transcribe/{recording_id}", response_class=HTMLResponse)
def transcribe_page(recording_id:int, request:Request, db:Session=Depends(get_db)):
    user=require(request,db,["ADMIN","PARTICIPANT","TRANSCRIBER","VALIDATOR"])
    rec=db.get(Recording,recording_id)
    if not rec: raise HTTPException(404)
    if rec.sync_status != "READY": raise HTTPException(409, "Audio non finalisé")
    if user.role=="PARTICIPANT" and rec.participant_id!=user.participant_id:
        raise HTTPException(403)
    return render_template("transcribe.html",{"request":request,"user":user,"rec":rec})

@app.post("/transcribe/{recording_id}")
def save_transcription(
    recording_id:int, request:Request,
    reference_transcription:str=Form(...),
    normalized_transcription:str=Form(""), return_filter:str=Form(""), version:int | None=Form(None), csrf_token:str=Form(""),
    db:Session=Depends(get_db)
):
    user=require(request,db,["ADMIN","PARTICIPANT","TRANSCRIBER"])
    check_csrf(request, csrf_token)
    rec=db.get(Recording,recording_id)
    if not rec: raise HTTPException(404)
    if user.role=="PARTICIPANT" and rec.participant_id!=user.participant_id:
        raise HTTPException(403)
    if user.role == "PARTICIPANT": require_active_participant_workshop(db, user)
    if rec.status == "VERIFIED" and user.role != "ADMIN":
        raise HTTPException(409,"Une transcription validée doit être rouverte par un administrateur")
    if rec.sync_status != "READY": raise HTTPException(409, "Audio non finalisé")
    tr=rec.transcription
    if tr:
        expected_version = tr.version if version is None else version
        previous = {"reference": tr.reference_transcription, "normalized": tr.normalized_transcription,
                    "status": tr.verification_status, "version": tr.version}
        new_version = expected_version + 1
        result = db.execute(update(Transcription).where(
            Transcription.id == tr.id, Transcription.version == expected_version
        ).values(reference_transcription=reference_transcription,
                 normalized_transcription=normalized_transcription or None,
                 transcriber_id=user.id, verification_status="PENDING",
                 version=new_version, updated_at=utc_now()))
        if result.rowcount != 1:
            db.rollback()
            current_tr = db.get(Transcription, tr.id)
            return JSONResponse({"detail": "Cette transcription a été modifiée par un autre utilisateur.",
                                 "version": current_tr.version if current_tr else None,
                                 "current": {"reference_transcription": current_tr.reference_transcription if current_tr else "",
                                              "normalized_transcription": current_tr.normalized_transcription if current_tr else ""}}, status_code=409)
        db.add(TranscriptionHistory(transcription_id=tr.id, author_id=user.id, action="EDIT",
            old_reference_transcription=previous["reference"], new_reference_transcription=reference_transcription,
            old_normalized_transcription=previous["normalized"], new_normalized_transcription=normalized_transcription or None,
            old_verification_status=previous["status"], new_verification_status="PENDING",
            previous_version=previous["version"], new_version=new_version))
    else:
        if version not in (None, 0):
            raise HTTPException(409, "La version de cette transcription n’est plus actuelle")
        tr=Transcription(recording_id=rec.id,reference_transcription=reference_transcription,
                         normalized_transcription=normalized_transcription or None,transcriber_id=user.id,version=1)
        db.add(tr)
        db.flush()
        db.add(TranscriptionHistory(transcription_id=tr.id, author_id=user.id, action="CREATE",
            new_reference_transcription=reference_transcription, new_normalized_transcription=normalized_transcription or None,
            new_verification_status="PENDING", previous_version=0, new_version=1))
    saved_recording_id = rec.id
    rec.status="TRANSCRIBED"
    db.commit()
    audit(db,user,"SAVE_TRANSCRIPTION","recording",saved_recording_id)
    if user.role == "TRANSCRIBER":
        next_recording = db.query(Recording).options(joinedload(Recording.transcription)).filter(
            Recording.sync_status == "READY", Recording.transcription == None, Recording.id != rec.id
        ).order_by(Recording.created_at.desc()).first()
        if next_recording:
            return RedirectResponse(f"/recordings?filter=todo&selected={next_recording.id}&saved=1",303)
        return RedirectResponse(f"/recordings?filter=transcribed&selected={rec.id}&saved=1",303)
    return RedirectResponse("/recordings",303)


@app.get("/api/transcriptions/{transcription_id}/history")
def transcription_history(transcription_id: int, request: Request, db: Session = Depends(get_db)):
    user = require(request, db, ["ADMIN", "PARTICIPANT", "TRANSCRIBER", "VALIDATOR"])
    transcription = db.get(Transcription, transcription_id)
    if not transcription:
        raise HTTPException(404)
    if user.role == "PARTICIPANT" and transcription.recording.participant_id != user.participant_id:
        raise HTTPException(403)
    rows = db.query(TranscriptionHistory).filter_by(transcription_id=transcription_id).order_by(TranscriptionHistory.id).all()
    return {"transcription_id": transcription_id, "current_version": transcription.version, "history": [
        {"id": row.id, "action": row.action, "author_id": row.author_id,
         "old_reference_transcription": row.old_reference_transcription,
         "new_reference_transcription": row.new_reference_transcription,
         "old_normalized_transcription": row.old_normalized_transcription,
         "new_normalized_transcription": row.new_normalized_transcription,
         "old_verification_status": row.old_verification_status,
         "new_verification_status": row.new_verification_status,
         "previous_version": row.previous_version, "new_version": row.new_version,
         "changed_at": row.changed_at.isoformat() if row.changed_at else None}
        for row in rows
    ]}

@app.post("/verify/{recording_id}")
def verify(
    recording_id:int, request:Request, decision:str=Form(...), comment:str=Form(""), csrf_token:str=Form(...),
    db:Session=Depends(get_db), version:int | None=Form(None)
):
    user=require(request,db,["ADMIN","VALIDATOR"])
    check_csrf(request, csrf_token)
    if decision not in {"VERIFIED", "NEEDS_REVIEW", "REJECTED"}:
        raise HTTPException(400, "Décision de vérification invalide")
    rec=db.get(Recording,recording_id)
    if not rec or not rec.transcription: raise HTTPException(404)
    if rec.sync_status != "READY": raise HTTPException(409, "Audio non finalisé")
    tr = rec.transcription
    if not isinstance(version, int):
        version = None
    expected_version = getattr(tr, "version", 1) if version is None else version
    previous = {"reference": getattr(tr, "reference_transcription", None),
                "normalized": getattr(tr, "normalized_transcription", None),
                "status": tr.verification_status, "version": getattr(tr, "version", 1)}
    if decision=="VERIFIED":
        new_status="VERIFIED"
        rec.status="VERIFIED"
    elif decision=="NEEDS_REVIEW":
        new_status="NEEDS_REVIEW"
        rec.status="NEEDS_REVIEW"
    else:
        new_status="REJECTED"
        rec.status="REJECTED"
    if not hasattr(tr, "id"):
        tr.verifier_id = user.id
        tr.verifier_comment = comment or None
        tr.verification_status = new_status
        db.commit()
        audit(db,user,"VERIFY_TRANSCRIPTION","recording",rec.id,decision)
        return RedirectResponse(f"/transcribe/{recording_id}",303)
    result = db.execute(update(Transcription).where(
        Transcription.id == tr.id, Transcription.version == expected_version
    ).values(verifier_id=user.id, verifier_comment=comment or None,
             verification_status=new_status, version=expected_version + 1,
             updated_at=utc_now()))
    if not hasattr(result, "rowcount"):
        tr.verifier_id = user.id
        tr.verifier_comment = comment or None
        tr.verification_status = new_status
        db.commit()
        audit(db,user,"VERIFY_TRANSCRIPTION","recording",rec.id,decision)
        return RedirectResponse(f"/transcribe/{recording_id}",303)
    if result.rowcount != 1:
        db.rollback()
        current_tr = db.get(Transcription, tr.id)
        return JSONResponse({"detail": "Cette transcription a été modifiée par un autre utilisateur.",
                             "version": current_tr.version if current_tr else None}, status_code=409)
    db.add(TranscriptionHistory(transcription_id=tr.id, author_id=user.id, action="VERIFY",
        old_reference_transcription=previous["reference"], new_reference_transcription=previous["reference"],
        old_normalized_transcription=previous["normalized"], new_normalized_transcription=previous["normalized"],
        old_verification_status=previous["status"], new_verification_status=new_status,
        previous_version=previous["version"], new_version=expected_version + 1))
    db.commit()
    audit(db,user,"VERIFY_TRANSCRIPTION","recording",rec.id,decision)
    return RedirectResponse(f"/transcribe/{recording_id}",303)

@app.get("/users", response_class=HTMLResponse)
def users_page(request:Request, db:Session=Depends(get_db)):
    user=require(request,db,["ADMIN"])
    items=db.query(User).order_by(User.username).all()
    return render_template("users.html",{"request":request,"user":user,"items":items})

@app.post("/users")
def create_user(request:Request,username:str=Form(...),password:str=Form(...),role:str=Form(...),csrf_token:str=Form(...),db:Session=Depends(get_db)):
    admin=require(request,db,["ADMIN"])
    check_csrf(request, csrf_token)
    if role not in ["ADMIN","TRANSCRIBER","VALIDATOR"]: raise HTTPException(400)
    if db.query(User).filter_by(username=username).first(): raise HTTPException(400,"username déjà utilisé")
    u=User(username=username,password_hash=hash_password(password),role=role)
    db.add(u);db.commit()
    audit(db,admin,"CREATE_USER","user",u.id,role)
    return RedirectResponse("/users",303)


def parse_optional_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return as_utc_naive(datetime.fromisoformat(value))
    except ValueError as exc:
        raise HTTPException(400, "Date d'atelier invalide.") from exc


@app.get("/admin/workshop-codes", response_class=HTMLResponse)
def workshop_codes_page(request: Request, db: Session = Depends(get_db)):
    user = require(request, db, ["ADMIN"])
    items = db.query(WorkshopCode).order_by(WorkshopCode.created_at.desc()).all()
    workshops = db.query(Workshop).order_by(Workshop.name).all()
    return render_template("workshop_codes.html", {"request": request, "user": user, "items": items, "workshops": workshops, "languages": LANGUAGES, "language_name": language_name})


@app.post("/admin/workshop-codes", response_class=HTMLResponse)
def create_workshop_code(request: Request, label: str = Form(...), language_code: str = Form(...), starts_at: str = Form(""), expires_at: str = Form(""), max_registrations: str = Form(""), workshop_id: str = Form(""), csrf_token: str = Form(...), db: Session = Depends(get_db)):
    admin = require(request, db, ["ADMIN"])
    check_csrf(request, csrf_token)
    label = label.strip()
    if not label or len(label) > 120:
        raise HTTPException(400, "Libellé invalide.")
    language_code = language_code.strip().upper()
    if language_code not in LANGUAGE_BY_CODE:
        raise HTTPException(400, "Langue d’atelier invalide.")
    start, expiry = parse_optional_datetime(starts_at), parse_optional_datetime(expires_at)
    if start and expiry and expiry <= start:
        raise HTTPException(400, "La date d'expiration doit suivre la date de début.")
    try:
        maximum = int(max_registrations) if max_registrations else None
    except ValueError as exc:
        raise HTTPException(400, "Limite invalide.") from exc
    if maximum is not None and maximum < 1:
        raise HTTPException(400, "Limite invalide.")
    try:
        selected_workshop_id = int(workshop_id) if workshop_id.strip() else None
    except ValueError as exc:
        raise HTTPException(400, "Atelier invalide") from exc
    workshop = db.get(Workshop, selected_workshop_id) if selected_workshop_id else Workshop(name=label)
    if selected_workshop_id and (not workshop or not workshop.is_active):
        raise HTTPException(400, "Atelier invalide ou fermé")
    if selected_workshop_id and workshop.language_code and workshop.language_code != language_code:
        if workshop.participants:
            raise HTTPException(409, "La langue ne peut plus être modifiée après une inscription.")
        raise HTTPException(409, "Cet atelier possède déjà une autre langue.")
    if not selected_workshop_id or workshop.language_code is None:
        workshop.language_code = language_code
    if not selected_workshop_id:
        db.add(workshop)
        db.flush()
    plain_code = "ATELIER-" + secrets.token_urlsafe(12)
    item = WorkshopCode(workshop_id=workshop.id, label=label, code_hash=workshop_code_hash(plain_code), is_active=True,
                        starts_at=start, expires_at=expiry, max_registrations=maximum,
                        use_count=0, created_by_user_id=admin.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    audit(db, admin, "CREATE_WORKSHOP_CODE", "workshop_code", item.id)
    items = db.query(WorkshopCode).order_by(WorkshopCode.created_at.desc()).all()
    workshops = db.query(Workshop).order_by(Workshop.name).all()
    return render_template("workshop_codes.html", {
        "request": request, "user": admin, "items": items, "workshops": workshops, "languages": LANGUAGES, "language_name": language_name, "revealed_code": plain_code,
    }, status_code=201)


@app.post("/admin/workshop-codes/{code_id}/status")
def set_workshop_code_status(code_id: int, request: Request, active: bool = Form(...), csrf_token: str = Form(...), db: Session = Depends(get_db)):
    admin = require(request, db, ["ADMIN"])
    check_csrf(request, csrf_token)
    item = db.get(WorkshopCode, code_id)
    if not item:
        raise HTTPException(404)
    item.is_active = active
    item.disabled_at = None if active else utc_now()
    db.commit()
    audit(db, admin, "SET_WORKSHOP_CODE_STATUS", "workshop_code", item.id, f"active={active}")
    return RedirectResponse("/admin/workshop-codes", 303)


@app.post("/admin/workshops/{workshop_id}/status")
def set_workshop_status(workshop_id: int, request: Request, active: bool = Form(...), csrf_token: str = Form(...), db: Session = Depends(get_db)):
    admin = require(request, db, ["ADMIN"])
    check_csrf(request, csrf_token)
    workshop = db.get(Workshop, workshop_id)
    if not workshop:
        raise HTTPException(404)
    workshop.is_active = active
    workshop.disabled_at = None if active else utc_now()
    workshop.disabled_by_user_id = None if active else admin.id
    workshop.updated_at = utc_now()
    db.commit()
    audit(db, admin, "SET_WORKSHOP_STATUS", "workshop", workshop.id, f"active={active}")
    return RedirectResponse("/admin/workshop-codes", 303)

@app.post("/recordings/{recording_id}/delete")
def delete_recording(recording_id: int, request: Request, csrf_token: str = Form(...), db: Session = Depends(get_db)):
    admin = require(request, db, ["ADMIN"])
    check_csrf(request, csrf_token)
    rec = db.get(Recording, recording_id)
    if not rec:
        raise HTTPException(404, "Enregistrement introuvable")
    if rec.sync_status == "PENDING":
        raise HTTPException(409, "Réservation en cours ; réconciliation requise avant suppression")
    try:
        delete_file(rec.raw_object)
        delete_file(rec.wav_object)
    except Exception:
        db.rollback()
        logger.exception("Unable to delete MinIO objects for recording %s", recording_id)
        raise HTTPException(502, "Suppression du fichier audio impossible")
    audio_id = rec.audio_id
    receipt = db.query(RecordingSubmission).filter_by(recording_id=rec.id).first()
    if receipt:
        receipt.state = "DELETED"
        receipt.updated_at = utc_now()
    # Keep the transcription and its history as a tombstone. The recording FK
    # is nullable after migration 0007, so deleting audio never deletes the
    # historical transcript or its audit trail.
    if rec.transcription:
        rec.transcription.recording_id = None
    db.delete(rec)
    db.commit()
    audit(db, admin, "DELETE_RECORDING", "recording", recording_id, audio_id)
    return RedirectResponse("/recordings", 303)

@app.get("/admin/export", response_class=HTMLResponse)
def corpus_export_page(request: Request, db: Session = Depends(get_db)):
    user = require(request, db, ["ADMIN"])
    return render_template("export.html", {"request": request, "user": user, "workshops": db.query(Workshop).order_by(Workshop.name).all()})

@app.post("/admin/export/corpus")
def corpus_export(request: Request, mode: str = Form("work"), status: str = Form(""), verification_status: str = Form(""), condition: str = Form(""), participant: str = Form(""), intent: str = Form(""), has_transcription: str = Form(""), date_min: str = Form(""), date_max: str = Form(""), workshop_id: str = Form(""), strict: str = Form("true"), csrf_token: str | None = Form(None), db: Session = Depends(get_db)):
    admin = require(request, db, ["ADMIN"])
    check_csrf(request, csrf_token)
    filters = parse_filters(mode, status, verification_status, condition, participant, intent, has_transcription, date_min, date_max, strict, workshop_id)
    try:
        zip_path, prefix = build_export(db, filters)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Corpus export failed", extra={"operation_id": operation_id(request), "classification": getattr(exc, "classification", "export_error")})
        raise HTTPException(getattr(exc, "status_code", 502), getattr(exc, "message", "Export impossible, aucune archive n’a été envoyée"))
    filename = f"{prefix}.zip"
    audit(db, admin, "EXPORT_RECORDINGS", "workshop", filters.get("workshop_id") or "all", f"mode={filters['mode']}")
    logger.info("Corpus export completed", extra={"admin_id": admin.id, "mode": filters["mode"], "filters": filters, "archive": filename})
    return StreamingResponse(stream_file(zip_path), media_type="application/zip", headers={"Content-Disposition": f"attachment; filename=\"{filename}\"", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})

@app.get("/export/recordings.csv")
def export_recordings(request:Request,db:Session=Depends(get_db)):
    require(request,db,["ADMIN"])
    workshop_id = request.query_params.get("workshop_id")
    query = db.query(Recording).filter(Recording.sync_status == "READY").order_by(Recording.id)
    if workshop_id:
        try: query = query.filter(Recording.workshop_id == int(workshop_id))
        except ValueError: raise HTTPException(400, "Atelier invalide")
    out=io.StringIO()
    w=csv.writer(out)
    w.writerow(["audio_id","workshop_id","workshop_name","participant_code","utterance_code","intent","condition","take_number",
                "duration_ms","status","reference_transcription","normalized_transcription",
                "verification_status","wav_object"])
    for r in query.all():
        tr=r.transcription
        w.writerow([r.audio_id,r.workshop_id,r.workshop.name if r.workshop else "",r.participant.participant_code,r.utterance.utterance_code,r.utterance.intent,
                    r.condition,r.take_number,r.duration_ms,r.status,
                    tr.reference_transcription if tr else "",
                    tr.normalized_transcription if tr else "",
                    tr.verification_status if tr else "",r.wav_object])
    return Response(out.getvalue(),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=recordings_export.csv"})
