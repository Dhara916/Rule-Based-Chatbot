from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# SQLite file stored in the project root; override via env var for production
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chatbot.db")

# connect_args is SQLite-specific: allows the same connection across threads
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False,          # set True to log all SQL queries (debugging)
)

# Each call to SessionLocal() produces a new DB session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All ORM models inherit from this base class
Base = declarative_base()


# Dependency
def get_db():
    """
    FastAPI dependency that yields a database session and closes it afterwards.
    Usage in route:  db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()