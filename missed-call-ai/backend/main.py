"""
Missed Call AI - missed-call text-back for home service businesses.

Flow:
  1. Customer calls the business's Twilio number -> /twilio/voice forwards it to the owner's cell.
  2. Owner doesn't pick up -> /twilio/dial-status texts the caller within seconds.
  3. Customer texts back -> /twilio/sms lets Claude qualify the job.
  4. Claude calls submit_job -> owner gets a text with name, address, issue, urgency and preferred time.
"""

import logging
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

load_dotenv()

from database import init_db, get_db, SessionLocal, Business, Call, Conversation, Message, Job  # noqa: E402
import ai  # noqa: E402
from sms import send_sms  # noqa: E402

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("missed-call-ai")

app = FastAPI(title="Missed Call AI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY") or "admin_" + secrets.token_urlsafe(16)
# Public URL Twilio calls, e.g. https://missed-call-ai.onrender.com (needed for signature checks behind a proxy)
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
MISSED_STATUSES = {"no-answer", "busy", "failed", "canceled"}
OPT_OUT_WORDS = {"stop", "stopall", "unsubscribe", "cancel", "end", "quit"}
OPT_IN_WORDS = {"start", "unstop", "yes"}


@app.on_event("startup")
async def startup():
    init_db()
    if not os.getenv("ADMIN_API_KEY"):
        log.warning("ADMIN_API_KEY not set; generated a temporary one: %s", ADMIN_API_KEY)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def twiml(body: str = "") -> Response:
    return Response(content=f'<?xml version="1.0" encoding="UTF-8"?><Response>{body}</Response>',
                    media_type="application/xml")


def xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&apos;"))


async def twilio_form(request: Request) -> dict:
    """Parse a Twilio webhook and verify its signature when TWILIO_AUTH_TOKEN is configured."""
    form = dict(await request.form())
    token = os.getenv("TWILIO_AUTH_TOKEN")
    if token:
        from twilio.request_validator import RequestValidator
        url = str(request.url)
        if PUBLIC_BASE_URL:
            url = PUBLIC_BASE_URL + request.url.path + (f"?{request.url.query}" if request.url.query else "")
        if not RequestValidator(token).validate(url, form, request.headers.get("X-Twilio-Signature", "")):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    return form


def business_for_number(db: Session, number: str) -> Business:
    business = db.query(Business).filter(Business.twilio_number == number, Business.is_active == True).first()  # noqa: E712
    if not business:
        raise HTTPException(status_code=404, detail="No active business for this number")
    return business


def verify_admin(x_admin_key: str = Header(...)):
    if not secrets.compare_digest(x_admin_key, ADMIN_API_KEY):
        raise HTTPException(status_code=403, detail="Invalid admin key")


def latest_conversation(db: Session, business: Business, phone: str) -> Optional[Conversation]:
    return (db.query(Conversation)
            .filter(Conversation.business_id == business.id, Conversation.customer_phone == phone)
            .order_by(Conversation.id.desc()).first())


def add_message(db: Session, convo: Conversation, role: str, content: str):
    db.add(Message(conversation_id=convo.id, role=role, content=content))
    convo.updated_at = datetime.utcnow()


# ---------------------------------------------------------------------------
# Core logic (shared by the Twilio webhooks and the demo simulator)
# ---------------------------------------------------------------------------

def handle_missed_call(db: Session, business: Business, caller: str) -> Optional[str]:
    """Start (or restart) a text thread with a caller we missed. Returns the text sent, if any."""
    convo = latest_conversation(db, business, caller)
    if convo and convo.status == "opted_out":
        return None
    # Reuse a thread from the last 24h so repeat callers don't get spammed
    if convo and convo.status == "open" and convo.updated_at > datetime.utcnow() - timedelta(hours=24):
        return None
    convo = Conversation(business_id=business.id, customer_phone=caller)
    db.add(convo)
    db.flush()
    text = ai.first_text(business)
    add_message(db, convo, "assistant", text)
    db.commit()
    send_sms(business.twilio_number, caller, text)
    return text


