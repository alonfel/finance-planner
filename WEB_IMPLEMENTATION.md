# Web Application Implementation — Complete Reference

**Date:** April 13, 2026  
**Status:** MVP Complete  
**Framework:** FastAPI (backend) + Vue 3 (frontend) + SQLite (database)

---

## Overview

A web application that displays cached financial simulation results for Israeli couples. Users can view individual scenarios, compare multiple scenarios side-by-side, and explore year-by-year breakdowns. This is an **output-first** MVP—no input forms yet.

**Tech Stack:**
- **Backend:** FastAPI (async Python) + SQLAlchemy ORM + SQLite
- **Frontend:** Vue 3 + Vite + Vue Router + Pinia
- **Charts:** Chart.js (linear & logarithmic scales)
- **Auth:** JWT + PBKDF2 password hashing
- **API:** RESTful JSON, Bearer token authentication

---

## Directory Structure

```
finance_planner/
├── web/                                 # NEW: Web application root
│   ├── README.md                        # Quick setup and architecture overview
│   ├── COMPARISON_GUIDE.md              # User guide for comparison feature
│   │
│   ├── backend/                         # FastAPI application
│   │   ├── requirements.txt             # Python dependencies
│   │   ├── __init__.py                  
│   │   ├── main.py                      # FastAPI app entry point
│   │   ├── database.py                  # SQLite setup + session management
│   │   ├── models.py                    # SQLAlchemy ORM models
│   │   ├── schemas.py                   # Pydantic request/response schemas
│   │   ├── auth.py                      # JWT + PBKDF2 authentication
│   │   ├── seed.py                      # Database seeding from cache
│   │   └── routers/                     # API endpoint handlers
│   │       ├── __init__.py
│   │       ├── auth.py                  # POST /auth/login
│   │       ├── profiles.py              # GET /profiles, /profiles/{id}/runs
│   │       └── scenarios.py             # GET /runs/{id}/scenarios, /scenarios/{id}, etc
│   │
│   └── frontend/                        # Vue 3 application
│       ├── package.json                 # Dependencies + scripts
│       ├── vite.config.js               # Vite configuration (port 5173)
│       ├── index.html                   # Entry HTML
│       └── src/
│           ├── main.js                  # App initialization
│           ├── App.vue                  # Root component
│           ├── router/
│           │   └── index.js             # Vue Router configuration + routes
│           ├── stores/
│           │   └── auth.js              # Pinia auth store (login/logout)
│           ├── views/                   # Full-page components
│           │   ├── LoginView.vue        # Login form
│           │   ├── DashboardView.vue    # Profile selector
│           │   ├── ScenariosView.vue    # Scenario list for profile
│           │   ├── ScenarioDetailView.vue  # Single scenario view
│           │   └── ComparisonView.vue   # Multi-scenario comparison
│           └── components/              # Reusable components
│               ├── PortfolioChart.vue   # Single-scenario line chart
│               ├── ComparisonChart.vue  # Multi-scenario line chart
│               ├── ComparisonTable.vue  # Side-by-side year table
│               └── YearDataTable.vue    # Single-scenario year table
│
├── QUICK_START_WEB.md                   # Quick start guide for development
└── data/
    ├── finance_planner.db               # SQLite database (auto-created by seed)
    └── profiles/
        └── alon/
            └── analyses/cache/
                └── simulation_cache.json # Cached simulation results (source)

```

---

## Backend Implementation

### Database Schema (5 Tables)

