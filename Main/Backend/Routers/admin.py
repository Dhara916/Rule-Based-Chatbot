# routers/admin.py
# ─────────────────────────────────────────────────────────────────────────────
# All endpoints require role == "admin" (enforced via require_admin dependency).
#
# Endpoints:
#   GET  /admin/analytics          – dashboard stats
#   GET  /admin/users              – list all users
#   PATCH /admin/users/{id}/toggle – activate / deactivate a user
#   PATCH /admin/users/{id}/role   – change a user's role
#   GET  /admin/logs               – recent usage logs
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timezone, timedelta

import models, schemas, auth
from database import get_db

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/analytics", response_model=schemas.AnalyticsOut)
def get_analytics(
    db         : Session     = Depends(get_db),
    _          : models.User = Depends(auth.require_admin),
):
    """
    Aggregate statistics for the admin dashboard:
    - User counts
    - Message / session counts
    - Average confidence score
    - Top 10 matched intents
    - Message counts for today and this week
    """
    now   = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week  = today - timedelta(days=7)

    total_users    = db.query(models.User).count()
    active_users   = db.query(models.User).filter(models.User.is_active == True).count()
    total_messages = db.query(models.ChatMessage).count()
    total_sessions = db.query(models.ChatSession).count()

    avg_confidence = (
        db.query(func.avg(models.UsageLog.confidence)).scalar() or 0.0
    )

    # Top intents by frequency
    top_intents_raw = (
        db.query(models.UsageLog.intent, func.count(models.UsageLog.id).label("count"))
        .group_by(models.UsageLog.intent)
        .order_by(desc("count"))
        .limit(10)
        .all()
    )
    top_intents = [{"intent": r[0], "count": r[1]} for r in top_intents_raw]

    messages_today = (
        db.query(models.UsageLog)
        .filter(models.UsageLog.timestamp >= today)
        .count()
    )
    messages_week = (
        db.query(models.UsageLog)
        .filter(models.UsageLog.timestamp >= week)
        .count()
    )

    return schemas.AnalyticsOut(
        total_users    = total_users,
        active_users   = active_users,
        total_messages = total_messages,
        total_sessions = total_sessions,
        avg_confidence = round(float(avg_confidence), 1),
        top_intents    = top_intents,
        messages_today = messages_today,
        messages_week  = messages_week,
    )


@router.get("/users", response_model=list[schemas.UserOut])
def list_users(
    db : Session     = Depends(get_db),
    _  : models.User = Depends(auth.require_admin),
):
    """Return all users ordered by registration date."""
    return db.query(models.User).order_by(models.User.created_at.desc()).all()


@router.patch("/users/{user_id}/toggle", response_model=schemas.UserOut)
def toggle_user(
    user_id: int,
    db     : Session     = Depends(get_db),
    admin  : models.User = Depends(auth.require_admin),
):
    """Flip the is_active flag for a user (cannot deactivate yourself)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/role", response_model=schemas.UserOut)
def change_role(
    user_id : int,
    role    : str        = Query(..., regex="^(admin|user)$"),
    db      : Session    = Depends(get_db),
    admin   : models.User = Depends(auth.require_admin),
):
    """Promote or demote a user (cannot change your own role)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    user.role = role
    db.commit()
    db.refresh(user)
    return user


@router.get("/logs", response_model=list[schemas.UsageLogOut])
def get_logs(
    limit : int      = Query(default=100, le=500),
    db    : Session  = Depends(get_db),
    _     : models.User = Depends(auth.require_admin),
):
    """Return the most recent usage log entries."""
    return (
        db.query(models.UsageLog)
        .order_by(models.UsageLog.timestamp.desc())
        .limit(limit)
        .all()
    )