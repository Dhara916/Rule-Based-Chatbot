from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """
    Stores registered users.
    role: "admin" | "user"  – controls access to the admin dashboard.
    is_active: False = soft-deleted / banned.
    """
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(50),  unique=True, index=True, nullable=False)
    email         = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role          = Column(String(10),  default="user")   # "admin" | "user"
    is_active     = Column(Boolean,     default=True)
    language      = Column(String(10),  default="en")     # preferred language
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    # One user → many chat sessions
    sessions      = relationship("ChatSession", back_populates="user",
                                 cascade="all, delete-orphan")


class ChatSession(Base):
    """
    A named conversation thread belonging to one user.
    Each session contains an ordered list of ChatMessage rows.
    """
    __tablename__ = "chat_sessions"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    title      = Column(String(200), default="New Chat")
    language   = Column(String(10),  default="en")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(),
                        server_default=func.now())

    user       = relationship("User",        back_populates="sessions")
    messages   = relationship("ChatMessage", back_populates="session",
                              cascade="all, delete-orphan",
                              order_by="ChatMessage.id")


class ChatMessage(Base):
    """
    One turn in a session.
    sender: "user" | "bot"
    confidence: fuzzy-match score (0-100) returned by rapidfuzz.
    """
    __tablename__ = "chat_messages"

    id         = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    sender     = Column(String(10), nullable=False)   # "user" | "bot"
    content    = Column(Text,       nullable=False)
    confidence = Column(Float,      default=0.0)      # match score 0-100
    language   = Column(String(10), default="en")
    timestamp  = Column(DateTime(timezone=True), server_default=func.now())

    session    = relationship("ChatSession", back_populates="messages")


class UsageLog(Base):
    """
    Admin analytics: every query gets a row here.
    Tracks which intent was matched and the confidence level.
    """
    __tablename__ = "usage_logs"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=True)
    query      = Column(Text,    nullable=False)
    intent     = Column(String(100), default="unknown")
    confidence = Column(Float,   default=0.0)
    language   = Column(String(10), default="en")
    timestamp  = Column(DateTime(timezone=True), server_default=func.now())