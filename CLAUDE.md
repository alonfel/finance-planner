# Claude Code Guidelines for Finance Planner

**Updated:** April 16, 2026 — **MAJOR: Probabilistic Events** — model uncertain outcomes (IPO, acquisition, bonus) with multiple weighted branches. simulate_branches() + Monte Carlo sampling + full UI. **FinancialStory domain model** — tree-structured narrative object with story_to_branches() + story_to_scenario(). 120 tests passing.

---

## Probabilistic Events (April 16, 2026)

Model uncertain outcomes — e.g., an IPO exit that may or may not happen, or a bonus with variable size.

**Access:** What-If Explorer → "Probabilistic Events" section (below One-Time Events)

**What it does:**
- Each event has N mutually exclusive outcomes; probabilities must sum to 100%
- Deterministic mode (`simulate_branches`): one simulation per outcome branch, returned as `[(label, probability, SimulationResult)]`
- Monte Carlo mode: each trial independently samples one outcome per event using probability weights, capturing the full distribution
- Chart overlays one colored line per branch; metrics show one card per branch with probability badge
- Save/load round-trips preserve events and outcomes exactly

**Python usage:**
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

**Multi-event cross-product:**
Two events with 2 outcomes each produce 4 branches (all probability combinations). Branch probabilities sum to 1.0.

**Validation:**
- `ProbabilisticEvent.__post_init__` raises `ValueError` if non-empty outcomes don't sum to 1.0 (±0.001 tolerance)
- UI blocks simulation and shows red badge until each event sums to 100%

**Files:**
- `domain/models.py` — `EventOutcome`, `ProbabilisticEvent` dataclasses; `Scenario.probabilistic_events` field
- `domain/simulation.py` — `simulate_branches()`, `_expand_branches()` (recursive cross-product)
- `domain/monte_carlo.py` — `_sample_probabilistic_events()` (per-trial outcome sampling)
- `web/backend/models.py` — `ScenarioProbabilisticEvent`, `ScenarioEventOutcome` ORM tables
- `web/backend/schemas.py` — `ProbabilisticEventSchema`, `EventOutcomeSchema`, `BranchResultSchema`
- `web/frontend/src/views/WhatIfView.vue` — Event Builder UI, `toApiRequest()`/`fromDefinition()` round-trip

**Tests:** `tests/test_simulation.py` — 19 tests across `TestProbabilisticEventModel`, `TestSimulateBranches`, `TestMonteCarloProbabilisticSampling`

---

## Quick Start

### Running the Simulation
```bash
python main.py
```

### Running Scenario Analysis (Configuration-Driven)
```bash
# Step 1: Simulate all scenarios (once)
python analysis/run_simulations.py

# Step 2: Run analysis (use cached results)
python analysis/run_analysis.py
```

### Switching Profiles
```bash
# Default profile (Daniel)
python analysis/run_simulations.py

# Alon's profile (2 core scenarios: Baseline + IPO Exit)
FINANCE_PROFILE=alon python analysis/run_simulations.py
FINANCE_PROFILE=alon python analysis/run_analysis.py
```

Each profile has its own `data/profiles/{name}/` directory.

**Note on Alon profile:** Simplified to 2 core scenarios (Baseline, IPO Year 2). Pension scenarios can be restored from git: `git checkout data/profiles/alon/scenario_nodes.json`.

### Running Tests
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

All **120 tests** should pass (97 simulation + 23 Monte Carlo).

### Running the Web Server

**Backend (FastAPI):**
```bash
cd web/backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server: `http://localhost:8000` — API docs: `http://localhost:8000/docs`