```sql
-- Users (seeded with demo account)
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL    -- Format: "salt$hash" (PBKDF2)
);

-- Profiles (maps to data/profiles/{name}/)
CREATE TABLE profiles (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,              -- "alon"
    display_name TEXT NOT NULL,             -- "Alon"
    description TEXT,
    created_at TEXT                        -- ISO timestamp
);

-- Simulation runs (one per execution of run_simulations.py)
CREATE TABLE simulation_runs (
    id INTEGER PRIMARY KEY,
    profile_id INTEGER REFERENCES profiles(id),
    generated_at TEXT NOT NULL,             -- Timestamp from cache
    num_scenarios INTEGER NOT NULL,
    label TEXT                              -- Optional: "April 2026"
);

-- Scenario results (one per scenario per run)
CREATE TABLE scenario_results (
    id INTEGER PRIMARY KEY,
    run_id INTEGER REFERENCES simulation_runs(id),
    scenario_name TEXT NOT NULL,            -- "Alon - Baseline"
    retirement_year INTEGER,                -- Year (1-20) or NULL
    retirement_age INTEGER,                 -- Age or NULL
    final_portfolio REAL NOT NULL,          -- Portfolio value at year 20
    total_savings REAL NOT NULL             -- Sum of all net_savings
);

-- Year-by-year data for each scenario
CREATE TABLE year_data (
    id INTEGER PRIMARY KEY,
    result_id INTEGER REFERENCES scenario_results(id),
    year INTEGER NOT NULL,
    age INTEGER NOT NULL,
    income REAL NOT NULL,
    expenses REAL NOT NULL,
    net_savings REAL NOT NULL,
    portfolio REAL NOT NULL,
    required_capital REAL NOT NULL,
    mortgage_active INTEGER NOT NULL,       -- 0/1 boolean
    pension_value REAL NOT NULL,
    pension_accessible INTEGER NOT NULL    -- 0/1 boolean
);
```

### Files

#### [main.py](web/backend/main.py)
- FastAPI app initialization
- CORS configuration (localhost only)
- Routes: `/api/v1/*`
- OpenAPI docs: `http://localhost:8000/docs`

#### [database.py](web/backend/database.py)
- SQLAlchemy engine setup
- Session management
- Database initialization (`init_db()`)
- Connection pooling

#### [models.py](web/backend/models.py)
SQLAlchemy ORM models:
- `User` — username + hashed password
- `Profile` — name, display_name, description
- `SimulationRun` — generated_at, num_scenarios
- `ScenarioResult` — scenario_name, retirement_year, final_portfolio
- `YearData` — year-by-year metrics

#### [schemas.py](web/backend/schemas.py)
Pydantic response schemas (match ORM models):
- `YearDataSchema` — Single year of data
- `ScenarioResultSchema` — Scenario with year_data[] array
- `SimulationRunSchema` — Run with scenario count
- `ProfileSchema` — Profile info
- `TokenResponse` — JWT token response
- `LoginRequest` — Username + password

#### [auth.py](web/backend/auth.py)
Authentication utilities:
- `hash_password(password)` — PBKDF2 with random salt
- `verify_password(password, hash)` — Compare with stored hash
- `create_access_token(data)` — Create JWT token (24hr expiry)
- `get_current_user(token)` — Dependency for protected routes

**Password Format:** `salt$hash`
- Salt: 16 random bytes (hex)
- Hash: PBKDF2-SHA256 with 100,000 iterations

#### [seed.py](web/backend/seed.py)
One-time database population:
1. Create demo user: `alon` / `alon123`
2. Load profile from `data/profiles/alon/profile.json`
3. Load simulation cache from `data/profiles/alon/analyses/cache/simulation_cache.json`
4. Populate: profiles, simulation_runs, scenario_results, year_data tables
5. Idempotent — skips if profile already seeded

**Run once:**
```bash
cd web/backend
python seed.py
```

### API Endpoints

All endpoints (except login) require `Authorization: Bearer {token}` header.

#### Authentication
```
POST /api/v1/auth/login
Content-Type: application/json

Request:
{
  "username": "alon",
  "password": "alon123"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### Profiles
```
GET /api/v1/profiles
Response:
[
  {
    "id": 1,
    "name": "alon",
    "display_name": "Alon",
    "description": "...",
    "created_at": "2026-04-13T..."
  }
]

GET /api/v1/profiles/{profileId}/runs
Response:
[
  {
    "id": 1,
    "generated_at": "2026-04-13T10:30:00",
    "num_scenarios": 3,
    "label": null
  }
]
```

#### Scenarios
```
GET /api/v1/runs/{runId}/scenarios
Response:
[
  {
    "id": 1,
    "scenario_name": "Alon - Baseline",
    "retirement_year": 11,
    "retirement_age": 52,
    "final_portfolio": 13220000,
    "total_savings": 6170000
  },
  ...
]

