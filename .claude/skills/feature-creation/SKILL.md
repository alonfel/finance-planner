---
name: feature-creation
description: Use this skill when the user asks to implement a new feature in the finance planner. Triggers on requests like "add X", "implement Y", "build a feature that does Z". Guides planning + backend-first implementation + basic tests with mandatory user confirmation before coding.
version: 1.0.0
disable-model-invocation: true
---

# Feature Creation Skill

## Purpose

Implement a new financial feature by integrating it cleanly into the existing codebase. This skill is the **first phase** of feature development — it focuses on design validation and happy-path implementation, not production polish.

After this skill completes, use **Feature Finish Cycle** skill to polish and commit.

---

## When to Use This Skill

Invoke `/feature-creation` when the user requests a new feature such as:
- "Add tax bracket modeling"
- "Support currency conversion"
- "Track real estate assets"
- "Add expense categories"
- Any request that extends scenario modeling, calculation, or UI

---

## Architecture Context (Finance Planner 4-Layer)

```
domain/              # Pure business logic, immutable models
infrastructure/      # Parsing, config loading
presentation/        # Output formatting
web/backend/        # FastAPI REST API + SQLite persistence
web/frontend/       # Vue 3 single-page application
```

**Key principles:**
- Models are immutable dataclasses with composition (Scenario has optional Mortgage, Pension)
- Each feature spans multiple layers: domain model → parser → simulation logic → API → UI
- Tests are pure (no mocks) with unittest + subTest for parameterization
- Always reuse existing patterns; don't invent new abstractions

---

## Execution: 5-Phase Workflow

### PHASE 1: PLANNING MODE (MANDATORY — NO CODE YET)

#### Step 1: Understand the Feature Request

Extract the behavioral requirement:
- **What does it do?** (e.g., "calculate taxes annually")
- **When does it matter?** (e.g., "during simulation", "at retirement", "per-event")
- **Is it optional or always present?**
- **Does it have settings?** (e.g., pension has `accessible_at_age`)

Ask clarification if unclear:
- Is this a model field or a calculation?
- Does it affect retirement detection?
- Does it interact with other features?

#### Step 2: Map to Existing Architecture

Identify which layers are affected:

