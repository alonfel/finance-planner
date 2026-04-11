# Claude Code Guidelines for Finance Planner

This document describes how to work with this codebase in Claude Code.

## Quick Start

### Running the Simulation
```bash
python main.py
```

Outputs:
- Year-by-year tables for both scenarios
- Validation checks
- Scenario comparison and insights

### Running Comprehensive Analysis
```bash
python compare_all_scenarios.py
```

Outputs:
- All scenarios simulated
- Quick overview table
- All pairwise scenario comparisons with insights

### Running Tests
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

All 29 tests should pass.

---

## Configuration Files (No Code Changes Needed)

### `scenarios.json` — Scenario Data
Change financial parameters without touching Python:

```json
{
  "scenarios": [
    {
      "name": "Baseline",
      "monthly_income": 45000,
      "monthly_expenses": 25000,
      "currency": "ILS",
      "initial_portfolio": 0,
      "age": 41,
      "mortgage": null,
      "events": []
    },
    {
      "name": "IPO Year 2",
      "monthly_income": 45000,
      "monthly_expenses": 25000,
      "currency": "ILS",
      "initial_portfolio": 0,
      "age": 41,
      "mortgage": null,
      "events": [
        {"year": 2, "portfolio_injection": 3000000, "description": "Stock offering"}
      ]
    }
  ]
}
```

**Edit this to:**
- Change income/expenses
- Adjust mortgage terms (principal, rate, duration)
- Add new scenarios (duplicate a scenario block and give it a new `name`)
- Set current age (used to calculate retirement age)
- Set initial portfolio balance
- Add one-time events (stock offerings, inheritances, emergencies)

### `settings.json` — Simulation & Output Configuration
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

**Edit the simulation section to:**
- Change simulation period (e.g., `"years": 30` for 30-year forecast)
- Change default investment return rate (e.g., `"return_rate": 0.06` for 6%)
- Change safe withdrawal rate (e.g., `"withdrawal_rate": 0.05` for 5% rule)

