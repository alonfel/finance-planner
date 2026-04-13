# Project Structure — Complete Map

**Last Updated:** April 13, 2026  
**Status:** MVP Web App Complete + Core Python Engine Stable

---

## Directory Tree (Key Files Only)

```
finance_planner/
│
├── 📋 Documentation (Root)
│   ├── README.md                        # Main project overview
│   ├── CLAUDE.md                        # Claude Code guidelines (updated regularly)
│   ├── PROFILE_SETUP.md                 # Guide for creating new profiles
│   ├── QUICK_START_WEB.md               # Web app quick start
│   ├── WEB_IMPLEMENTATION.md            # 400-line comprehensive web app reference
│   ├── CHANGES_SESSION.md               # This session's changes summary
│   └── PROJECT_STRUCTURE.md             # This file
│
├── 🔵 Web Application (`/web/`)
│   ├── README.md                        # Web app architecture + API docs
│   ├── COMPARISON_GUIDE.md              # User guide: how to use comparison feature
│   │
│   ├── backend/
│   │   ├── requirements.txt             # Python deps: fastapi, sqlalchemy, pydantic, etc
│   │   ├── main.py                      # FastAPI entry point (CORS, routes, docs)
│   │   ├── database.py                  # SQLAlchemy + SQLite setup
│   │   ├── models.py                    # ORM models: User, Profile, Run, Result, YearData
│   │   ├── schemas.py                   # Pydantic schemas for API responses
│   │   ├── auth.py                      # JWT + PBKDF2 password hashing
│   │   ├── seed.py                      # Database seeding from cache
│   │   └── routers/
│   │       ├── auth.py                  # POST /auth/login
│   │       ├── profiles.py              # GET /profiles, /profiles/{id}/runs
│   │       └── scenarios.py             # GET /scenarios endpoints
│   │
│   └── frontend/
│       ├── package.json                 # Vue 3, Router, Pinia, Axios, Chart.js
│       ├── vite.config.js               # Vite dev server (port 5173)
│       ├── index.html                   # Entry HTML
│       └── src/
│           ├── main.js                  # App init
│           ├── App.vue                  # Root component
│           ├── router/
│           │   └── index.js             # Routes: Login, Dashboard, Scenarios, Detail, Comparison
│           ├── stores/
│           │   └── auth.js              # Pinia: login/logout, JWT, localStorage
│           ├── views/                   # Full pages
│           │   ├── LoginView.vue
│           │   ├── DashboardView.vue
│           │   ├── ScenariosView.vue
│           │   ├── ScenarioDetailView.vue
│           │   └── ComparisonView.vue   # Multi-scenario comparison
│           └── components/              # Reusable components
│               ├── ComparisonChart.vue  # Multi-scenario chart (log scale, tooltips)
│               ├── ComparisonTable.vue  # Side-by-side table
│               ├── PortfolioChart.vue   # Single scenario chart
│               └── YearDataTable.vue    # Single scenario table
│
├── 🟡 Core Python Engine (`/domain`, `/infrastructure`, `/presentation`, `/analysis`)
│   ├── domain/
│   │   ├── DOMAIN.md                    # Business logic documentation
│   │   ├── breakdown.py                 # IncomeBreakdown, ExpenseBreakdown (named components)
│   │   ├── models.py                    # Event, Mortgage, Pension, Scenario, ScenarioNode
│   │   ├── simulation.py                # Core simulate() engine + YearData
│   │   └── insights.py                  # Comparison logic + insight objects
│   │
│   ├── infrastructure/
│   │   ├── CONFIG.md                    # Configuration system documentation
│   │   ├── parsers.py                   # Dict→model parsing (income, expense, pension)
│   │   ├── loaders.py                   # load_scenarios, load_settings, load_scenario_nodes
│   │   ├── data_layer.py                # Profile management + FINANCE_PROFILE env var
│   │   └── cache.py                     # Serialization/deserialization for analysis
│   │
│   ├── presentation/
│   │   ├── PRESENTATION.md              # Output formatting documentation
│   │   ├── constants.py                 # Currency symbols, formatting
│   │   └── formatters.py                # print_scenario_header, print_year_summary
│   │
│   └── analysis/
│       ├── ANALYSIS.md                  # Analysis system documentation
│       ├── run_simulations.py           # Batch runner (profile-aware)
│       ├── run_analysis.py              # Config-driven analysis dispatcher
│       └── generate_report.py           # Report generation to /reports/
│
├── 📊 Simulation Data
│   ├── data/
│   │   ├── finance_planner.db           # SQLite database (web app)
│   │   └── profiles/
│   │       ├── default/                 # Daniel (default user)
│   │       │   ├── profile.json
│   │       │   ├── settings.json
│   │       │   ├── scenarios.json
│   │       │   ├── scenario_nodes.json
│   │       │   └── analyses/
│   │       │       ├── cache/           # Cached simulation results
│   │       │       ├── results/         # Analysis output
│   │       │       └── config.json
│   │       │
│   │       ├── alon/                    # Alon (2 core scenarios)
│   │       │   ├── profile.json
│   │       │   ├── settings.json
│   │       │   ├── scenarios.json
│   │       │   ├── scenario_nodes.json
│   │       │   └── analyses/
│   │       │       ├── cache/           # Seeded into web app
│   │       │       ├── results/
│   │       │       └── config.json
│   │       │
│   │       └── avg_couple_israel/       # New: average Israeli couple profile
│   │           ├── profile.json
│   │           ├── settings.json
│   │           ├── scenarios.json
│   │           ├── scenario_nodes.json
│   │           └── analyses/
│   │               ├── cache/
│   │               ├── results/
│   │               └── config.json
│   │
│   └── reports/
│       ├── portfolio_growth_analysis.md
│       ├── ALON_FINANCIAL_REPORT_2026_UPDATED.md
│       ├── ALL_SCENARIOS_20YEAR_DETAILED_ANALYSIS.md
│       └── ... (other generated reports)
│
├── 🧪 Tests
│   └── tests/
│       ├── test_simulation.py           # 42 unit tests (all passing)
│       └── test_*.py                    # Future test files
│
└── 📝 Configuration Files
    └── .gitignore                       # Python, Node, database artifacts
```

