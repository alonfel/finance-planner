# Income & Expense Breakdowns Guide

The finance planner now supports **named income and expense components** for detailed financial analysis.

## Quick Start

### Simple Breakdown (JSON)

```json
{
  "name": "Alon - Baseline",
  "monthly_income": {
    "salary": 36000,
    "rsus": 9000
  },
  "monthly_expenses": {
    "rent": 8000,
    "food": 3500,
    "utilities": 1500,
    "childcare": 4000,
    "other": 5000
  },
  "initial_portfolio": 1400000,
  "age": 41,
  "currency": "ILS"
}
```

Output shows breakdown:
```
  Income:   ₪     45,000/month
    salary                 ₪     36,000/month
    rsus                   ₪      9,000/month
  Expenses: ₪     22,000/month
    rent                   ₪      8,000/month
    food                   ₪      3,500/month
    utilities              ₪      1,500/month
    childcare              ₪      4,000/month
    other                  ₪      5,000/month
  Net:      ₪     23,000/month
```

### Backward Compatible (Old Format Still Works)

```json
{
  "name": "Daniel - Baseline",
  "monthly_income": 35000,
  "monthly_expenses": 24000
}
```

Renders without component lines (single `{"income": 35000}` wrapping is transparent to user):
```
  Income:   ₪     35,000/month
  Expenses: ₪     24,000/month
  Net:      ₪     11,000/month
```

## Scenario Node Overrides (Deep Merge)

Child nodes can override **individual components** without redefining the entire breakdown.

### Example: Increase Freelance Income

**Parent scenario:**
```json
{
  "name": "Baseline",
  "monthly_income": {
    "salary": 30000,
    "freelance": 5000
  }
}
```

**Child override:**
```json
{
  "name": "Higher Freelance",
  "parent": "Baseline",
  "monthly_income": {
    "freelance": 15000
  }
}
```

**Result:** Child inherits `salary` from parent, overrides `freelance` to 15000.
- Salary: ₪30,000 (inherited)
- Freelance: ₪15,000 (overridden)
- **Total: ₪45,000**

This enables fine-grained scenario variations without repeating all components.

## Python API

### Create Breakdown from Components

```python
from domain.breakdown import IncomeBreakdown, ExpenseBreakdown

income = IncomeBreakdown({
    "salary": 36000,
    "rsus": 9000,
    "bonus": 5000
})

expenses = ExpenseBreakdown({
    "rent": 8000,
    "food": 3500,
    "utilities": 1500,
    "transport": 2000,
    "entertainment": 1000,
    "other": 2000
})

print(f"Total income: ₪{income.total:,}")      # ₪50,000
print(f"Total expenses: ₪{expenses.total:,}")  # ₪18,000
```

### Deep Merge Components

```python
# Child override
child_income = IncomeBreakdown({"rsus": 12000})

# Merge into parent
merged = income.merge(child_income)
# Result: {"salary": 36000, "rsus": 12000, "bonus": 5000}
print(merged.total)  # ₪53,000
```

### Use in Scenarios

```python
from domain.models import Scenario
from domain.breakdown import IncomeBreakdown, ExpenseBreakdown
from domain.simulation import simulate

scenario = Scenario(
    name="Test",
    monthly_income=IncomeBreakdown({"salary": 40000, "freelance": 10000}),
    monthly_expenses=ExpenseBreakdown({
        "housing": 10000,
        "food": 3000,
        "utilities": 1000,
        "other": 3000
    })
)

result = simulate(scenario, years=20)
print(f"Retires at year {result.retirement_year}")

# Access components
print(f"Income breakdown: {scenario.monthly_income.components}")
print(f"Income total: ₪{scenario.monthly_income.total:,}")
```

## Use Cases

### 1. Income Sensitivity Analysis

Vary one income source while keeping others constant:

```python
from domain.models import Scenario
from domain.breakdown import IncomeBreakdown, ExpenseBreakdown
from domain.simulation import simulate

base_expenses = ExpenseBreakdown({...})

# Test different freelance income levels
for freelance in [5000, 10000, 15000, 20000]:
    income = IncomeBreakdown({
        "salary": 40000,
        "freelance": freelance
    })
    scenario = Scenario(
        name=f"Freelance: ₪{freelance:,}",
        monthly_income=income,
        monthly_expenses=base_expenses
    )
    result = simulate(scenario, years=30)
    print(f"Retire year: {result.retirement_year}")
```