def handle_inbound_sms(db: Session, business: Business, customer: str, body: str) -> Optional[str]:
    """Process a customer's text and return the AI's reply (already sent via SMS)."""
    word = body.strip().lower()
    convo = latest_conversation(db, business, customer)

    if word in OPT_OUT_WORDS:
        if convo:
            convo.status = "opted_out"
            db.commit()
        return None  # Twilio sends the carrier-required opt-out confirmation itself
    if convo and convo.status == "opted_out":
        if word in OPT_IN_WORDS:
            convo.status = "open"
            db.commit()
        return None

    if not convo:
        convo = Conversation(business_id=business.id, customer_phone=customer)
        db.add(convo)
        db.flush()
    add_message(db, convo, "user", body)
    db.commit()

    history = [{"role": m.role, "content": m.content} for m in convo.messages]
    # Claude requires the conversation to start with a user turn
    while history and history[0]["role"] == "assistant":
        history.pop(0)
    if history and convo.messages[0].role == "assistant":
        history[0] = {"role": "user", "content": f"[We texted: \"{convo.messages[0].content}\"]\n{history[0]['content']}"}

    def run_tool(name: str, data: dict) -> str:
        if name == "submit_job":
            if db.query(Job).filter(Job.conversation_id == convo.id).first():
                return "A job was already submitted for this conversation. Do not submit again."
            job = Job(business_id=business.id, conversation_id=convo.id, customer_phone=customer,
                      customer_name=data.get("customer_name"), address=data.get("address"),
                      issue=data.get("issue"), urgency=data.get("urgency"),
                      preferred_time=data.get("preferred_time"))
            db.add(job)
            convo.status = "booked"
            db.commit()
            flag = "🚨 EMERGENCY " if job.urgency == "emergency" else ""
            send_sms(business.twilio_number, business.owner_phone,
                     f"{flag}New job from missed call:\n{job.customer_name} {customer}\n{job.address}\n"
                     f"Issue: {job.issue}\nUrgency: {job.urgency}\nWhen: {job.preferred_time or 'not given'}\n"
                     f"Call/text them back to confirm.")
            return "Job sent to the owner. Tell the customer the owner will reach out to confirm a time."
        if name == "hand_off_to_owner":
            convo.status = "handed_off"
            db.commit()
            send_sms(business.twilio_number, business.owner_phone,
                     f"Please follow up personally with {customer}: {data.get('reason')}")
            return "Owner notified. Tell the customer the owner will reach out personally soon."
        return "Unknown tool."

    try:
        reply = ai.generate_reply(business, history, run_tool)
    except Exception:
        log.exception("AI reply failed")
        reply = None
        send_sms(business.twilio_number, business.owner_phone,
                 f"Heads up: a customer at {customer} texted \"{body[:120]}\" and the assistant couldn't reply. "
                 f"Please follow up.")
    if not reply:
        return None
    add_message(db, convo, "assistant", reply)
    db.commit()
    send_sms(business.twilio_number, customer, reply)
    return reply


# ---------------------------------------------------------------------------
# Twilio webhooks
# ---------------------------------------------------------------------------

@app.post("/twilio/voice")
async def twilio_voice(request: Request, db: Session = Depends(get_db)):
    """Incoming call: ring the owner first."""
    form = await twilio_form(request)
    business = business_for_number(db, form.get("To", ""))
    if business.ring_seconds <= 0:
        # Calls arrive via conditional forwarding: the owner's phone already rang, so text right away
        return missed_call_twiml(db, business, form)
    action = f"{PUBLIC_BASE_URL}/twilio/dial-status" if PUBLIC_BASE_URL else "/twilio/dial-status"
    return twiml(f'<Dial timeout="{business.ring_seconds}" action="{action}" method="POST">'
                 f'{xml_escape(business.owner_phone)}</Dial>')