GET /api/v1/scenarios/{resultId}
Response:
{
  "id": 1,
  "scenario_name": "Alon - Baseline",
  "retirement_year": 11,
  "final_portfolio": 13220000,
  "year_data": [
    {
      "year": 1,
      "age": 42,
      "income": 45000,
      "expenses": 22000,
      "net_savings": 23000,
      "portfolio": 1700000,
      "required_capital": 6600000,
      "mortgage_active": 0,
      "pension_value": 2100000,
      "pension_accessible": 0
    },
    ...
  ]
}

GET /api/v1/scenarios/{resultId}/summary
Response:
{
  "scenario_name": "Alon - Baseline",
  "retirement_year": 11,
  "retirement_age": 52,
  "final_portfolio": 13220000,
  "total_savings": 6170000
}
```

---

## Frontend Implementation

### Architecture

**Routing:**
- `/` → Login
- `/dashboard` → Profile selector
- `/profiles/:profileId/scenarios` → Scenario list
- `/profiles/:profileId/compare` → Scenario comparison
- `/scenarios/:resultId` → Single scenario detail

**State Management:** Pinia auth store
- `login(username, password)` — Authenticate + store JWT
- `logout()` — Clear JWT
- `isLoggedIn` — Boolean computed property
- JWT persisted to localStorage

**HTTP Client:** Axios with bearer token interceptor

### Key Components

#### [LoginView.vue](web/frontend/src/views/LoginView.vue)
- Username + password form
- Demo credentials: `alon` / `alon123`
- Stores JWT on login, redirects to dashboard
- Error handling for failed login

#### [DashboardView.vue](web/frontend/src/views/DashboardView.vue)
- Loads profiles from `/api/v1/profiles`
- Displays profile cards (name, description)
- Click → navigate to scenario list for that profile
- Logout button in header

#### [ScenariosView.vue](web/frontend/src/views/ScenariosView.vue)
- Run selector dropdown (loads `/api/v1/profiles/{id}/runs`)
- Fetches scenarios for selected run
- Scenario grid cards showing:
  - Scenario name
  - Retirement year (green badge if retires)
  - Final portfolio (₪M format)
  - "Compare Scenarios" button

#### [ScenarioDetailView.vue](web/frontend/src/views/ScenarioDetailView.vue)
- Summary section: name, retirement year, age, final portfolio
- **PortfolioChart** — Single-scenario line chart
- **YearDataTable** — 20 rows of year data with all metrics

#### [ComparisonView.vue](web/frontend/src/views/ComparisonView.vue) — 463 lines
**Features:**
- **Selection Panel:**
  - Run dropdown selector
  - Checkbox list for scenarios (select 2+)
  - "Compare Selected" button
- **Comparison Display** (appears when 2+ selected):
  - **ComparisonChart** — Multi-scenario portfolio chart
  - **Metrics Cards** — Retirement year, age, final portfolio, total savings
  - **ComparisonTable** — Side-by-side year-by-year breakdown

#### [ComparisonChart.vue](web/frontend/src/components/ComparisonChart.vue) — 276 lines
**Multi-scenario line chart with:**
- **Color Palette:** 5 distinct colors (auto-rotates for 5+ scenarios)
- **Legend:** Shows scenario name + retirement year
  - Format: `"Alon - Baseline (Retire: Year 11)"` or `"Never"`
- **Retirement Markers:**
  - Large point at retirement year (radius 7 vs 4)
  - Highlighted in chart
- **Rich Tooltips:** Hover shows:
  - Year + calendar year: `"Year 8 (2033)"`
  - Age: `"Age 49"`
  - Portfolio: `"Alon - Baseline: ₪6.30M"`
  - Income/Expenses: `"Income: ₪45K | Expenses: ₪22K"`
  - Retirement marker: `"🎉 RETIREMENT YEAR"` (only at retirement year)
- **X-Axis:** Absolute years + simulation offset
  - Format: `"2036\n(+11y)"` (2025 base year + simulation year)
- **Y-Axis:** Portfolio value in ₪M
  - Linear (default) or Logarithmic (toggle)
- **Log Scale Toggle:**
  - Checkbox in chart header
  - Switches Y-axis between linear and logarithmic
  - Better for viewing growth rates vs absolute values

#### [ComparisonTable.vue](web/frontend/src/components/ComparisonTable.vue)
- Year column (sticky on left)
- Column group per scenario with:
  - Portfolio (₪M)
  - Age
  - Net savings (₪K)
- Retirement row highlight (green background)
- Row hover styling

#### [PortfolioChart.vue](web/frontend/src/components/PortfolioChart.vue)
Single-scenario chart showing:
- Portfolio line (primary)
- Required capital line (dashed, secondary)
- Retirement year vertical marker
- Pension value line (dimmer)

#### [YearDataTable.vue](web/frontend/src/components/YearDataTable.vue)
20-row table with columns:
- Year
- Age
- Income (₪K)
- Expenses (₪K)
- Net Savings (₪K)
- Portfolio (₪M)
- Required Capital (₪M)
- Pension (₪M)
- Pension Accessible (yes/no)
- Mortgage Active (yes/no)
- Retired? (icon)

Retirement year highlighted with green background.

### Styling

**Colors:**
- Primary: `#667eea` (indigo)
- Success: `#27ae60` (green) — retirement
- Danger: `#e74c3c` (red) — no retirement
- Secondary: `#764ba2` (purple) — compare button
- Neutral: `#555`, `#999` — text

