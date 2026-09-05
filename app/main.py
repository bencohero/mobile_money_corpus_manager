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
from .models import User, Participant, Utterance, Recording, Transcription, AuditLog
from .auth import verify_password, hash_password, create_token, get_current_user
from .storage import ensure_bucket, put_file, get_bytes, delete_file, stat_file, list_files
from .seed import seed

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
            logger.exception("MinIO compensation failed", extra={"operation_id": operation_id(request)})


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
    qrec = db.query(Recording)
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

@app.post("/api/recordings")
async def upload_recording(
    request: Request,
    utterance_id: int=Form(...),
    take_number: int=Form(1),
    condition: str=Form("CLEAN"),
    participant_id: int|None=Form(None),
    audio: UploadFile=File(...),
    db: Session=Depends(get_db)
):
    user=require(request,db,["PARTICIPANT","ADMIN"])
    check_csrf(request)
    pid=user.participant_id if user.role=="PARTICIPANT" else participant_id
    if not pid: raise HTTPException(400,"participant requis")
    participant=db.get(Participant,pid)
    utterance=db.get(Utterance,utterance_id)
    if not participant or not utterance: raise HTTPException(404)
    if not participant.consent_obtained: raise HTTPException(403,"consentement absent")
    if condition not in ALLOWED_CONDITIONS: raise HTTPException(400,"condition invalide")
    if take_number < 1 or take_number > 999: raise HTTPException(400,"numéro de prise invalide")
    content_type=(audio.content_type or "").split(";", 1)[0].lower()
    if content_type not in ALLOWED_AUDIO_TYPES: raise HTTPException(415,"format audio non accepté")
    audio_id=f"{participant.participant_code}_{utterance.utterance_code}_{condition}_T{take_number:02d}"
    if db.query(Recording).filter_by(audio_id=audio_id).first():
        raise HTTPException(409,"Cette prise existe déjà")

    suffix=Path(audio.filename or "audio.webm").suffix or ".webm"
    with tempfile.TemporaryDirectory() as td:
        raw=Path(td)/f"raw{suffix}"
        wav=Path(td)/"normalized.wav"
        size = 0
        with raw.open("wb") as target:
            while chunk := await audio.read(1024 * 1024):
                size += len(chunk)
                if size > settings.max_audio_mb * 1024 * 1024:
                    raise HTTPException(413, f"audio limité à {settings.max_audio_mb} Mo")
                target.write(chunk)
        if size == 0: raise HTTPException(400,"fichier audio vide")
        try:
            run_audio_command(["ffmpeg","-y","-loglevel","error","-i",str(raw),"-ar","16000","-ac","1","-c:a","pcm_s16le",str(wav)],check=True,timeout=settings.ffmpeg_timeout_seconds,capture_output=True)
        except ConversionSaturated:
            raise HTTPException(429,"Le traitement audio est momentanement sature. Reessayez.")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            raise HTTPException(422,"audio illisible ou conversion trop longue")
        try:
            with wave.open(str(wav), "rb") as normalized:
                if (normalized.getnchannels(), normalized.getsampwidth(), normalized.getframerate(), normalized.getnframes()) != (1, 2, 16000, normalized.getnframes()) or normalized.getnframes() <= 0:
                    raise ValueError("invalid normalized wav")
        except (wave.Error, OSError, EOFError, ValueError):
            raise audio_error(request, 422, "audio converti invalide")
        raw_obj=f"raw/{participant.participant_code}/{audio_id}{suffix}"
        wav_obj=f"normalized/{participant.participant_code}/{audio_id}.wav"
        uploaded=[]
        try:
            put_file(raw_obj,str(raw),audio.content_type or "application/octet-stream"); uploaded.append(raw_obj)
            put_file(wav_obj,str(wav),"audio/wav"); uploaded.append(wav_obj)
        except Exception:
            compensate_uploaded(uploaded, request)
            db.rollback()
            logger.exception("MinIO upload failed", extra={"operation_id": operation_id(request)})
            raise HTTPException(502,"Stockage audio temporairement indisponible")
        try:
            p=run_audio_command(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(wav)],capture_output=True,text=True,check=True,timeout=settings.ffprobe_timeout_seconds)
            duration_ms=int(float(p.stdout.strip() or "0")*1000)
            if not settings.min_audio_duration_seconds*1000 <= duration_ms <= settings.max_audio_duration_seconds*1000:
                raise ValueError("duration out of limits")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
            compensate_uploaded(uploaded, request)
            db.rollback()
            raise audio_error(request, 422, "audio illisible, durée invalide ou conversion trop longue")
        raw_bytes, wav_bytes = raw.read_bytes(), wav.read_bytes()
        raw_sha, wav_sha, wav_size = hashlib.sha256(raw_bytes).hexdigest(), hashlib.sha256(wav_bytes).hexdigest(), len(wav_bytes)

    rec=Recording(audio_id=audio_id,participant_id=pid,utterance_id=utterance_id,take_number=take_number,
                  condition=condition,raw_object=raw_obj,wav_object=wav_obj,duration_ms=duration_ms,sync_status="READY",raw_size_bytes=size,wav_size_bytes=wav_size,raw_sha256=raw_sha,wav_sha256=wav_sha,finalized_at=datetime.utcnow())
    db.add(rec)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        compensate_uploaded(uploaded, request)
        raise HTTPException(409,"Cette prise existe déjà")
    except Exception:
        db.rollback()
        compensate_uploaded(uploaded, request)
        logger.exception("PostgreSQL commit failed", extra={"operation_id": operation_id(request)})
        raise HTTPException(502,"Enregistrement audio temporairement indisponible")
    audit(db,user,"CREATE_RECORDING","recording",rec.id,audio_id)
    return {"ok":True,"audio_id":audio_id,"recording_id":rec.id}

