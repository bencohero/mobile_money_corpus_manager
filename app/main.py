import csv, io, logging, secrets, subprocess, tempfile, time, hashlib, uuid, wave
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from .config import settings
from .db import Base, engine, get_db, SessionLocal
from .models import User, Participant, Utterance, Recording, Transcription, AuditLog, RecordingSubmission
from .take_sequence import next_take_estimate, TakeLimitReached
from .recording_submission import reserve as reserve_recording, finish as finish_recording, mark_error as mark_recording_error, result as submission_result
from .auth import verify_password, hash_password, create_token, get_current_user
from .storage import ensure_bucket, put_file, get_bytes, delete_file, stat_file, list_files, verify_file
from .seed import seed
from .corpus_export import build_export, parse_filters, stream_file

logger = logging.getLogger("mobile_money_corpus_manager")
ALLOWED_AUDIO_TYPES = {"audio/webm", "audio/ogg", "audio/wav", "audio/x-wav", "audio/mp4", "audio/mpeg"}
ALLOWED_CONDITIONS = {"CLEAN", "NOISY"}
CONVERSION_SLOTS = __import__("threading").BoundedSemaphore(settings.max_concurrent_conversions)
class ConversionSaturated(Exception): pass
def run_audio_command(args, **kwargs):
    if not CONVERSION_SLOTS.acquire(blocking=False):
        raise ConversionSaturated()
    try:
        return subprocess.run(args, shell=False, **kwargs)
    finally:
        CONVERSION_SLOTS.release()

def operation_id(request):
    return request.headers.get("x-request-id") or uuid.uuid4().hex

def audio_error(request, status_code, message):
    op = operation_id(request)
    logger.warning("audio operation failed", extra={"operation_id": op, "status_code": status_code})
    return HTTPException(status_code, message, headers={"X-Operation-ID": op})

def compensate_uploaded(uploaded, request):
    for object_name in uploaded:
        try:
            delete_file(object_name)
        except Exception:
            logger.error("MinIO compensation failed; reconciliation required", extra={"operation_id": operation_id(request)})


app = FastAPI(title="Mobile Money Corpus Manager")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def startup():
    for _ in range(20):
        try:

            if settings.app_env == "development":
                Base.metadata.create_all(engine)
            ensure_bucket()
            with SessionLocal() as db:
                seed(db)
            return
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

def audit(db, user, action, entity_type=None, entity_id=None, detail=None):
    db.add(AuditLog(user_id=user.id if user else None, action=action,
                    entity_type=entity_type, entity_id=str(entity_id) if entity_id else None,
                    detail=detail))
    db.commit()

def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)

def check_csrf(request: Request, token: str | None = None):
    supplied = token or request.headers.get("x-csrf-token")
    expected = request.cookies.get("csrf_token")
    if not supplied or not expected or not secrets.compare_digest(supplied, expected):
        raise HTTPException(403, "Requête expirée ou invalide. Rechargez la page.")

def set_csrf_cookie(response: Response, token: str):
    response.set_cookie("csrf_token", token, httponly=False, samesite="strict",
                        secure=settings.cookie_secure, max_age=settings.access_token_minutes * 60)

@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        stat_file(settings.minio_bucket + "/.healthcheck") if False else None
        return {"status": "ok"}
    except Exception:
        logger.exception("Health check failed")
        raise HTTPException(503, "Service indisponible")

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    token = new_csrf_token()
    response = templates.TemplateResponse("login.html", {"request":request, "csrf_token":token})
    set_csrf_cookie(response, token)
    return response

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), csrf_token: str = Form(...), db: Session = Depends(get_db)):
    check_csrf(request, csrf_token)
    user = db.query(User).filter_by(username=username).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request":request,"error":"Identifiants incorrects", "csrf_token":csrf_token}, status_code=401)
    token = create_token(user)
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie("session", token, httponly=True, samesite="strict", secure=settings.cookie_secure, max_age=settings.access_token_minutes * 60)
    set_csrf_cookie(resp, csrf_token)
    audit(db,user,"LOGIN","user",user.id)
    return resp

@app.post("/logout")
def logout(request: Request, csrf_token: str = Form(...)):
    check_csrf(request, csrf_token)
    resp=RedirectResponse("/login",303)
    resp.delete_cookie("session")
    return resp

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = current(request,db)
    if not user: return RedirectResponse("/login",303)
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
    return templates.TemplateResponse("dashboard.html", {"request":request,"user":user,"stats":stats,"latest":latest})

@app.get("/participants", response_class=HTMLResponse)
def participants(request: Request, db: Session = Depends(get_db)):
    user=require(request,db,["ADMIN"])
    items=db.query(Participant).order_by(Participant.participant_code).all()
    return templates.TemplateResponse("participants.html", {"request":request,"user":user,"items":items})