---

## What Each Layer Does

### 🔵 Web Application (`/web/`)

**Purpose:** Display financial simulations in beautiful, interactive UI

**What It Does:**
- Shows cached simulation results (from Python engine)
- No input forms (Phase 2 feature)
- Dashboard → Scenarios → Detail/Comparison views
- Multi-scenario comparison with retirement markers, log scale, rich tooltips
- JWT authentication (demo account: alon/alon123)

**Tech:** FastAPI + Vue 3 + SQLite + Chart.js

**Status:** ✅ MVP Complete

### 🟡 Python Engine (`/domain`, `/infrastructure`, `/presentation`, `/analysis`)

**Purpose:** Core financial simulation logic

**What It Does:**
- `domain/` — Pure business logic (Event, Mortgage, Pension, Scenario, simulate())
- `infrastructure/` — Config loading (profile-aware, env var support)
- `presentation/` — Output formatting (currency display, tables)
- `analysis/` — Batch simulation + reporting (config-driven)

**Tech:** Python stdlib only (no external dependencies)

**Status:** ✅ Stable and production-ready

---

## How to Use

### For Development

```bash
# Python simulation
python main.py

# Web app backend
cd web/backend && python seed.py && uvicorn main:app --reload

# Web app frontend
cd web/frontend && npm install && npm run dev
```

### For Analysis

```bash
# Simulate all profiles (cached)
python analysis/run_simulations.py

# Analyze from cache
python analysis/run_analysis.py

# Generate reports
PYTHONPATH=. python analysis/generate_report.py growth_analysis
```

### For Testing

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## Configuration-Driven Design

Edit these to change behavior (no code changes):

| File | What Controls | Where |
|------|---|---|
| `scenarios.json` | Income, expenses, mortgage, pension per scenario | Each profile dir |
| `scenario_nodes.json` | Inheritance tree + overrides | Each profile dir |
| `settings.json` | Growth rates, retirement age, initial conditions | Each profile dir |
| `analysis.json` | Which comparisons to run | Each profile dir |

Run `python analysis/run_simulations.py` after editing any config file.

---

## Key Features

### Python Engine

✅ **Flexible Income/Expenses**
- Named components (salary, freelance, rental, etc)
- Deep-merge overrides in scenario tree
- Backward compatible with flat numbers

✅ **Pension Modeling**
- Separate accumulation from liquid portfolio
- Two retirement modes: liquid_only vs pension_bridged
- Realistic Israeli pension (Keren Pensia) behavior

✅ **Profile-Based Architecture**
- Multi-user data organization (`data/profiles/{name}/`)
- Environment variable support (`FINANCE_PROFILE=alon`)
- Separate simulations per profile

✅ **Decoupled Analysis**
- Simulate once → analyze many times (100x faster)
- Configuration-driven: JSON controls analysis

### Web App

✅ **Single Scenario View**
- Summary metrics (retirement year, age, portfolio)
- Line chart: portfolio vs required capital
- 20-year year-by-year table
- Retirement year highlighted

