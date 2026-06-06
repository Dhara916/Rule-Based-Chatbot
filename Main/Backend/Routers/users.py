# routers/users.py
# ─────────────────────────────────────────────────────────────────────────────
# Endpoints:
#   GET    /users/profile          – get own profile
#   PATCH  /users/profile          – update email / language / password
#   DELETE /users/profile          – delete own account
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models, schemas, auth
from database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/profile", response_model=schemas.UserOut)
def get_profile(current_user: models.User = Depends(auth.get_current_user)):
    """Return the authenticated user's profile."""
    return current_user


@router.patch("/profile", response_model=schemas.UserOut)
def update_profile(
    payload     : schemas.UserUpdate,
    db          : Session     = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Update email, preferred language, or password.
    Only fields that are provided (non-None) are updated.
    """
    if payload.email:
        # Make sure the new email is not taken by another user
        conflict = db.query(models.User).filter(
            models.User.email == payload.email,
            models.User.id    != current_user.id,
        ).first()
        if conflict:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = payload.email

    if payload.language:
        current_user.language = payload.language

    if payload.password:
        current_user.hashed_password = auth.hash_password(payload.password)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/profile", status_code=204)
def delete_account(
    db          : Session     = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Permanently delete the authenticated user's account and all their data."""
    db.delete(current_user)
    db.commit()