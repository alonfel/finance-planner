# Architecture & Design

This document describes the technical design, key decisions, and extension patterns.

---

## Design Philosophy

### 1. Model-First
Data structures drive behavior. Clean models → clean code.

- `Scenario` = all inputs to a financial simulation
- `YearData` = one year's snapshot (income, expenses, portfolio, etc.)
- `SimulationResult` = complete output of one simulation
- `ComparisonResult` = side-by-side comparison of two results

### 2. Pure Functions
- No global state
- No side effects
- `simulate(scenario, years)` is idempotent
- Tests don't need setup/teardown or mocking

### 3. Configuration-Driven
- **Code:** immutable business logic
- **Data:** editable JSON configuration
- Users change behavior by editing JSON, not Python

### 4. Minimal MVP
- Only features needed for MVP
- Clear extension points for future growth
- No premature abstraction

---

## Data Model

### Mortgage
```python
@dataclass
class Mortgage:
    principal: float           # Loan amount
    annual_rate: float         # Annual interest rate (e.g., 0.04 = 4%)
    duration_years: int        # Length of loan (e.g., 25)
    currency: str = "ILS"
    monthly_payment: float = field(init=False)  # Computed
```

**Design notes:**
- Monthly payment computed in `__post_init__` using standard amortization
- `principal / monthly_payment ≈ duration_years * 12` (for sanity checks)
- Formula handles zero-interest case gracefully
- Currency included for multi-currency support (future use)

### Scenario
```python
@dataclass
class Scenario:
    name: str                        # Human-readable label
    monthly_income: float
    monthly_expenses: float
    mortgage: Optional[Mortgage]     # None = no mortgage
    initial_portfolio: float = 0.0   # Starting invested assets
    return_rate: float = 0.07        # Annual return (7% default)
    withdrawal_rate: float = 0.04    # Safe withdrawal rate (4% rule)
    currency: str = "ILS"
```

**Design notes:**
- `mortgage` is optional — easily supports scenarios with/without mortgages
- `initial_portfolio` allows modeling existing wealth
- `return_rate` is nominal (not inflation-adjusted) — typical for financial planning
- `withdrawal_rate` implements the "4% rule" for retirement planning
- All fields are immutable (no methods, no state mutations)

### YearData
```python
@dataclass
class YearData:
    year: int                  # 1-indexed (year 1 = first year)
    income: float              # Annual gross income
    expenses: float            # Annual expenses (including mortgage if active)
    net_savings: float         # income - expenses
    portfolio: float           # End-of-year portfolio after growth
    required_capital: float    # Annual expenses / withdrawal_rate
    mortgage_active: bool      # Is mortgage payment included this year?
```

**Design notes:**
- `year` is 1-indexed (not 0-indexed) for human readability
- `expenses` includes mortgage payments when active (simplified view)
- `portfolio` is end-of-year value after growth/losses
- `required_capital` = capital needed to sustain retirement (at 4% withdrawal rate)
- `mortgage_active` is redundant with time but useful for debugging/display
- All derived values computed in the simulation loop, not stored in models

### SimulationResult
```python
@dataclass
class SimulationResult:
    scenario_name: str              # From scenario.name
    year_data: list[YearData]       # Year 1..N
    retirement_year: Optional[int]  # First year where portfolio ≥ required_capital
```

**Design notes:**
- Retirement is detected during simulation (first crossing)
- If never detected within N years, `retirement_year = None`
- All data immutable after creation
- Ready for JSON serialization (all native Python types)

### ComparisonResult
```python
@dataclass
class ComparisonResult:
    scenario_a_name: str
    scenario_b_name: str
    retirement_year_a: Optional[int]
    retirement_year_b: Optional[int]
    retirement_year_difference: Optional[int]  # B - A (None if either is None)
    final_portfolio_a: float
    final_portfolio_b: float
    final_portfolio_difference: float          # B - A
    years_simulated: int
```

**Design notes:**
- Retirement difference is **signed** (positive = B retires later)
- Portfolio difference is **signed** (negative = B has less)
- `retirement_year_difference = None` if either scenario never retires (not comparable)
- All fields enable easy reporting/comparison

