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

### Pension
Represents a locked retirement savings account that accumulates separately from liquid investments.

```python
Pension(
    initial_value=2_000_000,           # Accumulated pension today (₪)
    monthly_contribution=9_000,        # Monthly addition (₪)
    annual_growth_rate=0.06,           # Pension fund return (6% typical)
    accessible_at_age=67               # Age when pension unlocks (Israeli standard: 67)
)
```

**Behavior in simulation:**
- Accumulates independently: each year grows by `(pension + monthly_contributions) * (1 + growth_rate)`
- **Locked until `accessible_at_age`:** does NOT count toward retirement threshold before then
- **Unlocked at age:** from that year onward, pension value is added to liquid portfolio for retirement check
- Realistic for Israeli mandatory pension (Keren Pensia) — illiquid until retirement age (67)

**Design note:** Pension is optional on Scenario (defaults to None). Simulation checks `if scenario.pension` before applying pension logic, maintaining backward compatibility.

### Scenario
Complete financial scenario definition: income, expenses, optional mortgage, optional pension, events.

```python
Scenario(
    name="Buy Apartment",
    monthly_income=45_000,
    monthly_expenses=25_000,
    mortgage=mortgage_obj,              # Optional: fixed-rate mortgage
    pension=pension_obj,                # Optional: locked retirement savings
    initial_portfolio=0.0,
    return_rate=0.07,        # 7% annual portfolio return
    withdrawal_rate=0.04,    # 4% rule for retirement
    currency="ILS",
    age=41,
    events=[event1, event2]
)
```

**Pension integration:** If present, pension accumulates separately and counts toward retirement only after `pension.accessible_at_age`.

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
    mortgage_active=False,
    pension_value=2_234_480,          # Accumulated pension at year-end
    pension_accessible=False           # Whether pension counts toward retirement
)
```

**Pension fields** (added in v2):
- `pension_value` — Accumulated pension fund value after growth and contributions
- `pension_accessible` — True if scenario has pension AND current age ≥ pension.accessible_at_age

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
   - Grow pension fund if present: `(pension + monthly_contributions) * (1 + growth_rate)`
   - Grow portfolio at return_rate: `(portfolio + savings) * (1 + return_rate)`
   - Detect retirement: portfolio ≥ required_capital (or portfolio + accessible_pension ≥ required_capital)
   - Record YearData

2. **Key decisions:**
   - Portfolio grows AFTER adding savings: `(portfolio + savings) * (1 + return_rate)`
   - Pension grows INDEPENDENTLY and is only added to capital check if accessible
   - Required capital uses current year's expenses (drops after mortgage ends)
   - Retirement is first crossing (one-way check): portfolio alone before age unlock, then portfolio+pension
   - Return rate compounded annually (nominal, not inflation-adjusted)
   - Pension is "locked" and does NOT count toward retirement threshold until accessible_at_age is reached

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

### Without Pension
```python
from domain.models import Scenario, Mortgage, Event
from domain.simulation import simulate
from domain.insights import build_insights, format_insights

scenario = Scenario(
    name="Baseline",
    monthly_income=45_000,
    monthly_expenses=25_000,
    mortgage=Mortgage(principal=2_250_000, annual_rate=0.04, duration_years=25),
    events=[Event(year=2, portfolio_injection=2_000_000, description="Exit")]
)

result = simulate(scenario, years=20)
```

### With Pension
```python
from domain.models import Scenario, Mortgage, Pension, Event
from domain.simulation import simulate

scenario = Scenario(
    name="With Pension",
    monthly_income=45_000,
    monthly_expenses=25_000,
    mortgage=Mortgage(principal=2_250_000, annual_rate=0.04, duration_years=25),
    pension=Pension(initial_value=2_000_000, monthly_contribution=9_000, 
                    annual_growth_rate=0.06, accessible_at_age=67),
    age=41,
    events=[Event(year=2, portfolio_injection=2_000_000, description="Exit")]
)

result = simulate(scenario, years=30)

# Pension is locked until year 27 (age 67), then unlocks
for yd in result.year_data:
    if yd.year == 27:
        print(f"Pension unlocks: {yd.pension_accessible}, value: {yd.pension_value:,.0f}")
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
