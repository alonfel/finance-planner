# Financial Simulation Engine

A minimal, clean financial simulation engine that models scenarios (like "buy apartment with mortgage") and compares outcomes over time.

**No external dependencies. Pure Python. Configuration-driven.**

> **Latest Update (April 13, 2026):** Fixed pension bridge implementation bug. All pension scenarios now correctly accumulate and apply retirement modes. See [CHANGELOG.md](CHANGELOG.md) for details.

---

## Overview

Simulate financial scenarios year-by-year and answer questions like:
- **When can I retire?** (when portfolio ≥ safe withdrawal threshold)
- **How does a mortgage delay retirement?**
- **What's the portfolio difference in 20 years?**

The engine:
- ✅ Simulates portfolio growth with annual investment returns
- ✅ Tracks income, expenses, and net savings each year
- ✅ Applies mortgage payments when active
- ✅ Models one-time financial events (stock offerings, inheritances, emergencies)
- ✅ **Accumulates locked pension funds** with independent growth rate
- ✅ **Two retirement modes:** liquid_only (standard) and pension_bridged (stricter lifetime validation)
- ✅ Detects retirement (first year portfolio meets retirement goal)
- ✅ Shows retirement year, calendar year, and retirement age
- ✅ Named income/expense components for detailed breakdown analysis
- ✅ Scenario inheritance tree with deep-merge overrides
- ✅ Compares multiple scenarios and generates structured insights
- ✅ Configurable scenario parameter display in output
- ✅ 100% configuration-driven (no code changes needed)
- ✅ Pure functions, fully testable (42 unit tests, all passing)

---

## Workflow at a Glance

```
Define Scenarios         Run Simulations           Analyze & Compare
       ↓                        ↓                          ↓
scenarios.json           python main.py            Year-by-year tables
    or         +   →          or         +   →     Retirement timing
scenario_nodes.json      scenario_analysis/       Portfolio comparisons
                         run_analysis.py          Insights
                         
Edit JSON Config                                No Python Code Changes!
(No Code Changes!)
```

**Workflow:**
1. **Edit** configuration files (`scenarios.json`, `scenario_nodes.json`, `analysis.json`)
2. **Run** simulations (`python main.py` or `python scenario_analysis/run_analysis.py`)
3. **See** results (tables, comparisons, retirement timing, insights)

---

## Quick Start

### 1. Install
No dependencies needed. Just Python 3.7+.

```bash
cd /Users/alon/Documents/finance_planner
```

### 2. Run

**Basic scenario comparison:**
```bash
python main.py
```
- Year-by-year financial snapshot for each scenario
- Validation checks
- Comparison report and insights

**Configuration-driven analysis with decoupled caching (NEW!):**
```bash
# Step 1: Simulate all scenarios ONCE (when scenarios change)
python scenario_analysis/run_simulations.py

# Step 2: Analyze many times (fast, uses cached results)
python scenario_analysis/run_analysis.py
```
- Runs all analyses defined in `scenario_analysis/analysis.json`
- **No code changes needed** — just edit the JSON to add analyses
- ~100x faster iteration: change output format without re-simulating
- Supported analysis types:
  - Parameter pair comparison (e.g., income ₪45K vs ₪25K)
  - Parameter sweep (e.g., income range ₪25K-₪50K with/without exit)
  - Milestone snapshots (e.g., years 1, 5, 10, 15, 20)
  - Scenario tree exploration (structure, simulations, pairwise comparisons)
- **Built-in caching:** Results cached in `simulation_cache.json` for fast re-analysis

**Run tests:**
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### 3. Modify
Edit configuration files — **no Python code changes**:

**Change income/expenses/mortgage:**
```bash
Edit: scenarios.json  (for flat scenarios)
Or:   scenario_analysis/scenario_nodes.json  (for scenario trees)
```

**Change simulation period:**
```bash
Edit: settings.json  (change "years": 20)
```

**Add a new analysis:**
```bash
Edit: scenario_analysis/analysis.json  (add analysis block, no Python!)
```

---

## Understanding the Output: Graphs, Tables & Insights

Every analysis shows three components together:

1. **[YEARLY PORTFOLIO GROWTH]** — ASCII graph showing all scenarios on one chart
   - X-axis: Years 1-20
   - Y-axis: Portfolio values
   - Different characters (█ ▓ ▒ etc.) for each scenario
   - Year 2 dip shows surrogacy expense (-₪500K)

2. **[METRIC TABLE]** or **[MILESTONE SNAPSHOTS]** — Numerical data
   - Portfolio values at key years (1, 5, 10, 15, 20)
   - Retirement year, final portfolio, annual savings

3. **[Insights]** or **[SUMMARY]** — Interpretation
   - Which scenario retires earliest
   - How much exit/income changes retirement timing
   - Compounding effects

