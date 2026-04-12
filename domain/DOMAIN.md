# Domain Layer: Pure Business Logic & Models

This layer contains all financial domain models and the core simulation engine. Zero external dependencies (only stdlib).

## Models

### Event
Represents a one-time financial event (stock offering, inheritance, emergency expense).

```python
Event(
    year=2,                              # 1-indexed simulation year
    portfolio_injection=2_000_000,       # Positive: gain, Negative: expense
    description="Company exit proceeds"
)
```

### Mortgage
Fixed-rate mortgage with automatic amortization calculation.

```python
Mortgage(
    principal=2_250_000,
    annual_rate=0.04,      # 4% annual
    duration_years=25,
    currency="ILS"
)
```

**Design note:** Monthly payment computed in `__post_init__` using standard amortization formula. Handles zero-interest edge case gracefully.

### Scenario
Complete financial scenario definition: income, expenses, optional mortgage, events.

```python
Scenario(
    name="Buy Apartment",
    monthly_income=45_000,
    monthly_expenses=25_000,
    mortgage=mortgage_obj,
    initial_portfolio=0.0,
    return_rate=0.07,        # 7% annual portfolio return
    withdrawal_rate=0.04,    # 4% rule for retirement
    currency="ILS",
    age=41,
    events=[event1, event2]
)
```

### ScenarioNode
Inheritance-based scenario composition. Nodes form a tree where each child overrides parent fields.

```python
# Root node
ScenarioNode(
    name="Alon Baseline",
    base_scenario=scenario_obj  # Resolved from scenarios.json
)

# Child node
ScenarioNode(
    name="Alon - Buy Apartment",
    parent_name="Alon Baseline",  # Inherits from parent
    mortgage=new_mortgage,         # Override: adds mortgage
    event_mode="append",           # Inherit parent events + add new ones
    events=[down_payment_fee]
)
```

**Resolution:** Call `.resolve(all_nodes)` to walk ancestor chain and merge overrides root-to-leaf.

## Simulation Engine

### YearData
Annual snapshot during simulation (year 1..N).

```python
YearData(
    year=1,                           # 1-indexed
    income=540_000,                   # Annual gross
    expenses=300_000,                 # Including mortgage if active
    net_savings=240_000,              # income - expenses
    portfolio=1_722_000,              # End-of-year after growth
    required_capital=7_500_000,       # Needed to sustain retirement
    mortgage_active=False
)
```

### SimulationResult
Complete simulation output for one scenario.

```python
SimulationResult(
    scenario_name="Buy Apartment",
    year_data=[YearData(...), ...],   # 20 or 40 years of snapshots
    retirement_year=17                # First year >= required_capital, or None
)
```

### simulate(scenario, years=40) → SimulationResult
Core simulation loop:

1. **Each year:**
   - Apply annual income/expenses
   - Add mortgage payment if active (years 1..duration)
   - Apply one-time events (stock offerings, bonuses, etc.)
   - Grow portfolio at return_rate
   - Detect retirement (portfolio ≥ required_capital)
   - Record YearData

2. **Key decisions:**
   - Portfolio grows AFTER adding savings: `(portfolio + savings) * (1 + return_rate)`
   - Required capital uses current year's expenses (drops after mortgage ends)
   - Retirement is first crossing (one-way check)
   - Return rate compounded annually (nominal, not inflation-adjusted)

**Pure function:** Same input always produces same output. No side effects.

## Insights Layer

### Insight Types
Structured observations about simulation results:

- **RetirementInsight** — When does this scenario retire? (or never?)
- **RetirementDeltaInsight** — How much does one scenario delay/accelerate retirement?
- **PortfolioInsight** — Final portfolio comparison between two scenarios
- **MortgageInsight** — Mortgage period stats (years active, avg savings during)

### build_insights(result_a, result_b) → List[Insight]
Converts two raw SimulationResult objects into typed insight objects. Pure function, type-safe.

### format_insights(insights) → str
Renders insight objects to human-readable text. Dispatches on insight type using `isinstance`.

### generate_insights(result_a, result_b) → str
Convenience: `format_insights(build_insights(result_a, result_b))`

## Usage Example

```python
from domain.models import Scenario, Mortgage, Event
from domain.simulation import simulate
from domain.insights import build_insights, format_insights

# Define scenario
scenario = Scenario(
    name="Baseline",
    monthly_income=45_000,
    monthly_expenses=25_000,
    mortgage=Mortgage(principal=2_250_000, annual_rate=0.04, duration_years=25),
    events=[Event(year=2, portfolio_injection=2_000_000, description="Exit")]
)

# Simulate
result = simulate(scenario, years=20)

# Analyze
insights = build_insights(result_a, result_b)
print(format_insights(insights))
```

## Testing

42 unit tests cover:
- Mortgage amortization (edge cases: zero interest, large principal)
- Simulation engine (positive savings, portfolio growth, retirement detection)
- Events (positive/negative injections, multiple events same year)
- ScenarioNode (inheritance, event composition, cycle detection)
- Insights (correct insight types, correct differences)

All tests pure: construct objects directly, no JSON I/O.

## Key Design Principles

1. **Immutable:** No mutation after creation
2. **Pure functions:** `simulate()` is deterministic, no side effects
3. **Type-safe:** Dataclasses with type hints
4. **Minimal:** Only features needed for MVP
5. **Testable:** Direct construction, no mocking needed
