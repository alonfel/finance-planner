# Scenario Tree: Inheritance-Based Financial Planning

## Overview

The new **ScenarioNode** system enables building complex financial scenarios through inheritance. Instead of defining each scenario independently, you define a base scenario once and extend it with incremental changes.

## Example: The Real Impact

### The Tree Structure
```
Alon Baseline (root)
├─ Monthly income: ₪45,000
├─ Monthly expenses: ₪25,000
├─ Age: 41
│
└─ Alon - Buy Apartment (child)
   ├─ Inherits: income ₪45K, expenses ₪25K, age 41
   ├─ Adds: mortgage ₪2.25M @ 4%
   ├─ Adds: down payment fee -₪200K (year 1)
   │
   └─ Alon - Buy Apartment + Exit (grandchild)
      ├─ Inherits: everything from parent + mortgage
      ├─ Overrides: income → ₪35K
      ├─ Replaces events: ignores down payment, adds ₪5M exit (year 2)
```

## Simulation Results Over 20 Years

| Scenario | Retirement Year | Final Portfolio | Key Impact |
|----------|-----------------|-----------------|-----------|
| **Baseline** | Year 17 | ₪10.5M | Baseline achieves retirement |
| **+ Buy Apartment** | Never | ₪3.5M | Mortgage prevents retirement within 20 years |
| **+ Exit** | Year 14 | ₪17.1M | Exit proceeds overcome mortgage burden |

### What the Numbers Tell Us

1. **Baseline → Buy Apartment**: -7 years of savings/growth
   - Mortgage interest + payments delay retirement
   - Average annual net savings during mortgage: ₪97K (vs ₪200K without)

2. **Buy Apartment → + Exit**: +3 years accelerated retirement
   - ₪5M exit at year 2 compounds over 18 years at 7% = ₪18.7M
   - Overcomes mortgage burden despite lower salary

3. **What-if: Keep ₪45K salary after exit**: 
   - Accelerates retirement to **Year 11** (vs 14)
   - **₪5.26M additional** in portfolio by year 20
   - This small change compounds due to 1) higher annual savings and 2) longer compounding period

## Why This Matters: Compounding Effects

```
Year 2 (exit event):           ₪5,000,000
After 5 years @ 7%:            ₪7,012,760
After 10 years @ 7%:           ₪9,835,762
After 18 years @ 7% (by yr 20): ₪18,721,871
```

Plus: higher annual income → more savings → compounding on more principal

**Result: Small income decisions create multi-million-shekel outcomes over time.**

## How to Use the Tree

### Load and Simulate
```python
from scenario_nodes import load_scenario_nodes
from simulation import simulate

nodes = load_scenario_nodes()  # Loads scenario_nodes.json
resolved = nodes["Alon - Buy Apartment + Exit"].resolve(nodes)
result = simulate(resolved, years=20)
```

### Compare Scenarios
```python
from comparison import build_insights, format_insights

# Simulate two scenarios
result_a = simulate(nodes["Alon Baseline"].resolve(nodes), years=20)
result_b = simulate(nodes["Alon - Buy Apartment + Exit"].resolve(nodes), years=20)

# Get insights
insights = build_insights(result_a, result_b)
print(format_insights(insights))
```

### Create a New Variation
```python
from models import ScenarioNode, Event

# Create a variation by inheriting from an existing node
variation = ScenarioNode(
    name="My Custom Scenario",
    parent_name="Alon - Buy Apartment",
    monthly_income=50_000,  # Override: higher salary
    event_mode="append",
    events=[Event(year=5, portfolio_injection=-300_000, description="Home renovation")]
)

# Simulate it
all_nodes = {**nodes, "My Custom Scenario": variation}
resolved = variation.resolve(all_nodes)
result = simulate(resolved, years=20)
```

## The Tree System: How It Works

### Inheritance Chain
Every node resolves through its ancestor chain:
1. **Find the root**: Walk `parent_name` links until you find a node with `parent_name=None`
2. **Apply overrides root-to-leaf**: Each node in the chain overrides fields from its parent
3. **Merge events**: Each node controls its event composition via `event_mode`
   - `"append"`: adds events on top of inherited ones
   - `"replace"`: discards ancestor events, starts fresh

### Key Features

**1. Scalar Overrides (income, expenses, age, mortgage)**
```json
{
  "name": "Buy Apartment + Exit",
  "parent": "Alon - Buy Apartment",
  "monthly_income": 35000,  // Override: changes from parent's inherited ₪45K
  "mortgage": null          // Inherit: keeps parent's ₪2.25M mortgage
}
```

**2. Event Composition (controlled per node)**
```json
{
  "name": "Buy Apartment + Exit",
  "event_mode": "replace",  // Start fresh
  "events": [
    {"year": 2, "portfolio_injection": 5000000, "description": "Company exit"}
  ]
  // Note: This DISCARDS the parent's down payment fee
}
```

**3. Validation at Load Time**
- ✓ Cycles detected (A → B → A raises error)
- ✓ Missing parents caught (references that don't exist raise error)
- ✓ Root validation (all chains lead to a root with `base_scenario`)

## Running Examples

### Interactive Exploration
```bash
python explore_tree.py
```
Shows the full tree structure, simulations, and comparisons.

### Query Specific Nodes
```python
python -c "
from scenario_nodes import load_scenario_nodes
from simulation import simulate

nodes = load_scenario_nodes()
for name, node in nodes.items():
    resolved = node.resolve(nodes)
    result = simulate(resolved, years=20)
    print(f'{name}: retire={result.retirement_year}, portfolio=₪{result.year_data[-1].portfolio:,.0f}')
"
```

### Programmatic Variation Testing
```python
# Test a range of mortgage amounts
for principal in [1_500_000, 2_000_000, 2_500_000, 3_000_000]:
    node = ScenarioNode(
        name=f"Apartment ₪{principal:,.0f}",
        parent_name="Alon Baseline",
        mortgage=Mortgage(principal, 0.04, 25)
    )
    # Simulate and check retirement impact
```

## Files

- `scenario_nodes.json` — The scenario tree definition
- `scenario_nodes.py` — Loader + validator + tree resolution logic
- `models.py` — `ScenarioNode` class (unified with `Person`)
- `explore_tree.py` — Interactive exploration script
- `SCENARIO_TREE_GUIDE.md` — This guide

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| 3 levels max | Covers typical use cases (baseline → major event → variation); prevents deep complexity |
| Child controls event mode | Flexible: allows "append" for incremental changes, "replace" for major pivots |
| Validation at load time | Fail fast; detect cycles before simulation |
| `Person = ScenarioNode` alias | Backward compatible with existing code; unified inheritance concept |

## When to Use Inheritance

**Good use cases:**
- ✓ Exploring "what-if" scenarios (buy apartment, get exit, salary change)
- ✓ Comparing major life decisions (baseline → with mortgage → with exit proceeds)
- ✓ Modeling career changes (income bump, job loss, entrepreneurship)
- ✓ Testing portfolio impacts of incremental changes

**Not ideal:**
- ✗ Completely independent scenarios (just define them separately)
- ✗ More than 3-4 levels (structure becomes hard to track)

---

**Key Insight**: The power of the tree is **compounding**. Small changes in Year 2 compound over 18+ years. The scenario tree makes these connections explicit and testable.