**Edit the output section to:**
- Hide a field by removing it from `show_fields` (e.g., remove `"events"` if you don't want to see events)
- Reorder fields to change display order
- Valid field names: `"income_expenses"`, `"mortgage_details"`, `"events"`, `"rates_settings"`

---

## File Structure Overview

```
finance_planner/
├── models.py              # Data models: Scenario, Mortgage, Event, YearData
├── simulation.py          # Core engine: simulate()
├── comparison.py          # Insights model: build_insights(), format_insights()
├── scenarios.py           # Load scenarios from JSON
├── settings.py            # Load settings from JSON
├── main.py                # Entry point: run both scenarios with insights
├── compare_all_scenarios.py # Comprehensive analysis: all scenarios, all comparisons
├── scenarios.json         # Scenario data (EDIT THIS)
├── settings.json          # Simulation config + output display (EDIT THIS)
├── README.md              # Project overview
├── CLAUDE.md              # This file (guidelines for working in Claude Code)
├── ARCHITECTURE.md        # Technical design & extension patterns
└── tests/
    ├── __init__.py
    └── test_simulation.py # 29 unit tests
```

---

## Common Tasks

### Change Simulation Period
Edit `settings.json`:
```json
"years": 20  →  "years": 40
```

### Add a New Scenario
1. Edit `scenarios.json`
2. Duplicate one scenario block
3. Change `"name"` to something unique
4. Adjust parameters (income, expenses, mortgage, age, events)
5. Run `python main.py` — it auto-loads

Example with a stock offering event:
```json
{
  "name": "High Earner with IPO",
  "monthly_income": 100000,
  "monthly_expenses": 40000,
  "currency": "ILS",
  "initial_portfolio": 0,
  "age": 35,
  "mortgage": null,
  "events": [
    {"year": 3, "portfolio_injection": 5000000, "description": "Stock offering"}
  ]
}
```

### Add Events to a Scenario
Add to the `"events"` array:
```json
"events": [
  {"year": 2, "portfolio_injection": 3000000, "description": "Stock offering"},
  {"year": 3, "portfolio_injection": -500000, "description": "Surrogacy expense"}
]
```

Events apply before portfolio compounding, so they earn returns in the same year.

### Compare Different Scenarios in main.py
Currently `main.py` hardcodes `SCENARIO_A` and `SCENARIO_B`. To compare different scenarios:

1. Load them from `scenarios.py`:
   ```python
   from scenarios import load_scenarios
   all_scenarios = load_scenarios()
   
   # Compare "Baseline" vs "High Earner"
   result_baseline = simulate(all_scenarios["Baseline"], years=SETTINGS.years)
   result_high = simulate(all_scenarios["High Earner"], years=SETTINGS.years)
   ```

### Configure Output Display
Edit `settings.json` to show/hide scenario parameters:

**Show only income/expenses and mortgage:**
```json
"output": {
  "show_fields": [
    "income_expenses",
    "mortgage_details"
  ]
}
```

**Show everything (default):**
```json
"output": {
  "show_fields": [
    "income_expenses",
    "mortgage_details",
    "events",
    "rates_settings"
  ]
}
```

Fields are displayed in the order listed.

### Run Tests in Isolation
Test a specific test class:
```bash
python -m unittest tests.test_simulation.TestMortgage -v
```

Test a specific test:
```bash
python -m unittest tests.test_simulation.TestSimulate.test_scenario_a_always_positive_net_savings -v
```

### Access Structured Insights Programmatically
The insights layer separates computation from presentation:

```python
from scenarios import load_scenarios
from settings import SETTINGS
from simulation import simulate
from comparison import build_insights, format_insights

scenarios = load_scenarios()
result_a = simulate(scenarios["Baseline"], years=SETTINGS.years)
result_b = simulate(scenarios["Buy Apartment"], years=SETTINGS.years)

# Get structured insight objects
insights = build_insights(result_a, result_b)
for insight in insights:
    print(f"{insight.__class__.__name__}: {insight}")

# Or get formatted text
text = format_insights(insights)
print(text)
```

Insight types: `RetirementInsight`, `RetirementDeltaInsight`, `PortfolioInsight`, `MortgageInsight`

---

## Key Design Decisions

### Pure Functions, No Global State
- `simulate()` takes a `Scenario` and returns results
- No side effects — same input always produces same output
- Tests can call `simulate()` directly without mocking

### Configuration in JSON, Code Immutable
- **scenarios.json** — data you can edit
- **settings.json** — config you can edit
- **\*.py** — logic (don't modify unless adding features)

### Validation is Flexible
- `validate_scenario_b_behavior()` in `main.py` adapts to any mortgage period
- No hardcoded expectations about negative/positive savings
- Works for 20-year, 40-year, or any time period

### Currency Support
- `Scenario` and `Mortgage` accept `currency` field
- Display uses currency symbols (₪ for ILS, $ for USD, € for EUR)
- Easy to add more currencies

### Events Support
- `Scenario` contains optional `events` list
- Each event has: `year` (1-indexed), `portfolio_injection` (can be negative), `description`
- Events apply before annual compounding, so earnings compound that year
- Multiple events in same year all apply

### Structured Insights Layer
- `build_insights()` converts raw simulation results into typed insight objects
- `format_insights()` renders insight objects as human-readable text
- Enables both programmatic access and flexible output formats
- Insight types: `RetirementInsight`, `RetirementDeltaInsight`, `PortfolioInsight`, `MortgageInsight`

### Configurable Output Display
- `show_fields` list in `settings.json` controls which scenario parameters appear
- No code changes needed — edit JSON to reorder or hide fields
- Supports: `"income_expenses"`, `"mortgage_details"`, `"events"`, `"rates_settings"`

---

## Extending the System

### Add a Setting
1. Add field to `Settings` dataclass in `settings.py`
2. Update `load_settings()` to read from JSON
3. Add to `settings.json`
4. Use `SETTINGS.your_field` in `main.py`

### Add a Scenario Field
1. Add field to `Scenario` dataclass in `models.py`
2. Update `_scenario_from_dict()` in `scenarios.py` to load it
3. Add to `scenarios.json`
4. Use in simulation logic if needed

### Add a Mortgage Feature
Example: variable interest rates, or balloon payments
1. Extend `Mortgage` dataclass in `models.py`
2. Update mortgage payment calculation in `__post_init__`
3. Update `_scenario_from_dict()` in `scenarios.py`
4. Update `scenarios.json` schema

### Add More Scenarios
Edit `scenarios.json` and add to the `"scenarios"` array. Each scenario is automatically loadable.

### Create Scenario Variants
Use a script:
```python
from scenarios import load_scenarios
from settings import SETTINGS
from simulation import simulate
from comparison import generate_insights

scenarios = load_scenarios()
# Load any scenarios by name: scenarios["Baseline"], scenarios["Buy Apartment"], etc.
result_a = simulate(scenarios["Baseline"], years=SETTINGS.years)
result_b = simulate(scenarios["Buy Apartment"], years=SETTINGS.years)
print(generate_insights(result_a, result_b))
```

---

## Testing Philosophy

- Tests construct scenarios directly, **not** from JSON (isolation)
- If you change scenario values in `scenarios.json`, tests don't break
- Tests verify **logic**, not specific data
- Key tests:
  - Mortgage payment formula (correct amortization)
  - Scenario A: always positive savings, monotonic portfolio growth
  - Scenario B: negative → positive savings transition at mortgage end
  - Retirement detection works correctly

---

## Standard Library Only

No external dependencies. Uses only:
- `dataclasses` — data models
- `json` — config loading
- `pathlib` — file paths
- `unittest` — testing

This means:
- ✅ Easy to run anywhere
- ✅ Fast startup
- ✅ No version conflicts
- ✅ Easy to extend

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'settings'`
Make sure you're running from the `finance_planner` directory:
```bash
cd /Users/alon/Documents/finance_planner
python main.py
```

### JSON syntax error
Check `scenarios.json` or `settings.json` for trailing commas or missing quotes.

### Tests fail
Ensure you're using Python 3.7+ (dataclasses) and haven't modified test scenario construction.

### Validation fails
This usually means scenario parameters have changed (which is fine!). Check that mortgage extends into the simulation period if you expect negative savings.

---

## Summary: The Workflow

1. **Edit config files** (scenarios.json, settings.json)
2. **Run** `python main.py`
3. **See results** — year tables, validations, comparison
4. **Iterate** — change config, re-run
5. **Test** — `python -m unittest ...` to verify correctness

**No Python code changes needed for scenario tweaks!**