**Frontend (Vue 3):**
```bash
cd web/frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

See [web/FEATURES.md](web/FEATURES.md) for the complete user guide.

---

## Architecture Overview

**4-Layer Responsibility-Based Structure:**

```
finance_planner/
├── domain/              # Pure business logic
├── infrastructure/      # Config loading & caching
├── presentation/        # Output formatting
├── analysis/            # Scenario analysis subsystem
├── web/                 # FastAPI backend + Vue 3 frontend
└── tests/               # 108 unit tests (all passing)
```

**Key principle:** Each layer depends only on layers below. No circular dependencies.

---

## Component Documentation

| Layer | Purpose | Documentation |
|-------|---------|---|
| **domain/** | Financial models, simulation engine, insights | [domain/DOMAIN.md](domain/DOMAIN.md) |
| **infrastructure/** | Configuration loading, parsing, caching | [infrastructure/CONFIG.md](infrastructure/CONFIG.md) |
| **presentation/** | Output formatting, currency display | [presentation/PRESENTATION.md](presentation/PRESENTATION.md) |
| **analysis/** | Decoupled analysis system, scenario comparisons | [analysis/ANALYSIS.md](analysis/ANALYSIS.md) |
| **web/backend/** | FastAPI REST API, authentication, data persistence | [web/backend/README.md](web/backend/README.md), [API.md](web/backend/API.md), [ARCHITECTURE.md](web/backend/ARCHITECTURE.md) |
| **web/** | User-facing feature guides and workflows | [web/FEATURES.md](web/FEATURES.md) |

---

## File Structure

### Core Modules
- **domain/breakdown.py** — IncomeBreakdown, ExpenseBreakdown (named components with .total property)
- **domain/models.py** — Event, ProbabilisticEvent, Mortgage, Pension, Scenario, ScenarioNode dataclasses
- **domain/simulation.py** — Core simulate() + simulate_branches() engines, YearData, SimulationResult
- **domain/monte_carlo.py** — Monte Carlo engine (`run_monte_carlo`, `MonteCarloResult`)
- **domain/sensitivity.py** — OAT sensitivity analysis (`run_oat_sensitivity`, `SensitivityResult`)
- **domain/historical_returns.py** — Annual return data for S&P 500, NASDAQ, Bonds, Russell 2000 (1928–2024)
- **domain/insights.py** — Comparison logic + structured insight objects
- **infrastructure/parsers.py** — Consolidated dict→model parsing
- **infrastructure/loaders.py** — load_scenarios, load_settings, load_scenario_nodes (supports FINANCE_PROFILE env var)
- **infrastructure/data_layer.py** — Profile management + environment variable support
- **infrastructure/cache.py** — Serialization/deserialization for decoupled analysis
- **presentation/constants.py** — Currency symbols, formatting helpers
- **presentation/formatters.py** — print_scenario_header, print_year_summary
- **analysis/run_simulations.py** — Batch simulation runner (profile-aware)
- **analysis/run_analysis.py** — Configuration-driven analysis dispatcher (profile-aware)
- **main.py** — Entry point orchestrator

### Configuration Files
- **scenarios.json** — Scenario data (supports flat numbers and breakdown objects for income/expenses)
- **settings.json** — Simulation settings + output display options
- **scenario_analysis/scenario_nodes.json** — Scenario inheritance tree (deep-merge overrides)
- **scenario_analysis/analysis.json** — Analysis configurations

### Tests
- **tests/test_simulation.py** — 85 unit tests (simulation, historical returns, probabilistic events, insights)
- **tests/test_monte_carlo.py** — 23 unit tests (Monte Carlo engine, sensitivity analysis)

### Web Backend
- **web/backend/main.py** — FastAPI app initialization, router registration
- **web/backend/database.py** — SQLAlchemy ORM setup, session management
- **web/backend/auth.py** — JWT authentication, login endpoint
- **web/backend/models.py** — SQLAlchemy ORM models (Profile, SimulationRun, ScenarioResult, YearData, ScenarioDefinition, ProbabilisticEvent, EventOutcome)
- **web/backend/schemas.py** — Pydantic schemas; `WhatIfScenarioSchema` is the canonical source of truth for scenario state
- **web/backend/routers/auth.py** — Authentication endpoints
- **web/backend/routers/profiles.py** — Profile CRUD endpoints
- **web/backend/routers/scenarios.py** — Scenario retrieval; `_build_definition()` loads exact definition from DB
- **web/backend/routers/simulate.py** — What-If simulation; returns `branches[]` when probabilistic events present
- **web/backend/routers/whatif_saves.py** — Save What-If scenarios to SQLite with full event/outcome persistence
- **web/backend/routers/monte_carlo.py** — `POST /api/v1/monte-carlo`
- **web/backend/routers/generator.py** — Guided scenario generator questionnaire API (`POST /api/questionnaire/*`, `POST /api/generate-scenario`)
- **web/backend/services/scenario_generator.py** — Config-driven questionnaire → Scenario conversion service

### Web Frontend
- **web/frontend/src/views/WhatIfView.vue** — What-If Explorer (sliders, events, save modal); `toApiRequest()` + `fromDefinition()` are the canonical frontend mappers
- **web/frontend/src/views/MonteCarloView.vue** — Monte Carlo UI
- **web/frontend/src/views/ScenarioDetailView.vue** — Scenario detail with exact definition values
- **web/frontend/src/components/FanChart.vue** — p5/p50/p95 fan chart component

### Report Generation
- **reports/** — All generated reports
- **analysis/generate_report.py** — Report generator utility

---

## Features

### Probabilistic Events (April 16, 2026)

Extends the simulation engine to handle events with uncertain outcomes.

**Domain model:**
```python
@dataclass
class ProbabilisticEvent:
    name: str
    outcomes: list[EventOutcome]  # Each has: label, probability, amount, year, recurring

simulate_branches(scenario)  # Returns one SimulationResult per outcome branch (cross-product for multiple events)
```

**Monte Carlo integration:** Each trial draws one outcome per probabilistic event via weighted sampling, so the fan chart reflects the full probability-weighted return distribution.

**API:** `/simulate` returns `branches[]` when probabilistic events are present (empty list otherwise — fully backward compatible).

**Persistence:** `scenario_probabilistic_events` + `scenario_event_outcomes` tables; saved/restored via `whatif_saves.py` and `scenarios.py`.

---

### Monte Carlo Simulation (April 15, 2026)

Probabilistic financial planning via 500-trial lognormal return sampling.

**Access:** Dashboard → Profile → Monte Carlo

**What it does:**
- Generates N independent return sequences from a lognormal distribution (σ=15% default)
- Simulates each trial independently, aggregates to p5/p50/p95 percentile bands
- Reports retirement probability (% trials that retire within timeline) and survival probability (% trials portfolio > 0 at end)
- Runs OAT sensitivity analysis: varies return rate ±2pp, income ±20%, horizon ±5yr to rank which inputs matter most

**Python usage:**
```python
from domain.monte_carlo import run_monte_carlo
from domain.sensitivity import run_oat_sensitivity

result = run_monte_carlo(scenario, n_trials=500, years=40)
print(f"Retirement probability: {result.retirement_probability:.1%}")
print(f"Median portfolio year 20: ₪{result.percentile_p50[19]:,.0f}")

sensitivity = run_oat_sensitivity(scenario, n_trials=500, years=40)
for driver in sensitivity.drivers[:3]:
    print(f"{driver.name} {driver.direction}: {driver.delta:+.1%}")
```

---

### Multi-Index Historical Returns (April 14, 2026)

Simulate portfolio growth using actual annual returns from 4 major indices (1928–2024).

**Indices:**
- **S&P 500** (1928–2024) — `"sp500"` — default
- **NASDAQ Composite** (1972–2024) — `"nasdaq"`
- **US 10-Year Treasury Bonds** (1928–2024) — `"bonds"`
- **Russell 2000** (1979–2024) — `"russell2000"`

**JSON config:**
```json
{
  "historical_start_year": 1999,
  "historical_index": "nasdaq"
}
```

**Web UI:** 5-pill segmented control (Fixed % | S&P 500 | NASDAQ | Bonds | Russell 2000) with dynamic year slider min per index.

**Wrap-around:** If simulation exceeds available data, years wrap from the index's start year.

**Backward compatibility:** `historical_index=None` defaults to `"sp500"`; `historical_start_year=None` uses fixed `return_rate`.

---

### What-If Explorer

Real-time scenario exploration with sliders. Key architecture:

- **`WhatIfScenarioSchema`** — Canonical source of truth for scenario state (backend)
- **`toApiRequest()`** — All saves/simulates send this format (frontend)
- **`fromDefinition(def)`** — All loads restore exact values (frontend)

Adding a new field: add to schema + update two mappers.

**Save as Scenario:** Persists to SQLite with full fidelity (events, mortgage, pension, probabilistic events, return mode).

---

### Guided Scenario Generator

Questionnaire-based scenario creation. **Endpoints:**
- `POST /api/questionnaire/config` — Get questionnaire configuration
- `POST /api/questionnaire/completeness` — Calculate data completeness score
- `POST /api/generate-scenario` — Generate scenario from answers

Config-driven: all rules and question templates in JSON, no hardcoding.

---

## Pension Modeling

Pension accumulates separately from the liquid portfolio and enables two retirement modes.

### Pension Fields
```json
"pension": {
  "initial_value": 2000000,
  "monthly_contribution": 9000,
  "annual_growth_rate": 0.06,
  "accessible_at_age": 67
}
```

### Retirement Modes

**`liquid_only` (default):** Portfolio must sustain from retirement age until age 100. Pension ignored for retirement validation.

**`pension_bridged`:** Two-phase check:
1. Phase 1 (retirement → pension access age): Portfolio must sustain alone
2. Phase 2 (pension access age → 100): Portfolio + Pension combined must sustain

Typically delays retirement by 1-3 years vs liquid-only, but provides lifetime security confidence.

### YearData Fields
- `pension_value: float` — Accumulated pension at year-end
- `pension_accessible: bool` — Whether pension unlocked

---

## Income & Expense Breakdowns

### Flat numbers (backward compatible)
```json
"monthly_income": 45000,
"monthly_expenses": 22000
```

### Named components
```json
"monthly_income": { "salary": 36000, "freelance": 5000, "rental": 4000 },
"monthly_expenses": { "rent": 8000, "food": 3500, "other": 5000 }
```

### ScenarioNode deep-merge overrides
Child nodes can override individual components without redefining the full breakdown:
```json
{ "name": "Higher Freelance", "parent": "Baseline", "monthly_income": { "freelance": 15000 } }
```

---

## Common Tasks

### Simulate a Scenario
```python
from domain.models import Scenario
from domain.breakdown import IncomeBreakdown, ExpenseBreakdown
from domain.simulation import simulate

scenario = Scenario(
    name="Test",
    monthly_income=IncomeBreakdown({"salary": 35000, "bonus": 15000}),
    monthly_expenses=ExpenseBreakdown({"housing": 10000, "living": 10000, "other": 10000})
)
result = simulate(scenario, years=20)
print(f"Retires at year {result.retirement_year}")
```

### Simulate with Pension
```python
from domain.models import Scenario, Pension
from domain.simulation import simulate

pension = Pension(initial_value=2_000_000, monthly_contribution=9_000,
                  annual_growth_rate=0.06, accessible_at_age=67)
scenario = Scenario(name="With Pension", monthly_income=50_000,
                    monthly_expenses=30_000, pension=pension, age=41)
result = simulate(scenario, years=30)
```

### Run Monte Carlo
```python
from domain.monte_carlo import run_monte_carlo
result = run_monte_carlo(scenario, n_trials=500, years=40)
print(f"Retirement probability: {result.retirement_probability:.1%}")
```

### Simulate Branches (Probabilistic Events)
```python
from domain.simulation import simulate_branches
branches = simulate_branches(scenario)  # One SimulationResult per outcome cross-product
```

### Compare Two Scenarios
```python
from domain.insights import build_insights, format_insights
insights = build_insights(result_a, result_b)
print(format_insights(insights))
```

### Load Scenarios
```python
from infrastructure.loaders import load_scenarios, load_scenario_nodes

scenarios = load_scenarios()
nodes = load_scenario_nodes()
resolved = nodes["Alon - Buy Apartment + Exit"].resolve(nodes)
```

### Add a New Scenario
1. Edit **scenarios.json** — Add scenario block
2. Run `python main.py` — Auto-loads

### Add a New Analysis
1. Edit **scenario_analysis/analysis.json** — Add analysis block
2. Run `python analysis/run_analysis.py` — No code changes

---

## Creating a New Profile

See [PROFILE_SETUP.md](PROFILE_SETUP.md) for the complete guide.

Quick reference:
1. Create `data/profiles/{name}/`
2. Add `settings.json`, `scenarios.json`, `scenario_nodes.json`, `analyses/config.json`
3. Run simulations + analysis

---

## Configuration-Driven Design

**Philosophy:** Data/config in JSON. Logic immutable. Users don't edit Python.

- ✅ Edit: `scenarios.json`, `scenario_nodes.json`, `analysis.json`, `settings.json`
- ❌ Don't edit (unless extending): `models.py`, `simulation.py`, `main.py`

---

## Key Design Principles

1. **Pure functions** — No side effects, idempotent
2. **Immutable models** — Dataclasses, no mutations
3. **No external deps** — Only Python stdlib (domain layer)
4. **Decoupled** — Simulate once, analyze many times
5. **Configuration-driven** — JSON controls behavior
6. **Type-safe** — All models typed
7. **Well-tested** — 108 unit tests, all passing

---

## Troubleshooting

### ModuleNotFoundError
```bash
cd /Users/alon/Documents/finance_planner
python main.py
```

### Tests fail
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### Stale cache
```bash
FINANCE_PROFILE=alon rm data/profiles/alon/analyses/cache/simulation_cache.json
FINANCE_PROFILE=alon python analysis/run_simulations.py
FINANCE_PROFILE=alon python analysis/run_analysis.py
```

---

## Summary

✅ Modular (4 layers)  
✅ 120 tests, all passing  
✅ Extensible (JSON-driven)  
✅ Documented (component guides)  
✅ Fast (decoupled simulation/analysis)  
✅ Monte Carlo + OAT sensitivity  
✅ Multi-index historical returns (S&P 500, NASDAQ, Bonds, Russell 2000)  
✅ Probabilistic events (simulate_branches + Monte Carlo sampling)  
✅ Income/Expense breakdowns with named components and deep-merge overrides  
✅ Backward compatible  

For detailed info, see component guides linked above.