---

## Simulation Engine

### Function: `simulate(scenario: Scenario, years: int = 40) -> SimulationResult`

**Input:** Scenario definition + time horizon
**Output:** Year-by-year results + retirement year

**Algorithm:**

```python
portfolio = scenario.initial_portfolio
retirement_year = None

for year_num in range(1, years + 1):
    # Annual amounts
    annual_income = scenario.monthly_income * 12
    annual_expenses = scenario.monthly_expenses * 12
    
    # Mortgage active if year <= duration
    if scenario.mortgage and year_num <= scenario.mortgage.duration_years:
        annual_expenses += scenario.mortgage.monthly_payment * 12
        mortgage_active = True
    else:
        mortgage_active = False
    
    # Core simulation
    net_savings = annual_income - annual_expenses
    portfolio = (portfolio + net_savings) * (1 + scenario.return_rate)
    required_capital = annual_expenses / scenario.withdrawal_rate
    
    # Retirement check
    if portfolio >= required_capital and retirement_year is None:
        retirement_year = year_num
    
    # Record
    year_data.append(YearData(...))

return SimulationResult(scenario_name, year_data, retirement_year)
```

**Key decisions:**

1. **Portfolio grows after adding savings, not before**
   - `(portfolio + savings) * (1 + return)` not `portfolio * (1 + return) + savings`
   - Makes intuitive sense: you earn interest on new savings too
   - Mathematically: applies return to end-of-year balance

2. **Required capital uses current year's expenses**
   - Not peak/maximum expenses
   - After mortgage ends, required capital drops
   - Reflects reality: retirement costs less after debt paid

3. **Mortgage payment is annual obligation in expenses**
   - Simplified view (no amortization schedule detail)
   - `mortgage.monthly_payment * 12` added to annual expenses
   - Easy to understand, sufficient for scenario comparison

4. **Return rate is compounded annually**
   - Typical for financial planning models
   - Input `return_rate=0.07` means 7% annual return
   - Compound formula: `portfolio * (1 + 0.07)` each year

5. **Retirement is first crossing (not average)**
   - First year where `portfolio >= required_capital`
   - Not dependent on future years (one-way check)
   - Conservative: assumes you retire immediately

---

## Configuration Loading

### scenarios.py: Load Scenarios from JSON

```python
def load_scenarios(path: Path) -> dict[str, Scenario]:
    """Load all scenarios, keyed by name."""
    with open(path) as f:
        data = json.load(f)
    return {s["name"]: _scenario_from_dict(s) for s in data["scenarios"]}
```

**Design:**
- Returns `dict[str, Scenario]` — keyed by scenario name for easy lookup
- Handles optional fields with defaults (e.g., `initial_portfolio` defaults to 0)
- Constructs `Mortgage` objects from nested JSON
- Safe defaults: `return_rate=0.07`, `withdrawal_rate=0.04`, `currency="ILS"`

**JSON Schema:**
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

### OutputConfig (settings.py)

```python
@dataclass
class OutputConfig:
    """Configuration for scenario parameter display in output."""
    show_fields: List[str] = field(default_factory=lambda: [
        "income_expenses",
        "mortgage_details",
        "events",
        "rates_settings"
    ])
```

**Design:**
- Ordered list of field names to display in scenario headers
- Valid field names: `"income_expenses"`, `"mortgage_details"`, `"events"`, `"rates_settings"`
- Remove a field to hide it; reorder to change display order
- Enables flexible, user-configurable output without code changes

### settings.py: Load Settings from JSON

```python
@dataclass
class Settings:
    years: int = 40  # Default fallback
    return_rate: float = 0.07
    withdrawal_rate: float = 0.04
    output: OutputConfig = field(default_factory=OutputConfig)

def load_settings(path: Path) -> Settings:
    """Load simulation and output settings."""
    with open(path) as f:
        data = json.load(f)
    sim = data.get("simulation", {})
    output_data = data.get("output", {})
    return Settings(
        years=sim.get("years", 40),
        return_rate=sim.get("return_rate", 0.07),
        withdrawal_rate=sim.get("withdrawal_rate", 0.04),
        output=OutputConfig(
            show_fields=output_data.get("show_fields", [...defaults...])
        )
    )
```

