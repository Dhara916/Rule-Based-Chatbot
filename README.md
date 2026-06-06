# 🤖 Rule-Based Chatbot

> A full-stack chatbot built with Python & FastAPI — no AI, no LLM, just pure rule-based logic with fuzzy matching.

---

## Overview

A rule-based chatbot application where user input is matched against a hand-crafted knowledge base using fuzzy string matching. The closer the input to a known pattern, the higher the confidence score and the better the response.

---

## Features

| Feature | Description |
|---------|-------------|
| 🔐 JWT Authentication | Secure login with token-based auth |
| 👥 Role-Based Access | Admin and User roles |
| 🔍 Fuzzy Matching | Understands typos and variations (rapidfuzz) |
| 🌐 Bilingual | Supports English and Hindi |
| 💬 Chat History | Persistent sessions stored in database |
| 📊 Admin Dashboard | Analytics, charts, user management |
| 🎤 Voice Input | Speak instead of typing |
| 🔊 Voice Output | Bot reads responses aloud |
| 📄 Export Chats | Download as PDF or TXT |
| 🌙 Dark / Light Mode | Theme preference saved locally |

---

## Tech Stack

**Backend**
- Python 3.11
- FastAPI
- SQLAlchemy + SQLite
- rapidfuzz (fuzzy matching)
- python-jose (JWT)
- passlib + bcrypt (password hashing)
- fpdf2 (PDF export)

**Frontend**
- HTML, CSS, JavaScript (Vanilla)
- Chart.js (admin charts)
- Web Speech API (voice input/output)

---

## Project Structure

```
chatbot/
├── requirements.txt
├── backend/
│   ├── app.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── chatbot.py
│   └── routers/
│       ├── auth.py
│       ├── chat.py
│       ├── admin.py
│       └── users.py
└── frontend/
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── chat.html
    └── settings.html
```

---

## Getting Started

**1. Clone the repository**
```bash
git clone https://github.com/Dhara916/Rule-Based-Chatbot.git
cd Rule-Based-Chatbot
```

**2. Install dependencies**
```bash
py -3.11 -m pip install fastapi "uvicorn[standard]" sqlalchemy "pydantic[email]" pydantic-settings "python-jose[cryptography]" "passlib[bcrypt]" "bcrypt==4.0.1" python-multipart rapidfuzz fpdf2 langdetect python-dotenv aiofiles
```

**3. Start the backend server**
```bash
cd backend
py -3.11 -m uvicorn app:app --reload --port 8000
```

**4. Open the frontend**

Open `frontend/login.html` in your browser.

>First registered user is automatically assigned the **Admin** role.

---

## How It Works

```
User Input
    ↓
Normalize (lowercase, strip)
    ↓
Fuzzy Match against Knowledge Base (rapidfuzz WRatio)
    ↓
Score ≥ 55%  →  Return matched response
Score < 55%  →  Return fallback message
```

---

## API Docs

Once the server is running, visit:

```
http://localhost:8000/docs
```

---

##  Author

**Dhara R**
GitHub: [@Dhara916](https://github.com/Dhara916)

---