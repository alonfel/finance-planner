# Claude Code Guidelines for Finance Planner

**Updated:** April 14, 2026 — **MAJOR: Model-centric architecture refactoring** completed for What-If Explorer. 7 data integrity bugs fixed (NULL scenario_id, hardcoded values, missing fields). Auto-generated scenario names added. Backend and frontend fully synchronized. All 17 backend tests passing. See recent updates section below.

---

## Recent Updates (April 14, 2026)

### Model-Centric Architecture Refactoring (COMPLETED)

**Problem Solved:**
When saving and reloading What-If scenarios, critical data was missing or incorrect:
- Events and mortgages silently absent for seeded scenarios (scenario_id was NULL)
- Growth rate hardcoded to 7% on reload instead of reading saved value
- Initial portfolio back-calculated from year_data, losing precision
- Disabled events were saved anyway (inconsistent behavior)
- Pension fields completely absent from What-If flow
- withdrawal_rate, retirement_mode, currency hardcoded instead of persisted

**Architecture Fix:**
Introduced `WhatIfScenarioSchema` as canonical source of truth for scenario state. Backend returns this exact schema when loading saved scenarios. Frontend has two pure mapping functions:
- `toApiRequest()` — All saves/simulates send this format
- `fromDefinition(def)` — All loads restore exact values

Adding a new field now requires: add to schema + update two mappers (automatic for UI/API roundtrip).

**Files Modified:**

| File | Changes |
|------|---------|
| `web/backend/schemas.py` | Created `WhatIfScenarioSchema`; updated `SimulateRequest`, `SaveScenarioRequest`, `ScenarioResultSchema` |
| `web/backend/routers/simulate.py` | Pass pension, withdrawal_rate, retirement_mode, currency to Scenario constructor |
| `web/backend/routers/whatif_saves.py` | Save pension to scenario_pensions table; use body fields instead of hardcoded defaults |
| `web/backend/routers/scenarios.py` | New `_build_definition()` function loads exact definition from DB; endpoint returns `definition` field |
| `web/backend/seed.py` | Call `link_scenario_results(db)` to backfill NULL scenario_id on seeded rows |
| `web/frontend/src/views/WhatIfView.vue` | Added `toApiRequest()` + `fromDefinition()` pure functions; mortgage now collapsible; events always visible |
| `web/frontend/src/views/ScenarioDetailView.vue` | Display exact definition values (returnRate, withdrawalRate) instead of approximations; fixed goToWhatIf navigation |

**Bugs Fixed:**
1. ✅ Seeded scenario events/mortgage NULL — backfilled via link_scenario_results()
2. ✅ Growth rate hardcoded to 7% — now reads from definition.return_rate
3. ✅ Initial portfolio approximated — now stored and returned exactly
4. ✅ Disabled events saved anyway — filter in toApiRequest()
5. ✅ Mortgage not restored on query-param path — fromDefinition() now handles all fields
6. ✅ Pension absent end-to-end — added to all layers (model → schema → UI)
7. ✅ withdrawal_rate/retirement_mode/currency hardcoded — now persisted in all scenarios

**Verification:**
- `SELECT count(*) FROM scenario_results WHERE scenario_id IS NULL` → 0 (all seeded scenarios linked)
- Save scenario with 6% growth → reload → Growth Rate shows 6% (not hardcoded 7%)
- Save scenario with pension → reload → pension fields populated
- Disabled events excluded from saves (consistent with simulate behavior)
- All 17 backend tests passing
- ScenarioDetailView shows exact growth rate and withdrawal rate

---

### Auto-Generated Scenario Names (COMPLETED)

**Feature:** Save dialog now pre-fills name with intelligent default.

**Format:** `{BaseScenarioName} - Modified {HH:MM AM/PM}`

**Examples:**
- "Baseline - Modified 04:32 PM"
- "IPO Year 2 - Modified 02:15 AM"

