# 🤖 Rule-Based Chatbot – Complete Project

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start backend
cd backend
uvicorn app:app --reload --port 8000

# 3. Open frontend (any of these)
open ../frontend/login.html       # macOS
start ../frontend/login.html      # Windows
xdg-open ../frontend/login.html   # Linux
```

> First registered user automatically becomes **Admin**.

---

## Project Structure

```
chatbot/
├── requirements.txt
├── backend/
│   ├── app.py          ← FastAPI app, CORS, route registration
│   ├── database.py     ← SQLite engine + session factory
│   ├── models.py       ← ORM tables (User, Session, Message, Log)
│   ├── schemas.py      ← Pydantic request/response models
│   ├── auth.py         ← JWT creation, bcrypt hashing, dependencies
│   ├── chatbot.py      ← Fuzzy matching engine + knowledge base
│   └── routers/
│       ├── auth.py     ← /auth/register, /auth/login, /auth/me
│       ├── chat.py     ← /chat/message, /chat/sessions, export
│       ├── admin.py    ← /admin/analytics, /admin/users
│       └── users.py    ← /users/profile (GET/PATCH/DELETE)
└── frontend/
    ├── login.html      ← JWT login form
    ├── register.html   ← Registration + password strength
    ├── dashboard.html  ← Admin analytics + user management
    ├── chat.html       ← Full chat UI with voice I/O
    └── settings.html   ← Profile, password, preferences
```

---

## File-by-File Explanation

### `backend/database.py`
- Creates a **SQLite** database (`chatbot.db`) using SQLAlchemy
- `SessionLocal` → factory for DB sessions
- `get_db()` → FastAPI dependency injected into every route
- To use PostgreSQL: change `DATABASE_URL = "postgresql://user:pass@host/db"`

### `backend/models.py`
Four ORM tables:

| Table | Purpose |
|-------|---------|
| `users` | Stores accounts. `role` = admin/user. `is_active` for banning. |
| `chat_sessions` | Named conversation threads per user |
| `chat_messages` | Individual turns. `sender` = user/bot. `confidence` = fuzzy score |
| `usage_logs` | Every query logged for analytics (intent, score, language) |

### `backend/schemas.py`
Pydantic v2 models for **validation** (inputs) and **serialisation** (outputs):
- `UserRegister / UserLogin / Token` → auth flow
- `ChatRequest / ChatResponse / MessageOut` → chat flow  
- `AnalyticsOut` → admin dashboard data
- `model_config = {"from_attributes": True}` replaces Pydantic v1's `orm_mode`

### `backend/auth.py`
- **bcrypt** hashing via `passlib` — passwords never stored in plain text
- **JWT** tokens via `python-jose` — encode `{username, role, exp}`
- `get_current_user` dependency — decodes Bearer token on every protected route
- `require_admin` dependency — additionally checks `role == "admin"`
- Token expiry: **8 hours** (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)

### `backend/chatbot.py`
The core AI engine — **no LLM required**:

```
User message
    ↓
Normalize (lowercase + strip)
    ↓
rapidfuzz.process.extractOne(
    query,
    all_patterns,          ← 100+ example phrases
    scorer=fuzz.WRatio     ← handles word order, partial matches
)
    ↓
score >= 55?  →  return matching response (random from list)
            No →  return fallback message