**Design:**
- `"simulation"` key holds simulation parameters
- `"output"` key holds display configuration (new)
- Provides defaults if JSON is incomplete
- `SETTINGS = load_settings()` loaded at import time
- `SETTINGS.years`, `SETTINGS.output.show_fields` used throughout

**JSON Schema:**
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

---

## Comparison & Insights Layer

The insights layer separates **computation from presentation**, enabling both programmatic access and flexible output formats.

### Insight Data Models (comparison.py)

Structured insight types (Union):

```python
@dataclass
class RetirementInsight:
    """When does each scenario retire?"""
    scenario_name: str
    retirement_year: Optional[int]
    years_simulated: int

@dataclass
class RetirementDeltaInsight:
    """How much does one scenario delay retirement?"""
    scenario_a_name: str
    scenario_b_name: str
    year_difference: int

@dataclass
class PortfolioInsight:
    """How different are final portfolios?"""
    scenario_a_name: str
    scenario_b_name: str
    final_portfolio_a: float
    final_portfolio_b: float
    difference: float
    years_simulated: int
    currency_symbol: str = "₪"

@dataclass
class MortgageInsight:
    """When is mortgage active, and how does it impact savings?"""
    scenario_name: str
    first_mortgage_year: int
    last_mortgage_year: int
    avg_net_savings_during_mortgage: float
    currency_symbol: str = "₪"

Insight = Union[RetirementInsight, RetirementDeltaInsight, PortfolioInsight, MortgageInsight]
```

**Design:**
- Each insight is a typed, named object (not free-form strings)
- Can be processed programmatically (inspect, analyze, reformat)
- Enables future output formats (JSON, charts, etc.)
- Separates interpretation (build_insights) from presentation (format_insights)

### Function: `build_insights(result_a, result_b) -> List[Insight]`

**Inputs:** Two `SimulationResult` objects
**Output:** List of structured insight objects

**Algorithm:**
1. Create `RetirementInsight` for scenario A
2. Create `RetirementInsight` for scenario B
3. If both retire: create `RetirementDeltaInsight` showing difference
4. Create `PortfolioInsight` showing final portfolio comparison
5. If either has mortgage: create `MortgageInsight` for each

**Design:**
- Pure function: same input → same output
- No string formatting (separates concerns)
- Ready for any presentation layer
- Handles edge cases (one scenario never retires, etc.)

### Function: `format_insights(insights: List[Insight]) -> str`

**Input:** List of insight objects
**Output:** Human-readable text

**Algorithm:**
- Dispatch on each insight type using `isinstance()`
- Format each insight as text paragraph
- Combine into single multi-line string

**Design:**
- Pure text generation (no side effects)
- Reads from typed objects (type-safe)
- Easy to modify output format without changing build_insights
- Multiple formatters possible (text, JSON, HTML, etc.)

### Function: `generate_insights(result_a, result_b) -> str`

**Convenience function:**
```python
def generate_insights(result_a, result_b) -> str:
    return format_insights(build_insights(result_a, result_b))
```

**Design:**
- One-liner composition
- Preserves backward compatibility
- Users can call either `build_insights()` (for programmatic access) or `generate_insights()` (for text)

---

## Output & Display

### Scenario Parameter Headers

Scenario input parameters (income, expenses, mortgage, events, rates) are displayed in configurable headers using the `show_fields` list in `settings.json`.

### Function: `print_scenario_header(scenario, settings)`

**Input:** Scenario object + Settings object
**Output:** Formatted text block showing scenario parameters

**Display fields (conditional on show_fields):**

| Field name | Content |
|---|---|
| `"income_expenses"` | Monthly income, monthly expenses, net monthly savings |
| `"mortgage_details"` | Principal, annual rate, duration, computed monthly payment |
| `"events"` | List of events: year, description, amount (with +/− sign) |
| `"rates_settings"` | Return rate, withdrawal rate, simulation years, scenario age |

**Design:**
- Reads `settings.output.show_fields` list
- Only displays fields in the list
- Order matches list order
- Currency formatting using scenario's currency
- Works in both `main.py` and `compare_all_scenarios.py`

