"""
Thin wrapper around Twilio so the rest of the app (and tests) don't care whether SMS is live.
"""

import logging
import os

log = logging.getLogger("missed-call-ai")

# Messages "sent" while Twilio isn't configured (local dev, demos, tests)
outbox: list[dict] = []

_client = None


def _twilio():
    global _client
    sid, token = os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN")
    if not (sid and token):
        return None
    if _client is None:
        from twilio.rest import Client
        _client = Client(sid, token)
    return _client


def send_sms(from_number: str, to_number: str, body: str) -> None:
    client = _twilio()
    if client is None:
        log.info("[dry-run SMS] %s -> %s: %s", from_number, to_number, body)
        outbox.append({"from": from_number, "to": to_number, "body": body})
        return
    try:
        client.messages.create(from_=from_number, to=to_number, body=body)
    except Exception:
        log.exception("Failed to send SMS to %s", to_number)
