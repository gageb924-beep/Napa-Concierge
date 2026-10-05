"""
Database models for Missed Call AI - multi-tenant missed-call text-back for home service businesses
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./missed_call_ai.db")

# Handle Render's postgres:// vs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Business(Base):
    """A contractor using the service (HVAC, plumbing, roofing, ...)"""
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)          # "River City Heating & Air"
    trade = Column(String(50), default="hvac")           # hvac, plumbing, roofing, electrical, pest, solar
    twilio_number = Column(String(20), unique=True, index=True, nullable=False)  # E.164, the number customers call
    owner_phone = Column(String(20), nullable=False)     # where calls forward + job alerts go
    owner_email = Column(String(255))
    service_area = Column(Text, default="Sacramento, Elk Grove, Roseville, Folsom, Citrus Heights, Rancho Cordova")
    business_hours = Column(String(255), default="Mon-Fri 7am-6pm, emergency service 24/7")
    custom_knowledge = Column(Text)                      # pricing, services, warranties, promos
    avg_job_value = Column(Float, default=450.0)         # used for "revenue saved" reporting
    ring_seconds = Column(Integer, default=20)           # how long to ring the owner before text-back
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    calls = relationship("Call", back_populates="business", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="business", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="business", cascade="all, delete-orphan")


class Call(Base):
    """Every inbound call, answered or missed"""
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    caller = Column(String(20), index=True)
    call_sid = Column(String(64))
    status = Column(String(20))                          # completed, no-answer, busy, failed, canceled
    missed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="calls")


class Conversation(Base):
    """An SMS thread between the AI and one caller"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    customer_phone = Column(String(20), index=True, nullable=False)
    status = Column(String(20), default="open")          # open, booked, handed_off, opted_out
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan",
                            order_by="Message.id")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20))                            # user (customer) or assistant
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class Job(Base):
    """A qualified job request captured by the AI and sent to the owner"""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    customer_name = Column(String(255))
    customer_phone = Column(String(20))
    address = Column(Text)
    issue = Column(Text)
    urgency = Column(String(20))                         # emergency, soon, flexible
    preferred_time = Column(String(255))
    status = Column(String(20), default="new")           # new, scheduled, won, lost
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="jobs")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