**Configuration Example:**

```json
{
  "output": {
    "show_fields": [
      "income_expenses",
      "mortgage_details"
    ]
  }
}
```

This would show only income/expenses and mortgage (hide events and rates).

---

## Analysis Layer: Decoupled Simulation & Analysis

The analysis system decouples simulation (expensive) from analysis/output (fast), enabling rapid iteration on visualizations and reports without re-running scenarios.

### Two-Step Workflow

**Step 1: `run_simulations.py` — Simulate & Cache**

```python
# run_all_simulations(all_nodes: Dict) -> Dict[str, Dict]
# - Iterates through all ScenarioNode objects
# - Resolves each node via .resolve(all_nodes)
# - Calls simulate(scenario, years=20)
# - Converts each SimulationResult to JSON-serializable dict
# - Saves to simulation_cache.json with timestamp
```

**Key functions:**
- `simulation_result_to_dict(result)` — Serializes SimulationResult to dict
- `year_data_to_dict(year_data)` — Serializes YearData to dict
- `save_cache(results, path)` — Writes JSON with metadata

**Output:** `simulation_cache.json`
```json
{
  "generated_at": "2026-04-12T08:52:19.653433",
  "num_scenarios": 8,
  "results": {
    "Alon Baseline": {
      "scenario_name": "Alon Baseline",
      "retirement_year": 16,
      "year_data": [
        {"year": 1, "income": 540000, "expenses": 325000, ...},
        // ... years 2-20
      ]
    },
    // ... 7 more scenarios
  }
}
```

**Step 2: `run_analysis.py` — Load Cache & Analyze**

```python
# load_cache(path) -> Optional[Dict]
# - Reads simulation_cache.json
# - Returns results dict or None if missing

# dict_to_simulation_result(data: Dict) -> SimulationResult
# - Reconstructs SimulationResult from cached dict
# - Rebuilds YearData objects
# - Maintains object structure for handlers

# analyze(analysis_config, cached_results)
# - Dispatches to type-specific handler
# - Handler uses cached results instead of simulating
# - Produces formatted output (graphs, tables, insights)
```

### Architecture Benefits

| Benefit | How |
|---------|-----|
| **Fast iteration** | Edit analysis.json, re-run Step 2 (~1s vs ~2s to re-simulate all) |
| **Consistent results** | Same cache used across multiple analyses |
| **Programmatic access** | Load cache.json directly to process raw data |
| **Fallback safety** | If cache missing, run_analysis.py simulates inline |
| **Version control** | Cache included in git (41KB, human-readable JSON) |

### Handler Pattern

Each analysis type has a handler that accepts cached results:

```python
def handle_milestone_snapshots(
    analysis: Dict,
    all_nodes: Dict[str, ScenarioNode],
    cached_results: Dict[str, SimulationResult] = None
):
    """
    Load cached results and produce analysis output.
    
    If cached_results provided: use it (fast)
    If cached_results missing: simulate inline (slow but works)
    """
    results = {}
    for scenario_info in scenarios:
        node = all_nodes[node_name]
        
        # Try cache first
        if cached_results and node.name in cached_results:
            result = cached_results[node.name]
        else:
            # Fallback: simulate
            resolved = node.resolve(all_nodes)
            result = simulate(resolved, years=20)
        
        results[label] = result
    
    # Produce output using results
    plot_scenarios_graph(results)
    print_milestone_table(results, milestones, metrics)
```

### When to Re-Simulate

Re-run `run_simulations.py` when:
- ✅ Adding new scenario nodes to `scenario_nodes.json`
- ✅ Changing scenario parameters (income, expenses, mortgage, events)
- ✅ Modifying simulation settings (return_rate, withdrawal_rate, years)
- ✅ Needing fresh results after upstream changes

Don't re-simulate when:
- ❌ Changing analysis output format (edit analysis.json, re-run analysis)
- ❌ Adding new analyses (same scenarios, different groupings)
- ❌ Modifying graphs/tables (same results, different display)

### Storage Hierarchy

