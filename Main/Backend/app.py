from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from database import engine, Base
import models  # noqa – registers all ORM models before create_all
from routers import auth, chat, admin, users

# Create all DB tables
# In production use Alembic migrations instead.
Base.metadata.create_all(bind=engine)

#App instance 
app = FastAPI(
    title       = "Rule-Based Chatbot API",
    description = "JWT-authenticated chatbot with fuzzy matching and analytics",
    version     = "1.0.0",
)

# CORS 
# In production, replace "*" with your frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# Routers 
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(users.router)

# Serve frontend static files 
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def serve_login():
        return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

    @app.get("/{page}.html", include_in_schema=False)
    def serve_page(page: str):
        path = os.path.join(FRONTEND_DIR, f"{page}.html")
        if os.path.exists(path):
            return FileResponse(path)
        return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))


# Health check 
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "version": "1.0.0"}