**How It Works:**
1. User clicks "💾 Save as Scenario" button
2. Dialog opens with pre-generated name (based on origin scenario + current time)
3. User can edit the name or accept the default
4. Time-based identifier makes multiple same-day saves distinguishable

**Files Modified:**
- `web/frontend/src/views/WhatIfView.vue` — Added `generateDefaultScenarioName()` and `openSaveModal()` functions

**Benefits:**
✅ Identifies origin scenario  
✅ Timestamp distinguishes multiple saves on same day  
✅ User-editable (default is suggestion, not forced)  
✅ No manual typing required (better UX)  
✅ Clear, concise naming convention  

---

### UI Improvements

**Events Visibility:**
- Mortgage section now colapsible (hidden by default)
- Events list remains visible without scrolling
- Increased sliders-section height from 45vh to 55vh
- Parameter controls more accessible

**Definition Display (ScenarioDetailView):**
- Now shows Growth Rate and Withdrawal Rate (previously missing)
- Uses exact values from definition when available
- Falls back to year_data approximation for legacy scenarios
- Retirement mode and currency now available for display

---

### Historical S&P 500 Return Rate Simulation (NEW)

**Feature:** Simulate portfolio growth using actual S&P 500 annual returns from any calendar year (1928–2024), enabling backtesting and stress-testing scenarios.

**Use Case:** "What if I had started investing in 2000?" — See portfolio behavior through the dot-com crash (-9.1%, -11.9%, -22.1%) or "What if I started in 1990?" — Experience the strong 90s bull market (+30.58%, +7.44%, etc.).

**How to Use:**

**Method 1: From scenarios.json or scenario_nodes.json**
```json
{
  "name": "Backtesting: Dot-Com Crash",
  "monthly_income": 45000,
  "monthly_expenses": 25000,
  "historical_start_year": 2000
}
```

**Method 2: From Python**
```python
from domain.models import Scenario
from domain.breakdown import IncomeBreakdown, ExpenseBreakdown
from domain.simulation import simulate

scenario = Scenario(
    name="1990s Bull Market",
    monthly_income=IncomeBreakdown({"income": 45000}),
    monthly_expenses=ExpenseBreakdown({"expenses": 25000}),
    historical_start_year=1990  # Use S&P 500 returns from 1990 onward
)
result = simulate(scenario, years=30)
print(f"Retirement year: {result.retirement_year}")
```

**Method 3: Web UI (WhatIf Explorer)**
- Toggle: "Growth Rate (Fixed)" ↔ "Historical S&P 500"
- Slider: Pick start year (1928–2024)
- Chart shows portfolio impact of actual historical returns

**Behavior:**

| Scenario | Retirement Year | Final Portfolio | Why |
|----------|---|---|---|
| Fixed 7% | Year 11 | ₪8.2M | Constant steady growth |
| Start 1990 | Year 10 | ₪9.1M | Strong 90s bull market |
| Start 2000 | Year 13 | ₪6.4M | Dot-com crash delayed retirement |

**Data Coverage:** S&P 500 annual total returns (including dividends) from 1928–2024 (97 years).

**Overflow Behavior:** If simulation exceeds available data (e.g., 30-year simulation starting in 2010), years wrap around deterministically from 1928 (e.g., 2025 → 1928, 2026 → 1929, etc.). This is useful for stress-testing longer periods.

**Backward Compatibility:**
- `historical_start_year=None` (default) → uses fixed `return_rate` (7% default)
- Existing scenarios without this field are unaffected
- Can freely mix historical and fixed-rate scenarios

**Files Modified:**
- `domain/historical_returns.py` — S&P 500 data (1928–2024) + helper function
- `domain/models.py` — Added `historical_start_year` field to `Scenario` and `ScenarioNode`
- `domain/simulation.py` — Uses historical rates in year loop when field is set
- `infrastructure/parsers.py` — Parses `historical_start_year` from JSON
- `tests/test_simulation.py` — 12 new tests (happy path, edge cases, ScenarioNode inheritance)