```
scenario_nodes.json  (scenario tree definitions)
      ↓
run_simulations.py   (resolve + simulate)
      ↓
simulation_cache.json (raw results, JSON-serialized)
      ↓
run_analysis.py      (load cache, format output)
      ↓
analysis.json        (define what to analyze)
```

Each layer is independent: changing analysis doesn't re-run simulation.

---

## Extension Patterns

### Pattern 1: Add a Scenario Field

**Goal:** Add inflation adjustment

**Steps:**

1. **Update `Scenario` model** (models.py)
   ```python
   @dataclass
   class Scenario:
       # ... existing fields ...
       inflation_rate: float = 0.0  # New field
   ```

2. **Update loader** (scenarios.py)
   ```python
   def _scenario_from_dict(d: dict) -> Scenario:
       # ...
       inflation_rate=d.get("inflation_rate", 0.0),
   ```

3. **Update simulation** (simulation.py)
   ```python
   # In the simulation loop, adjust expenses:
   adjusted_expenses = annual_expenses * ((1 + scenario.inflation_rate) ** year_num)
   ```

4. **Add to config** (scenarios.json)
   ```json
   {
     "name": "Baseline",
     "inflation_rate": 0.02,
     ...
   }
   ```

### Pattern 2: Add a Global Setting

**Goal:** Add default return rate for all scenarios

**Steps:**

1. **Update `Settings`** (settings.py)
   ```python
   @dataclass
   class Settings:
       years: int = 40
       default_return_rate: float = 0.07  # New
   ```

2. **Update loader** (settings.py)
   ```python
   def load_settings(path: Path) -> Settings:
       # ...
       sim = data.get("simulation", {})
       return Settings(
           years=sim.get("years", 40),
           default_return_rate=sim.get("default_return_rate", 0.07),
       )
   ```

3. **Add to config** (settings.json)
   ```json
   {
     "simulation": {
       "years": 20,
       "default_return_rate": 0.06
     }
   }
   ```

4. **Use in code** (main.py, simulation.py)
   - Pass to scenarios or use as fallback

### Pattern 3: Add a Scenario Type (Tree Branching)

**Goal:** Model "what if income changes at year 10?"

**Design:**
```python
@dataclass
class Scenario:
    # ... existing ...
    branches: list[tuple[int, 'Scenario']] = field(default_factory=list)
    # e.g., [(10, scenario_higher_income)]
```

**Simulation logic:**
```python
for year_num in range(1, years + 1):
    # Check if we need to branch
    for branch_year, branch_scenario in scenario.branches:
        if year_num == branch_year:
            scenario = branch_scenario  # Switch scenarios

    # Continue simulation with new scenario...
```

### Pattern 4: Add Events (Irregular Income/Expenses)

**Goal:** Model bonuses, inheritance, emergency expenses

**Design:**
```python
@dataclass
class Event:
    year: int
    income_override: Optional[float] = None
    expense_override: Optional[float] = None
    portfolio_injection: Optional[float] = None
    description: str = ""

@dataclass
class Scenario:
    # ... existing ...
    events: list[Event] = field(default_factory=list)
```

**Simulation logic:**
```python
for year_num in range(1, years + 1):
    # Check for events
    event = next((e for e in scenario.events if e.year == year_num), None)
    if event:
        if event.income_override is not None:
            annual_income = event.income_override
        if event.expense_override is not None:
            annual_expenses = event.expense_override
        if event.portfolio_injection is not None:
            portfolio += event.portfolio_injection

    # Continue as normal...
```

### Pattern 5: Multiple Assets (Different Return Rates)

**Goal:** Model portfolio with 60% stocks (10% return), 40% bonds (3% return)

**Design:**
```python
@dataclass
class Allocation:
    name: str
    weight: float  # 0.0 to 1.0
    return_rate: float

@dataclass
class Scenario:
    # ... either single return_rate OR allocations ...
    allocations: list[Allocation] = field(default_factory=list)
```

**Effective return:**
```python
if scenario.allocations:
    effective_return = sum(a.weight * a.return_rate for a in scenario.allocations)
else:
    effective_return = scenario.return_rate

portfolio = (portfolio + net_savings) * (1 + effective_return)
```