@app.post("/participants")
def create_participant(
    request: Request,
    participant_code: str=Form(...), username: str=Form(...), password: str=Form(...), csrf_token: str=Form(...),
    language: str=Form("mos"), age_group: str=Form(""), gender: str=Form(""),
    region: str=Form(""), consent_obtained: bool=Form(False),
    db: Session=Depends(get_db)
):
    admin=require(request,db,["ADMIN"])
    check_csrf(request, csrf_token)
    if db.query(Participant).filter_by(participant_code=participant_code).first():
        raise HTTPException(400,"participant_code déjà utilisé")
    if db.query(User).filter_by(username=username).first():
        raise HTTPException(400,"username déjà utilisé")
    p=Participant(participant_code=participant_code,language=language,age_group=age_group or None,
                  gender=gender or None,region=region or None,consent_obtained=consent_obtained)
    db.add(p); db.flush()
    u=User(username=username,password_hash=hash_password(password),role="PARTICIPANT",participant_id=p.id)
    db.add(u); db.commit()
    audit(db,admin,"CREATE_PARTICIPANT","participant",p.id,participant_code)
    return RedirectResponse("/participants",303)

@app.get("/record", response_class=HTMLResponse)
def record_page(request: Request, db: Session=Depends(get_db)):
    user=require(request,db,["PARTICIPANT","ADMIN"])
    if user.role=="PARTICIPANT":
        participant=db.get(Participant,user.participant_id)
        if not participant or not participant.consent_obtained:
            return templates.TemplateResponse("message.html",{"request":request,"user":user,"message":"Consentement non enregistré. Contactez l'administrateur."},status_code=403)
    else:
        participant=None
    utterances=db.query(Utterance).filter_by(active=True).order_by(Utterance.utterance_code).all()
    participants=db.query(Participant).order_by(Participant.participant_code).all() if user.role=="ADMIN" else []
    return templates.TemplateResponse("record.html",{"request":request,"user":user,"participant":participant,"participants":participants,"utterances":utterances})

def recording_context(db, user, participant_id, utterance_id, condition):
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
        fingerprint = hashlib.sha256(f"{participant.id}:{utterance.id}:{condition}:{content_type}:{raw_sha}".encode()).hexdigest()
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
    if user.role=="PARTICIPANT":
        q=q.filter(Recording.participant_id==user.participant_id)
    items=q.order_by(Recording.created_at.desc()).all()
    return templates.TemplateResponse("recordings.html",{"request":request,"user":user,"items":items})

@app.get("/audio/{recording_id}")
def audio(recording_id:int, request:Request, db:Session=Depends(get_db)):
    user=require(request,db,["ADMIN","PARTICIPANT","TRANSCRIBER","VALIDATOR"])
    rec=db.get(Recording,recording_id)
    if not rec: raise HTTPException(404)
    if rec.sync_status != "READY": raise HTTPException(409, "Audio non finalisé")
    if user.role=="PARTICIPANT" and rec.participant_id!=user.participant_id:
        raise HTTPException(403)
    return Response(get_bytes(rec.wav_object),media_type="audio/wav")

@app.get("/transcribe/{recording_id}", response_class=HTMLResponse)
def transcribe_page(recording_id:int, request:Request, db:Session=Depends(get_db)):
    user=require(request,db,["ADMIN","PARTICIPANT","TRANSCRIBER","VALIDATOR"])
    rec=db.get(Recording,recording_id)
    if not rec: raise HTTPException(404)
    if rec.sync_status != "READY": raise HTTPException(409, "Audio non finalisé")
    if user.role=="PARTICIPANT" and rec.participant_id!=user.participant_id:
        raise HTTPException(403)
    return templates.TemplateResponse("transcribe.html",{"request":request,"user":user,"rec":rec})

@app.post("/transcribe/{recording_id}")
def save_transcription(
    recording_id:int, request:Request,
    reference_transcription:str=Form(...),
    normalized_transcription:str=Form(""), csrf_token:str=Form(...),
    db:Session=Depends(get_db)
):
    user=require(request,db,["ADMIN","PARTICIPANT","TRANSCRIBER"])
    check_csrf(request, csrf_token)
    rec=db.get(Recording,recording_id)
    if not rec: raise HTTPException(404)
    if user.role=="PARTICIPANT" and rec.participant_id!=user.participant_id:
        raise HTTPException(403)
    if rec.status == "VERIFIED" and user.role != "ADMIN":
        raise HTTPException(409,"Une transcription validée doit être rouverte par un administrateur")
    if rec.sync_status != "READY": raise HTTPException(409, "Audio non finalisé")
    tr=rec.transcription
    if tr:
        tr.reference_transcription=reference_transcription
        tr.normalized_transcription=normalized_transcription or None
        tr.transcriber_id=user.id
        tr.verification_status="PENDING"
    else:
        tr=Transcription(recording_id=rec.id,reference_transcription=reference_transcription,
                         normalized_transcription=normalized_transcription or None,transcriber_id=user.id)
        db.add(tr)
    rec.status="TRANSCRIBED"
    db.commit()
    audit(db,user,"SAVE_TRANSCRIPTION","recording",rec.id)
    return RedirectResponse("/recordings",303)

