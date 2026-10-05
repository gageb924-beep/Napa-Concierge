"""
End-to-end flow tests with Claude and Twilio mocked out.
Run from missed-call-ai/backend:  python -m pytest -q
"""

import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DATABASE_URL"] = "sqlite:///./test_missed_call_ai.db"
os.environ["ADMIN_API_KEY"] = "test-admin"
os.environ.pop("TWILIO_AUTH_TOKEN", None)
os.environ.pop("TWILIO_ACCOUNT_SID", None)

from fastapi.testclient import TestClient  # noqa: E402

import ai  # noqa: E402
import sms  # noqa: E402
from database import Base, engine  # noqa: E402
from main import app  # noqa: E402

ADMIN = {"X-Admin-Key": "test-admin"}
BIZ_NUMBER = "+19165550000"
OWNER = "+19165559999"
CUSTOMER = "+19165551234"


def text_block(t):
    return SimpleNamespace(type="text", text=t)


def tool_block(name, data, id_="tu_1"):
    return SimpleNamespace(type="tool_use", name=name, input=data, id=id_)


class FakeClaude:
    """Returns scripted responses and records what it was sent."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        content = self.responses.pop(0)
        stop = "tool_use" if any(b.type == "tool_use" for b in content) else "end_turn"
        return SimpleNamespace(content=content, stop_reason=stop)


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    sms.outbox.clear()
    with TestClient(app) as c:
        r = c.post("/admin/businesses", headers=ADMIN, json={
            "name": "River City Heating & Air", "twilio_number": BIZ_NUMBER, "owner_phone": OWNER,
            "custom_knowledge": "Diagnostic visit $89, waived with repair.", "avg_job_value": 500,
        })
        assert r.status_code == 200
        c.business_id = r.json()["id"]
        yield c


def test_admin_requires_key(client):
    assert client.get("/admin/businesses").status_code == 422
    assert client.get("/admin/businesses", headers={"X-Admin-Key": "nope"}).status_code == 403


def test_incoming_call_forwards_to_owner(client):
    r = client.post("/twilio/voice", data={"To": BIZ_NUMBER, "From": CUSTOMER, "CallSid": "CA1"})
    assert r.status_code == 200
    assert f"<Dial timeout=\"20\"" in r.text and OWNER in r.text


def test_forwarded_line_texts_immediately(client):
    client.put(f"/admin/businesses/{client.business_id}", headers=ADMIN, json={"ring_seconds": 0})
    r = client.post("/twilio/voice", data={"To": BIZ_NUMBER, "From": CUSTOMER, "CallSid": "CA1"})
    assert "<Dial" not in r.text and "<Say>" in r.text
    assert sms.outbox[-1]["to"] == CUSTOMER


def test_answered_call_sends_no_text(client):
    r = client.post("/twilio/dial-status",
                    data={"To": BIZ_NUMBER, "From": CUSTOMER, "CallSid": "CA1", "DialCallStatus": "completed"})
    assert r.status_code == 200
    assert sms.outbox == []


def test_full_missed_call_to_booked_job(client, monkeypatch):
    # 1. Missed call -> caller gets a text
    r = client.post("/twilio/dial-status",
                    data={"To": BIZ_NUMBER, "From": CUSTOMER, "CallSid": "CA1", "DialCallStatus": "no-answer"})
    assert "<Say>" in r.text
    assert sms.outbox[-1]["to"] == CUSTOMER and "River City" in sms.outbox[-1]["body"]

    # 2. Customer replies; Claude asks a question
    fake = FakeClaude([
        [text_block("So sorry! Is the AC blowing warm air or not turning on at all? And what's your address?")],
        [tool_block("submit_job", {"customer_name": "Maria", "address": "123 J St, Sacramento",
                                   "issue": "AC blowing warm air", "urgency": "soon",
                                   "preferred_time": "tomorrow morning"})],
        [text_block("Got it Maria, the owner will text you shortly to confirm tomorrow morning.")],
    ])
    monkeypatch.setattr(ai, "get_client", lambda: fake)
    client.post("/twilio/sms", data={"To": BIZ_NUMBER, "From": CUSTOMER, "Body": "my AC isn't cooling"})
    assert sms.outbox[-1]["to"] == CUSTOMER and "warm air" in sms.outbox[-1]["body"]
    # The first call to Claude starts with a user turn that includes our opening text for context
    first_msgs = fake.calls[0]["messages"]
    assert first_msgs[0]["role"] == "user" and "We texted" in first_msgs[0]["content"]

    # 3. Customer gives details; Claude submits the job; owner gets alerted
    client.post("/twilio/sms", data={"To": BIZ_NUMBER, "From": CUSTOMER,
                                     "Body": "Maria, 123 J St Sacramento, tomorrow morning works"})
    owner_alerts = [m for m in sms.outbox if m["to"] == OWNER]
    assert len(owner_alerts) == 1 and "123 J St" in owner_alerts[0]["body"]
    assert sms.outbox[-1]["to"] == CUSTOMER and "confirm" in sms.outbox[-1]["body"]

    jobs = client.get(f"/admin/businesses/{client.business_id}/jobs", headers=ADMIN).json()
    assert len(jobs) == 1 and jobs[0]["urgency"] == "soon"

    stats = client.get(f"/admin/businesses/{client.business_id}/stats", headers=ADMIN).json()
    assert stats["missed_calls"] == 1
    assert stats["jobs_captured"] == 1
    assert stats["estimated_revenue_saved"] == 500


def test_emergency_flagged_to_owner(client, monkeypatch):
    fake = FakeClaude([
        [tool_block("submit_job", {"customer_name": "Bob", "address": "9 Elm, Elk Grove",
                                   "issue": "No AC, elderly parent, 108F", "urgency": "emergency"})],
        [text_block("I've flagged this as urgent. The owner will call you ASAP.")],
    ])
    monkeypatch.setattr(ai, "get_client", lambda: fake)
    client.post(f"/admin/businesses/{client.business_id}/simulate/sms", headers=ADMIN,
                json={"customer_phone": CUSTOMER, "body": "AC dead, my mom is 85, its 108 out"})
    assert any(m["to"] == OWNER and "EMERGENCY" in m["body"] for m in sms.outbox)


def test_stop_opts_out_and_blocks_future_texts(client, monkeypatch):
    client.post(f"/admin/businesses/{client.business_id}/simulate/missed-call", headers=ADMIN,
                json={"customer_phone": CUSTOMER})
    sent_before = len(sms.outbox)
    client.post("/twilio/sms", data={"To": BIZ_NUMBER, "From": CUSTOMER, "Body": "STOP"})
    monkeypatch.setattr(ai, "get_client", lambda: pytest.fail("Claude should not be called"))
    client.post("/twilio/sms", data={"To": BIZ_NUMBER, "From": CUSTOMER, "Body": "hello?"})
    r = client.post(f"/admin/businesses/{client.business_id}/simulate/missed-call", headers=ADMIN,
                    json={"customer_phone": CUSTOMER})
    assert r.json()["sent"] is None
    assert len(sms.outbox) == sent_before


def test_ai_failure_alerts_owner(client, monkeypatch):
    def boom():
        raise RuntimeError("api down")
    monkeypatch.setattr(ai, "get_client", boom)
    client.post("/twilio/sms", data={"To": BIZ_NUMBER, "From": CUSTOMER, "Body": "need a plumber"})
    assert sms.outbox[-1]["to"] == OWNER and "need a plumber" in sms.outbox[-1]["body"]


def test_unknown_number_404(client):
    r = client.post("/twilio/voice", data={"To": "+10000000000", "From": CUSTOMER})
    assert r.status_code == 404


def test_twilio_signature_enforced(client, monkeypatch):
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "secret")
    r = client.post("/twilio/voice", data={"To": BIZ_NUMBER, "From": CUSTOMER},
                    headers={"X-Twilio-Signature": "bad"})
    assert r.status_code == 403