**TODO (Web Layer):**
- ❌ Add `historical_start_year` to API schema (`web/backend/schemas.py`)
- ❌ Persist to database (`web/backend/models.py` + migration)
- ❌ API error handling: invalid start year → HTTP 422
- ❌ UI toggle in WhatIf Explorer (`web/frontend/src/views/WhatIfView.vue`)

---

## Quick Start

### Running the Simulation
```bash
python main.py
```

Outputs:
- Year-by-year tables for both scenarios
- Validation checks
- Scenario comparisons and insights

### Running Scenario Analysis (Configuration-Driven)
```bash
# Step 1: Simulate all scenarios (once)
python analysis/run_simulations.py

# Step 2: Run analysis (use cached results)
python analysis/run_analysis.py

# Edit scenario_analysis/analysis.json to add/modify analyses
# Step 3: Re-run Step 2 (no re-simulation!)
python analysis/run_analysis.py
```

### Switching Profiles
```bash
# Run default profile (Daniel)
python analysis/run_simulations.py

# Run Alon's profile (2 core scenarios: Baseline + IPO Exit)
FINANCE_PROFILE=alon python analysis/run_simulations.py
FINANCE_PROFILE=alon python analysis/run_analysis.py
```

Each profile has its own `data/profiles/{name}/` directory with separate simulations and results.

**Note on Alon profile:** Previously had 7 scenarios including pension variations. Simplified to 2 core scenarios (Baseline, IPO Year 2) to streamline analysis. Pension scenarios can be restored from git: `git checkout data/profiles/alon/scenario_nodes.json`.

### Running Tests
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

All 42 tests should pass.

### Running the Web Server

The web application consists of a FastAPI backend and Vue 3 frontend.

**Backend (FastAPI):**
```bash
cd web/backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server runs at `http://localhost:8000`
API docs (Swagger UI): `http://localhost:8000/docs`

**Frontend (Vue 3):**
```bash
cd web/frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

Access the app at: `http://localhost:5173`

**Features:**
- What-If Explorer: Real-time scenario exploration with sliders
- Save as Scenario: Persist What-If configurations as named scenarios
- Scenarios View: Browse and compare saved scenarios
- Authentication: Login-required access to profiles

See [web/FEATURES.md](web/FEATURES.md) for complete user guide.

---

## Recent Updates (April 13, 2026)

### What-If Explorer UI Restructuring

**Changes:**
1. **Sidebar Layout** — Left sidebar (280px fixed) contains:
   - Simulation Run selector
   - Base Scenario selector
   - "Save as Scenario" button
   
2. **Parameter Controls** — Main content split into:
   - Parameters section (top, scrollable):
     - 2-column grid of sliders: Monthly Income, Monthly Expenses, Growth Rate, Starting Age, Initial Portfolio
     - One-Time Events subsection coupled with parameters
     - Add/Remove event buttons integrated
   - Chart section (fixed 350px height):
     - Portfolio growth comparison chart
     - Log scale toggle (enabled by default with 0 showing on Y-axis)
   - Metrics section (scrollable):
     - Retirement year and final portfolio comparisons
     - Original vs What-If scenario metrics

3. **Events Feature** — Now coupled with scenario parameters:
   - Events display in-line with sliders
   - Can add/remove/toggle events without leaving parameters section
   - Events saved together with scenario when using "Save as Scenario"

**Files Modified:**
- `web/frontend/src/views/WhatIfView.vue` — Complete layout restructuring with sidebar and consolidated sections
- `web/frontend/src/components/ComparisonChart.vue` — Reduced chart height to 280px for proper overflow handling

### Save As Scenario Feature (Fully Implemented)

**Workflow:**
1. User adjusts sliders and events in What-If Explorer
2. Clicks "Save as Scenario" button
3. Modal prompts for scenario name
4. Backend validates uniqueness, runs simulation in-process
5. Scenario persisted to SQLite database:
   - `scenario_definitions` table (with `saved_from='whatif'` marker and timestamp)
   - `scenario_events` table (linked via `scenario_id` FK)
   - `scenario_mortgages` table (if mortgage present)
   - "What-If Saves" `SimulationRun` for grouping
   - `ScenarioResult` and `YearData` tables
