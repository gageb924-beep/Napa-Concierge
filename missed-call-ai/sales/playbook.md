# Sales Playbook: Sacramento Missed Call AI

Goal: **3 free pilots in 30 days → 10 paying customers by day 90 (~$3-4k MRR).**

## 1. The offer

| Plan | Price | What they get |
|---|---|---|
| **Starter** | $297/mo | Missed-call text-back, AI job qualification, owner alerts, monthly report |
| **Pro** | $497/mo | Starter + emergency priority alerts, custom knowledge (pricing, promos), review requests (roadmap) |
| Setup | $0 during pilots, $199 after | We configure everything and test it with them |

**Pilot:** first 30 days free; no contract, cancel by text. In exchange they give a testimonial if it captures at least one job.

**The math to say out loud:** *"If this catches one $450 service call a month, it's paid for. Most shops miss 5-15 calls a week in summer."*

## 2. Who to target first

Best fit, in order:
1. **HVAC** (summer 100°F+ days mean panic calls and high ticket values). Pitch May through September, and furnace season Nov-Jan.
2. **Plumbing** (emergencies year-round)
3. **Roofing** (rainy season Nov-Mar; big tickets)
4. **Garage door, electrical, pest control**

Sweet spot: **owner-operator or 2-10 trucks**. The owner is on jobs all day, there's no full-time receptionist, and they have 20-200 Google reviews. Skip companies with call centers.

Areas: Sacramento, Elk Grove, Roseville, Rocklin, Folsom, Citrus Heights, Rancho Cordova, Natomas, Carmichael, West Sac, Davis.

### Build the list
- Google Maps: search "HVAC Elk Grove", "plumber Roseville", etc. Export name, phone, website, review count. (A scraper such as Outscraper or Apify works; or do it manually, 50 per evening.)
- Find owner emails on their website "About" page, BBB listing, CSLB license lookup (cslb.ca.gov shows the license holder's name), or Hunter.io.
- Load into Instantly as a new campaign, the same setup as Concierge Edge (`../../instantly-campaign-setup.md`), but **use a separate sending domain** for this brand.

## 3. The killer move: the after-hours call test

Before emailing anyone, **call them**: at 5:30-7pm, or midday when crews are out. Log the result in your sheet:

| Business | Called at | Answered? | Called back? | Hours until callback |
|---|---|---|---|---|

Anyone who doesn't answer becomes a personalized pitch: *"I called you Tuesday at 6:10pm and got voicemail. You never called back."* That's not hypothetical, it's their lost job. Expect 30-50% to miss.

## 4. Cold email sequence (Instantly)

**Email 1 (day 0)**
> Subject: called {{companyName}} tuesday
>
> Hi {{firstName}},
>
> I called {{companyName}} Tuesday around 6pm and went to voicemail. Totally normal when you're on a job, but most people who hit voicemail just call the next HVAC company on Google.
>
> I set up a simple system for Sacramento contractors: when you miss a call, the customer gets a text from your business within seconds. It finds out what they need and their address, then texts you the job.
>
> Want me to set it up free for 30 days and see how many jobs it catches?
>
> Gage
> 916-XXX-XXXX

**Email 2 (day 3)**
> Subject: re: called {{companyName}} tuesday
>
> Quick math: if it catches one $400 repair a month, it pays for itself. In July most shops miss 10+ calls a week.
>
> No new app, no new phone number for you to learn. Calls still ring your cell first. Worth a 10-minute look?

**Email 3 (day 7)**
> Subject: demo
>
> Here's a 60-second video of it working: a missed call, the text conversation, and the job alert that lands on the owner's phone. [Loom link]
>
> Reply "yes" and I'll set yours up this week. Free for 30 days.

**Email 4 (day 14, breakup)**
> Subject: closing the loop
>
> I'll stop reaching out. If missed calls ever become a headache in peak season, just reply to this and I'll get you set up in a day.

Use `{{companyName}}`-style variables matching your Instantly CSV columns. Only reference a call test you actually did; for businesses you didn't call, swap the first line to *"Most Sacramento HVAC shops miss 30-40% of calls in summer."*

## 5. Phone / walk-in script

> "Hey, is this the owner? I'm Gage, local here in Sacramento. Quick question: when you're on a job and miss a call, what happens to that customer?"
>
> *(They usually say "they leave a voicemail" or "I call them back later.")*
>
> "Right, and a lot of them don't leave one; they just call the next guy. I set up a thing where your business texts them back automatically within seconds, gets the job details, and texts you the summary. Can I show you on my phone? Takes 60 seconds."

**Then do the live demo** from the dashboard on your phone or laptop: simulate a missed call with *their* business name loaded. Seeing their own name in the text closes the deal.

### Objections
- **"I call everyone back."** "Great. How fast? Customers with no AC call the next company within 5 minutes. This just buys you time."
- **"I don't want a robot talking to my customers."** "It only texts people you already missed, and you can read every conversation. It never quotes prices or promises times. It hands off to you."
- **"Too expensive."** "It's free for 30 days. If it doesn't catch a job worth more than the fee, cancel by text."
- **"I already have an answering service."** "How much is it per month, and does it answer at 9pm Sunday? This runs 24/7 for less, and you get the job details in writing."

## 6. Onboarding checklist (per customer, ~30 min)

- [ ] Signed pilot agreement (simple one-pager; adapt `../../frontend/contract.html`)
- [ ] Buy a 916/279 Twilio number, add it to your A2P Messaging Service, and set the webhooks
- [ ] Add the business in the dashboard: services, price ranges they're OK sharing, service area, hours, avg job value
- [ ] Set up conditional call forwarding from their business line (or put the number on Google Business Profile)
- [ ] Test: call from your phone, don't answer, complete the text flow, confirm the owner gets the alert
- [ ] Check in at day 7 and day 21 with their stats. At day 25, show the "jobs captured / revenue saved" numbers and convert to paid.

## 7. Business setup (do in week 1)

- [ ] Pick a name and domain (check Sacramento County fictitious business name + CA SOS availability)
- [ ] Separate LLC or a DBA under your existing entity. Ask your accountant which is better for running two businesses.
- [ ] Separate business bank account + Stripe
- [ ] **Start Twilio A2P 10DLC registration now** (it takes 1-3 weeks)
- [ ] Google Workspace email on the new domain, plus a separate cold-email domain for Instantly (warm it up 2 weeks)
- [ ] Record the 60-second Loom demo

## 8. 90-day plan

| Weeks | Focus | Target |
|---|---|---|
| 1-2 | Entity, domain, Twilio + A2P, deploy, Loom demo, call-test 50 shops | System live on your own number |
| 3-4 | Emails + calls + walk-ins | 3 pilots live |
| 5-8 | Convert pilots; ask each for 1 referral; keep outreach running | 5 paying |
| 9-12 | Monthly report email, raise setup fee, start on roadmap item #2 | 10 paying (~$3-4k MRR) |

Time split with Concierge Edge: one fixed day a week for Napa (support + sales), the rest here until you hit 10 customers.
