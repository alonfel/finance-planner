# Financial Simulation Engine

A minimal, clean financial simulation engine that models scenarios (like "buy apartment with mortgage") and compares outcomes over time.

**No external dependencies. Pure Python. Configuration-driven.**

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
- ✅ Detects retirement (first year portfolio meets retirement goal)
- ✅ Shows retirement year, calendar year, and retirement age
- ✅ Compares multiple scenarios and generates structured insights
- ✅ Configurable scenario parameter display in output
- ✅ 100% configuration-driven (no code changes needed)
- ✅ Pure functions, fully testable (29 unit tests, all passing)

---

## Quick Start

### 1. Install
No dependencies needed. Just Python 3.7+.

```bash
cd /Users/alon/Documents/finance_planner
```

### 2. Run
```bash
python main.py
```

**Output:**
- Year-by-year financial snapshot for each scenario
- Validation checks
- Comparison report and insights

### 3. Modify
Edit configuration files — **no Python code changes**:

**Change income/expenses/mortgage:**
```bash
Edit: scenarios.json
```

**Change simulation period:**
```bash
Edit: settings.json  (change "years": 20)
```

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
Create two scenarios: with and without mortgage, run `main.py` to compare.

### Question: "What if I get a stock offering in 2 years?"
Add an event to your scenario in `scenarios.json`:
```json
"events": [
  {"year": 2, "portfolio_injection": 3000000, "description": "Stock offering"}
]
```
Compare timing (year 2 vs year 10 vs year 29) to see impact on retirement.

### Question: "What if I earn more?"
Edit `scenarios.json`, change income, run again. See how retirement timeline changes.

### Question: "How sensitive is this to investment returns?"
Edit `settings.json`, change `"return_rate"`, run again.

---

## Current Features

- ✅ **Events** — one-time portfolio injections/withdrawals (stock offerings, emergencies)
- ✅ **Age tracking** — see retirement year and retirement age
- ✅ **Global settings** — return_rate and withdrawal_rate in settings.json

## Future Extensions

The design cleanly supports:

- **Scenario Trees** — branching scenarios at specific years (income changes)
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
| `models.py` | Data models: Scenario, Mortgage, YearData, SimulationResult, Event |
| `simulation.py` | Core simulation engine: `simulate(scenario, years)` |
| `comparison.py` | Insights model: `build_insights()`, `format_insights()`, `generate_insights()` |
| `scenarios.py` | Load scenarios from `scenarios.json` |
| `settings.py` | Load settings from `settings.json` (simulation + output config) |
| `main.py` | Entry point: runs scenarios, displays results with configurable headers |
| `compare_all_scenarios.py` | Comprehensive analysis: all scenarios, all pairwise comparisons |
| `scenarios.json` | **CONFIG:** Scenario data (income, expenses, mortgage, events) |
| `settings.json` | **CONFIG:** Simulation settings (years, rates) + output display fields |
| `README.md` | This file — project overview |
| `CLAUDE.md` | How to work with this codebase in Claude Code |
| `ARCHITECTURE.md` | Technical design and extension patterns |
| `tests/test_simulation.py` | 29 unit tests (all passing) |

---

## Questions?

1. **How do I change the scenario?** → Edit `scenarios.json`
2. **How do I change simulation period?** → Edit `settings.json`
3. **How do I add a new scenario?** → Add to `scenarios.json` array
4. **How do I extend this?** → See `ARCHITECTURE.md` → Extension Patterns
5. **How do I understand the code?** → See `CLAUDE.md` or `ARCHITECTURE.md`

---

**Built with care for clarity, testability, and extensibility.**