```

- **17 intent categories**: greeting, farewell, joke, python, india, food, study, motivation…
- **Bilingual**: every intent has `responses_en` + `responses_hi`
- **Extensible**: add a new dict to `KNOWLEDGE_BASE` for new topics

### `backend/routers/auth.py`
```
POST /auth/register  →  creates user, hashes password, auto-admin if first user
POST /auth/login     →  verifies password, returns JWT
GET  /auth/me        →  returns profile of token holder
```

### `backend/routers/chat.py`
```
POST   /chat/message              →  runs chatbot, saves both messages, logs analytics
GET    /chat/sessions             →  list all sessions (newest first)
GET    /chat/sessions/{id}        →  session + all messages
DELETE /chat/sessions/{id}        →  delete session + cascade messages
GET    /chat/sessions/{id}/export →  download as TXT or PDF (fpdf2)
```

### `backend/routers/admin.py`
All endpoints require `role == "admin"`:
```
GET   /admin/analytics          →  stats: users, messages, avg confidence, top intents
GET   /admin/users              →  full user list
PATCH /admin/users/{id}/toggle  →  ban / unban
PATCH /admin/users/{id}/role    →  promote / demote
GET   /admin/logs               →  recent usage logs
```

### `backend/routers/users.py`
```
GET    /users/profile  →  own profile
PATCH  /users/profile  →  update email, language, or password
DELETE /users/profile  →  permanently delete account + all data
```

### `backend/app.py`
- Instantiates FastAPI, registers all 4 routers
- Adds **CORS middleware** (allow all origins for dev)
- Runs `Base.metadata.create_all()` on startup → creates DB tables
- Mounts `frontend/` as static files at `/static`
- Serves HTML pages at `/{page}.html`

---

## Frontend Pages

### `login.html`
- Username + password form
- Calls `POST /auth/login`, stores `token`, `role`, `username` in `localStorage`
- Redirects admin → `dashboard.html`, users → `chat.html`
- Enter key submits, shows spinner during request

### `register.html`
- Full registration form with **live password strength meter**
- 5-level strength: Very Weak → Very Strong (colour-coded bar)
- Validates min length, email format, password confirmation
- Calls `POST /auth/register`

### `dashboard.html` (Admin only)
- **4 stat cards**: total users, messages, sessions, avg confidence
- **Bar chart** (Chart.js): top matched intents
- **Doughnut chart**: messages today vs rest of week
- **Users table**: username, email, role badge, status badge, ban/promote buttons
- Guards redirect if not admin token

### `chat.html` ← Main feature page
- **Sidebar**: session history list, new chat button, nav links
- **Topbar**: session title, language switcher, theme toggle, TTS toggle, export menu
- **Messages**: user bubbles (right) + bot bubbles (left) with confidence dot + timestamp
- **Typing indicator**: animated 3-dot bounce while waiting for response
- **Voice Input**: Web Speech API — click 🎤, speak, transcript fills input
  - Language-aware: `hi-IN` for Hindi, `en-US` for English
- **Voice Output (TTS)**: SpeechSynthesis reads bot replies aloud
- **Export**: downloads current session as `.txt` or `.pdf` via backend
- **Suggestion chips**: clickable example prompts on empty state
- **Auto-resize textarea**: grows up to 120px as you type
- **Dark/Light mode**: persisted to `localStorage`

### `settings.html`
- **Profile section**: update email, preferred language
- **Password section**: change password (re-login enforced after change)
- **Preferences**: toggle dark mode, TTS, sound effects (all persisted)
- **My Activity**: session and member-since stats
- **Danger Zone**: permanent account deletion with double confirmation

---

## Features Checklist

| Feature | Implementation |
|---------|---------------|
| JWT Authentication | `python-jose` + `passlib[bcrypt]` |
| Role-Based Access | `require_admin` dependency |
| Fuzzy Matching | `rapidfuzz.fuzz.WRatio`, threshold 55 |
| Multilingual (EN/HI) | Knowledge base has both response sets |
| Persistent Chat History | SQLite via SQLAlchemy |
| Admin Dashboard | Analytics + user management |
| Usage Analytics | `UsageLog` table, aggregated by intent |
| Voice Input | Web Speech Recognition API |
| Voice Output | Web Speech Synthesis API |
| Export TXT | StreamingResponse with plain text |
| Export PDF | `fpdf2` library |
| Dark Mode | CSS variables + `localStorage` |

---

## Adding New Intents

Edit `backend/chatbot.py` — append to `KNOWLEDGE_BASE`:

```python
{
    "intent": "my_topic",
    "patterns": [
        "question one", "question two", "related phrase",
        "hindi equivalent", "another variant",
    ],
    "responses_en": [
        "English reply A",
        "English reply B (chosen randomly)",
    ],
    "responses_hi": [
        "हिन्दी जवाब",
    ],
},
```

No restart needed if using `--reload`. New patterns are picked up immediately.

---

## API Docs
Once the server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**:      http://localhost:8000/redoc