6. Scenario immediately available in Scenarios view

**Files Implemented:**
- `web/backend/routers/whatif_saves.py` — Save endpoint with database persistence
- `web/backend/schemas.py` — SaveScenarioRequest/Response models
- `web/frontend/src/views/WhatIfView.vue` — Save button and modal UI
- `web/backend/requirements.txt` — Removed `filelock` dependency (database replaces file locking)

**Architecture:**
- Database-first persistence in SQLite (scenario_definitions table)
- Transactional integrity (ACID guarantees, automatic rollback on error)
- Foreign key relationships (scenario_id links definitions to results)
- 201 Created status on success, 409 Conflict if name exists
- Scenario simulation runs on backend (ensures consistency)
- JSON files kept as read-only backups for portability

---

## Recent Bug Fixes (April 13, 2026)

### Mortgage Rate Conversion Bug Fixed (CRITICAL)

**Problem:** Graph displayed mathematically nonsensical values when mortgage scenarios were loaded. The issue was a 100x mismatch in mortgage rate calculations.

**Root cause:** Frontend was sending mortgage `annual_rate` as a percentage (e.g., 4.5 for 4.5%) but the backend expected a decimal (e.g., 0.045). This caused the backend to calculate mortgage payments at 100x the correct rate.

**Example impact:**
- User sets mortgage rate slider to 4.5%
- Frontend displays ₪8,000-10,000/month (correct in UI)
- Backend receives: `annual_rate: 4.5` (percentage instead of decimal)
- Backend calculates: `r = 4.5 / 12 = 0.375` (37.5% per month!)
- Monthly payment: ₪4,500,000+ (100x too large)
- Result: Expenses crash portfolio to zero immediately

**Solution implemented:** Convert mortgage `annual_rate` to decimal before sending to backend, matching how `return_rate` is already handled.

**Files modified:**
- `web/frontend/src/views/WhatIfView.vue` — Added `/100` conversion in three places:
  - Line 507: `refreshOriginalScenario()` 
  - Line 541: `runSimulation()`
  - Line 639: `saveScenario()`

**Verification:** Monthly payment for ₪1.5M mortgage at 4.5% over 20 years now correctly calculates to ₪9,490/month instead of ₪4.5M/month.

---

### Pension Bridge Implementation Fixed

**Problem:** ScenarioNode inheritance tree was not properly transferring `pension` and `retirement_mode` fields to resolved Scenario objects. This caused:
1. Pension scenarios to show `pension_value: 0.0` (pension not accumulating)
2. Pension-bridged retirement mode not being applied (all scenarios defaulting to "liquid_only")
3. Pension bridge retirement years identical to non-bridged versions

**Root cause:** Two missing components:
- `ScenarioNode` class lacked `pension` and `retirement_mode` fields
- `parse_scenario_node()` parser was not reading these fields from JSON
- `ScenarioNode.resolve()` was not transferring these fields during inheritance chain resolution

**Solution implemented:**
1. Added `pension: Optional[Pension]` and `retirement_mode: Optional[str]` fields to ScenarioNode dataclass
2. Updated `parse_scenario_node()` to parse and pass these fields from JSON
3. Updated `ScenarioNode.resolve()` to transfer both fields during override application
4. Re-ran all simulations; pension-bridged scenarios now show correct retirement years

**Files modified:**
- `domain/models.py` — Added fields to ScenarioNode, updated resolve() logic
- `infrastructure/parsers.py` — Added pension/retirement_mode parsing in parse_scenario_node()

**Verification:** Pension bridge scenarios now correctly delay retirement by 1-3 years vs liquid-only, reflecting stricter two-phase lifetime sustainability validation.

---

## Architecture Overview