---

## Testing Strategy

### Unit Tests (tests/test_simulation.py)

**Philosophy:**
- Test behavior, not implementation
- Construct scenarios directly (not from JSON)
- Assert on observable outcomes
- All 29 tests should pass, always

**Coverage areas:**

1. **Mortgage** — Amortization formula
   - Standard case: 1.5M @ 4% for 25 years ≈ 7,916/month
   - Edge case: 0% interest rate
   - Property: payment is always positive

2. **Scenario A** — Baseline (no mortgage)
   - Always positive net savings
   - Portfolio grows monotonically
   - Retirement detected early

3. **Scenario B** — With mortgage
   - Negative/positive savings during/after mortgage
   - Portfolio recovers after mortgage ends
   - Retirement delayed vs. Scenario A

4. **Simulation** — Core engine
   - Retirement is first crossing
   - No retirement if never reaches threshold
   - Year count matches requested
   - Pure function (deterministic)

5. **Events** — Portfolio injections/withdrawals
   - Positive events (stock offerings)
   - Negative events (expenses)
   - Multiple events in one scenario
   - Events compound in same year

6. **Insights** — Structured insight objects
   - RetirementInsight count and correctness
   - RetirementDeltaInsight only when both retire
   - PortfolioInsight difference sign
   - MortgageInsight presence/absence
   - format_insights() output format

---

## File Dependency Graph

```
models.py (no imports from project)
  ↓
scenarios.py (imports models)
scenario_nodes.py (imports models, scenarios)
  ↓
simulation.py (imports models)
  ↓
comparison.py (imports simulation)
  ↓
settings.py (no imports from project)
  ↓
main.py (imports all of above)
compare_all_scenarios.py (imports all of above)
explore_tree.py (imports all of above)

tests/test_simulation.py (imports models, simulation, scenarios, scenario_nodes, comparison)
```

**Key:** No circular dependencies. Clean layering. Scripts (`main.py`, `compare_all_scenarios.py`, `explore_tree.py`) are standalone and import everything above them. `scenario_nodes.py` depends on `scenarios.py` (for resolving base_scenario references).

---

## Performance Considerations

**Current:**
- 40-year simulation: < 1ms
- All 16 tests: < 2ms total
- Fast startup (no external dependencies)

**Scaling:**
- Simulation is O(n) in years (linear)
- Comparison is O(n) in year count (linear)
- Currently no bottlenecks

**Future optimization (not needed now):**
- Batch simulations (parallel runs of many scenarios)
- Caching of intermediate results
- Vectorized computation (numpy, if deps allowed)

---

## Scenario Trees (ScenarioNode)

### Motivation

Instead of defining each scenario independently, **ScenarioNode** enables building complex scenarios through **inheritance**. This makes compounding effects explicit and "what-if" exploration efficient.

**Example:**
```
Baseline (root node)
├─ Buy Apartment (child: add mortgage)
│  └─ Buy Apartment + Exit (grandchild: change income + events)
```

### ScenarioNode Data Model

```python
@dataclass
class ScenarioNode:
    name: str
    base_scenario: Optional[Scenario] = None  # Root nodes only
    parent_name: Optional[str] = None         # Child nodes only

    # Scalar overrides (None = inherit from parent)
    monthly_income: Optional[float] = None
    monthly_expenses: Optional[float] = None
    age: Optional[int] = None
    initial_portfolio: Optional[float] = None
    return_rate: Optional[float] = None
    withdrawal_rate: Optional[float] = None
    currency: Optional[str] = None

    # Mortgage override
    mortgage: Optional[Mortgage] = None

    # Event composition
    event_mode: str = "append"                 # "append" | "replace"
    events: list[Event] = field(default_factory=list)

    def resolve(self, all_nodes: dict[str, "ScenarioNode"] = None) -> Scenario:
        """Resolve node into flat Scenario by walking ancestor chain."""
        ...
```

**Design notes:**
- Root nodes: `parent_name=None`, `base_scenario` set
- Child nodes: `parent_name="SomeName"`, `base_scenario=None`
- `resolve(all_nodes)` walks parent chain and merges overrides root-to-leaf
- Event merging: "append" accumulates events, "replace" discards ancestors
- `Person = ScenarioNode` alias for backward compatibility

