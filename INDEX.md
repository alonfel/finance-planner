# Finance Planner — Documentation Index

**Project Status:** MVP Complete (Apr 13, 2026)  
**Last Session:** Web Application MVP Implementation  
**Next Phase:** Input Forms & Israeli Defaults

---

## 📚 Start Here

### For Everyone
1. **[README.md](README.md)** — Project overview and philosophy
2. **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** — Directory tree and what each part does

### For Users (No Coding)
3. **[QUICK_START_WEB.md](QUICK_START_WEB.md)** — How to run the app locally
4. **[web/COMPARISON_GUIDE.md](web/COMPARISON_GUIDE.md)** — User guide: how to use comparison feature

### For Developers
5. **[CLAUDE.md](CLAUDE.md)** — Claude Code guidelines (updated regularly)
6. **[WEB_IMPLEMENTATION.md](WEB_IMPLEMENTATION.md)** — Complete web app reference (400 lines)
7. **[CHANGES_SESSION.md](CHANGES_SESSION.md)** — This session's implementation summary

---

## 🔍 Find What You Need

### Building / Running

| Task | Where |
|------|-------|
| Run Python simulation | `python main.py` |
| Run web app backend | [QUICK_START_WEB.md](QUICK_START_WEB.md) |
| Run web app frontend | [QUICK_START_WEB.md](QUICK_START_WEB.md) |
| Run tests | `python -m unittest discover -s tests` |
| Generate reports | `python analysis/generate_report.py growth_analysis` |

### Configuration

| Topic | File |
|-------|------|
| Simulation settings | `data/profiles/{name}/settings.json` |
| Scenario definitions | `data/profiles/{name}/scenarios.json` |
| Scenario inheritance tree | `data/profiles/{name}/scenario_nodes.json` |
| Analysis configs | `data/profiles/{name}/analyses/config.json` |
| Web app API | [web/README.md](web/README.md) |

### Understanding the Code