**4-Layer Responsibility-Based Structure:**

```
finance_planner/
├── domain/              # Pure business logic
├── infrastructure/      # Config loading & caching
├── presentation/        # Output formatting
├── analysis/            # Scenario analysis subsystem
└── tests/              # 42 unit tests (all passing)
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
| **web/features/** | User-facing feature guides and workflows | [web/FEATURES.md](web/FEATURES.md) |

---

## File Structure

### Core Modules
- **domain/breakdown.py** — IncomeBreakdown, ExpenseBreakdown (named components with .total property)
- **domain/models.py** — Event, Mortgage, Pension, Scenario, ScenarioNode dataclasses
- **domain/simulation.py** — Core simulate() engine + YearData (with pension tracking), SimulationResult
- **domain/insights.py** — Comparison logic + structured insight objects
- **infrastructure/parsers.py** — Consolidated dict→model parsing (includes parse_income/expense_breakdown, parse_pension)
- **infrastructure/loaders.py** — load_scenarios, load_settings, load_scenario_nodes (supports FINANCE_PROFILE env var)
- **infrastructure/data_layer.py** — Profile management + environment variable support
- **infrastructure/cache.py** — Serialization/deserialization for decoupled analysis
- **presentation/constants.py** — Currency symbols, formatting helpers
- **presentation/formatters.py** — print_scenario_header (with component display), print_year_summary
- **analysis/run_simulations.py** — Batch simulation runner (profile-aware)
- **analysis/run_analysis.py** — Configuration-driven analysis dispatcher (profile-aware)
- **main.py** — Entry point orchestrator

### Configuration Files
- **scenarios.json** — Scenario data (supports both flat numbers and breakdown objects for income/expenses)
- **settings.json** — Simulation settings + output display options
- **scenario_analysis/scenario_nodes.json** — Scenario inheritance tree (income/expenses can be overridden with deep merge)
- **scenario_analysis/analysis.json** — Analysis configurations
- **scenario_analysis/simulation_cache.json** — Generated by run_simulations.py

### Tests
- **tests/test_simulation.py** — 42 unit tests (all pure, no mocks)

### Web Backend
- **web/backend/main.py** — FastAPI app initialization, router registration
- **web/backend/database.py** — SQLAlchemy ORM setup, session management
- **web/backend/auth.py** — JWT authentication, login endpoint
- **web/backend/models.py** — SQLAlchemy ORM models (Profile, SimulationRun, ScenarioResult, YearData)
- **web/backend/schemas.py** — Pydantic request/response validation models
- **web/backend/routers/auth.py** — Authentication endpoints
- **web/backend/routers/profiles.py** — Profile CRUD endpoints
- **web/backend/routers/scenarios.py** — Scenario retrieval endpoints
- **web/backend/routers/simulate.py** — One-off What-If simulation (stateless)
- **web/backend/routers/whatif_saves.py** — Save What-If scenarios to disk + SQLite
- **web/backend/requirements.txt** — Python dependencies (FastAPI, SQLAlchemy, filelock, etc.)

### Report Generation
- **reports/** — Organized folder for all generated reports
- **analysis/generate_report.py** — Utility for generating reports to reports/ folder
- Reports include: Portfolio growth analysis, financial summaries, scenario comparisons

---

## Reports & Analysis Output

All generated reports are organized in the **`reports/`** folder.

### Generating Reports

**Portfolio Growth & Acceleration Analysis:**
```bash
PYTHONPATH=/Users/alon/Documents/finance_planner python analysis/generate_report.py growth_analysis
```

Reports automatically save to: `/Users/alon/Documents/finance_planner/reports/`

### Available Reports

- **portfolio_growth_analysis.md** — Year-by-year portfolio growth, acceleration rates, milestone analysis
- **ALON_FINANCIAL_REPORT_2026_UPDATED.md** — Comprehensive Alon financial analysis (20+ pages)
- **RECENT_CHANGES_SUMMARY.md** — Quick reference for recent bug fixes and changes
- See `reports/README.md` for complete report inventory

### Report Contents

Each report includes:
- Scenario overview and parameters
- Year-by-year growth analysis
- Acceleration metrics and inflection points
- Cross-scenario comparisons
- Milestone analysis (reaching specific wealth targets)
- Strategic insights

---

## Creating a New Profile

**See [PROFILE_SETUP.md](PROFILE_SETUP.md) for complete guide to creating new profiles from scratch.**

Quick reference:
1. Create directory: `data/profiles/{name}/`
2. Add config files: `settings.json`, `scenarios.json`, `scenario_nodes.json`, `analyses/config.json`
3. Run: `python analysis/run_simulations.py` → `python analysis/run_analysis.py`

The guide includes:
- Complete file format reference with examples
- Step-by-step walkthrough for "John's Consulting Profile"
- Data requirements checklist
- Common patterns (mortgages, events, inheritance, **pension**)
- Troubleshooting

---

## Pension Modeling

Scenarios can include **optional pension wealth** that accumulates separately from the investment portfolio. Pension enables two retirement modes: `liquid_only` (standard) and `pension_bridged` (stricter validation).

### Pension Fields (in scenarios.json or scenario_nodes.json)
```json
"pension": {
  "initial_value": 2000000,           # Accumulated pension value today (₪)
  "monthly_contribution": 9000,       # Monthly addition to pension fund (₪)
  "annual_growth_rate": 0.06,         # Pension fund return rate (6% typical)
  "accessible_at_age": 67             # Age when pension unlocks (Israeli standard: 67)
}
```

### Retirement Modes

**Mode 1: `liquid_only` (default)**
- Retirement check: Portfolio must sustain from retirement age until age 100
- Pension exists but is ignored for retirement validation
- Typical use: When liquid portfolio is sufficient alone

**Mode 2: `pension_bridged`**
- Two-phase retirement check:
  1. **Phase 1** (retirement → pension_accessible_at_age): Portfolio must sustain alone
  2. **Phase 2** (pension_accessible_at_age → 100): Portfolio + Pension combined must sustain
- More conservative; ensures lifetime security even if portfolio underperforms
- Typical use: When wanting pension-backed safety net for age 67+ period

### Pension Behavior in Simulations

- **Accumulates independently** from liquid portfolio: each year grows by `(pension + contributions) * (1 + growth_rate)`
- **Locked until access age**: before `accessible_at_age`, pension does NOT count toward retirement (shown as `pension_accessible: false`)
- **Unlocks at access age**: from that year onward, pension counts toward retirement in bridged mode
- **Realistic modeling**: captures Israeli mandatory pension (Keren Pensia) that's illiquid until retirement age

### Example: Baseline Scenario

| Year | Age | Liquid Portfolio | Pension Value | Mode | Retire? |
|------|-----|------------------|----------------|------|---------|
| 1 | 42 | ₪1.7M | ₪2.1M | liquid_only | ❌ |
| 11 | 52 | ₪6.3M | ₪4.8M | liquid_only | ✅ Year 11 |
| 11 | 52 | ₪6.3M | ₪4.8M | pension_bridged | ❌ (stricter) |
| 12 | 53 | ₪6.9M | ₪4.9M | pension_bridged | ✅ Year 12 |
| 20 | 61 | ₪13.2M | ₪10.6M | both modes | ✅ |

**Key insight:** Pension-bridged mode delays retirement by 1-3 years vs liquid-only, but provides confidence that combined portfolio+pension sustains through age 100.

### YearData Includes
- `pension_value: float` — Accumulated pension at year-end
- `pension_accessible: bool` — Whether pension unlocked and counts toward retirement

---

## Income & Expense Breakdowns

Scenarios now support **named components** for income and expenses, enabling detailed breakdown analysis and flexible scenario variations.

### Breakdown Fields (in scenarios.json)

**Option 1: Simple flat numbers (backward compatible)**
```json
"monthly_income": 45000,
"monthly_expenses": 22000
```

**Option 2: Named components (new)**
```json
"monthly_income": {
  "salary": 36000,
  "freelance": 5000,
  "rental": 4000
},
"monthly_expenses": {
  "rent": 8000,
  "food": 3500,
  "utilities": 1500,
  "childcare": 4000,
  "other": 5000
}
```

### Breakdown Behavior in Simulations

- **Component names are arbitrary** — Use labels that match your financial reality ("salary", "gig", "dividend", etc.)
- **Totals calculated automatically** — `.total` property sums all components
- **Display includes breakdown** — When multiple components exist, scenario header shows each line item
- **Single-component renders like flat float** — Backward compatible output for plain numbers

### Scenario Output with Breakdown

```
  Income:   ₪     45,000/month
    salary                 ₪     36,000/month
    freelance              ₪      5,000/month
    rental                 ₪      4,000/month
  Expenses: ₪     22,000/month
    rent                   ₪      8,000/month
    food                   ₪      3,500/month
    utilities              ₪      1,500/month
    childcare              ₪      4,000/month
    other                  ₪      5,000/month
  Net:      ₪     23,000/month
