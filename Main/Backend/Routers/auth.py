# routers/auth.py
# ─────────────────────────────────────────────────────────────────────────────
# Endpoints:
#   POST /auth/register  – create a new account
#   POST /auth/login     – returns a JWT token
#   GET  /auth/me        – returns the logged-in user's profile
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models, schemas, auth
from database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user.
    - Checks that username and email are not already taken.
    - Hashes the password before storing.
    - First registered user automatically becomes admin.
    """
    # Duplicate checks
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # First user = admin
    is_first_user = db.query(models.User).count() == 0
    role = "admin" if is_first_user else "user"

    user = models.User(
        username        = payload.username,
        email           = payload.email,
        hashed_password = auth.hash_password(payload.password),
        language        = payload.language,
        role            = role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate and return a JWT.
    The token encodes username + role and expires after 8 hours.
    """
    user = db.query(models.User).filter(
        models.User.username == payload.username
    ).first()

    if not user or not auth.verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = auth.create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    return schemas.Token(
        access_token=token,
        token_type="bearer",
        role=user.role,
        username=user.username,
    )


@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    """Return the profile of the currently authenticated user."""
    return current_user