### Resolution Algorithm

For each node in the ancestor chain (root → leaf):
1. Apply scalar overrides via `dataclasses.replace()` (None values skipped)
2. Apply event merge:
   - If `event_mode="replace"`: `accumulated_events = node.events`
   - If `event_mode="append"`: `accumulated_events += node.events`

**Example:**
```
Root:  base_scenario.events=[E1]       → accumulated=[E1]
Child: event_mode="append", events=[E2] → accumulated=[E1, E2]
Grand: event_mode="replace", events=[E3] → accumulated=[E3]
```

### Validation (at load time)

- **Cycle detection:** No node can be its own ancestor
- **Parent validation:** All `parent_name` references must exist in the dict
- **Root validation:** Every ancestor chain must lead to a root with `base_scenario`

### Usage Example

```python
from scenario_nodes import load_scenario_nodes
from simulation import simulate

nodes = load_scenario_nodes()
resolved = nodes["Alon - Buy Apartment + Exit"].resolve(nodes)
result = simulate(resolved, years=20)
```

### Files

- **scenario_nodes.py** — Loader + validator + tree resolution
- **scenario_nodes.json** — Tree definitions
- **explore_tree.py** — Interactive exploration script
- **SCENARIO_TREE_GUIDE.md** — User guide + examples

---

## Extensibility Roadmap

**Phase 1 (MVP)** ✅ — Complete
- Single scenario timeline
- Fixed income/expenses
- One mortgage per scenario

**Phase 2** ✅ — Complete
- Events (bonuses, inheritance, emergencies)
- Structured insights layer (build_insights + format_insights)
- Configurable output display (show_fields)
- Comprehensive pairwise analysis (compare_all_scenarios.py)

**Phase 3** ✅ — Complete
- Scenario trees with inheritance (ScenarioNode)
- Event composition control ("append" vs "replace")
- Full validation + cycle detection
- Up to 3 levels deep

**Phase 4** (Planned)
- Inflation adjustment
- Multiple asset allocations
- Branching at specific years (income changes)

**Phase 4** (Possible)
- Tax modeling
- Retirement spending adjustments (e.g., travel budget drops)
- Monte Carlo simulations (vary returns, inflation)
- Sensitivity analysis (how sensitive to interest rate changes?)
- Tax-efficient withdrawal strategies

---

## Standards & Conventions

### Naming
- `Scenario` — singular, capitalized (class)
- `scenario` — lowercase (variable/parameter)
- `scenarios.json` — plural, lowercase (config file)
- `SCENARIO_A` — all caps (module-level constant)
- `SETTINGS` — all caps (singleton)

### Documentation
- Docstrings on public functions
- Type hints on all function signatures
- Comments explain "why", not "what"

### Testing
- Test class per component (TestMortgage, TestSimulate, etc.)
- Test method name describes behavior (test_scenario_a_always_positive_net_savings)
- One assertion per test (or closely related assertions)

### Formatting
- Standard Python conventions (PEP 8)
- f-strings for formatting
- Dataclasses for data structures (not custom __init__)

---

## When to Extend vs. When to Refactor

### Extend (add capability without changing existing code):
- Add a new field to Scenario ✓ (backward-compatible)
- Add a new validation check ✓
- Add a new insight message ✓

### Refactor (restructure existing logic):
- Change simulation loop algorithm ✓ (if tests still pass)
- Split a large function ✓ (if API doesn't change)

### Don't touch (stable interfaces):
- `simulate(scenario, years)` signature ✗
- `Scenario` dataclass fields ✗ (only add new ones)
- JSON schemas ✗ (versioning needed)

---

## Summary

**This architecture is designed to be:**

1. **Understandable** — data-first, pure functions, single responsibility
2. **Testable** — no global state, easy to mock/construct
3. **Extensible** — clear patterns for adding features
4. **Configurable** — behavior lives in JSON, not code
5. **Maintainable** — minimal code, no over-engineering

All decisions are documented here. Questions? See CLAUDE.md or README.md.