| Topic | File |
|-------|------|
| Business logic (simulation, pension, mortgage) | [domain/DOMAIN.md](domain/DOMAIN.md) |
| Configuration loading & caching | [infrastructure/CONFIG.md](infrastructure/CONFIG.md) |
| Output formatting (currency, tables) | [presentation/PRESENTATION.md](presentation/PRESENTATION.md) |
| Analysis system (batch runs, reporting) | [analysis/ANALYSIS.md](analysis/ANALYSIS.md) |
| Web app backend (FastAPI, auth, DB) | [WEB_IMPLEMENTATION.md](WEB_IMPLEMENTATION.md#backend) |
| Web app frontend (Vue 3, components) | [WEB_IMPLEMENTATION.md](WEB_IMPLEMENTATION.md#frontend) |

### Creating New Profiles

| Task | File |
|-------|------|
| Create new profile from scratch | [PROFILE_SETUP.md](PROFILE_SETUP.md) |
| Understand profile structure | [infrastructure/CONFIG.md](infrastructure/CONFIG.md) |

---

## 📁 Directory Guide

```
📋 Documentation (Root-level .md files)
├── README.md                      Main overview
├── CLAUDE.md                      Claude Code guidelines
├── PROFILE_SETUP.md               Profile creation guide
├── QUICK_START_WEB.md             Web app quick start
├── WEB_IMPLEMENTATION.md          Web app comprehensive reference
├── CHANGES_SESSION.md             This session's changes
├── PROJECT_STRUCTURE.md           Complete project map
└── INDEX.md                       This file

🔵 Web Application
├── web/README.md                  Web app architecture
├── web/COMPARISON_GUIDE.md        Comparison feature user guide
├── web/backend/                   FastAPI application
│   ├── main.py                    Entry point
│   ├── database.py                SQLite setup
│   ├── models.py                  ORM models
│   ├── auth.py                    JWT + PBKDF2
│   └── routers/                   API endpoints
└── web/frontend/                  Vue 3 application
    ├── index.html                 Entry point
    ├── src/router/                Routes
    ├── src/stores/                Pinia stores
    ├── src/views/                 Full-page components
    └── src/components/            Reusable components

🟡 Python Engine
├── domain/                        Business logic
│   ├── DOMAIN.md                  Business logic docs
│   ├── models.py                  Scenario, Pension, Mortgage
│   ├── simulation.py              Core simulate() engine
│   └── insights.py                Comparison logic
├── infrastructure/                Config & loading
│   ├── CONFIG.md                  Config system docs
│   ├── loaders.py                 Load profiles & scenarios
│   └── parsers.py                 JSON → model parsing
├── presentation/                  Output formatting
│   ├── PRESENTATION.md            Output docs
│   └── formatters.py              Currency, tables
└── analysis/                      Batch & reporting
    ├── ANALYSIS.md                Analysis system docs
    ├── run_simulations.py         Batch runner
    ├── run_analysis.py            Config-driven analysis
    └── generate_report.py         Report generation

📊 Data
├── data/
│   ├── finance_planner.db         SQLite database
│   └── profiles/
│       ├── default/               Daniel profile
│       ├── alon/                  Alon profile
│       └── avg_couple_israel/     Israeli couple profile
└── reports/                       Generated reports

🧪 Tests
└── tests/
    └── test_simulation.py         42 unit tests
```

---

## 🎯 Common Workflows

### I want to...

#### **See a scenario simulation**
```bash
python main.py
```
→ Shows Alon - Baseline simulation with 20 years of data

---

#### **Use the web app**
```bash
# Terminal 1: Backend
cd web/backend && python seed.py && uvicorn main:app --reload

# Terminal 2: Frontend
cd web/frontend && npm install && npm run dev

# Browser
http://localhost:5173
Login: alon / alon123
```
→ Dashboard → click Alon → view scenarios or compare

---

#### **Compare scenarios visually**
Via web app → Scenarios page → click "📊 Compare Scenarios" button → select 2+ scenarios → view chart with retirement markers, log scale, tooltips

---

#### **Run analysis on all profiles**
```bash
python analysis/run_simulations.py
python analysis/run_analysis.py
```
→ Cached results → instant analysis (no re-simulation)

---

#### **Create a new profile**
1. Read [PROFILE_SETUP.md](PROFILE_SETUP.md)
2. Create `data/profiles/{name}/` with config files
3. Run `python analysis/run_simulations.py`
4. (Optional) Add to web app by editing seed.py

---

#### **Generate a financial report**
```bash
PYTHONPATH=. python analysis/generate_report.py growth_analysis
```
→ Saves to `/reports/`

---

#### **Add a new scenario to Alon's profile**
1. Edit `data/profiles/alon/scenarios.json` (add scenario block)
2. OR edit `data/profiles/alon/scenario_nodes.json` (add inheritance node)
3. Run `python analysis/run_simulations.py`
4. (Optional) Refresh web app: clear DB cache if needed

---

#### **Change simulation settings**
Edit `data/profiles/{name}/settings.json` (growth rates, initial conditions, etc.)

Then run:
```bash
python analysis/run_simulations.py
```

---

#### **Run tests**
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

All 42 tests should pass.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────┐
│      User (via Web App or CLI)          │
└──────────────┬──────────────────────────┘
               │
               ├─────────────────────┬────────────────────┐
               │                     │                    │
       ┌───────▼────────┐   ┌────────▼──────┐   ┌────────▼──────┐
       │   Web App      │   │  CLI (main.py)│   │  Analysis CLI  │
       │  (Vue 3 UI)    │   │  (simulation) │   │  (reporting)   │
       └───────┬────────┘   └────────┬──────┘   └────────┬──────┘
               │                     │                    │
       ┌───────▼────────────────────▼────────────────────▼─────┐
       │                                                        │
       │         Python Engine (4 Layers)                      │
       │  ┌──────────────────────────────────────────────┐    │
       │  │ Infrastructure: Config Loading (profiles)   │    │
       │  └────────────────┬─────────────────────────────┘    │
       │                   │                                   │
       │  ┌────────────────▼─────────────────────────────┐    │
       │  │ Domain: Business Logic (simulation engine)  │    │
       │  │  - Scenario (income, expenses, pension)     │    │
       │  │  - YearData (portfolio, age, retirement)    │    │
       │  │  - Pension, Mortgage, Event models          │    │
       │  └────────────┬────────────────────────────────┘    │
       │               │                                      │
       │  ┌────────────▼─────────────────────────────────┐    │
       │  │ Presentation: Output Formatting             │    │
       │  │  - Currency display (₪)                     │    │
       │  │  - Table formatting                         │    │
       │  └─────────────────────────────────────────────┘    │
       │                                                      │
       │  ┌──────────────────────────────────────────────┐    │
       │  │ Analysis: Batch Processing & Insights       │    │
       │  │  - Simulate all profiles (profile-aware)    │    │
       │  │  - Generate reports                         │    │
       │  └──────────────────────────────────────────────┘    │
       │                                                        │
       └─────────────────┬──────────────────────────────────────┘
                         │
        ┌────────────────┴───────────────────┐
        │                                    │
   ┌────▼─────────┐               ┌─────────▼──────┐
   │  SQLite DB   │               │  Cached JSON   │
   │ (web app)    │               │ (source data)  │
   └──────────────┘               └────────────────┘
```

---

## 📊 Key Statistics

| Category | Count |
|----------|-------|
| **Python source files** | ~15 |
| **Vue/JS components** | 11 |
| **Test cases** | 42 |
| **Database tables** | 5 |
| **API endpoints** | 8 |
| **Frontend routes** | 5 |
| **Profiles** | 3 |
| **Total lines of code** | ~2,500 |
| **Total lines of documentation** | ~2,000 |

---

## 🚀 Quick Commands Reference

```bash
# Simulation
python main.py                          # Run single scenario

# Web App
cd web/backend && python seed.py        # Setup DB
uvicorn main:app --reload               # Start backend
cd web/frontend && npm run dev           # Start frontend

# Analysis
python analysis/run_simulations.py       # Batch simulate
python analysis/run_analysis.py          # Config-driven analysis
python analysis/generate_report.py TYPE  # Generate reports

# Testing
python -m unittest discover -s tests -p "test_*.py" -v

# Environment Variables
FINANCE_PROFILE=alon python main.py      # Run Alon profile
FINANCE_PROFILE=alon python analysis/run_simulations.py
```

---

## 📞 Help

| Need | Resource |
|------|----------|
| **Setup web app** | [QUICK_START_WEB.md](QUICK_START_WEB.md) |
| **Use comparison** | [web/COMPARISON_GUIDE.md](web/COMPARISON_GUIDE.md) |
| **Create profile** | [PROFILE_SETUP.md](PROFILE_SETUP.md) |
| **Understand architecture** | [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) |
| **Component details** | [WEB_IMPLEMENTATION.md](WEB_IMPLEMENTATION.md) |
| **Business logic** | [domain/DOMAIN.md](domain/DOMAIN.md) |
| **Config system** | [infrastructure/CONFIG.md](infrastructure/CONFIG.md) |

---

## ✅ Status Checklist

- ✅ Core Python engine (simulation, pension, mortgage)
- ✅ Profile-based data layer (multi-user support)
- ✅ Configuration-driven analysis system
- ✅ Web application MVP
  - ✅ Authentication (JWT + demo account)
  - ✅ Dashboard (profile selector)
  - ✅ Scenarios list view
  - ✅ Single scenario detail (chart + table)
  - ✅ **Multi-scenario comparison with retirement markers, log scale, rich tooltips**
- ✅ Comprehensive documentation
- ✅ 42 unit tests (all passing)

---

## 🔮 Next Steps (Phase 2+)

- [ ] Input forms for creating scenarios
- [ ] Israeli defaults template layer
- [ ] AI insights & what-if analysis
- [ ] Mobile app layout
- [ ] User registration
- [ ] Real-time scenario editing

---

**Created:** Apr 13, 2026  
**Web App Status:** ✅ MVP Complete  
**Python Engine Status:** ✅ Production Ready  
**Documentation Status:** ✅ Comprehensive