```

### ScenarioNode Overrides with Deep Merge

Child nodes can override individual components without redefining the entire breakdown.

```json
{
  "name": "Higher Freelance Income",
  "parent": "Baseline",
  "monthly_income": {
    "freelance": 15000
  }
}
```

**Result:** Child inherits `salary` from parent, but `freelance` is overridden to 15000. Total income becomes salary + 15000.

### Example: Income Variation Analysis

```python
from domain.models import Scenario
from domain.breakdown import IncomeBreakdown, ExpenseBreakdown
from domain.simulation import simulate

# Base scenario with components
base = Scenario(
    name="Baseline",
    monthly_income=IncomeBreakdown({"salary": 30000, "freelance": 5000}),
    monthly_expenses=ExpenseBreakdown({"rent": 8000, "other": 3000}),
)

# Simulate at different freelance income levels
for freelance_amount in [3000, 5000, 10000, 15000]:
    scenario = Scenario(
        name=f"Freelance: ₪{freelance_amount:,}",
        monthly_income=IncomeBreakdown({"salary": 30000, "freelance": freelance_amount}),
        monthly_expenses=base.monthly_expenses,
    )
    result = simulate(scenario, years=30)
    print(f"{scenario.name}: Retire at year {result.retirement_year}")
```

### Backward Compatibility

- ✅ Old JSON with flat `"monthly_income": 45000` continues to work
- ✅ Plain floats are automatically wrapped as `{"income": 45000}` internally
- ✅ Simulation math unchanged — uses `.total` which sums components
- ✅ Tests cover both flat and breakdown formats

---

## Common Tasks

### Simulate a Scenario (with Breakdowns)
```python
from domain.models import Scenario
from domain.breakdown import IncomeBreakdown, ExpenseBreakdown
from domain.simulation import simulate