@app.post("/twilio/dial-status")
async def twilio_dial_status(request: Request, db: Session = Depends(get_db)):
    """Called when the forwarded leg ends. If nobody answered, text the caller."""
    form = await twilio_form(request)
    business = business_for_number(db, form.get("To", ""))
    status = form.get("DialCallStatus", "")
    if status not in MISSED_STATUSES:
        db.add(Call(business_id=business.id, caller=form.get("From", ""), call_sid=form.get("CallSid"),
                    status=status, missed=False))
        db.commit()
        return twiml()
    return missed_call_twiml(db, business, form, status)


def missed_call_twiml(db: Session, business: Business, form: dict, status: str = "no-answer") -> Response:
    caller = form.get("From", "")
    db.add(Call(business_id=business.id, caller=caller, call_sid=form.get("CallSid"), status=status, missed=True))
    db.commit()
    handle_missed_call(db, business, caller)
    return twiml(f"<Say>Sorry we missed you. We just sent you a text message from {xml_escape(business.name)} "
                 f"so we can help you right away.</Say><Hangup/>")


def _process_sms_in_background(business_id: int, customer: str, body: str):
    db = SessionLocal()
    try:
        business = db.get(Business, business_id)
        handle_inbound_sms(db, business, customer, body)
    finally:
        db.close()


@app.post("/twilio/sms")
async def twilio_sms(request: Request, background: BackgroundTasks, db: Session = Depends(get_db)):
    """Inbound text. Reply asynchronously so Twilio's 15s webhook timeout is never an issue."""
    form = await twilio_form(request)
    business = business_for_number(db, form.get("To", ""))
    customer, body = form.get("From", ""), form.get("Body", "")
    if customer != business.owner_phone and body.strip():
        background.add_task(_process_sms_in_background, business.id, customer, body)
    return twiml()


# ---------------------------------------------------------------------------
# Admin API
# ---------------------------------------------------------------------------

class BusinessIn(BaseModel):
    name: str
    trade: str = "hvac"
    twilio_number: str
    owner_phone: str
    owner_email: Optional[str] = None
    service_area: Optional[str] = None
    business_hours: Optional[str] = None
    custom_knowledge: Optional[str] = None
    avg_job_value: float = 450.0
    ring_seconds: int = 20


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    trade: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_email: Optional[str] = None
    service_area: Optional[str] = None
    business_hours: Optional[str] = None
    custom_knowledge: Optional[str] = None
    avg_job_value: Optional[float] = None
    ring_seconds: Optional[int] = None
    is_active: Optional[bool] = None


class JobStatusIn(BaseModel):
    status: str


class SimulateIn(BaseModel):
    customer_phone: str = "+19165550100"
    body: Optional[str] = None


def business_dict(b: Business) -> dict:
    return {c.name: getattr(b, c.name) for c in b.__table__.columns}