@app.get("/recordings", response_class=HTMLResponse)
def recordings_page(request: Request, db: Session=Depends(get_db)):
    user=require(request,db,["ADMIN","PARTICIPANT","TRANSCRIBER","VALIDATOR"])
    q=db.query(Recording)
    if user.role=="PARTICIPANT":
        q=q.filter(Recording.participant_id==user.participant_id)
    items=q.order_by(Recording.created_at.desc()).all()
    return templates.TemplateResponse("recordings.html",{"request":request,"user":user,"items":items})

@app.get("/audio/{recording_id}")
def audio(recording_id:int, request:Request, db:Session=Depends(get_db)):
    user=require(request,db,["ADMIN","PARTICIPANT","TRANSCRIBER","VALIDATOR"])
    rec=db.get(Recording,recording_id)
    if not rec: raise HTTPException(404)
    if user.role=="PARTICIPANT" and rec.participant_id!=user.participant_id:
        raise HTTPException(403)
    return Response(get_bytes(rec.wav_object),media_type="audio/wav")

@app.get("/transcribe/{recording_id}", response_class=HTMLResponse)
def transcribe_page(recording_id:int, request:Request, db:Session=Depends(get_db)):
    user=require(request,db,["ADMIN","PARTICIPANT","TRANSCRIBER","VALIDATOR"])
    rec=db.get(Recording,recording_id)
    if not rec: raise HTTPException(404)
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
    try:
        delete_file(rec.raw_object)
        delete_file(rec.wav_object)
    except Exception:
        db.rollback()
        logger.exception("Unable to delete MinIO objects for recording %s", recording_id)
        raise HTTPException(502, "Suppression du fichier audio impossible")
    audio_id = rec.audio_id
    if rec.transcription:
        db.delete(rec.transcription)
    db.delete(rec)
    db.commit()
    audit(db, admin, "DELETE_RECORDING", "recording", recording_id, audio_id)
    return RedirectResponse("/recordings", 303)

@app.get("/export/recordings.csv")
def export_recordings(request:Request,db:Session=Depends(get_db)):
    require(request,db,["ADMIN"])
    out=io.StringIO()
    w=csv.writer(out)
    w.writerow(["audio_id","participant_code","utterance_code","intent","condition","take_number",
                "duration_ms","status","reference_transcription","normalized_transcription",
                "verification_status","wav_object"])
    for r in db.query(Recording).order_by(Recording.id).all():
        tr=r.transcription
        w.writerow([r.audio_id,r.participant.participant_code,r.utterance.utterance_code,r.utterance.intent,
                    r.condition,r.take_number,r.duration_ms,r.status,
                    tr.reference_transcription if tr else "",
                    tr.normalized_transcription if tr else "",
                    tr.verification_status if tr else "",r.wav_object])
    return Response(out.getvalue(),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=recordings_export.csv"})
