from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

# Config 
# In production, load SECRET_KEY from environment variables / secrets manager.
SECRET_KEY      = "CHANGE_ME_super_secret_key_32chars!!"
ALGORITHM       = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8   # 8 hours

# Helpers 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# tokenUrl must match the login endpoint path
oauth2_scheme  = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the plain-text password."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Encode data into a signed JWT.
    Always adds an 'exp' (expiry) claim.
    """
    to_encode = data.copy()
    expire    = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> schemas.TokenData:
    """
    Decode and validate a JWT.
    Raises HTTP 401 if the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role    : str = payload.get("role", "user")
        if username is None:
            raise credentials_exception
        return schemas.TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception


# FastAPI Dependencies 

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db   : Session = Depends(get_db),
) -> models.User:
    """
    Dependency: decode the Bearer token and return the matching User row.
    Raises 401 if the token is bad; 403 if the account is inactive.
    """
    token_data = decode_token(token)
    user = db.query(models.User).filter(
        models.User.username == token_data.username
    ).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    return user


def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    Dependency: wraps get_current_user and additionally requires role == 'admin'.
    Usage in route:  user = Depends(require_admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user