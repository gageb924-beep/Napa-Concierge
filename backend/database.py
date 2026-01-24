"""
Database models for Napa Concierge multi-tenant SaaS
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import secrets

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./napa_concierge.db")

# Handle Render's postgres:// vs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def generate_api_key():
    """Generate a unique API key for a business"""
    return f"nc_{secrets.token_urlsafe(32)}"


class Business(Base):
    """A business/client using the concierge service"""
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    api_key = Column(String(64), unique=True, index=True, default=generate_api_key)

    # Business info
    name = Column(String(255), nullable=False)  # "The Vineyard Inn"
    business_type = Column(String(50), default="hotel")  # hotel, winery, restaurant
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    website = Column(String(255))

    # Widget customization
    primary_color = Column(String(7), default="#722F37")  # Hex color
    welcome_message = Column(Text)
    widget_title = Column(String(100), default="Concierge")
    widget_subtitle = Column(String(200), default="Your personal wine country guide")

    # Custom AI knowledge for this business
    custom_knowledge = Column(Text)  # Business-specific info for the AI prompt

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversations = relationship("Conversation", back_populates="business")
    leads = relationship("Lead", back_populates="business")


class Conversation(Base):
    """A chat conversation session"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    session_id = Column(String(64), index=True)  # Browser session identifier

    # Analytics
    started_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    message_count = Column(Integer, default=0)

    # Store conversation for analytics (optional)
    messages = Column(JSON, default=list)

    # Visitor info
    visitor_ip = Column(String(45))  # IPv6 max length
    user_agent = Column(String(500))
    referrer = Column(String(500))

    business = relationship("Business", back_populates="conversations")


class Lead(Base):
    """Captured lead information from chat"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))

    # Lead info
    name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))

    # Context
    interest = Column(String(255))  # What they were asking about
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="leads")


class Analytics(Base):
    """Aggregated analytics per business per day"""
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    date = Column(DateTime, nullable=False)

    # Metrics
    total_conversations = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    leads_captured = Column(Integer, default=0)

    # Popular topics (stored as JSON)
    top_topics = Column(JSON, default=list)


class ContractSignature(Base):
    """Signed service agreements from clients"""
    __tablename__ = "contract_signatures"

    id = Column(Integer, primary_key=True, index=True)

    # Signer info
    signer_name = Column(String(255), nullable=False)
    signer_email = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    company_type = Column(String(50))  # winery, hotel, restaurant, tour, other

    # Contract details
    contract_version = Column(String(20), default="1.0")

    # Audit trail
    signed_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(String(500))


def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