**Example:** When comparing "No Exit" vs "₪2M Exit" vs "₪3M Exit":
- Graph shows three lines with different heights
- Year 1: Exit scenarios jump up (₪2M/₪3M injection)
- Year 2: All dip together (surrogacy)
- Years 3-20: Exit scenarios grow faster (bigger base × 5% compounding)
- Table shows exact portfolio at years 1, 5, 10, 15, 20
- Summary shows retirement years: No Exit = Year 16, ₪2M = Year 9, ₪3M = Year 6

See [GRAPH_GUIDE.md](GRAPH_GUIDE.md) for detailed walkthrough with examples.

---

## Example: Current Scenarios

### Scenario A — Baseline
- Monthly income: **₪45,000**
- Monthly expenses: **₪25,000**
- Net savings: **₪20,000/month**
- No mortgage
- **Result:** Retires in year 17

### Scenario B — Buy Apartment
- Same income/expenses
- Mortgage: **₪2,250,000** @ 4% for 25 years
- Monthly payment: **~₪11,323**
- Net savings during mortgage: **~₪8,677/month** (still positive!)
- **Result:** Does not retire within 20 years
- **Delay:** 10 years compared to Scenario A

---

## Configuration Files

### `scenarios.json` — Financial Data

```json
{
  "scenarios": [
    {
      "name": "Baseline",
      "monthly_income": 45000,
      "monthly_expenses": 25000,
      "currency": "ILS",
      "initial_portfolio": 0,
      "return_rate": 0.07,
      "withdrawal_rate": 0.04,
      "mortgage": null
    },
    {
      "name": "Buy Apartment",
      "monthly_income": 45000,
      "monthly_expenses": 25000,
      "mortgage": {
        "principal": 2250000,
        "annual_rate": 0.04,
        "duration_years": 25,
        "currency": "ILS"
      }
    }
  ]
}
```

**Edit to:**
- Change income/expenses
- Adjust mortgage (principal, rate, years)
- Add new scenarios
- Change investment return rate
- Set initial portfolio

### `settings.json` — Simulation Config

```json
{
  "simulation": {
    "years": 20,
    "return_rate": 0.07,
    "withdrawal_rate": 0.04
  },
  "output": {
    "show_fields": [
      "income_expenses",
      "mortgage_details",
      "events",
      "rates_settings"
    ]
  }
}
```

**Edit to:**
- Change simulation period (`"years": 40` for 40-year forecast)
- Change default investment return rate (`"return_rate": 0.06` for 6%)
- Change safe withdrawal rate (`"withdrawal_rate": 0.05` for 5% rule)
- Customize scenario header output (remove/reorder fields in `show_fields` list)

---

## Architecture

### File Structure
```
models.py         → Data models (Scenario, Mortgage, YearData, SimulationResult)
simulation.py     → Core engine (simulate function)
comparison.py     → Comparison logic (compare scenarios, generate insights)
scenarios.py      → Load scenarios.json
settings.py       → Load settings.json
main.py           → Entry point (runs simulations, displays results)
```

### Data Flow

```
scenarios.json → scenarios.py ──┐
                                 ├→ simulate() ──→ SimulationResult ──→ main.py
settings.json → settings.py ────┘                                         ↓
                                                                     generate_insights()
```

### Key Classes

**Scenario** (models.py)
```python
@dataclass
class Scenario:
    name: str
    monthly_income: float
    monthly_expenses: float
    mortgage: Optional[Mortgage] = None
    initial_portfolio: float = 0.0
    return_rate: float = 0.07
    withdrawal_rate: float = 0.04
    currency: str = "ILS"
    age: int = 30
    events: list[Event] = field(default_factory=list)
```

**Event** (models.py)
```python
@dataclass
class Event:
    year: int                    # Which simulation year
    portfolio_injection: float   # + = gain, - = expense
    description: str = ""        # Event label
```

**Mortgage** (models.py)
```python
@dataclass
class Mortgage:
    principal: float
    annual_rate: float
    duration_years: int
    currency: str = "ILS"
    # monthly_payment computed via standard amortization
```

**SimulationResult** (simulation.py)
```python
@dataclass
class SimulationResult:
    scenario_name: str
    year_data: list[YearData]        # Year 1..N
    retirement_year: Optional[int]   # First year portfolio ≥ required_capital
```

### Simulation Logic

For each year:

1. **Income** = monthly_income × 12
2. **Expenses** = monthly_expenses × 12
3. If mortgage is active (year ≤ duration):
   - **Expenses** += monthly_payment × 12
4. **Net savings** = income − expenses
5. **Apply events:** portfolio += any event injections for this year
6. **Portfolio growth** = (portfolio + net_savings) × (1 + return_rate)
7. **Required capital** = expenses / withdrawal_rate
8. If portfolio ≥ required_capital: **Retirement detected**
9. **Output retirement:** simulation year, calendar year, retirement age