**Chart Colors (5-scenario palette):**
1. `#667eea` (indigo)
2. `#27ae60` (green)
3. `#e74c3c` (red)
4. `#f39c12` (orange)
5. `#9b59b6` (purple)

**Layout:**
- Desktop-first responsive design
- Max width 1400px for content
- Flexbox + CSS Grid
- White cards on light gray background

---

## Setup & Running

### Prerequisites
- Python 3.9+
- Node.js 16+ (npm)

### Backend Setup

```bash
cd web/backend
pip install -r requirements.txt --break-system-packages
python seed.py
uvicorn main:app --reload
```

Backend runs on: `http://localhost:8000`  
API docs: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd web/frontend
npm install
npm run dev
```

Frontend runs on: `http://localhost:5173`

### First Login

1. Navigate to `http://localhost:5173`
2. Username: `alon`
3. Password: `alon123`

### Complete User Flow

```
1. Login (alon/alon123) → Dashboard
2. Click "Alon" profile card → Scenarios List
3. See: "Alon - Baseline", "Alon - IPO Year 2", "Alon - IPO Year 3"
4. Option A: Click scenario → Single detail view (chart + table)
5. Option B: Click "📊 Compare Scenarios" → Comparison view (multi-scenario)
   a. Select 2+ scenarios (checkboxes)
   b. Click "Compare Selected"
   c. View: chart, metrics, side-by-side table
   d. Toggle log scale checkbox on chart
```

---

## Dependencies