### 2. Expense Breakdown Analysis

Understand which expense categories have the biggest impact:

```python
# Baseline
expenses = ExpenseBreakdown({
    "housing": 10000,
    "food": 3000,
    "childcare": 4000,
    "transport": 1000,
    "other": 2000
})

# Vary housing cost
for housing in [8000, 10000, 12000, 15000]:
    adjusted = ExpenseBreakdown({
        "housing": housing,
        "food": 3000,
        "childcare": 4000,
        "transport": 1000,
        "other": 2000
    })
    # Simulate and compare
```

### 3. JSON Configuration with Deep Merge

In `scenario_nodes.json`, override a specific income component:

```json
{
  "name": "IPO Year 2 - Higher Equity",
  "parent": "IPO Year 2",
  "monthly_income": {
    "equity": 25000
  }
}
```

The child inherits salary and bonus from parent, but RSUs/equity is overridden.

## Design Details

### Internal Representation

Scenario always stores income/expenses as breakdown objects:
- `Scenario.monthly_income: IncomeBreakdown`
- `Scenario.monthly_expenses: ExpenseBreakdown`

When loading from JSON:
- **Dict format** → parsed as-is into breakdown components
- **Flat number** → auto-wrapped as `{"income": amount}` or `{"expenses": amount}`

### Simulation

The core simulation logic uses `.total` property:
```python
annual_income = scenario.monthly_income.total * 12
annual_expenses = scenario.monthly_expenses.total * 12
```

Component breakdown is metadata — not stored in YearData, only used for display.

### Display

When printing scenario header:
- **Multiple components** → Show each component as indented line item
- **Single component** → Show only the total (backward compatible with flat format)

Example output with multiple:
```
  Income:   ₪     50,000/month
    salary                 ₪     40,000/month
    freelance              ₪     10,000/month
```

Example output with single (backward compat):
```
  Income:   ₪     50,000/month
```

### Backward Compatibility

✅ Old JSON with flat numbers works unchanged  
✅ Old Python code expecting floats will need `IncomeBreakdown(...)` wrapping (type change)  
✅ Simulation results unchanged (same totals)  
✅ Display degrades gracefully for single-component scenarios  

## Component Naming Conventions

No forced naming — use labels that match your financial reality:

**Income examples:**
- `salary`, `wage`
- `freelance`, `consulting`, `gig`
- `rental`, `dividend`, `interest`
- `bonus`, `stock_options`, `rsu`
- `side_business`, `passive`

**Expense examples:**
- `rent`, `mortgage`, `housing`
- `food`, `groceries`
- `utilities`, `electricity`, `water`
- `childcare`, `education`
- `transport`, `car`, `public_transit`
- `healthcare`, `insurance`
- `entertainment`, `dining`
- `personal`, `clothing`, `haircut`
- `misc`, `other`

## Troubleshooting

### "monthly_income must be a number or dict"

The parser encountered an unexpected type. Ensure your JSON has:
```json
"monthly_income": 45000            // number
// or
"monthly_income": {"salary": 45000}  // object
```

Not:
```json
"monthly_income": "45000"  // string ✗
"monthly_income": [45000]  // array ✗
```

### Deep merge not working in ScenarioNode

Ensure child node specifies only the components to override, not the full breakdown:

```json
// ✓ Correct: Child overrides just freelance
{
  "name": "Child",
  "parent": "Parent",
  "monthly_income": {"freelance": 15000}
}

// ✗ Wrong: Child repeats salary (should be inherited)
{
  "name": "Child",
  "parent": "Parent",
  "monthly_income": {"salary": 40000, "freelance": 15000}
}
```

The second approach works but defeats the purpose of deep merge — it replaces instead of merging.

## Examples

See `data/profiles/alon/scenarios.json` for a complete example with income/expense breakdowns.

Run:
```bash
FINANCE_PROFILE=alon python analysis/run_simulations.py
FINANCE_PROFILE=alon python analysis/run_analysis.py
```

Output will show component breakdowns in scenario headers.
