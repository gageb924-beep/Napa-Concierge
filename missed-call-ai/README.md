# Missed Call AI

**Never lose a job to voicemail.** When a customer calls a contractor and nobody picks up, this texts them back within seconds, has an AI qualify the job, and sends the owner a ready-to-book summary.

Built for Sacramento-area home service businesses: HVAC, plumbing, roofing, electrical, pest control, solar, garage doors. Runs separately from Napa Concierge (own server, own database, own Twilio numbers).

```
Customer calls  ──►  Business's Twilio number  ──►  rings owner's cell (20s)
                                                      │
                                         answered ◄───┴───► missed
                                                              │
                         "Sorry we missed you! What can we help with?"  (SMS, ~3 sec)
                                                              │
                         AI texts back & forth: problem, address, urgency, time
                                                              │
                         Owner gets:  🚨 EMERGENCY New job: Maria, 123 J St,
                                      AC blowing warm air, tomorrow AM
```

## What's included

| Piece | Where |
|---|---|
| Twilio voice + SMS webhooks, forwarding, text-back | `backend/main.py` |
| Claude prompt + job-capture tools (`submit_job`, `hand_off_to_owner`) | `backend/ai.py` |
| Multi-business database (calls, conversations, jobs) | `backend/database.py` |
| Admin dashboard + **live demo phone** for sales meetings | `frontend/dashboard.html` (served at `/`) |
| Tests (Claude + Twilio mocked) | `backend/tests/` |
| Render deploy blueprint | `render.yaml` |
| Sales playbook: prospecting, scripts, emails, pricing | `sales/playbook.md` |

Built-in safeguards:
- Twilio signature verification on every webhook
- STOP/START opt-out handling (no texts to opted-out numbers, ever)
- No double-texting a repeat caller within 24h
- Emergency jobs flagged to the owner
- If the AI errors, the owner is texted to follow up so no lead is dropped
- AI never quotes exact prices or arrival times

## Run it locally (5 min, no Twilio needed)

```bash
cd missed-call-ai/backend
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                                # add ANTHROPIC_API_KEY and ADMIN_API_KEY
python main.py
```

Open http://localhost:8000, enter your admin key, add a business, and use the **Live demo** phone: "Simulate missed call", then text as the customer. Without Twilio credentials, texts are logged instead of sent (dry-run mode).

Tests: `python -m pytest -q`

## Go live

1. **Deploy**: In Render, choose New > Blueprint and select `missed-call-ai/render.yaml`. Set `ANTHROPIC_API_KEY`, `ADMIN_API_KEY`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `PUBLIC_BASE_URL` (your Render URL, e.g. `https://missed-call-ai.onrender.com`). Use a paid instance ($7/mo) for real customers, since the free tier sleeps and Twilio would time out.
2. **Twilio account**: Sign up and upgrade from trial.
3. **A2P 10DLC registration** (required to text US customers from a local number). **Start this first, because approval takes 1-3 weeks.** In Twilio Console go to Messaging > Regulatory Compliance. Register your brand (your LLC + EIN) and one campaign, use case "Customer Care", sample message: *"Hi, this is River City Heating & Air. Sorry we missed your call! What can we help you with? Reply STOP to opt out."* Opt-in description: *"Customers initiate contact by calling the business's phone number; we text back only the number that called."*
4. **Buy a number per customer** (916 or 279 area code, ~$1.15/mo). Under its config:
   - *A call comes in* → Webhook `POST https://YOUR-URL/twilio/voice`
   - *A message comes in* → Webhook `POST https://YOUR-URL/twilio/sms`
   - Add the number to your A2P campaign's Messaging Service.
5. **Add the business** in the dashboard with that Twilio number and the owner's cell.
6. **Customer points calls at it**, either by:
   - **Conditional call forwarding** (easiest): forward *unanswered/busy* calls from their existing business line to the Twilio number. Most carriers: dial `*71` + number (Verizon), `**61*number#` (AT&T/T-Mobile). Set `ring_seconds` to `0` (dashboard API: `PUT /admin/businesses/{id}`) so the call isn't rung again and the text goes out immediately.
   - **Or** put the Twilio number on their Google Business Profile, website, and ads. It rings their cell first, then texts back if missed. This also gives you clean call tracking.

> **Voicemail gotcha:** If the owner's cell voicemail picks up before `ring_seconds` runs out, Twilio counts the call as answered and no text goes out. Keep `ring_seconds` (default 20) shorter than their voicemail delay (usually ~25s), or have them extend their voicemail delay.

## Costs per customer (approx.)

| Item | Monthly |
|---|---|
| Twilio number | $1.15 |
| SMS (~150 missed calls × ~6 texts) | ~$8-10 incl. carrier fees |
| Claude API | ~$3-8 |
| Render share | ~$1-2 |
| **Total** | **~$15-20** vs. $297+ price = **~93% margin** |

## Admin API

All endpoints need header `X-Admin-Key`.

| Method | Path | |
|---|---|---|
| POST/GET | `/admin/businesses` | create / list |
| PUT/DELETE | `/admin/businesses/{id}` | update / delete |
| GET | `/admin/businesses/{id}/stats?days=30` | missed calls, jobs, revenue saved |
| GET | `/admin/businesses/{id}/jobs` | captured jobs |
| PUT | `/admin/jobs/{id}` | `{"status": "scheduled" \| "won" \| "lost"}` |
| GET | `/admin/businesses/{id}/conversations` | full SMS transcripts |
| POST | `/admin/businesses/{id}/simulate/missed-call` | demo without a phone |
| POST | `/admin/businesses/{id}/simulate/sms` | `{"customer_phone","body"}` |

## Roadmap (after first paying customers)

1. Monthly "you'd have lost X jobs" email report (reuse Concierge Edge's Resend report code)
2. Calendar booking (Google Calendar → Jobber / Housecall Pro / ServiceTitan)
3. AI voice answering instead of ring-then-text (Vapi / Retell / Twilio ConversationRelay)
4. Customer-facing login so owners see their own dashboard
5. Review requests: text "how did we do?" + Google review link after a job is marked won
6. Stripe billing