# Using component breakdowns
scenario = Scenario(
    name="Test",
    monthly_income=IncomeBreakdown({"salary": 35000, "bonus": 15000}),
    monthly_expenses=ExpenseBreakdown({"housing": 10000, "living": 10000, "other": 10000})
)
result = simulate(scenario, years=20)
print(f"Retires at year {result.retirement_year}")
print(f"Income components: {scenario.monthly_income.components}")
print(f"Total income: ₪{scenario.monthly_income.total:,}")
```

### Simulate a Scenario (Simple / Backward Compatible)
```python
from domain.models import Scenario
from domain.breakdown import IncomeBreakdown, ExpenseBreakdown
from domain.simulation import simulate

# Plain numbers (auto-wrapped internally)
scenario = Scenario(
    name="Simple",
    monthly_income=IncomeBreakdown({"income": 50000}),  # Or just use flat number
    monthly_expenses=ExpenseBreakdown({"expenses": 30000})
)
result = simulate(scenario, years=20)
```

### Simulate with Pension
```python
from domain.models import Scenario, Pension
from domain.simulation import simulate

pension = Pension(
    initial_value=2_000_000,
    monthly_contribution=9_000,
    annual_growth_rate=0.06,
    accessible_at_age=67
)

scenario = Scenario(
    name="With Pension",
    monthly_income=50_000,
    monthly_expenses=30_000,
    pension=pension,
    age=41
)