def get_business_or_404(db: Session, business_id: int) -> Business:
    business = db.get(Business, business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


@app.post("/admin/businesses", dependencies=[Depends(verify_admin)])
async def create_business(data: BusinessIn, db: Session = Depends(get_db)):
    if db.query(Business).filter(Business.twilio_number == data.twilio_number).first():
        raise HTTPException(status_code=400, detail="That Twilio number is already assigned")
    business = Business(**data.model_dump(exclude_none=True))
    db.add(business)
    db.commit()
    db.refresh(business)
    return business_dict(business)


@app.get("/admin/businesses", dependencies=[Depends(verify_admin)])
async def list_businesses(db: Session = Depends(get_db)):
    return [business_dict(b) for b in db.query(Business).order_by(Business.id).all()]


@app.put("/admin/businesses/{business_id}", dependencies=[Depends(verify_admin)])
async def update_business(business_id: int, data: BusinessUpdate, db: Session = Depends(get_db)):
    business = get_business_or_404(db, business_id)
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(business, key, value)
    db.commit()
    return business_dict(business)


@app.delete("/admin/businesses/{business_id}", dependencies=[Depends(verify_admin)])
async def delete_business(business_id: int, db: Session = Depends(get_db)):
    business = get_business_or_404(db, business_id)
    db.delete(business)
    db.commit()
    return {"deleted": business_id}


@app.get("/admin/businesses/{business_id}/stats", dependencies=[Depends(verify_admin)])
async def business_stats(business_id: int, days: int = 30, db: Session = Depends(get_db)):
    """The numbers that sell the renewal: missed calls recovered and revenue saved."""
    business = get_business_or_404(db, business_id)
    since = datetime.utcnow() - timedelta(days=days)
    calls = db.query(Call).filter(Call.business_id == business.id, Call.created_at >= since).all()
    convos = db.query(Conversation).filter(Conversation.business_id == business.id,
                                           Conversation.created_at >= since).all()
    jobs = db.query(Job).filter(Job.business_id == business.id, Job.created_at >= since).all()
    replied = sum(1 for c in convos if any(m.role == "user" for m in c.messages))
    return {
        "days": days,
        "total_calls": len(calls),
        "missed_calls": sum(1 for c in calls if c.missed),
        "conversations": len(convos),
        "customers_replied": replied,
        "jobs_captured": len(jobs),
        "emergencies": sum(1 for j in jobs if j.urgency == "emergency"),
        "jobs_won": sum(1 for j in jobs if j.status == "won"),
        "estimated_revenue_saved": round(len(jobs) * (business.avg_job_value or 0), 2),
    }


@app.get("/admin/businesses/{business_id}/jobs", dependencies=[Depends(verify_admin)])
async def list_jobs(business_id: int, db: Session = Depends(get_db)):
    get_business_or_404(db, business_id)
    jobs = db.query(Job).filter(Job.business_id == business_id).order_by(Job.id.desc()).limit(200).all()
    return [{c.name: getattr(j, c.name) for c in j.__table__.columns} for j in jobs]


@app.put("/admin/jobs/{job_id}", dependencies=[Depends(verify_admin)])
async def update_job(job_id: int, data: JobStatusIn, db: Session = Depends(get_db)):
    if data.status not in {"new", "scheduled", "won", "lost"}:
        raise HTTPException(status_code=400, detail="status must be new, scheduled, won or lost")
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = data.status
    db.commit()
    return {"id": job.id, "status": job.status}


@app.get("/admin/businesses/{business_id}/conversations", dependencies=[Depends(verify_admin)])
async def list_conversations(business_id: int, db: Session = Depends(get_db)):
    get_business_or_404(db, business_id)
    convos = (db.query(Conversation).filter(Conversation.business_id == business_id)
              .order_by(Conversation.updated_at.desc()).limit(100).all())
    return [{
        "id": c.id, "customer_phone": c.customer_phone, "status": c.status, "updated_at": c.updated_at,
        "messages": [{"role": m.role, "content": m.content, "at": m.created_at} for m in c.messages],
    } for c in convos]


# --- Demo simulator: show prospects the whole flow without a phone ---------

@app.post("/admin/businesses/{business_id}/simulate/missed-call", dependencies=[Depends(verify_admin)])
async def simulate_missed_call(business_id: int, data: SimulateIn, db: Session = Depends(get_db)):
    business = get_business_or_404(db, business_id)
    db.add(Call(business_id=business.id, caller=data.customer_phone, call_sid="SIMULATED",
                status="no-answer", missed=True))
    db.commit()
    return {"sent": handle_missed_call(db, business, data.customer_phone)}


@app.post("/admin/businesses/{business_id}/simulate/sms", dependencies=[Depends(verify_admin)])
async def simulate_sms(business_id: int, data: SimulateIn, db: Session = Depends(get_db)):
    business = get_business_or_404(db, business_id)
    if not data.body:
        raise HTTPException(status_code=400, detail="body is required")
    return {"reply": handle_inbound_sms(db, business, data.customer_phone, data.body)}


# ---------------------------------------------------------------------------

DASHBOARD = Path(__file__).resolve().parent.parent / "frontend" / "dashboard.html"


@app.get("/")
async def dashboard():
    return FileResponse(DASHBOARD)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
