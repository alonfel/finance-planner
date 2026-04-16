# Finance Planner Web App

FastAPI backend + Vue 3 frontend for real-time financial scenario exploration, Monte Carlo simulation, and probabilistic retirement planning.

## Setup

### Backend

```bash
cd web/backend
pip install -r requirements.txt
python seed.py          # first time — seeds DB from Alon profile cache
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

### Frontend

```bash
cd web/frontend
npm install
npm run dev
```

- App: `http://localhost:5173`

**Login:** `alon` / `alon123`

---

## Features

- **What-If Explorer** — Real-time sliders for income, expenses, growth rate, starting age, initial portfolio. Add/toggle one-time events and probabilistic events. Save any configuration as a named scenario.
- **Probabilistic Events** — Model uncertain outcomes (IPO, acquisition, bonus) with multiple weighted branches. Chart overlays one line per branch; metrics show probability badges.
- **Monte Carlo** — 500-trial fan chart (p5/p50/p95), retirement probability, survival probability, OAT sensitivity ranking.
- **Historical Backtesting** — S&P 500, NASDAQ, Bonds, Russell 2000 from any start year (1928–2024).
- **Scenario Browser** — Browse, compare, and delete saved scenarios.
- **Scenario Detail** — Portfolio chart, year-by-year table, exact definition values (growth rate, withdrawal rate, return mode).
- **Comparison View** — Side-by-side scenario comparison with combined chart.
- **Scenario Generator** — Questionnaire-driven guided scenario creation.

---

## Architecture

### Backend (`web/backend/`)

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, router registration |
| `database.py` | SQLAlchemy + SQLite setup, session management |
| `models.py` | ORM models (Profile, SimulationRun, ScenarioResult, YearData, ScenarioDefinition, events, mortgages, pensions, probabilistic events) |
| `schemas.py` | Pydantic schemas; `WhatIfScenarioSchema` is the canonical scenario state contract |
| `auth.py` | JWT authentication |
| `seed.py` | Seeds DB from Alon profile simulation cache |
| `migration.py` | Idempotent schema migrations |
| `routers/auth.py` | `POST /api/v1/auth/login` |
| `routers/profiles.py` | Profile listing, simulation runs |
| `routers/scenarios.py` | Scenario retrieval and deletion |
| `routers/simulate.py` | Stateless What-If simulation; returns `branches[]` for probabilistic events |
| `routers/whatif_saves.py` | Save What-If state to SQLite with full event/outcome round-trip |
| `routers/monte_carlo.py` | `POST /api/v1/monte-carlo` |
| `routers/generator.py` | Questionnaire API (`/api/questionnaire/*`, `/api/generate-scenario`) |
| `services/scenario_generator.py` | Config-driven questionnaire → Scenario conversion |

### Frontend (`web/frontend/src/`)

| Path | Purpose |
|------|---------|
| `views/LoginView.vue` | Login page |
| `views/DashboardView.vue` | Profile overview |
| `views/ScenariosView.vue` | Scenario browser |
| `views/ScenarioView.vue` | Single scenario detail |
| `views/ScenarioDetailView.vue` | Detailed scenario with definition values |
| `views/WhatIfView.vue` | What-If Explorer — main interactive view |
| `views/MonteCarloView.vue` | Monte Carlo fan chart + sensitivity |
| `views/ComparisonView.vue` | Side-by-side scenario comparison |
| `components/FanChart.vue` | p5/p50/p95 fan chart |
| `components/ComparisonChart.vue` | Multi-series portfolio chart |
| `components/PortfolioChart.vue` | Single-scenario portfolio chart |
| `components/YearDataTable.vue` | Year-by-year data table |
| `components/ScenarioGeneratorModal.vue` | Guided scenario creation modal |
| `components/SaveAsModal.vue` | Save What-If as named scenario |
| `stores/auth.js` | Pinia auth store (JWT) |

### Frontend architecture notes

- **`WhatIfScenarioSchema`** (backend) is the canonical source of truth for scenario state
- **`toApiRequest()`** in WhatIfView — serializes all state for saves/simulates
- **`fromDefinition(def)`** in WhatIfView — restores all state from a saved definition
- Adding a new field requires: update schema + update two mappers

---

## API Reference

All endpoints except login require `Authorization: Bearer <JWT>`.

```
POST   /api/v1/auth/login

GET    /api/v1/profiles/{profile_id}/runs
GET    /api/v1/runs/{run_id}/scenarios
GET    /api/v1/scenarios/{result_id}
GET    /api/v1/scenarios/{result_id}/summary
DELETE /api/v1/scenarios/{result_id}

POST   /api/v1/simulate
POST   /api/v1/monte-carlo
POST   /api/v1/profiles/{profile_id}/saved-scenarios

POST   /api/questionnaire/config
POST   /api/questionnaire/completeness
POST   /api/questionnaire/visible-questions
POST   /api/generate-scenario
```

`POST /api/v1/simulate` returns `branches: []` when no probabilistic events are present (backward compatible), or one `BranchResultSchema` per outcome cross-product when they are.

---

## Database Schema

```
users                           — auth
profiles                        — user profiles
simulation_runs                 — run metadata
scenario_results                — per-scenario results
year_data                       — year-by-year output
scenario_definitions            — What-If saved state
scenario_events                 — one-time events → scenario_definitions
scenario_mortgages              — mortgage → scenario_definitions
scenario_pensions               — pension → scenario_definitions
scenario_probabilistic_events   — probabilistic event definitions
scenario_event_outcomes         — outcome branches per probabilistic event
```

---

## Troubleshooting

**Backend not responding:**
```bash
lsof -i :8000
ls -la data/finance_planner.db
```

**Frontend build issues:**
```bash
rm -rf web/frontend/node_modules && npm install
```

**Database reset:**
```bash
rm data/finance_planner.db
python web/backend/seed.py
```
