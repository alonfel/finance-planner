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
python scenario_analysis/compare_all_scenarios.py
```

Outputs:
- All scenarios simulated
- Quick overview table
- All pairwise scenario comparisons with insights

### Comparing Your Scenarios (Personal Analysis)
```bash
python scenario_analysis/compare_your_baseline_vs_exit_vs_friend.py
```

Outputs:
- Year-by-year snapshots at milestones (1, 5, 10, 15, 20 years)
- Your baseline (no exit), You + ₪2M exit, You + ₪3M exit, and Friend's scenario
- Detailed metrics: portfolio value, retirement year, annual savings
- Side-by-side comparison table
- Key differences and strategic insights

### Exploring Scenario Trees (New!)
```bash
python scenario_analysis/explore_tree.py
```

Outputs:
- Tree structure visualization
- Simulation results for each node
- Pairwise comparisons showing inheritance impacts
- How-to examples for creating variations

### Running Tests
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

All 52 tests should pass (36 core + 16 ScenarioNode tests).

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
├── models.py              # Data models: Scenario, ScenarioNode, Mortgage, Event
├── simulation.py          # Core engine: simulate()
├── comparison.py          # Insights model: build_insights(), format_insights()
├── scenarios.py           # Load scenarios from JSON
├── settings.py            # Load settings from JSON
├── main.py                # Entry point: run scenarios with insights
├── scenarios.json         # Scenario data (EDIT THIS)
├── settings.json          # Simulation config + output display (EDIT THIS)
├── README.md              # Project overview
├── CLAUDE.md              # This file
├── ARCHITECTURE.md        # Technical design & extension patterns
├── SCENARIO_TREE_GUIDE.md # Scenario trees guide
├── scenario_analysis/     # Scenario tree analysis and comparisons
│   ├── __init__.py
│   ├── scenario_nodes.py  # Load scenario trees from JSON
│   ├── scenario_nodes.json # Scenario tree definitions (EDIT THIS)
│   ├── compare_your_baseline_vs_exit_vs_friend.py # Personal scenario comparison
│   ├── compare_with_without_exit.py # Exit impact analysis
│   └── explore_tree.py    # Interactive tree exploration
└── tests/
    ├── __init__.py
    ├── test_simulation.py  # 42 core unit tests
    ├── test_income_exit_clusters.py # Income variation analysis
    └── test_scenario_clusters.py # Multi-scenario exploration
```

---

## Scenario Trees (Inheritance-Based Composition)

### What Are Scenario Trees?

Build complex scenarios through **inheritance** instead of defining them flat:

```
Baseline (root)
├─ Buy Apartment (add mortgage)
│  └─ Buy Apartment + Exit (change income + inject exit proceeds)
```

Each node inherits from its parent and adds small, understandable changes.

### How to Use Scenario Trees

**Load and explore:**
```bash
python scenario_analysis/explore_tree.py
```

**Programmatically:**
```python
from scenario_analysis.scenario_nodes import load_scenario_nodes
from simulation import simulate

nodes = load_scenario_nodes()
resolved = nodes["Alon - Buy Apartment + Exit"].resolve(nodes)
result = simulate(resolved, years=20)
```

**Compare nodes:**
```python
from comparison import build_insights, format_insights

result_a = simulate(nodes["Alon Baseline"].resolve(nodes), years=20)
result_b = simulate(nodes["Alon - Buy Apartment + Exit"].resolve(nodes), years=20)
insights = build_insights(result_a, result_b)
print(format_insights(insights))
```

### scenario_nodes.json Format