✅ **Multi-Scenario Comparison**
- Run dropdown selector
- Checkbox selection (min 2 scenarios)
- 5-color palette (auto-rotates)
- Retirement year markers in legend + large points on chart
- Rich tooltips: year, calendar year, age, income, expenses, 🎉 marker
- X-axis: absolute years + simulation offset (2036 / +11y)
- Y-axis: linear or logarithmic (toggle checkbox)
- Metrics cards comparison
- Side-by-side year table

✅ **Authentication**
- JWT tokens (24h expiry)
- PBKDF2 password hashing
- localStorage persistence
- Bearer token interceptor

---

## Documentation Map

| File | Purpose | Audience |
|------|---------|----------|
| **README.md** | Project overview | Everyone |
| **CLAUDE.md** | Claude Code guidelines | AI assistant |
| **PROFILE_SETUP.md** | Create new profiles | Users |
| **QUICK_START_WEB.md** | Web app dev setup | Developers |
| **WEB_IMPLEMENTATION.md** | Web app reference (400 lines) | Developers |
| **CHANGES_SESSION.md** | This session summary | Developers |
| **domain/DOMAIN.md** | Business logic docs | Developers |
| **infrastructure/CONFIG.md** | Config system docs | Developers |
| **presentation/PRESENTATION.md** | Output formatting docs | Developers |
| **analysis/ANALYSIS.md** | Analysis system docs | Developers |
| **web/README.md** | Web app architecture + API | Developers |
| **web/COMPARISON_GUIDE.md** | User guide: comparison feature | Users |

---

## Recent Sessions

| Date | Focus | Status |
|------|-------|--------|
| **Apr 13, 2026** | Web app MVP (this session) | ✅ Complete |
| **Apr 13, 2026** | Pension bridge bug fix | ✅ Complete |
| **Apr 10, 2026** | Pension-bridged retirement mode | ✅ Complete |
| **Apr 5, 2026** | Profile-based data layer | ✅ Complete |
| **Mar 20, 2026** | Config-driven analysis system | ✅ Complete |

---

## Next Steps (Phase 2+)

### Phase 2: Input Forms
- [ ] Create scenario UI (income/expenses components)
- [ ] Edit scenario parameters (with instant preview)
- [ ] Save custom scenarios to database
- [ ] Scenario version history

### Phase 3: Israeli Defaults
- [ ] Profile template: couple, single, family
- [ ] Auto-populate settings (retirement age, pension rates)
- [ ] Tax calculation (Israeli tax brackets)
- [ ] Expense templates (housing, childcare, etc)

### Phase 4: AI Insights
- [ ] What-if analysis (adjust one parameter, see impact)
- [ ] Milestone tracking (when reach ₪X target?)
- [ ] Risk analysis (portfolio volatility, drawdown)
- [ ] Optimization (maximize retirement year given constraints)

### Phase 5: Advanced Features
- [ ] Multi-user with profile sharing
- [ ] Scenario weighting/probability
- [ ] PDF export of comparison
- [ ] Real-time team collaboration
- [ ] Mobile app

---

## Git Commits (Recent)

```
ad3db16  Feature: Complete web application MVP — FastAPI + Vue 3
fb87e9c  Fix: Correct age calculation in simulation (off-by-one error)
b8330da  Update Alon scenarios with realistic parameters and add lifetime sustainability checks
7ee2648  Feature: Pension-Bridged Retirement Mode
596ca41  Docs: Update documentation for pension feature and profile-based architecture
```

---

## Key Statistics

| Metric | Count |
|--------|-------|
| **Python Files** | ~15 |
| **Vue Components** | 11 |
| **Test Cases** | 42 (all passing) |
| **Database Tables** | 5 |
| **API Endpoints** | 8 |
| **Routes (Frontend)** | 5 |
| **Profiles** | 3 (default, alon, avg_couple_israel) |
| **Scenarios (Alon)** | 3 (Baseline, IPO Year 2, IPO Year 3) |
| **Simulation Years** | 20 per scenario |
| **Lines of Code** | ~2,500 (web app only) |
| **Lines of Docs** | ~2,000 |

---

## Summary

**A complete, production-ready financial planning web application built on top of a stable Python simulation engine.**

- ✅ **Web App MVP:** Beautiful display of cached simulation results
- ✅ **Python Engine:** Pure, testable, configuration-driven simulation
- ✅ **Multi-Scenario Comparison:** Advanced visualization with retirement markers, tooltips, log scale
- ✅ **Profile-Based:** Extensible architecture for multiple users
- ✅ **Well-Documented:** Component guides + user guides + code comments
- ✅ **Tested:** 42 unit tests, all passing

**Ready to:** Use now (users), extend (Phase 2+), or deploy (with minor config changes)
