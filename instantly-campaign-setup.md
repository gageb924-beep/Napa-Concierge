# Instantly.ai Campaign Setup Guide

## Step 1: Import Your Leads

### For Hotels Campaign:
1. Go to **Leads** → **Upload Leads**
2. Upload `instantly-hotels.csv`
3. Map columns:
   - Email → Email
   - Company → Company Name
   - Website → Website
   - Phone → Phone
   - Location → Custom Variable
   - Personalization → Personalization

### For Wineries Campaign:
1. Same process with `instantly-wineries.csv`

---

## Step 2: Create Hotel Campaign

**Campaign Name:** Napa Concierge - Hotels

### Email 1 (Day 0)

**Subject:** Your guests are asking the same questions every day

**Body:**
```
Hi,

I noticed {{Company}} gets great reviews for guest experience - especially {{Personalization}}.

Quick question: how much time does your front desk spend answering "where should we eat?" and "which wineries should we visit?"

I built an AI concierge specifically for Napa Valley hotels. It knows every winery, restaurant, and hidden gem in the valley - and answers guests 24/7 via a chat widget on your site.

Here's a 30-second demo: [YOUR_DEMO_URL]

A few hotels are already using it to:
• Free up front desk staff for higher-value tasks
• Capture guest emails before they even check in
• Provide consistent, knowledgeable recommendations at 2am

Would a quick 10-minute call be useful? I can show you exactly how it would look on {{Company}}'s website.

Best,
[Your Name]

P.S. - The widget matches your brand colors and can include your specific partnerships.
```

---

### Email 2 (Day 4)

**Subject:** Re: Your guests are asking the same questions every day

**Body:**
```
Hi,

Just floating this back up - I know hospitality keeps you busy.

Here's the 30-second version: AI concierge for {{Company}}'s website that knows Napa Valley inside and out. Answers guest questions 24/7, captures leads, matches your brand.

Demo takes 2 minutes to watch: [YOUR_DEMO_URL]

Happy to jump on a quick call if it looks interesting.

[Your Name]
```

---

### Email 3 (Day 11)

**Subject:** Should I close your file?

**Body:**
```
Hi,

I've reached out a couple times about the AI concierge - totally understand if it's not a fit right now.

If you're interested in exploring this later, just reply "later" and I'll check back in a few months.

Either way, no hard feelings. Cheers to a great season in wine country.

[Your Name]
```

---

## Step 3: Create Winery Campaign

**Campaign Name:** Napa Concierge - Wineries

### Email 1 (Day 0)

**Subject:** Idea for {{Company}} tasting room

**Body:**
```
Hi,

I saw {{Company}} offers incredible tasting experiences - especially {{Personalization}}.

Here's a thought: what if visitors could get personalized recommendations *before* they arrive? Things like what to eat nearby, what other wineries to visit, or how to plan their day around their {{Company}} appointment.

I built an AI concierge for Napa Valley that does exactly this. It lives on your website and helps visitors:
• Plan their day around their tasting appointment
• Get dining recommendations that pair with your wines
• Answer questions 24/7 (even when you're pouring)

Quick demo: [YOUR_DEMO_URL]

It also captures visitor emails and interests - so you know who's coming and what they care about before they walk through your doors.

Worth a 10-minute look?

Best,
[Your Name]
```

---

### Email 2 (Day 4)

**Subject:** Re: Idea for {{Company}} tasting room

**Body:**
```
Hi,

Just circling back on this - I know harvest season and tastings keep you slammed.

Quick recap: AI concierge for your website that helps visitors plan around their {{Company}} appointment. Answers questions 24/7, captures leads before they arrive.

2-minute demo: [YOUR_DEMO_URL]

Worth a quick look?

[Your Name]
```

---

### Email 3 (Day 11)

**Subject:** Should I close your file?

**Body:**
```
Hi,

I've reached out a couple times about the AI concierge - totally understand if it's not the right time.

If you want to revisit this later, just reply "later" and I'll reach out in a few months.

Either way, wishing you a great vintage this year.

[Your Name]
```

---

## Step 4: Campaign Settings

### Sending Schedule:
- **Days:** Tuesday, Wednesday, Thursday only
- **Time:** 8:00 AM - 10:00 AM Pacific
- **Timezone:** America/Los_Angeles

### Sending Limits:
- **Daily limit:** Start with 15/day per email account
- **Ramp up:** Increase by 5/day each week until you hit 40-50/day

### Tracking:
- ✅ Enable open tracking
- ✅ Enable click tracking
- ✅ Enable reply detection (stops sequence on reply)

### Warmup:
- ✅ Keep warmup ON even while sending campaigns
- Set warmup to "Conservative" mode

---

## Step 5: Before You Launch

### Checklist:
- [ ] Replace `[YOUR_DEMO_URL]` with your actual demo page URL
- [ ] Replace `[Your Name]` with your name
- [ ] Connect your sending email account
- [ ] Run warmup for at least 7-14 days before sending
- [ ] Verify your sending domain has SPF, DKIM, DMARC set up
- [ ] Test send to yourself first

---

## Tips for Success

1. **Start with Hotels** - They're a better fit and will respond faster

2. **Personalization matters** - The {{Personalization}} field has specific things about each business. Use it!

3. **Reply quickly** - When someone responds, reply within 2 hours if possible

4. **Track in your spreadsheet** - Update `prospects.csv` with responses

5. **Don't over-send** - 15-20 emails/day is plenty to start

---

## Handling Responses

### If they say "interested":
Book a call immediately. Use Calendly or just propose 2-3 times.

### If they say "not now" or "later":
Add to a "Follow up in 3 months" list. Thank them and move on.

### If they say "unsubscribe":
Remove immediately. Never email them again.

### If they ask questions:
Answer quickly, then pivot to booking a demo call.
