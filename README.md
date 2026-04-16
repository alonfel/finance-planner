# Finance Planner

A full-stack personal finance simulation platform. Model retirement scenarios, run Monte Carlo projections, explore what-ifs in real time, and stress-test outcomes against historical market data.

**108 tests passing. Pure Python domain layer. FastAPI + Vue 3 web app.**

---

## What It Does

- **Retirement simulation** — Year-by-year portfolio growth; detects the first year your portfolio can sustain withdrawals indefinitely
- **Monte Carlo** — 500-trial lognormal sampling → p5/p50/p95 fan chart, retirement probability, survival probability
- **Probabilistic events** — Model uncertain outcomes (IPO, acquisition, bonus) with multiple weighted branches
- **Historical backtesting** — Replay actual S&P 500, NASDAQ, Bonds, or Russell 2000 returns from any start year (1928–2024)
- **What-If Explorer** — Real-time slider playground; save any configuration as a named scenario
- **Scenario generator** — Questionnaire-driven scenario creation (guided onboarding)
- **Pension modeling** — Israeli-style locked pension (Keren Pensia) with two retirement modes: `liquid_only` and `pension_bridged`
- **Scenario inheritance** — Tree of scenarios with deep-merge overrides; no duplication
- **OAT sensitivity analysis** — Ranks which inputs (return rate, income, horizon) affect outcomes most

---

## Quick Start

### CLI — Scenario Analysis

```bash
# Run the default simulation
python main.py

# Simulate all scenarios and cache results
python analysis/run_simulations.py

# Run analyses (fast, uses cache)
python analysis/run_analysis.py

# Alon's profile
FINANCE_PROFILE=alon python analysis/run_simulations.py
FINANCE_PROFILE=alon python analysis/run_analysis.py
```

### Web App

**Backend:**
```bash
cd web/backend
pip install -r requirements.txt
python seed.py          # first time only
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd web/frontend
npm install
npm run dev
```

Open `http://localhost:5173` — login with `alon` / `alon123`.

### Tests

```bash
python -m unittest discover -s tests -p "test_*.py" -v
# → 108 tests, 0 failures
```

---

## Architecture

```
finance_planner/
├── domain/               # Pure business logic — no I/O, no deps
│   ├── models.py         # Scenario, Event, ProbabilisticEvent, Mortgage, Pension, ScenarioNode
│   ├── simulation.py     # simulate(), simulate_branches()
│   ├── monte_carlo.py    # run_monte_carlo(), MonteCarloResult
│   ├── sensitivity.py    # run_oat_sensitivity(), SensitivityResult
│   ├── historical_returns.py  # S&P 500, NASDAQ, Bonds, Russell 2000 (1928–2024)
│   ├── breakdown.py      # IncomeBreakdown, ExpenseBreakdown
│   └── insights.py       # build_insights(), format_insights()
├── infrastructure/       # Config loading, profile management, caching
├── presentation/         # CLI output formatting
├── analysis/             # Batch simulation runner + configuration-driven analysis
├── web/
│   ├── backend/          # FastAPI REST API + SQLite persistence
│   └── frontend/         # Vue 3 + Chart.js SPA
├── tests/
│   ├── test_simulation.py   # 85 tests
│   └── test_monte_carlo.py  # 23 tests
└── data/
    └── profiles/         # Per-user scenario data and cached results
```

**Key principle:** Domain layer has zero I/O and zero external deps. Everything above it depends downward only.

---

## Features

### Probabilistic Events

Model outcomes with uncertain probabilities:

```python
from domain.models import ProbabilisticEvent, EventOutcome, Scenario
from domain.simulation import simulate_branches

scenario = Scenario(
    name="IPO Scenario",
    monthly_income=IncomeBreakdown({"salary": 50_000}),
    monthly_expenses=ExpenseBreakdown({"expenses": 25_000}),
    initial_portfolio=1_000_000,
    age=40,
    probabilistic_events=[
        ProbabilisticEvent(
            name="IPO Exit",
            outcomes=[
                EventOutcome(year=3, probability=0.70, portfolio_injection=2_000_000, description="Success"),
                EventOutcome(year=3, probability=0.30, portfolio_injection=0.0, description="No event"),
            ]
        )
    ]
)

branches = simulate_branches(scenario, years=30)
for label, prob, result in branches:
    print(f"{label} ({prob:.0%}): retire year {result.retirement_year}")
```

Multi-event cross-product: two events × 2 outcomes each → 4 branches. Monte Carlo trials sample one outcome per event via weighted probability.

### Monte Carlo

