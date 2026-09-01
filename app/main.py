import csv, io, logging, os, subprocess, tempfile, time
from pathlib import Path
from fastapi import FastAPI, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from .db import Base, engine, get_db, SessionLocal
from .models import User, Participant, Utterance, Recording, Transcription, AuditLog
from .auth import verify_password, hash_password, create_token, get_current_user
from .storage import ensure_bucket, put_file, get_bytes
from .seed import seed

logger = logging.getLogger("mobile_money_corpus_manager")

app = FastAPI(title="Mobile Money Corpus Manager")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def startup():
    for _ in range(20):
        try:
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

@app.get("/health")
def health():
    return {"status":"ok"}

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request":request})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=username).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request":request,"error":"Identifiants incorrects"}, status_code=401)
    token = create_token(user)
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie("session", token, httponly=True, samesite="lax", secure=False, max_age=43200)
    audit(db,user,"LOGIN","user",user.id)
    return resp

@app.get("/logout")
def logout():
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
    participant_code: str=Form(...), username: str=Form(...), password: str=Form(...),
    language: str=Form("mos"), age_group: str=Form(""), gender: str=Form(""),
    region: str=Form(""), consent_obtained: bool=Form(False),
    db: Session=Depends(get_db)
):
    admin=require(request,db,["ADMIN"])
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
    pid=user.participant_id if user.role=="PARTICIPANT" else participant_id
    if not pid: raise HTTPException(400,"participant requis")
    participant=db.get(Participant,pid)
    utterance=db.get(Utterance,utterance_id)
    if not participant or not utterance: raise HTTPException(404)
    if not participant.consent_obtained: raise HTTPException(403,"consentement absent")
    audio_id=f"{participant.participant_code}_{utterance.utterance_code}_{condition}_T{take_number:02d}"
    if db.query(Recording).filter_by(audio_id=audio_id).first():
        raise HTTPException(409,"Cette prise existe déjà")

    suffix=Path(audio.filename or "audio.webm").suffix or ".webm"
    with tempfile.TemporaryDirectory() as td:
        raw=Path(td)/f"raw{suffix}"
        wav=Path(td)/"normalized.wav"
        raw.write_bytes(await audio.read())
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(raw),"-ar","16000","-ac","1","-c:a","pcm_s16le",str(wav)],check=True)
        raw_obj=f"raw/{participant.participant_code}/{audio_id}{suffix}"
        wav_obj=f"normalized/{participant.participant_code}/{audio_id}.wav"
        put_file(raw_obj,str(raw),audio.content_type or "application/octet-stream")
        put_file(wav_obj,str(wav),"audio/wav")
        # duration
        p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(wav)],capture_output=True,text=True)
        duration_ms=int(float(p.stdout.strip() or "0")*1000)

    rec=Recording(audio_id=audio_id,participant_id=pid,utterance_id=utterance_id,take_number=take_number,
                  condition=condition,raw_object=raw_obj,wav_object=wav_obj,duration_ms=duration_ms)
    db.add(rec); db.commit()
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
    normalized_transcription:str=Form(""),
    db:Session=Depends(get_db)
):
    user=require(request,db,["ADMIN","PARTICIPANT","TRANSCRIBER"])
    rec=db.get(Recording,recording_id)
    if not rec: raise HTTPException(404)
    if user.role=="PARTICIPANT" and rec.participant_id!=user.participant_id:
        raise HTTPException(403)
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
    recording_id:int, request:Request, decision:str=Form(...), comment:str=Form(""),
    db:Session=Depends(get_db)
):
    user=require(request,db,["ADMIN","VALIDATOR"])
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
def create_user(request:Request,username:str=Form(...),password:str=Form(...),role:str=Form(...),db:Session=Depends(get_db)):
    admin=require(request,db,["ADMIN"])
    if role not in ["ADMIN","TRANSCRIBER","VALIDATOR"]: raise HTTPException(400)
    if db.query(User).filter_by(username=username).first(): raise HTTPException(400,"username déjà utilisé")
    u=User(username=username,password_hash=hash_password(password),role=role)
    db.add(u);db.commit()
    audit(db,admin,"CREATE_USER","user",u.id,role)
    return RedirectResponse("/users",303)

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