| Layer | How to Extend |
|-------|---|
| **domain/models.py** | Add field to @dataclass or create new sub-dataclass |
| **infrastructure/parsers.py** | Add `parse_X()` function for new types |
| **domain/simulation.py** | Add logic in `simulate()` year loop |
| **web/backend/schemas.py** | Add Pydantic request/response classes |
| **web/backend/routers/** | Add endpoint or modify existing router |
| **web/frontend/src/views/** | Add Vue component or modify view |
| **tests/test_simulation.py** | Add test class with setUp and test methods |

Look for similar features (e.g., "tax" is similar to "withdrawal_rate", "real estate" is similar to "mortgage")
and reuse their abstractions.

#### Step 3: Present Design to User

Show the user your planned architecture:
```
Feature: Tax bracket modeling

Domain Model:
  → Add TaxBracket dataclass
  → Add tax_brackets field to Scenario

Parser:
  → Add parse_tax_brackets() in infrastructure/parsers.py

Simulation:
  → Calculate taxes annually in year loop
  
Tests:
  → TestTaxBrackets with happy path + edge cases

Later (Feature Finish Cycle):
  → API schema updates
  → UI sliders
```

**Ask explicitly:** "Does this approach match your expectation? Any changes before I code?"

Wait for user approval. Do NOT proceed to Phase 2 without it.

---

### PHASE 2: IMPLEMENTATION (Backend First)

After user approval, implement in this order:

#### Step 1: Domain Model (domain/models.py)

Add the core dataclass(es):

```python
@dataclass
class TaxBracket:
    annual_income_threshold: float
    rate: float  # 0.17, 0.20, etc.

# Add to Scenario:
tax_brackets: list[TaxBracket] = field(default_factory=list)
```

**Rules:**
- Use composition for complex features (create sub-dataclass like TaxBracket, don't extend Scenario)
- Always add type hints
- Optional fields → `None` default or `field(default_factory=...)`
- Immutable: no mutations in __init__

#### Step 2: Parser (infrastructure/parsers.py)

Create defensive parsing function:

```python
def parse_tax_brackets(data: list[dict]) -> list[TaxBracket]:
    """Parse tax brackets from JSON, backward compatible."""
    if not data:
        return []
    return [
        TaxBracket(
            annual_income_threshold=item["annual_income_threshold"],
            rate=item["rate"]
        )
        for item in data
    ]
```

**Rules:**
- Handle missing/malformed data gracefully
- Support backward compatibility (old JSON without the field)
- Document with docstring (Args, Returns)
- Place immediately after similar parsers (e.g., after `parse_mortgage`)

#### Step 3: Simulation Logic (domain/simulation.py)

Update the `simulate()` function's year loop:

```python
# In the year loop, after computing annual_expenses:
if scenario.tax_brackets:
    taxes = calculate_annual_taxes(annual_income, scenario.tax_brackets)
    annual_expenses += taxes
```

If calculation is complex, extract to a helper function:

```python
def calculate_annual_taxes(annual_income: float, brackets: list[TaxBracket]) -> float:
    """Calculate total tax from progressive income brackets.
    
    Args:
        annual_income: Gross annual income before taxes
        brackets: List of TaxBracket objects (sorted by threshold)
    
    Returns:
        Total annual tax owed
    """
    total_tax = 0.0
    for bracket in brackets:
        if annual_income > bracket.annual_income_threshold:
            taxable_in_bracket = annual_income - bracket.annual_income_threshold
            total_tax += taxable_in_bracket * bracket.rate
    return total_tax
```

**Rules:**
- Don't refactor unrelated code
- Use targeted edits only
- Add comments only for non-obvious logic
- Use clear variable names (not `ai`, use `annual_income`)

#### Step 4: Output Data (YearData in domain/models.py, if needed)

If users need to see the calculated value (e.g., "annual taxes paid"):

```python
@dataclass
class YearData:
    # ... existing fields ...
    annual_taxes: float = 0.0  # NEW
```

Update simulate() to populate it:

```python
year_data = YearData(
    # ... existing ...
    annual_taxes=taxes if scenario.tax_brackets else 0.0
)
```

---

### PHASE 3: CORE SCENARIOS & TESTING

#### Add Test Class (tests/test_simulation.py)

```python
class TestTaxBrackets(unittest.TestCase):
    def test_single_bracket_below_threshold(self):
        """Income below threshold → no tax."""
        brackets = [TaxBracket(100_000, 0.20)]
        tax = calculate_annual_taxes(50_000, brackets)
        self.assertEqual(tax, 0.0)
    
    def test_single_bracket_above_threshold(self):
        """Income above threshold → tax on excess."""
        brackets = [TaxBracket(100_000, 0.20)]
        tax = calculate_annual_taxes(150_000, brackets)
        self.assertAlmostEqual(tax, 10_000, delta=1)  # 50k * 0.20
    
    def test_multi_bracket_progressive(self):
        """Multiple brackets → cumulative tax."""
        brackets = [
            TaxBracket(100_000, 0.10),
            TaxBracket(200_000, 0.20),
        ]
        tax = calculate_annual_taxes(250_000, brackets)
        self.assertAlmostEqual(tax, 25_000, delta=1)
    
    def test_scenario_with_taxes(self):
        """Full scenario with tax brackets → retirement year affected."""
        scenario = Scenario(
            name="With Taxes",
            monthly_income=IncomeBreakdown({"salary": 100_000}),  # 1.2M annual
            monthly_expenses=ExpenseBreakdown({"expenses": 60_000}),
            tax_brackets=[TaxBracket(100_000, 0.25)],  # 25% above 100k
            starting_age=40,
            initial_portfolio=1_000_000,
        )
        result = simulate(scenario, years=30)
        # Taxes should delay retirement vs scenario without taxes
        self.assertGreater(result.retirement_year, 10)
```

**Rules:**
- Happy path first (typical usage)
- At least one edge case (zero income, below threshold, etc.)
- At least one full scenario test (if it affects simulation)
- Use `subTest` for parameterized cases
- No mocks; use real data

#### Run Tests

```bash
cd /Users/alon/Documents/finance_planner
python -m unittest tests.test_simulation.TestTaxBrackets -v
```

All tests must pass before moving forward.

---

### PHASE 4: MARK TODOs (Don't Finish Them)

Add inline TODO comments for work left to Feature Finish Cycle:

```python
# TODO (Feature Finish Cycle):
#   - Add tax_brackets to SimulateRequest schema (web/backend/schemas.py)
#   - Add tax bracket endpoints to simulate router
#   - Add tax bracket UI sliders to WhatIfView.vue
#   - Validate tax_brackets are sorted by threshold
#   - Add test for overlapping brackets edge case
#   - Update CLAUDE.md with tax modeling documentation
```

---

### PHASE 5: SUMMARY OUTPUT

Return a structured summary for the Feature Finish Cycle skill:

```
## Feature Summary
Implement progressive income tax modeling for scenarios.

## Changes Made

### domain/models.py
- Added TaxBracket dataclass (lines X-Y)
- Added tax_brackets field to Scenario (line Z)

### infrastructure/parsers.py
- Added parse_tax_brackets() function

### domain/simulation.py
- Updated year loop to calculate taxes (lines X-Y)
- Added calculate_annual_taxes() helper function

### domain/models.py (YearData)
- Added annual_taxes field to YearData

### tests/test_simulation.py
- Added TestTaxBrackets class with 4 tests

## Flow Description
1. User defines tax brackets in scenario JSON
2. Parser converts to TaxBracket objects via parse_tax_brackets()
3. Each simulation year: calculate_annual_taxes() applied to annual income
4. Taxes added to annual expenses (reduces portfolio growth)
5. Annual taxes stored in YearData output

## Assumptions
- Tax brackets are provided in sorted order by threshold
- Taxes are applied after all income is earned (not progressive calculation)
- Tax brackets are optional (default to [] for backward compatibility)

## TODOs / Gaps
- Tax bracket validation (must be sorted, no overlaps)
- API schema and endpoints (web/backend/schemas.py, routers/)
- UI controls (WhatIfView.vue, scenario builder)
- CLAUDE.md documentation

## Risks
- If brackets not sorted, tax calculation incorrect (need validation)
- Performance: calculating taxes each year is O(brackets) — negligible
- Backward compatibility: old scenarios without tax_brackets default to [] ✅

## Scenarios Covered
1. ✅ No taxes (tax_brackets = []) — same behavior as before
2. ✅ Single bracket below threshold
3. ✅ Single bracket above threshold (taxes assessed)
4. ✅ Multiple brackets (progressive taxation)
5. ✅ Zero income (no taxes)
6. ✅ Full scenario with taxes delays retirement
```

---

## Golden Rules

1. **Never rewrite large functions** — Use targeted edits only
2. **Always add tests** — At least happy path + one edge case
3. **Never duplicate parsing logic** — Write once, use everywhere
4. **Composition over inheritance** — Create sub-dataclasses
5. **Preserve backward compatibility** — Optional fields default to None or []
6. **Don't guess missing fields** — Ask the user
7. **No over-engineering** — Minimal diff, working solution

---

## Output Checklist

Before moving to Feature Finish Cycle, ensure:

- [ ] Feature request is understood (asked clarifications if needed)
- [ ] Architecture is designed (shown to user and approved)
- [ ] Happy path implemented (backend only, no API/UI yet)
- [ ] Tests written and passing
- [ ] TODOs marked for refinement
- [ ] Summary structured for Feature Finish Cycle
- [ ] User ready for polish phase? Ask: "Should I polish and commit now, or iterate on the design?"

---

## Next Step

After this skill completes and user approves:

1. **If changes needed:** Iterate in this skill (go back to PHASE 1: Understanding)
2. **If ready to ship:** Invoke `/feature-finish-cycle` to polish, test fully, and commit