result = simulate(scenario, years=30)
for yd in result.year_data:
    if yd.year in [1, 20, 27]:  # Year 27 is age 67 (pension unlocks)
        print(f"Year {yd.year}: Portfolio={yd.portfolio:,.0f}, Pension={yd.pension_value:,.0f}, Accessible={yd.pension_accessible}")
```

### Compare Two Scenarios
```python
from domain.insights import build_insights, format_insights

insights = build_insights(result_a, result_b)
print(format_insights(insights))
```

### Load Scenarios
```python
from infrastructure.loaders import load_scenarios

scenarios = load_scenarios()
baseline = scenarios["Baseline"]
```

### Load Scenario Tree
```python
from infrastructure.loaders import load_scenario_nodes

nodes = load_scenario_nodes()
resolved = nodes["Alon - Buy Apartment + Exit"].resolve(nodes)
result = simulate(resolved, years=20)
```

### Add a New Scenario
1. Edit **scenarios.json** — Add new scenario block
2. Run `python main.py` — Auto-loads

### Add a New Analysis
1. Edit **scenario_analysis/analysis.json** — Add analysis block
2. Run `python analysis/run_analysis.py` — No code changes!

### Change Simulation Settings
1. Edit **settings.json**
2. Run `python analysis/run_simulations.py` — Re-simulate
3. Run `python analysis/run_analysis.py` — View results

---

## Configuration-Driven Design

**Philosophy:** Data/config in JSON. Logic immutable. Users don't edit Python.

### Edit These Files
- ✅ scenarios.json (income/expenses can be flat numbers OR component objects; optional pension field)
- ✅ scenario_nodes.json (income/expense overrides support deep merge of components)
- ✅ analysis.json
- ✅ settings.json

### Don't Edit (Unless Extending)
- ❌ models.py, simulation.py, main.py (unless adding features)

---

## Backward Compatibility

Old imports still work:
```python
# Old way (still works)
from models import Scenario
from simulation import simulate
from comparison import build_insights

# New way (recommended)
from domain.models import Scenario
from domain.simulation import simulate
from domain.insights import build_insights
```

---

## Key Design Principles

1. **Pure functions** — No side effects, idempotent
2. **Immutable models** — Dataclasses, no mutations
3. **No external deps** — Only Python stdlib
4. **Decoupled** — Simulate once, analyze many times (100x faster)
5. **Configuration-driven** — JSON controls behavior
6. **Type-safe** — All models typed
7. **Well-tested** — 42 unit tests, all passing

---

## Troubleshooting

### ModuleNotFoundError
```bash
cd /Users/alon/Documents/finance_planner
python main.py
```

### JSON syntax error
Check for trailing commas, missing quotes in JSON files.

### Tests fail
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### Stale cache
```bash
# Default profile
rm data/profiles/default/analyses/cache/simulation_cache.json

# Or any profile
FINANCE_PROFILE=alon rm data/profiles/alon/analyses/cache/simulation_cache.json

# Then re-simulate
FINANCE_PROFILE=alon python analysis/run_simulations.py
FINANCE_PROFILE=alon python analysis/run_analysis.py
```

---

## Summary

✅ Modular (4 layers)  
✅ Testable (42 tests, all passing)  
✅ Extensible (JSON-driven)  
✅ Documented (component guides)  
✅ Fast (decoupled simulation/analysis)  
✅ **New:** Income/Expense breakdowns with named components and deep-merge overrides  
✅ **Backward compatible:** Old flat-number JSON still works  

For detailed info, see component guides (links above).
