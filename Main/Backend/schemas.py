from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# Auth 

class UserRegister(BaseModel):
    """Payload sent by the registration form."""
    username : str        = Field(..., min_length=3, max_length=50)
    email    : EmailStr
    password : str        = Field(..., min_length=6)
    language : str        = Field(default="en")


class UserLogin(BaseModel):
    """Payload sent by the login form."""
    username : str
    password : str


class Token(BaseModel):
    """JWT token returned after successful login."""
    access_token : str
    token_type   : str = "bearer"
    role         : str
    username     : str


class TokenData(BaseModel):
    """Data encoded inside the JWT."""
    username : Optional[str] = None
    role     : Optional[str] = None


# User 

class UserOut(BaseModel):
    """Public user profile (never exposes hashed_password)."""
    id         : int
    username   : str
    email      : str
    role       : str
    is_active  : bool
    language   : str
    created_at : datetime

    model_config = {"from_attributes": True}   # replaces orm_mode in Pydantic v2


class UserUpdate(BaseModel):
    """Fields a user can change in settings."""
    email    : Optional[EmailStr] = None
    language : Optional[str]      = None
    password : Optional[str]      = Field(default=None, min_length=6)


# Chat 

class ChatRequest(BaseModel):
    """Single message sent by the frontend."""
    message    : str  = Field(..., min_length=1, max_length=2000)
    session_id : Optional[int] = None    # None = create new session
    language   : str  = Field(default="en")


class MessageOut(BaseModel):
    """A single chat message returned to the frontend."""
    id         : int
    sender     : str          # "user" | "bot"
    content    : str
    confidence : float
    language   : str
    timestamp  : datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    """Full response from POST /chat/message."""
    session_id   : int
    session_title: str
    user_message : MessageOut
    bot_message  : MessageOut


class SessionOut(BaseModel):
    """Summary of a chat session (no messages)."""
    id         : int
    title      : str
    language   : str
    created_at : datetime
    updated_at : datetime

    model_config = {"from_attributes": True}


class SessionDetail(SessionOut):
    """Full session including all messages."""
    messages : List[MessageOut] = []


# Admin 

class AnalyticsOut(BaseModel):
    """High-level stats for the admin dashboard."""
    total_users    : int
    active_users   : int
    total_messages : int
    total_sessions : int
    avg_confidence : float
    top_intents    : List[dict]
    messages_today : int
    messages_week  : int


class UsageLogOut(BaseModel):
    intent     : str
    confidence : float
    language   : str
    timestamp  : datetime
    query      : str

    model_config = {"from_attributes": True}