@app.post("/verify/{recording_id}")
def verify(
    recording_id:int, request:Request, decision:str=Form(...), comment:str=Form(""), csrf_token:str=Form(...),
    db:Session=Depends(get_db)
):
    user=require(request,db,["ADMIN","VALIDATOR"])
    check_csrf(request, csrf_token)
    rec=db.get(Recording,recording_id)
    if not rec or not rec.transcription: raise HTTPException(404)
    if rec.sync_status != "READY": raise HTTPException(409, "Audio non finalisé")
    rec.transcription.verifier_id=user.id
    rec.transcription.verifier_comment=comment or None
    if decision=="VERIFIED":
        rec.transcription.verification_status="VERIFIED"
        rec.status="VERIFIED"
    elif decision=="NEEDS_REVIEW":
        rec.transcription.verification_status="NEEDS_REVIEW"
        rec.status="NEEDS_REVIEW"
    else:
        rec.transcription.verification_status="REJECTED"
        rec.status="REJECTED"
    db.commit()
    audit(db,user,"VERIFY_TRANSCRIPTION","recording",rec.id,decision)
    return RedirectResponse(f"/transcribe/{recording_id}",303)

@app.get("/users", response_class=HTMLResponse)
def users_page(request:Request, db:Session=Depends(get_db)):
    user=require(request,db,["ADMIN"])
    items=db.query(User).order_by(User.username).all()
    return templates.TemplateResponse("users.html",{"request":request,"user":user,"items":items})

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
        receipt.updated_at = datetime.utcnow()
    if rec.transcription:
        db.delete(rec.transcription)
    db.delete(rec)
    db.commit()
    audit(db, admin, "DELETE_RECORDING", "recording", recording_id, audio_id)
    return RedirectResponse("/recordings", 303)

@app.get("/admin/export", response_class=HTMLResponse)
def corpus_export_page(request: Request, db: Session = Depends(get_db)):
    user = require(request, db, ["ADMIN"])
    return templates.TemplateResponse("export.html", {"request": request, "user": user})

@app.post("/admin/export/corpus")
def corpus_export(request: Request, mode: str = Form("work"), status: str = Form(""), verification_status: str = Form(""), condition: str = Form(""), participant: str = Form(""), intent: str = Form(""), has_transcription: str = Form(""), date_min: str = Form(""), date_max: str = Form(""), strict: str = Form("true"), csrf_token: str | None = Form(None), db: Session = Depends(get_db)):
    admin = require(request, db, ["ADMIN"])
    check_csrf(request, csrf_token)
    filters = parse_filters(mode, status, verification_status, condition, participant, intent, has_transcription, date_min, date_max, strict)
    try:
        zip_path, prefix = build_export(db, filters)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Corpus export failed", extra={"operation_id": operation_id(request), "classification": getattr(exc, "classification", "export_error")})
        raise HTTPException(getattr(exc, "status_code", 502), getattr(exc, "message", "Export impossible, aucune archive n’a été envoyée"))
    filename = f"{prefix}.zip"
    logger.info("Corpus export completed", extra={"admin_id": admin.id, "mode": filters["mode"], "filters": filters, "archive": filename})
    return StreamingResponse(stream_file(zip_path), media_type="application/zip", headers={"Content-Disposition": f"attachment; filename=\"{filename}\"", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})

@app.get("/export/recordings.csv")
def export_recordings(request:Request,db:Session=Depends(get_db)):
    require(request,db,["ADMIN"])
    out=io.StringIO()
    w=csv.writer(out)
    w.writerow(["audio_id","participant_code","utterance_code","intent","condition","take_number",
                "duration_ms","status","reference_transcription","normalized_transcription",
                "verification_status","wav_object"])
    for r in db.query(Recording).filter(Recording.sync_status == "READY").order_by(Recording.id).all():
        tr=r.transcription
        w.writerow([r.audio_id,r.participant.participant_code,r.utterance.utterance_code,r.utterance.intent,
                    r.condition,r.take_number,r.duration_ms,r.status,
                    tr.reference_transcription if tr else "",
                    tr.normalized_transcription if tr else "",
                    tr.verification_status if tr else "",r.wav_object])
    return Response(out.getvalue(),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=recordings_export.csv"})