```json
{
  "scenario_nodes": [
    {
      "name": "Alon Baseline",
      "base_scenario": "Baseline",
      "monthly_income": 45000,
      "monthly_expenses": 25000,
      "age": 41,
      "event_mode": "append",
      "events": []
    },
    {
      "name": "Alon - Buy Apartment",
      "parent": "Alon Baseline",
      "mortgage": {
        "principal": 2250000,
        "annual_rate": 0.04,
        "duration_years": 25
      },
      "event_mode": "append",
      "events": [
        {"year": 1, "portfolio_injection": -200000, "description": "Down payment fees"}
      ]
    },
    {
      "name": "Alon - Buy Apartment + Exit",
      "parent": "Alon - Buy Apartment",
      "monthly_income": 35000,
      "event_mode": "replace",
      "events": [
        {"year": 2, "portfolio_injection": 5000000, "description": "Company exit"}
      ]
    }
  ]
}
```

**Key concepts:**
- Root nodes: have `"base_scenario"`, no `"parent"`
- Child nodes: have `"parent"`, no `"base_scenario"`
- Event composition: `"append"` = add to parent's events, `"replace"` = discard parent's events
- Inheritance: child inherits all parent's fields; only override what changes

### Creating a New Tree Node

```python
from models import ScenarioNode, Event
from scenario_analysis.scenario_nodes import load_scenario_nodes

nodes = load_scenario_nodes()

# Create a variation
new_node = ScenarioNode(
    name="Custom Variation",
    parent_name="Alon - Buy Apartment",
    monthly_income=50_000,  # Override: different from parent
    event_mode="append",
    events=[Event(year=5, portfolio_injection=-300_000, description="Home renovation")]
)

# Simulate it
all_nodes = {**nodes, "Custom Variation": new_node}
resolved = new_node.resolve(all_nodes)
result = simulate(resolved, years=20)
```

### Why Scenario Trees Matter

1. **DRY (Don't Repeat Yourself)** — Define base once, extend as needed
2. **Inheritance clarity** — See exactly what each node changes
3. **Compounding visibility** — Small changes compound over time; easy to test
4. **"What-if" exploration** — Quickly model variations without duplication

### Further Reading

See [SCENARIO_TREE_GUIDE.md](SCENARIO_TREE_GUIDE.md) for:
- Real financial examples with outcomes
- How inheritance chains resolve
- Sensitivity analysis examples
- Design decisions and rationale

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

### Add a Scenario Tree Node

1. Edit `scenario_nodes.json`
2. Add a new node with a unique `"name"`
3. Set `"parent"` to an existing node name (or use `"base_scenario"` for root)
4. Override fields as needed
5. Set `event_mode` ("append" or "replace") and `events` list
6. Run `python explore_tree.py` to see the tree

**Example:**
```json
{
  "name": "My Custom Scenario",
  "parent": "Alon - Buy Apartment",
  "monthly_income": 50000,
  "event_mode": "append",
  "events": []
}
```

Then resolve and simulate:
```python
from scenario_nodes import load_scenario_nodes
nodes = load_scenario_nodes()
result = simulate(nodes["My Custom Scenario"].resolve(nodes), years=20)
```

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
- Key test areas:
  - **Mortgage:** amortization formula, edge cases (0% rate)
  - **Simulation:** core engine, events, retirement detection
  - **Insights:** structured objects, comparison logic
  - **ScenarioNode:** inheritance resolution, event composition, validation
    - Root nodes resolve like Person (backward compat)
    - 2-level and 3-level chains inherit correctly
    - Event modes ("append" vs "replace") work as expected
    - Cycle detection and validation happen at load time

**Total: 52 tests** (36 core + 16 ScenarioNode) — all passing

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

### For Flat Scenarios:
1. **Edit config** (scenarios.json, settings.json)
2. **Run** `python main.py` or `python compare_all_scenarios.py`
3. **See results** — year tables, comparisons, insights
4. **Iterate** — change config, re-run

### For Scenario Trees:
1. **Edit** scenario_nodes.json
2. **Explore** `python explore_tree.py` (or programmatic: load_scenario_nodes)
3. **Resolve** nodes into flat Scenarios via `.resolve(all_nodes)`
4. **Simulate** using existing simulate() function
5. **Compare** using existing comparison tools

**No Python code changes needed!**

Both approaches coexist: flat scenarios (scenarios.json) and trees (scenario_nodes.json) work independently or together.