---

## Testing

29 unit tests verify correctness:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

**Test coverage:**
- Mortgage payment formula (standard amortization)
- Scenario A: always positive savings, monotonic portfolio growth
- Scenario B: correctly handles mortgage burden
- **Events:** positive injections, negative withdrawals, multiple events, compounding
- Retirement detection
- Pure function behavior (deterministic)
- **Insights:** structured insight object creation, formatting, comparison logic

---

## Design Principles

### 1. Configuration-Driven
- **Scenarios** live in `scenarios.json`
- **Settings** live in `settings.json`
- Python code is immutable
- Change behavior by editing JSON

### 2. Pure Functions
- `simulate(scenario, years)` has no side effects
- Same input → same output, always
- Easy to test, compose, parallelize

### 3. Minimal & Extensible
- Only what's needed for MVP
- Clear extension points (new fields, new settings)
- Standard library only (no dependencies)

### 4. Real Financial Modeling
- Proper mortgage amortization formula
- Annual investment return compounding
- Safe withdrawal rate logic (4% rule)
- Currency support built-in

---

## Example Use Cases

### Question: "When can I retire?"
Edit `scenarios.json` with your income/expenses/age, run:
```bash
python main.py
```
Look for output like: `✓ Retirement achieved in year 10 (expected: 2035, age: 50)`

### Question: "Should I buy the apartment?"
Create two scenario nodes in `scenario_analysis/scenario_nodes.json`:
```json
{
  "name": "Without Apartment",
  "parent": "Alon Baseline"
},
{
  "name": "With Apartment",
  "parent": "Alon Baseline",
  "mortgage": { "principal": 2250000, "annual_rate": 0.04, "duration_years": 25 }
}
```
Then add an analysis to `analysis.json` to compare them.

### Question: "What if income varies from ₪30K to ₪60K, with and without a ₪2M exit?"
Edit `scenario_analysis/analysis.json` and add:
```json
{
  "id": "income_sensitivity_30_to_60k",
  "type": "parameter_sweep",
  "base_scenario": "Alon Baseline",
  "parameter": "monthly_income",
  "range": { "min": 30000, "max": 60000, "step": 5000 },
  "test_variations": [
    { "name": "No Exit", "events": [] },
    { "name": "₪2M Exit", "events": [{"year": 2, "portfolio_injection": 2000000}] }
  ],
  "metrics": ["retirement_year", "portfolio_final"],
  "outputs": ["detailed_tables", "comparison_table"]
}
```
Run: `python scenario_analysis/run_analysis.py`

### Question: "What if I create a scenario tree for different life paths?"
Edit `scenario_analysis/scenario_nodes.json`:
```json
{
  "name": "Base: No Mortgage",
  "base_scenario": "Baseline"
},
{
  "name": "Path A: Buy Apartment",
  "parent": "Base: No Mortgage",
  "mortgage": { ... }
},
{
  "name": "Path A + Exit",
  "parent": "Path A: Buy Apartment",
  "monthly_income": 35000,
  "events": [{"year": 2, "portfolio_injection": 5000000}]
}
```
Add `tree_exploration` analysis in `analysis.json` to visualize the tree.

### Question: "How sensitive is retirement to investment returns?"
Edit `settings.json`, change `"return_rate"` from 0.07 to 0.06 (or another value), run:
```bash
python main.py
```

---

## Current Features

- ✅ **Events** — one-time portfolio injections/withdrawals (stock offerings, emergencies)
- ✅ **Age tracking** — see retirement year and retirement age
- ✅ **Global settings** — return_rate and withdrawal_rate in settings.json
- ✅ **Scenario Trees** — inheritance-based scenario composition
  - Define base scenarios, extend with child nodes
  - Control event composition ("append" or "replace")
  - Explore "what-if" variations efficiently
- ✅ **Configuration-Driven Analysis** — no Python code needed
  - Define analyses in `analysis.json`
  - Support for parameter comparisons, sweeps, milestones, tree exploration
  - Unified output formatting and insights

## Adding New Scenarios

**For simple scenarios:** Edit `scenarios.json`
```json
{
  "name": "My Scenario",
  "monthly_income": 50000,
  "monthly_expenses": 30000,
  "mortgage": null,
  "events": [
    {"year": 2, "portfolio_injection": 1000000, "description": "Bonus"}
  ]
}
```

**For scenario variations (inheritance):** Edit `scenario_analysis/scenario_nodes.json`
```json
{
  "name": "My Variation",
  "parent": "Alon Baseline",
  "monthly_income": 55000,
  "event_mode": "append",
  "events": []
}
```

