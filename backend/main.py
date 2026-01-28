"""
Napa Valley AI Concierge - Multi-tenant SaaS Backend
Pro Package: Analytics, Lead Capture, Custom Branding
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from anthropic import Anthropic
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date
import os
import secrets

from database import (
    init_db, get_db, Business, Conversation, Lead, Analytics, ContractSignature, generate_api_key
)

load_dotenv()

app = FastAPI(title="Napa Valley AI Concierge - Pro")

# Allow CORS for widget embedding on any domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup():
    init_db()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Admin API key for managing businesses
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "admin_" + secrets.token_urlsafe(16))

BASE_SYSTEM_PROMPT = """You are a friendly, knowledgeable concierge for Napa Valley, California. You help hotel guests and visitors plan perfect wine country experiences.

## CRITICAL RULES
1. **ONLY recommend places that are actually in Napa Valley** (Napa, Yountville, St. Helena, Calistoga, Oakville, Rutherford, American Canyon). NEVER recommend places in San Francisco, Oakland, Sacramento, or other cities.
2. **ALWAYS include clickable links** for every place you mention using the exact formats below.
3. **Only recommend places you have specific knowledge about** - don't make up restaurants or businesses.

## Your Personality
- Warm and welcoming, like a knowledgeable local friend
- Enthusiastic about Napa but honest about what fits each guest's preferences
- Concise but helpful - respect people's time

## Your Knowledge

### Wine Regions & Styles
- **Oakville/Rutherford**: Bold Cabernet Sauvignons, prestigious estates (Opus One, Robert Mondavi, Caymus)
- **Stags Leap District**: Elegant Cabernets, famous for the 1976 Judgment of Paris
- **Yountville**: Walkable, great restaurants, approachable wineries
- **St. Helena**: Classic Napa, mix of historic and modern wineries
- **Calistoga**: Northern Napa, warmer climate, great Zinfandels, hot springs
- **Carneros**: Cooler climate, excellent Pinot Noir and Chardonnay, sparkling wines

### Top Winery Recommendations by Style

**First-Time Visitors (Great Intro Experiences):**
- Robert Mondavi Winery - iconic, educational tours
- Sterling Vineyards - aerial tram with valley views
- Domaine Chandon - beautiful grounds, sparkling wine
- V. Sattui - picnic grounds, no appointment needed

