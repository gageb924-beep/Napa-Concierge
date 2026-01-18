"""Quick test to find the error"""
import os
from dotenv import load_dotenv
load_dotenv()

from database import init_db, SessionLocal, Business, Conversation, Analytics
from datetime import datetime, date
import secrets
from anthropic import Anthropic

# Init
init_db()
db = SessionLocal()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

print("1. Testing database...")
try:
    business = db.query(Business).filter(Business.api_key == "nc_ZN9lp9vkTaK2E8L2js9f944t9ZNiLfTD-w9dSjZXtvo").first()
    if business:
        print(f"   Found business: {business.name}")
    else:
        print("   ERROR: Business not found!")
        exit(1)
except Exception as e:
    print(f"   ERROR: {e}")
    exit(1)

print("2. Testing conversation creation...")
try:
    session_id = "test_" + secrets.token_urlsafe(8)
    conv = Conversation(
        business_id=business.id,
        session_id=session_id,
        message_count=0
    )
    db.add(conv)
    db.commit()
    print(f"   Created conversation: {conv.id}")
except Exception as e:
    print(f"   ERROR: {e}")
    db.rollback()

print("3. Testing Anthropic API...")
try:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{"role": "user", "content": "Say hello"}]
    )
    print(f"   API response: {response.content[0].text[:50]}...")
except Exception as e:
    print(f"   ERROR: {e}")

print("\nDone!")
db.close()