### Backend (`requirements.txt`)
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
python-jose>=3.3.0
passlib>=1.7.4
```

### Frontend (`package.json`)
```
vue@3
vue-router@4
pinia@2
axios
chart.js
vue-chartjs
vite
```

---

## File Summary

| File | Purpose | Lines |
|------|---------|-------|
| **Backend** | | |
| main.py | FastAPI app + CORS | 40 |
| database.py | SQLAlchemy setup | 45 |
| models.py | ORM models (5 tables) | 80 |
| schemas.py | Pydantic schemas | 120 |
| auth.py | JWT + PBKDF2 | 75 |
| seed.py | Database seeding | 120 |
| routers/auth.py | Login endpoint | 30 |
| routers/profiles.py | Profile endpoints | 40 |
| routers/scenarios.py | Scenario endpoints | 60 |
| **Frontend** | | |
| router/index.js | Routes + middleware | 50 |
| stores/auth.js | Pinia auth store | 45 |
| LoginView.vue | Login form | 100 |
| DashboardView.vue | Profile selector | 150 |
| ScenariosView.vue | Scenario list | 140 |
| ScenarioDetailView.vue | Single scenario | 250 |
| ComparisonView.vue | Multi-scenario | 463 |
| ComparisonChart.vue | Multi-scenario chart | 276 |
| ComparisonTable.vue | Comparison table | 166 |
| PortfolioChart.vue | Single chart | 200 |
| YearDataTable.vue | Single table | 180 |
| **Total Source Code** | | **~2,000 lines** |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Vue 3 Frontend (5173)                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  LoginView ──→ DashboardView ──→ ScenariosView             │
│                                   ├─→ ScenarioDetailView   │
│                                   └─→ ComparisonView       │
│                                       ├─ ComparisonChart   │
│                                       ├─ ComparisonTable   │
│                                       └─ Metrics Cards     │
│                                                              │
│  Pinia Auth Store ←──→ localStorage (JWT token)            │
│                                                              │
│  Axios HTTP Client ←──────────────┐                        │
└────────────────────────────────────┼────────────────────────┘
                                    │ Bearer Token
┌────────────────────────────────────┼────────────────────────┐
│            FastAPI Backend (8000)   │                       │
├────────────────────────────────────┼────────────────────────┤
│                                    ▼                        │
│  /auth/login ←─ auth.py (JWT + PBKDF2)                     │
│  /profiles    ←─ routers/profiles.py                       │
│  /scenarios   ←─ routers/scenarios.py                      │
│                                                              │
│  SQLAlchemy ORM (5 tables) ←─ database.py                  │
│                                 │                          │
│                                 ▼                          │
│                        data/finance_planner.db (SQLite)    │
│                                 │                          │
│                                 ▼                          │
│            data/profiles/alon/analyses/cache/              │
│                    simulation_cache.json (source)          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

1. **Output-First:** Display existing cached results before building input forms
2. **Profile-Based:** Multi-user support via `data/profiles/{name}/` directories
3. **JWT Auth:** Simple token-based authentication, no session management
4. **SQLite:** Lightweight, file-based, no external DB server needed
5. **Pinia Stores:** Centralized state for auth + reusable across views
6. **Axios Interceptors:** Bearer token automatically added to all API calls
7. **Responsive Charts:** Chart.js for flexibility (linear/log scale, colors, tooltips)
8. **Comparison-First:** Emphasis on multi-scenario analysis (side-by-side view)

---

## Future Enhancements (Phase 2+)

- [ ] Input forms for creating/editing scenarios
- [ ] Israeli defaults template layer
- [ ] AI insights ("What if?" analysis)
- [ ] Mobile layout
- [ ] User registration
- [ ] Save custom analyses/notes
- [ ] PDF export of comparisons
- [ ] Real-time scenario editing with instant preview
- [ ] What-if parameter sliders
- [ ] Scenario weighting/probability analysis
- [ ] Multi-user support with profile sharing

---

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install -r requirements.txt --break-system-packages --upgrade

# Reset database
rm data/finance_planner.db
python seed.py
```

### Frontend won't start
```bash
# Clear cache + reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Login fails
```bash
# Verify seed completed
sqlite3 data/finance_planner.db "SELECT * FROM users;"

# Should show: (1, 'alon', 'salt$hash...')
```

### Charts not rendering
1. Open browser console (F12)
2. Check for JavaScript errors
3. Verify API is returning data: `curl -H "Authorization: Bearer {token}" http://localhost:8000/api/v1/scenarios/1`

---

## Documentation

- [web/README.md](web/README.md) — Architecture + API overview
- [web/COMPARISON_GUIDE.md](web/COMPARISON_GUIDE.md) — User guide for comparison feature
- [QUICK_START_WEB.md](QUICK_START_WEB.md) — Development quick start
- [CLAUDE.md](CLAUDE.md) — Main project guidelines

---

**Implementation Complete.** All features from the MVP plan are functional and tested.