**Luxury/Special Occasion:**
- Opus One - architectural masterpiece, appointment only
- HALL Wines - stunning art collection
- Castello di Amorosa - medieval castle experience
- Inglenook (Coppola's estate) - historic and grand

**Hidden Gems/Off the Beaten Path:**
- Frog's Leap - organic, fun atmosphere
- Tres Sabores - small family winery, authentic
- Smith-Madrone - mountain views, family-run since 1971
- Matthiasson - focused, minimalist winemaking

**Best Views:**
- Sterling Vineyards - gondola ride
- Artesa - modern architecture, Carneros views
- Castello di Amorosa - castle on a hill
- Pride Mountain - straddles Napa/Sonoma

### Dining Recommendations

**Fine Dining:**
- The French Laundry (Yountville) - 3 Michelin stars, book months ahead
- Meadowood Restaurant (St. Helena) - elegant, estate setting
- Kenzo Napa (Napa) - Japanese-California fusion
- Bottega (Yountville) - Michael Chiarello's Italian
- Bouchon Bistro (Yountville) - Thomas Keller's French bistro

**Farm-to-Table & American:**
- Farmstead at Long Meadow Ranch (St. Helena) - farm-to-table
- Goose & Gander (St. Helena) - great cocktails, gastropub
- Mustards Grill (Yountville) - Napa classic since 1983
- Cindy's Backstreet Kitchen (St. Helena) - comfort food
- Gott's Roadside (multiple locations) - gourmet burgers

**Mexican & Latin Restaurants in Napa Valley:**
- La Taquiza (Napa) - 2007 Redwood Rd, fresh fish tacos, casual outdoor seating, great margaritas
- Taqueria Maria (Napa) - 1781 Old Sonoma Rd, family-run since 1998, generous portions, great salsa bar
- Villa Corona (St. Helena) - 1138 Main St, local favorite, traditional recipes, friendly atmosphere
- Pancha's (Yountville) - 6764 Washington St, beloved for breakfast burritos, cash only, no-frills spot
- La Luna Market & Taqueria (Rutherford) - 1153 Rutherford Rd, taqueria inside a local market, quick and delicious
- Azteca Market (St. Helena) - 1245 Main St, great tamales and homemade tortillas
- C Casa (Napa, Oxbow Market) - 610 1st St, modern Mexican, craft cocktails, inside Oxbow Public Market

**Casual/Quick:**
- Oxbow Public Market (Napa) - food hall with multiple vendors
- Model Bakery (St. Helena & Yountville) - famous English muffins
- Oakville Grocery - picnic supplies since 1881

### Activities Beyond Wine

- **Hot Air Balloons**: Napa Valley Balloons, Calistoga Balloons (book early morning)
- **Napa Valley Wine Train**: Scenic rail journey with food/wine
- **Calistoga Hot Springs**: Old Faithful Geyser, mud baths, spas
- **Biking**: Napa Valley Vine Trail, rent bikes in Yountville
- **Olive Oil Tasting**: Long Meadow Ranch, Round Pond
- **Art**: di Rosa Center for Contemporary Art, Hess Collection

### Practical Tips
- Most wineries require reservations (especially since 2020)
- Tasting fees: $30-100+ per person, often waived with purchase
- Designate a driver or use Uber/taxi/tour company
- Best months: September-October (harvest), March-May (mustard season)
- Avoid Highway 29 on weekends - use Silverado Trail instead

## How to Help Guests

1. **Ask about preferences**: What wines do they like? Budget? Interests beyond wine?
2. **Consider logistics**: How many days? Where are they staying? Transportation?
3. **Build balanced itineraries**: Mix of experiences, don't over-schedule (3-4 wineries max/day)
4. **Offer specific names**: Don't be vague - give actual winery/restaurant names
5. **Mention booking requirements**: Many places need reservations

When building itineraries, format them clearly with times and locations. Always ask follow-up questions to personalize recommendations.

## IMPORTANT: Always Include Links

EVERY place you mention MUST have a clickable link. Use these exact formats:

### For places with known websites, use the website:
- [Robert Mondavi Winery](https://www.robertmondaviwinery.com)
- [The French Laundry](https://www.thomaskeller.com/tfl)
- [Opus One](https://www.opusonewinery.com)
- [Bottega](https://www.botteganapavalley.com)
- [Mustards Grill](https://www.mustardsgrill.com)
- [Gott's Roadside](https://www.gotts.com)
- [Oxbow Public Market](https://www.oxbowpublicmarket.com)

### For restaurants/places without a website, use Google Maps with the EXACT address:
Format: `https://www.google.com/maps/search/FULL+ADDRESS+CITY+STATE`

**Mexican Restaurant Links (use these exact links):**
- [La Taquiza](https://www.google.com/maps/search/2007+Redwood+Rd+Napa+CA)
- [Taqueria Maria](https://www.google.com/maps/search/1781+Old+Sonoma+Rd+Napa+CA)
- [Villa Corona](https://www.google.com/maps/search/1138+Main+St+St+Helena+CA)
- [Pancha's](https://www.google.com/maps/search/6764+Washington+St+Yountville+CA)
- [La Luna Market & Taqueria](https://www.google.com/maps/search/1153+Rutherford+Rd+Rutherford+CA)
- [Azteca Market](https://www.google.com/maps/search/1245+Main+St+St+Helena+CA)
- [C Casa](https://www.google.com/maps/search/610+First+St+Napa+CA+Oxbow+Market)

### Known Website URLs:
**Wineries:**
- Robert Mondavi: robertmondaviwinery.com
- Opus One: opusonewinery.com
- Domaine Chandon: chandon.com
- Sterling Vineyards: sterlingvineyards.com
- V. Sattui: vsattui.com
- Castello di Amorosa: castellodiamorosa.com
- HALL Wines: hallwines.com
- Frog's Leap: frogsleap.com
- Inglenook: inglenook.com
- Artesa: artesawinery.com

**Restaurants:**
- The French Laundry: thomaskeller.com/tfl
- Bouchon Bistro: thomaskeller.com/bouchonbistro
- Bottega: botteganapavalley.com
- Farmstead: longmeadowranch.com/eat-drink/farmstead-restaurant
- Gott's Roadside: gotts.com
- Mustards Grill: mustardsgrill.com
- Oxbow Public Market: oxbowpublicmarket.com
- Goose & Gander: goosegander.com

**IMPORTANT:** If you don't have a specific address, use this format with the restaurant name AND city:
`https://www.google.com/maps/search/Restaurant+Name+City+CA+Napa+Valley`

Example: [Villa Corona](https://www.google.com/maps/search/Villa+Corona+St+Helena+CA)

NEVER just link to a generic city or area - always include the business name and specific location.

## Lead Capture

If a guest seems very interested in booking something or wants to be contacted, politely ask if they'd like to share their email or phone number so the staff can follow up with them personally. Say something like: "Would you like me to have someone from our team reach out to help you book this? I can pass along your contact info."

NEVER be pushy about this - only offer when it's genuinely helpful."""


# ============== Pydantic Models ==============

class ChatMessage(BaseModel):
    message: str
    conversation_history: list = []
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_history: list
    session_id: str

class LeadCapture(BaseModel):
    session_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    interest: Optional[str] = None
    notes: Optional[str] = None

class BusinessCreate(BaseModel):
    name: str
    business_type: str = "hotel"
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    primary_color: str = "#722F37"
    welcome_message: Optional[str] = None
    widget_title: str = "Concierge"
    widget_subtitle: str = "Your personal wine country guide"
    custom_knowledge: Optional[str] = None

class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    primary_color: Optional[str] = None
    welcome_message: Optional[str] = None
    widget_title: Optional[str] = None
    widget_subtitle: Optional[str] = None
    custom_knowledge: Optional[str] = None
    is_active: Optional[bool] = None

class ContractSign(BaseModel):
    signer_name: str
    signer_email: str
    company_name: str
    company_type: Optional[str] = None


# ============== Helper Functions ==============

def get_business_by_api_key(api_key: str, db: Session) -> Business:
    """Get business by API key or raise 401"""
    business = db.query(Business).filter(Business.api_key == api_key, Business.is_active == True).first()
    if not business:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return business

def verify_admin_key(api_key: str):
    """Verify admin API key"""
    if api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin API key")

def build_system_prompt(business: Business) -> str:
    """Build customized system prompt for a business"""
    prompt = BASE_SYSTEM_PROMPT

    # Add business-specific context
    business_context = f"""

## About This Business

You are the AI concierge for **{business.name}**. When greeting guests or referring to the property, use this name.
"""

    if business.custom_knowledge:
        business_context += f"""

## Special Information About {business.name}

{business.custom_knowledge}
"""

    return prompt + business_context

def update_analytics(db: Session, business_id: int, message_text: str):
    """Update daily analytics for a business"""
    today = date.today()
    analytics = db.query(Analytics).filter(
        Analytics.business_id == business_id,
        Analytics.date == today
    ).first()

    if not analytics:
        analytics = Analytics(business_id=business_id, date=today, total_conversations=0, total_messages=0, unique_visitors=0, leads_captured=0)
        db.add(analytics)

    analytics.total_messages = (analytics.total_messages or 0) + 1
    db.commit()


# ============== Public API (Widget) ==============

@app.get("/")
async def root():
    return {"status": "Napa Valley AI Concierge Pro is running"}

@app.get("/widget/config")
async def get_widget_config(
    api_key: str,
    db: Session = Depends(get_db)
):
    """Get widget configuration for a business"""
    business = get_business_by_api_key(api_key, db)

    return {
        "business_name": business.name,
        "primary_color": business.primary_color,
        "welcome_message": business.welcome_message or f"Welcome to {business.name}! I'm your personal Napa Valley concierge. How can I help you today?",
        "widget_title": business.widget_title,
        "widget_subtitle": business.widget_subtitle
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(
    chat_message: ChatMessage,
    request: Request,
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Chat endpoint - requires business API key"""
    business = get_business_by_api_key(api_key, db)

    # Get or create conversation
    session_id = chat_message.session_id or secrets.token_urlsafe(16)
    conversation = db.query(Conversation).filter(
        Conversation.business_id == business.id,
        Conversation.session_id == session_id
    ).first()

    if not conversation:
        conversation = Conversation(
            business_id=business.id,
            session_id=session_id,
            visitor_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")[:500],
            referrer=request.headers.get("referer", "")[:500],
            message_count=0
        )
        db.add(conversation)

        # Update unique visitors in analytics
        today = date.today()
        analytics = db.query(Analytics).filter(
            Analytics.business_id == business.id,
            Analytics.date == today
        ).first()
        if not analytics:
            analytics = Analytics(business_id=business.id, date=today, total_conversations=0, total_messages=0, unique_visitors=0, leads_captured=0)
            db.add(analytics)
        analytics.total_conversations = (analytics.total_conversations or 0) + 1
        analytics.unique_visitors = (analytics.unique_visitors or 0) + 1

    conversation.message_count = (conversation.message_count or 0) + 1
    conversation.last_message_at = datetime.utcnow()

    try:
        # Build messages list with history
        messages = chat_message.conversation_history.copy()
        messages.append({"role": "user", "content": chat_message.message})

        # Call Claude with business-specific prompt
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=build_system_prompt(business),
            messages=messages
        )

        assistant_message = response.content[0].text

        # Update conversation history
        updated_history = messages.copy()
        updated_history.append({"role": "assistant", "content": assistant_message})

        # Store messages for analytics
        conversation.messages = updated_history

        # Update analytics
        update_analytics(db, business.id, chat_message.message)

        db.commit()

        return ChatResponse(
            response=assistant_message,
            conversation_history=updated_history,
            session_id=session_id
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/lead")
async def capture_lead(
    lead_data: LeadCapture,
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Capture a lead from the chat widget"""
    business = get_business_by_api_key(api_key, db)

    # Find conversation
    conversation = db.query(Conversation).filter(
        Conversation.business_id == business.id,
        Conversation.session_id == lead_data.session_id
    ).first()

    lead = Lead(
        business_id=business.id,
        conversation_id=conversation.id if conversation else None,
        name=lead_data.name,
        email=lead_data.email,
        phone=lead_data.phone,
        interest=lead_data.interest,
        notes=lead_data.notes
    )
    db.add(lead)

    # Update analytics
    today = date.today()
    analytics = db.query(Analytics).filter(
        Analytics.business_id == business.id,
        Analytics.date == today
    ).first()
    if analytics:
        analytics.leads_captured += 1

    db.commit()

    return {"status": "success", "message": "Lead captured"}


# ============== Admin API ==============

@app.post("/admin/businesses")
async def create_business(
    business_data: BusinessCreate,
    x_admin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Create a new business (admin only)"""
    verify_admin_key(x_admin_key)

    business = Business(
        name=business_data.name,
        business_type=business_data.business_type,
        contact_email=business_data.contact_email,
        contact_phone=business_data.contact_phone,
        website=business_data.website,
        primary_color=business_data.primary_color,
        welcome_message=business_data.welcome_message,
        widget_title=business_data.widget_title,
        widget_subtitle=business_data.widget_subtitle,
        custom_knowledge=business_data.custom_knowledge
    )
    db.add(business)
    db.commit()
    db.refresh(business)

    return {
        "id": business.id,
        "api_key": business.api_key,
        "name": business.name,
        "message": "Business created successfully. Share the API key with the client."
    }

@app.get("/admin/businesses")
async def list_businesses(
    x_admin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """List all businesses (admin only)"""
    verify_admin_key(x_admin_key)

    businesses = db.query(Business).all()
    return [
        {
            "id": b.id,
            "api_key": b.api_key,
            "name": b.name,
            "business_type": b.business_type,
            "is_active": b.is_active,
            "created_at": b.created_at
        }
        for b in businesses
    ]

@app.get("/admin/businesses/{business_id}")
async def get_business(
    business_id: int,
    x_admin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get business details (admin only)"""
    verify_admin_key(x_admin_key)

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    return {
        "id": business.id,
        "api_key": business.api_key,
        "name": business.name,
        "business_type": business.business_type,
        "contact_email": business.contact_email,
        "contact_phone": business.contact_phone,
        "website": business.website,
        "primary_color": business.primary_color,
        "welcome_message": business.welcome_message,
        "widget_title": business.widget_title,
        "widget_subtitle": business.widget_subtitle,
        "custom_knowledge": business.custom_knowledge,
        "is_active": business.is_active,
        "created_at": business.created_at
    }

@app.put("/admin/businesses/{business_id}")
async def update_business(
    business_id: int,
    updates: BusinessUpdate,
    x_admin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Update a business (admin only)"""
    verify_admin_key(x_admin_key)

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(business, field, value)

    db.commit()
    return {"status": "success", "message": "Business updated"}


@app.delete("/admin/businesses/{business_id}")
async def delete_business(
    business_id: int,
    x_admin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Delete a business and all its data (admin only)"""
    verify_admin_key(x_admin_key)

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    business_name = business.name

    try:
        # Delete in correct order due to foreign key constraints
        # 1. Leads first (references conversations)
        db.query(Lead).filter(Lead.business_id == business_id).delete(synchronize_session=False)
        # 2. Conversations
        db.query(Conversation).filter(Conversation.business_id == business_id).delete(synchronize_session=False)
        # 3. Analytics
        db.query(Analytics).filter(Analytics.business_id == business_id).delete(synchronize_session=False)
        # 4. Business
        db.delete(business)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")

    return {"status": "success", "message": f"Business '{business_name}' deleted"}

@app.get("/admin/businesses/{business_id}/analytics")
async def get_business_analytics(
    business_id: int,
    days: int = 30,
    x_admin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get analytics for a business (admin only)"""
    verify_admin_key(x_admin_key)

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    from datetime import timedelta
    start_date = date.today() - timedelta(days=days)

    analytics = db.query(Analytics).filter(
        Analytics.business_id == business_id,
        Analytics.date >= start_date
    ).order_by(Analytics.date.desc()).all()

    # Get totals
    total_conversations = sum(a.total_conversations for a in analytics)
    total_messages = sum(a.total_messages for a in analytics)
    total_leads = sum(a.leads_captured for a in analytics)

    return {
        "business_name": business.name,
        "period_days": days,
        "totals": {
            "conversations": total_conversations,
            "messages": total_messages,
            "leads_captured": total_leads
        },
        "daily": [
            {
                "date": str(a.date),
                "conversations": a.total_conversations,
                "messages": a.total_messages,
                "leads": a.leads_captured
            }
            for a in analytics
        ]
    }

@app.get("/admin/businesses/{business_id}/leads")
async def get_business_leads(
    business_id: int,
    x_admin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get leads for a business (admin only)"""
    verify_admin_key(x_admin_key)

    leads = db.query(Lead).filter(Lead.business_id == business_id).order_by(Lead.created_at.desc()).all()

    return [
        {
            "id": l.id,
            "name": l.name,
            "email": l.email,
            "phone": l.phone,
            "interest": l.interest,
            "notes": l.notes,
            "created_at": l.created_at
        }
        for l in leads
    ]

@app.post("/admin/send-weekly-reports")
async def send_weekly_reports(
    x_admin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Send weekly reports to all businesses with contact emails (admin only)"""
    verify_admin_key(x_admin_key)

    resend_api_key = os.getenv("RESEND_API_KEY")
    if not resend_api_key:
        raise HTTPException(status_code=400, detail="RESEND_API_KEY not configured")

    import resend
    resend.api_key = resend_api_key

    from datetime import timedelta
    start_date = date.today() - timedelta(days=7)

    businesses = db.query(Business).filter(Business.is_active == True).all()
    sent_count = 0
    errors = []

    for business in businesses:
        if not business.contact_email:
            continue

        # Get analytics for this business
        analytics = db.query(Analytics).filter(
            Analytics.business_id == business.id,
            Analytics.date >= start_date
        ).all()

        total_conversations = sum(a.total_conversations for a in analytics)
        total_messages = sum(a.total_messages for a in analytics)
        total_leads = sum(a.leads_captured for a in analytics)

        # Get new leads this week
        new_leads = db.query(Lead).filter(
            Lead.business_id == business.id,
            Lead.created_at >= datetime.combine(start_date, datetime.min.time())
        ).all()

        # Build email HTML
        leads_html = ""
        if new_leads:
            leads_html = "<h3>New Leads This Week:</h3><ul>"
            for lead in new_leads:
                leads_html += f"<li><strong>{lead.name or 'Unknown'}</strong> - {lead.email or ''} {lead.phone or ''}</li>"
            leads_html += "</ul>"

        html_content = f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; max-width: 600px;">
            <h2 style="color: #722F37;">Weekly Concierge Report</h2>
            <p>Hi! Here's your weekly summary for <strong>{business.name}</strong>:</p>

            <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0;">This Week's Stats</h3>
                <p><strong>Conversations:</strong> {total_conversations}</p>
                <p><strong>Messages:</strong> {total_messages}</p>
                <p><strong>Leads Captured:</strong> {total_leads}</p>
            </div>

            {leads_html}

            <p style="color: #666; font-size: 14px; margin-top: 30px;">
                Your 24/7 concierge is working hard for you!<br>
                - Napa Concierge
            </p>
        </body>
        </html>
        """

        try:
            resend.Emails.send({
                "from": "Napa Concierge <onboarding@resend.dev>",
                "to": [business.contact_email],
                "subject": f"Weekly Report: {total_conversations} conversations, {total_leads} new leads",
                "html": html_content
            })
            sent_count += 1
        except Exception as e:
            errors.append({"business": business.name, "error": str(e)})

    return {
        "status": "success",
        "reports_sent": sent_count,
        "errors": errors
    }


@app.get("/admin/businesses/{business_id}/weekly-report")
async def get_weekly_report(
    business_id: int,
    x_admin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get weekly report data for a business (admin only)"""
    verify_admin_key(x_admin_key)

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    from datetime import timedelta
    start_date = date.today() - timedelta(days=7)

    analytics = db.query(Analytics).filter(
        Analytics.business_id == business_id,
        Analytics.date >= start_date
    ).all()

    total_conversations = sum(a.total_conversations for a in analytics)
    total_messages = sum(a.total_messages for a in analytics)
    total_leads = sum(a.leads_captured for a in analytics)

    new_leads = db.query(Lead).filter(
        Lead.business_id == business_id,
        Lead.created_at >= datetime.combine(start_date, datetime.min.time())
    ).all()

    return {
        "business_name": business.name,
        "period": "Last 7 days",
        "stats": {
            "conversations": total_conversations,
            "messages": total_messages,
            "leads_captured": total_leads
        },
        "new_leads": [
            {
                "name": l.name,
                "email": l.email,
                "phone": l.phone,
                "interest": l.interest,
                "created_at": l.created_at
            }
            for l in new_leads
        ]
    }


@app.get("/admin/businesses/{business_id}/monthly-report")
async def get_monthly_report(
    business_id: int,
    x_admin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get monthly report data for a business (admin only)"""
    verify_admin_key(x_admin_key)

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    from datetime import timedelta
    start_date = date.today() - timedelta(days=30)
    prev_start_date = date.today() - timedelta(days=60)
    prev_end_date = date.today() - timedelta(days=30)

    # Current period analytics
    analytics = db.query(Analytics).filter(
        Analytics.business_id == business_id,
        Analytics.date >= start_date
    ).all()

    # Previous period analytics for comparison
    prev_analytics = db.query(Analytics).filter(
        Analytics.business_id == business_id,
        Analytics.date >= prev_start_date,
        Analytics.date < prev_end_date
    ).all()

    total_conversations = sum(a.total_conversations for a in analytics)
    total_messages = sum(a.total_messages for a in analytics)
    total_leads = sum(a.leads_captured for a in analytics)

    prev_conversations = sum(a.total_conversations for a in prev_analytics)
    prev_messages = sum(a.total_messages for a in prev_analytics)
    prev_leads = sum(a.leads_captured for a in prev_analytics)

    new_leads = db.query(Lead).filter(
        Lead.business_id == business_id,
        Lead.created_at >= datetime.combine(start_date, datetime.min.time())
    ).all()

    return {
        "business_name": business.name,
        "period": "Last 30 days",
        "stats": {
            "conversations": total_conversations,
            "messages": total_messages,
            "leads_captured": total_leads
        },
        "previous_period": {
            "conversations": prev_conversations,
            "messages": prev_messages,
            "leads_captured": prev_leads
        },
        "new_leads": [
            {
                "name": l.name,
                "email": l.email,
                "phone": l.phone,
                "interest": l.interest,
                "created_at": l.created_at
            }
            for l in new_leads
        ]
    }


class SendReportRequest(BaseModel):
    period: str = "weekly"  # "weekly" or "monthly"


@app.post("/admin/businesses/{business_id}/send-report")
async def send_business_report(
    business_id: int,
    request_data: SendReportRequest,
    x_admin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Send a report to a specific business on-demand (admin only)"""
    verify_admin_key(x_admin_key)

    resend_api_key = os.getenv("RESEND_API_KEY")
    if not resend_api_key:
        raise HTTPException(status_code=400, detail="RESEND_API_KEY not configured")

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    if not business.contact_email:
        raise HTTPException(status_code=400, detail="Business has no contact email configured")

    import resend
    resend.api_key = resend_api_key

    from datetime import timedelta

    # Determine period
    if request_data.period == "monthly":
        days = 30
        period_label = "Monthly"
        start_date = date.today() - timedelta(days=30)
        prev_start_date = date.today() - timedelta(days=60)
        prev_end_date = date.today() - timedelta(days=30)
    else:
        days = 7
        period_label = "Weekly"
        start_date = date.today() - timedelta(days=7)
        prev_start_date = date.today() - timedelta(days=14)
        prev_end_date = date.today() - timedelta(days=7)

    # Current period analytics
    analytics = db.query(Analytics).filter(
        Analytics.business_id == business_id,
        Analytics.date >= start_date
    ).order_by(Analytics.date).all()

    # Previous period for comparison
    prev_analytics = db.query(Analytics).filter(
        Analytics.business_id == business_id,
        Analytics.date >= prev_start_date,
        Analytics.date < prev_end_date
    ).all()

    total_conversations = sum(a.total_conversations for a in analytics)
    total_messages = sum(a.total_messages for a in analytics)
    total_leads = sum(a.leads_captured for a in analytics)

    prev_conversations = sum(a.total_conversations for a in prev_analytics)
    prev_messages = sum(a.total_messages for a in prev_analytics)
    prev_leads = sum(a.leads_captured for a in prev_analytics)

    # Calculate changes
    def calc_change(current, previous):
        if previous == 0:
            return "+100%" if current > 0 else "0%"
        change = ((current - previous) / previous) * 100
        return f"+{change:.0f}%" if change >= 0 else f"{change:.0f}%"

    conv_change = calc_change(total_conversations, prev_conversations)
    msg_change = calc_change(total_messages, prev_messages)
    lead_change = calc_change(total_leads, prev_leads)

    # Get new leads
    new_leads = db.query(Lead).filter(
        Lead.business_id == business_id,
        Lead.created_at >= datetime.combine(start_date, datetime.min.time())
    ).all()

    # Build daily breakdown
    daily_rows = ""
    for a in analytics:
        daily_rows += f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">{a.date.strftime('%b %d')}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee; text-align: center;">{a.total_conversations}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee; text-align: center;">{a.total_messages}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee; text-align: center;">{a.leads_captured}</td>
        </tr>
        """

    # Build leads HTML
    leads_html = ""
    if new_leads:
        leads_html = """
        <div style="margin-top: 30px;">
            <h3 style="color: #333; margin-bottom: 15px;">New Leads</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f5f5f5;">
                        <th style="padding: 10px; text-align: left;">Name</th>
                        <th style="padding: 10px; text-align: left;">Contact</th>
                        <th style="padding: 10px; text-align: left;">Interest</th>
                    </tr>
                </thead>
                <tbody>
        """
        for lead in new_leads:
            contact = lead.email or lead.phone or "N/A"
            leads_html += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{lead.name or 'Unknown'}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{contact}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{lead.interest or '-'}</td>
                </tr>
            """
        leads_html += "</tbody></table></div>"

    html_content = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; max-width: 700px; margin: 0 auto; background: #f5f5f5;">
        <div style="background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #722F37; margin: 0;">{period_label} Concierge Report</h1>
                <p style="color: #666; margin-top: 5px;">{business.name}</p>
            </div>

            <div style="display: flex; gap: 15px; margin-bottom: 30px;">
                <div style="flex: 1; background: linear-gradient(135deg, #722F37 0%, #4a1f24 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                    <div style="font-size: 32px; font-weight: 700;">{total_conversations}</div>
                    <div style="font-size: 14px; opacity: 0.9;">Conversations</div>
                    <div style="font-size: 12px; margin-top: 5px; opacity: 0.8;">{conv_change} vs prev</div>
                </div>
                <div style="flex: 1; background: linear-gradient(135deg, #2c5282 0%, #1a365d 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                    <div style="font-size: 32px; font-weight: 700;">{total_messages}</div>
                    <div style="font-size: 14px; opacity: 0.9;">Messages</div>
                    <div style="font-size: 12px; margin-top: 5px; opacity: 0.8;">{msg_change} vs prev</div>
                </div>
                <div style="flex: 1; background: linear-gradient(135deg, #276749 0%, #1a4731 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                    <div style="font-size: 32px; font-weight: 700;">{total_leads}</div>
                    <div style="font-size: 14px; opacity: 0.9;">Leads</div>
                    <div style="font-size: 12px; margin-top: 5px; opacity: 0.8;">{lead_change} vs prev</div>
                </div>
            </div>

            <div style="margin-top: 30px;">
                <h3 style="color: #333; margin-bottom: 15px;">Daily Breakdown</h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                    <thead>
                        <tr style="background: #f5f5f5;">
                            <th style="padding: 10px 12px; text-align: left;">Date</th>
                            <th style="padding: 10px 12px; text-align: center;">Conversations</th>
                            <th style="padding: 10px 12px; text-align: center;">Messages</th>
                            <th style="padding: 10px 12px; text-align: center;">Leads</th>
                        </tr>
                    </thead>
                    <tbody>
                        {daily_rows}
                    </tbody>
                </table>
            </div>

            {leads_html}

            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; text-align: center;">
                <p style="color: #666; font-size: 14px; margin: 0;">
                    Your AI concierge is working 24/7 for you!<br>
                    <span style="color: #722F37; font-weight: 600;">- Napa Concierge Team</span>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        resend.Emails.send({
            "from": "Napa Concierge <onboarding@resend.dev>",
            "to": [business.contact_email],
            "subject": f"{period_label} Report: {total_conversations} conversations, {total_leads} new leads - {business.name}",
            "html": html_content
        })
        return {
            "status": "success",
            "message": f"{period_label} report sent to {business.contact_email}",
            "stats": {
                "conversations": total_conversations,
                "messages": total_messages,
                "leads": total_leads
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@app.get("/health")
async def health():
    return {"status": "healthy"}


# ============== Contract Signing ==============

@app.post("/contract/sign")
async def sign_contract(
    contract_data: ContractSign,
    request: Request,
    db: Session = Depends(get_db)
):
    """Sign the service agreement"""
    signature = ContractSignature(
        signer_name=contract_data.signer_name,
        signer_email=contract_data.signer_email,
        company_name=contract_data.company_name,
        company_type=contract_data.company_type,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500]
    )
    db.add(signature)
    db.commit()
    db.refresh(signature)

    return {
        "status": "success",
        "message": "Contract signed successfully",
        "signature_id": signature.id,
        "signed_at": signature.signed_at
    }


@app.get("/admin/contracts")
async def list_contracts(
    x_admin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """List all signed contracts (admin only)"""
    verify_admin_key(x_admin_key)

    signatures = db.query(ContractSignature).order_by(ContractSignature.signed_at.desc()).all()
    return [
        {
            "id": s.id,
            "signer_name": s.signer_name,
            "signer_email": s.signer_email,
            "company_name": s.company_name,
            "company_type": s.company_type,
            "contract_version": s.contract_version,
            "signed_at": s.signed_at,
            "ip_address": s.ip_address
        }
        for s in signatures
    ]


if __name__ == "__main__":
    import uvicorn
    print(f"\n{'='*50}")
    print("ADMIN API KEY (save this!):")
    print(ADMIN_API_KEY)
    print(f"{'='*50}\n")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