```python
from domain.monte_carlo import run_monte_carlo
from domain.sensitivity import run_oat_sensitivity

result = run_monte_carlo(scenario, n_trials=500, years=40)
print(f"Retirement probability: {result.retirement_probability:.1%}")
print(f"p50 portfolio at year 20: ₪{result.percentile_p50[19]:,.0f}")

sensitivity = run_oat_sensitivity(scenario, n_trials=500, years=40)
for driver in sensitivity.drivers[:3]:
    print(f"{driver.name} {driver.direction}: {driver.delta:+.1%}")
```

### Historical Returns

```python
scenario = Scenario(
    ...,
    historical_start_year=1999,
    historical_index="nasdaq"   # "sp500" | "nasdaq" | "bonds" | "russell2000"
)
```

| Index | Coverage | Notes |
|-------|----------|-------|
| S&P 500 | 1928–2024 | Default |
| NASDAQ | 1972–2024 | Tech-heavy |
| Bonds (10Y Treasury) | 1928–2024 | Fixed income |
| Russell 2000 | 1979–2024 | Small-cap |

If simulation exceeds available data, years wrap from the index's start year.

### Pension Modeling

```json
"pension": {
  "initial_value": 2000000,
  "monthly_contribution": 9000,
  "annual_growth_rate": 0.06,
  "accessible_at_age": 67
}
```

**`liquid_only` (default):** Portfolio must sustain alone. Pension ignored for retirement validation.

**`pension_bridged`:** Phase 1 (retirement → age 67): portfolio alone. Phase 2 (67 → 100): portfolio + pension combined. Typically delays retirement 1–3 years but ensures lifetime security.

### Income & Expense Breakdowns

```json
"monthly_income": { "salary": 36000, "freelance": 5000, "rental": 4000 }
```

ScenarioNode deep-merge: child overrides only the components it specifies.

### Scenario Inheritance

```json
{ "name": "Higher Freelance", "parent": "Baseline", "monthly_income": { "freelance": 15000 } }
```

---

## Configuration Files

| File | Purpose |
|------|---------|
| `scenarios.json` | Flat scenario definitions (income, expenses, mortgage, events, pension) |
| `settings.json` | Simulation settings (years, return_rate, withdrawal_rate, output fields) |
| `scenario_analysis/scenario_nodes.json` | Scenario inheritance tree with deep-merge overrides |
| `scenario_analysis/analysis.json` | Analysis configurations (no Python needed to add analyses) |
| `data/profiles/{name}/` | Per-profile data directories |

---

## Web App

### Views
- **Dashboard** — Profile overview and navigation
- **Scenarios** — Browse and compare saved scenarios
- **Scenario Detail** — Year-by-year table, portfolio chart, exact definition values
- **What-If Explorer** — Real-time slider exploration with save-as-scenario
- **Monte Carlo** — Fan chart (p5/p50/p95), retirement probability, OAT sensitivity
- **Comparison** — Side-by-side scenario comparison
- **Scenario Generator** — Questionnaire-driven scenario creation

### API Endpoints

All endpoints except `/api/v1/auth/login` require `Bearer <JWT>`.

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

### Database Tables (SQLite)

| Table | Purpose |
|-------|---------|
| `users` | Authentication |
| `profiles` | User profiles |
| `simulation_runs` | Simulation run metadata |
| `scenario_results` | Per-scenario results |
| `year_data` | Year-by-year simulation output |
| `scenario_definitions` | What-If saved scenario state |
| `scenario_events` | One-time events linked to definitions |
| `scenario_mortgages` | Mortgage data linked to definitions |
| `scenario_pensions` | Pension data linked to definitions |
| `scenario_probabilistic_events` | Probabilistic event definitions |
| `scenario_event_outcomes` | Outcome branches per probabilistic event |

---

## Profiles

Each user has their own `data/profiles/{name}/` directory. Switch with `FINANCE_PROFILE=name`.

See [PROFILE_SETUP.md](PROFILE_SETUP.md) for creating new profiles from scratch.

---

## Troubleshooting

**ModuleNotFoundError:** Run from the project root: `cd /Users/alon/Documents/finance_planner && python main.py`

**Stale cache:**
```bash
FINANCE_PROFILE=alon rm data/profiles/alon/analyses/cache/simulation_cache.json
FINANCE_PROFILE=alon python analysis/run_simulations.py
```

**Database reset:**
```bash
rm data/finance_planner.db
python web/backend/seed.py
```

**Port in use:** `lsof -i :8000`

---

For working-with-this-codebase details, see [CLAUDE.md](CLAUDE.md).
