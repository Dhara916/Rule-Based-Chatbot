# routers/chat.py
# ─────────────────────────────────────────────────────────────────────────────
# Endpoints:
#   POST /chat/message              – send a message, get bot reply
#   GET  /chat/sessions             – list user's sessions
#   GET  /chat/sessions/{id}        – full session with messages
#   DELETE /chat/sessions/{id}      – delete a session
#   GET  /chat/sessions/{id}/export – download session as TXT or PDF
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
import io

import models, schemas, auth, chatbot
from database import get_db, get_db as _get_db

router = APIRouter(prefix="/chat", tags=["Chat"])


# ── Helper ────────────────────────────────────────────────────────────────────
def _get_or_create_session(
    db: Session, user_id: int, session_id: int | None, language: str
) -> models.ChatSession:
    """Return an existing session or create a new one."""
    if session_id:
        session = db.query(models.ChatSession).filter(
            models.ChatSession.id      == session_id,
            models.ChatSession.user_id == user_id,
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session

    session = models.ChatSession(user_id=user_id, language=language)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/message", response_model=schemas.ChatResponse)
def send_message(
    payload     : schemas.ChatRequest,
    db          : Session       = Depends(get_db),
    current_user: models.User   = Depends(auth.get_current_user),
):
    """
    Core chat endpoint.
    1. Stores the user's message.
    2. Runs the chatbot engine to get a reply.
    3. Stores the bot's reply.
    4. Logs the query for analytics.
    5. Returns both messages to the client.
    """
    session = _get_or_create_session(
        db, current_user.id, payload.session_id, payload.language
    )

    # ── User message ─────────────────────────────────────────────────────────
    user_msg = models.ChatMessage(
        session_id = session.id,
        sender     = "user",
        content    = payload.message,
        language   = payload.language,
        confidence = 100.0,
    )
    db.add(user_msg)

    # ── Bot response ─────────────────────────────────────────────────────────
    response_text, intent, confidence = chatbot.get_response(
        payload.message, payload.language
    )
    bot_msg = models.ChatMessage(
        session_id = session.id,
        sender     = "bot",
        content    = response_text,
        confidence = confidence,
        language   = payload.language,
    )
    db.add(bot_msg)

    # ── Auto-title session from first user message ───────────────────────────
    msg_count = db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == session.id
    ).count()
    if msg_count == 0:                        # before this flush
        title = payload.message[:60] + ("…" if len(payload.message) > 60 else "")
        session.title = title

    # ── Analytics log ────────────────────────────────────────────────────────
    log = models.UsageLog(
        user_id    = current_user.id,
        query      = payload.message,
        intent     = intent,
        confidence = confidence,
        language   = payload.language,
    )
    db.add(log)
    db.commit()
    db.refresh(user_msg)
    db.refresh(bot_msg)
    db.refresh(session)

    return schemas.ChatResponse(
        session_id    = session.id,
        session_title = session.title,
        user_message  = schemas.MessageOut.model_validate(user_msg),
        bot_message   = schemas.MessageOut.model_validate(bot_msg),
    )


@router.get("/sessions", response_model=list[schemas.SessionOut])
def list_sessions(
    db          : Session     = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Return all chat sessions for the current user, newest first."""
    return (
        db.query(models.ChatSession)
        .filter(models.ChatSession.user_id == current_user.id)
        .order_by(models.ChatSession.updated_at.desc())
        .all()
    )


@router.get("/sessions/{session_id}", response_model=schemas.SessionDetail)
def get_session(
    session_id  : int,
    db          : Session     = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Return a single session with all its messages."""
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id      == session_id,
        models.ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id  : int,
    db          : Session     = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Delete a session and all its messages."""
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id      == session_id,
        models.ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()


@router.get("/sessions/{session_id}/export")
def export_session(
    session_id  : int,
    format      : str         = Query(default="txt", regex="^(txt|pdf)$"),
    db          : Session     = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Export a session as TXT or PDF.
    PDF uses fpdf2; TXT is plain-text.
    """
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id      == session_id,
        models.ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_id)
        .order_by(models.ChatMessage.id)
        .all()
    )

    filename_base = f"chat_{session_id}_{session.title[:20].replace(' ', '_')}"

    # ── TXT export ────────────────────────────────────────────────────────────
    if format == "txt":
        lines = [f"Chat Export: {session.title}", f"Date: {session.created_at}", "─" * 50, ""]
        for msg in messages:
            prefix = "You" if msg.sender == "user" else "Bot"
            ts     = msg.timestamp.strftime("%H:%M")
            lines.append(f"[{ts}] {prefix}: {msg.content}")
        content = "\n".join(lines).encode("utf-8")
        return StreamingResponse(
            BytesIO(content),
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.txt"'},
        )

    # ── PDF export ────────────────────────────────────────────────────────────
    try:
        from fpdf import FPDF
    except ImportError:
        raise HTTPException(status_code=500, detail="fpdf2 not installed")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Chat: {session.title}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Exported on: {session.created_at.strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.ln(4)

    for msg in messages:
        sender = "You" if msg.sender == "user" else "ChatBot"
        ts     = msg.timestamp.strftime("%H:%M")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(30, 100, 200) if msg.sender == "user" else pdf.set_text_color(50, 150, 50)
        pdf.cell(0, 6, f"[{ts}] {sender}:", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(0, 0, 0)
        # multi_cell handles long messages with word wrap
        pdf.multi_cell(0, 5, msg.content)
        pdf.ln(2)

    pdf_bytes = pdf.output()          # returns bytearray in fpdf2
    return StreamingResponse(
        BytesIO(bytes(pdf_bytes)),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename_base}.pdf"'},
    )