**Scenario trees** (inheritance-based composition) let you:
- Define a base scenario once
- Create child nodes that override specific fields
- Control event composition (append vs. replace)
- Easily explore "what-if" variations

See [SCENARIO_TREE_GUIDE.md](SCENARIO_TREE_GUIDE.md) for detailed examples.

## Adding New Analyses

**Edit `scenario_analysis/analysis.json`** — no Python code needed!

```json
{
  "id": "my_analysis",
  "title": "My Custom Analysis",
  "type": "parameter_sweep",
  "base_scenario": "Alon Baseline",
  "parameter": "monthly_income",
  "range": { "min": 30000, "max": 60000, "step": 5000 },
  "test_variations": [
    { "name": "Without Exit", "events": [] },
    { "name": "With ₪3M Exit", "events": [{"year": 2, "portfolio_injection": 3000000}] }
  ],
  "metrics": ["retirement_year", "portfolio_final"],
  "outputs": ["detailed_tables", "comparison_table"]
}
```

Then run: `python scenario_analysis/run_analysis.py`

**Supported analysis types:**
- `parameter_pair_comparison` — Compare scenarios at 2 param values
- `parameter_sweep` — Vary parameter across range
- `milestone_snapshots` — Show snapshots at specific years
- `tree_exploration` — Visualize tree and pairwise comparisons

For new analysis types, add a handler to `run_analysis.py`.

## Future Extensions

The design cleanly supports:

- **Inflation** — adjust expenses by inflation rate annually
- **Multiple Assets** — portfolio with different return rates (stocks, bonds, real estate)
- **Advanced Outputs** — charts, sensitivity analysis, Monte Carlo simulations
- **Tax modeling** — incorporate taxes into withdrawal calculations

---

## For Claude Code / Claude Engineers

See **CLAUDE.md** for:
- How to work with this codebase
- Where to make changes
- Testing patterns
- Common tasks

See **ARCHITECTURE.md** for:
- Technical design decisions
- Data model rationale
- Extension patterns
- Extensibility roadmap

---

## Requirements

- Python 3.7+
- No external dependencies (standard library only)

## Running

```bash
# Simulate scenarios
python main.py

# Run tests
python -m unittest discover -s tests -p "test_*.py" -v

# Run specific test
python -m unittest tests.test_simulation.TestMortgage -v
```

---

## File Summary

| File | Purpose |
|---|---|
| `models.py` | Data models: Scenario, ScenarioNode, Mortgage, YearData, SimulationResult, Event |
| `simulation.py` | Core simulation engine: `simulate(scenario, years)` |
| `comparison.py` | Insights model: `build_insights()`, `format_insights()`, `generate_insights()` |
| `scenarios.py` | Load scenarios from `scenarios.json` |
| `settings.py` | Load settings from `settings.json` (simulation + output config) |
| `main.py` | Entry point: runs scenarios, displays results with configurable headers |
| `scenarios.json` | **CONFIG:** Scenario data (income, expenses, mortgage, events) |
| `settings.json` | **CONFIG:** Simulation settings (years, rates) + output display fields |
| `README.md` | This file — project overview |
| `CLAUDE.md` | How to work with this codebase in Claude Code |
| `ARCHITECTURE.md` | Technical design and extension patterns |
| `SCENARIO_TREE_GUIDE.md` | Scenario trees: complete usage guide |
| `scenario_analysis/` | **Folder:** Configuration-driven analysis system |
| `scenario_analysis/run_analysis.py` | Generic analysis runner (interprets analysis.json) |
| `scenario_analysis/analysis.json` | **CONFIG:** Analysis definitions (edit this to add analyses) |
| `scenario_analysis/scenario_nodes.py` | Load scenario trees from `scenario_nodes.json` |
| `scenario_analysis/scenario_nodes.json` | **CONFIG:** Scenario tree definitions (EDIT for new scenarios) |
| `tests/test_simulation.py` | 42 core unit tests (all passing) |

---

## Questions?

1. **How do I change a scenario?** → Edit `scenarios.json` (flat) or `scenario_analysis/scenario_nodes.json` (tree)
2. **How do I add a new scenario?** → Add to `scenarios.json` (simple) or `scenario_analysis/scenario_nodes.json` (with inheritance)
3. **How do I add a new analysis?** → Edit `scenario_analysis/analysis.json` (no Python code!)
4. **How do I change simulation period?** → Edit `settings.json` (change `"years"`)
5. **How do I run an analysis?** → `python scenario_analysis/run_analysis.py`
6. **How do I extend this?** → See `ARCHITECTURE.md` → Extension Patterns
7. **How do I understand the code?** → See `CLAUDE.md` or `ARCHITECTURE.md`

---

**Built with care for clarity, testability, and extensibility.**
