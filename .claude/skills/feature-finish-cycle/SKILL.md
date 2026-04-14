---
name: feature-finish-cycle
description: Use this skill when a feature is working but needs polish before merging. Triggers after Feature Creation, or when user says "finish this feature", "clean up and commit", "make this production-ready". Runs mandatory 7-step pipeline with NO SKIPPING.
version: 1.0.0
disable-model-invocation: true
---

# Feature Finish Cycle Skill

## Purpose

Upgrade a partially-implemented feature to production quality and safely commit it.

This is the **second phase** of feature development. It runs a **mandatory 7-step pipeline** with
**no skipping**. Each step must pass before moving to the next.

---

## When to Use This Skill

Invoke `/feature-finish-cycle` when:

1. Feature Creation skill is complete (happy path working, tests pass)
2. User approved the design and said "polish it"
3. Feature needs production quality (full test coverage, validation, documentation, clean commit)

---

## Mandatory 7-Step Pipeline

⚠️ **NO SKIPPING.** Each step must pass before proceeding. This is non-negotiable.

---

### STEP 1: Architecture Validation

**Review the actual code for:**

- ✅ Does it follow existing patterns? (e.g., is TaxBracket similar to Mortgage?)
- ✅ Is it in the correct module? (domain vs infrastructure vs web?)
- ✅ Any duplication vs existing logic?
- ✅ Any unnecessary abstraction? (does TaxBracket need to exist or could it be a dict?)
- ✅ Are defaults correct? (None vs field(default_factory=list))
- ✅ Any mutable defaults in dataclasses? (FORBIDDEN)

**Fix issues BEFORE proceeding.**

Example:

```python
# BAD: Tax logic mixed into simulate()
def simulate(...):
    # ... lots of code ...
    if scenario.tax_brackets:
        for bracket in scenario.tax_brackets:  # ← Logic here is duplicated elsewhere
            ...
    # ... more code ...

# GOOD: Extract to pure function
def calculate_annual_taxes(annual_income: float, brackets: list[TaxBracket]) -> float:
    # Logic once, reused everywhere

# Then in simulate():
taxes = calculate_annual_taxes(annual_income, scenario.tax_brackets)
```

**Stop here if architecture is wrong.** Fix it, then re-run step 1.

---

### STEP 2: Code Quality & Clarity

**Review for:**

- ✅ Variable names clear? (use `annual_income`, not `ai`)
- ✅ Function names describe behavior? (use `calculate_taxes()`, not `compute_tax()`)
- ✅ Type hints complete? (no untyped parameters)
- ✅ Docstrings for public functions? (Args, Returns, Raises)
- ✅ Comments only for non-obvious logic
- ✅ No unnecessary imports or dead code

**Example improvement:**

```python
# Before: unclear
def calc_t(inc, br):
    t = 0
    for b in br:
        if inc > b["threshold"]:
            t += (inc - b["threshold"]) * b["rate"]
    return t

# After: clear
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

**Stop here if code quality needs work.** Fix it, then re-run step 2.

---

### STEP 3: Test Coverage (MANDATORY)

**Review existing tests:**

- ✅ Happy path test(s) work?
- ✅ Edge cases covered? (zero, boundary, off-by-one)
- ✅ Error cases tested? (invalid input, malformed data)
- ✅ Integration test? (full scenario with feature active)
- ✅ Regression test? (scenario without feature behaves same as before)

**Add missing tests** to reach this checklist:

```python
class TestTaxBrackets(unittest.TestCase):
    def test_single_bracket_below_threshold(self):
        """EDGE: Income below threshold → no tax."""
        brackets = [TaxBracket(100_000, 0.20)]
        tax = calculate_annual_taxes(50_000, brackets)
        self.assertEqual(tax, 0.0)
    
    def test_single_bracket_above_threshold(self):
        """HAPPY PATH: Income above threshold → tax on excess."""
        brackets = [TaxBracket(100_000, 0.20)]
        tax = calculate_annual_taxes(150_000, brackets)
        self.assertAlmostEqual(tax, 10_000, delta=1)
    
    def test_multi_bracket_progressive(self):
        """HAPPY PATH: Multiple brackets → cumulative tax."""
        brackets = [
            TaxBracket(100_000, 0.10),
            TaxBracket(200_000, 0.20),
        ]
        tax = calculate_annual_taxes(250_000, brackets)
        self.assertAlmostEqual(tax, 25_000, delta=1)
    
    def test_zero_income(self):
        """EDGE: Zero income → no tax."""
        brackets = [TaxBracket(50_000, 0.20)]
        tax = calculate_annual_taxes(0, brackets)
        self.assertEqual(tax, 0.0)
    
    def test_no_regression_scenario_without_taxes(self):
        """REGRESSION: Scenario without taxes behaves same as before."""
        scenario = Scenario(
            name="No Taxes",
            monthly_income=IncomeBreakdown({"salary": 100_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 50_000}),
            tax_brackets=[],  # No taxes
            starting_age=40,
            initial_portfolio=1_000_000,
        )
        result = simulate(scenario, years=20)
        # Should match known-good result from before feature
        self.assertEqual(result.retirement_year, 11)
    
    def test_scenario_with_taxes_affects_retirement(self):
        """INTEGRATION: Taxes delay retirement vs no-tax scenario."""
        scenario_no_tax = Scenario(
            name="No Taxes",
            monthly_income=IncomeBreakdown({"salary": 100_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 60_000}),
            tax_brackets=[],
            starting_age=40,
            initial_portfolio=1_000_000,
        )
        
        scenario_with_tax = Scenario(
            name="With Taxes",
            monthly_income=IncomeBreakdown({"salary": 100_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 60_000}),
            tax_brackets=[TaxBracket(100_000, 0.25)],
            starting_age=40,
            initial_portfolio=1_000_000,
        )
        
        result_no_tax = simulate(scenario_no_tax, years=30)
        result_with_tax = simulate(scenario_with_tax, years=30)
        
        # Taxes should delay retirement
        self.assertGreater(result_with_tax.retirement_year, result_no_tax.retirement_year)
```

**Run all tests:**

```bash
cd /Users/alon/Documents/finance_planner
python -m unittest tests.test_simulation.TestTaxBrackets -v
```

**All tests must pass.** If not, fix the implementation (NOT the tests), then re-run.

**Stop here if tests fail.** Fix code, re-test, then continue.

---

### STEP 4: Documentation

**Add doc ONLY for:**

- Public functions with non-obvious behavior
- Model fields that aren't self-explanatory
- Configuration JSON structure (in CLAUDE.md if user-facing)

**Don't document:**

- Simple getters or obvious code
- Self-explanatory variable names

**Example — if feature is user-facing, update CLAUDE.md:**

```markdown
### Tax Modeling

Scenarios can include optional progressive income tax brackets:

```json
{
  "tax_brackets": [
    { "annual_income_threshold": 100000, "rate": 0.10 },
    { "annual_income_threshold": 200000, "rate": 0.20 }
  ]
}
```

**Behavior:**
- Taxes are calculated year-by-year during simulation
- Income below first threshold → no tax
- Income above threshold → tax on excess at that bracket's rate
- Multiple brackets are cumulative (progressive taxation)

**Example:** Annual income of ₪250,000 with brackets above:
- ₪100,000 @ 10% = ₪10,000
- ₪100,000 @ 20% = ₪20,000
- Total tax: ₪30,000
```

---

### STEP 5: Self-Review Checklist

✅ Verify each item before proceeding:

- [ ] Code integrates cleanly with existing code? (no hidden coupling)
- [ ] Any naming conflicts or shadowed variables?
- [ ] Any unnecessary imports?
- [ ] Defaults safe? (no mutable defaults in dataclasses)
- [ ] Error handling matches existing patterns?
- [ ] Any potential regressions? (test passes for scenario without feature)
- [ ] Performance acceptable? (no O(n²) loops)
- [ ] Backward compatibility preserved? (old scenarios still work)

**If any item is ❌, fix it before Step 6.**

---

### STEP 6: User Verification (MANDATORY STOP ✋)

**Show the user what you changed, and ask for approval.**

Present:

1. **What changed** (minimal diff summary)
2. **What the feature does** (behavior examples)
3. **What tests cover it** (test names + coverage)
4. **Ask explicitly:**

```
I've completed the production-ready version of tax bracket modeling:

## Changes Made

**domain/models.py**
- Added TaxBracket dataclass
- Added tax_brackets field to Scenario

**infrastructure/parsers.py**
- Added parse_tax_brackets() function

**domain/simulation.py**
- Added calculate_annual_taxes() helper
- Updated year loop to apply taxes

**tests/test_simulation.py**
- Added TestTaxBrackets with 6 tests (all passing)
- Coverage: happy path, edge cases, integration, regression

## Behavior

Tax brackets are optional. If provided, taxes are calculated annually:
- Income below first threshold → no tax
- Income above threshold → tax on excess at bracket's rate
- Multiple brackets cumulative (progressive)

Example: Income ₪250k with brackets [100k@10%, 200k@20%]
→ Tax = (100k × 10%) + (100k × 20%) = ₪30k

## Tests Passing

✅ test_single_bracket_below_threshold
✅ test_single_bracket_above_threshold
✅ test_multi_bracket_progressive
✅ test_zero_income
✅ test_no_regression_scenario_without_taxes
✅ test_scenario_with_taxes_affects_retirement

All tests passing, full coverage.

## Questions for You

1. Does this match your expectation of how taxes should work?
2. Should taxes be displayed in simulation results (YearData)?
3. Should tax brackets have validation (sorted, no overlaps)?
4. Ready to commit this? Any changes before I push?
```

**STOP AND WAIT.** Do NOT proceed without explicit user approval.

---

### STEP 7: Git Commit

After user approval, create a clean commit.

**Stage specific files (not everything):**

```bash
cd /Users/alon/Documents/finance_planner
git add domain/models.py
git add infrastructure/parsers.py
git add domain/simulation.py
git add tests/test_simulation.py
# Include CLAUDE.md only if documentation was added
git add CLAUDE.md
```

**Craft commit message:**

```bash
git commit -m "$(cat <<'EOF'
Feature: Progressive income tax modeling

- Add TaxBracket dataclass (domain/models.py)
- Add parse_tax_brackets() parser (infrastructure/parsers.py)
- Integrate tax calculation into simulate() year loop
- Add calculate_annual_taxes() helper function
- Add 6 unit tests covering happy path, edge cases, integration, regression
- Scenario.tax_brackets field is optional (backward compatible)

Behavior: Scenarios can include optional progressive tax brackets. Taxes
are calculated year-by-year during simulation. Income below first threshold
incurs no tax; excess is taxed at appropriate bracket rate. Multiple
brackets are cumulative (progressive taxation).

Tests: TestTaxBrackets covers happy path (single/multi-bracket), edge cases
(zero income, below threshold), integration (full scenario), and regression
(scenario without taxes behaves same as before).

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
EOF
)"
```

**Commit message structure:**
- **Line 1:** `Feature:` or `Fix:` — concise title (under 70 chars)
- **Blank line**
- **Bullet points:** What changed and why
- **Blank line**
- **Behavior section:** What does the feature do?
- **Tests section:** What's tested?
- **Co-author line**

**Do NOT push** without explicit user approval.

---

## Golden Rules (Mandatory)

1. **No skipping steps** — Each step must pass before next. If it fails, fix and re-run.
2. **Ask user before API/UI** — Feature Finish covers domain/tests only. API/UI changes are separate.
3. **User approval is mandatory** — Don't commit without explicit "go ahead"
4. **Tests must all pass** — Never merge failing tests
5. **No refactoring unrelated code** — Stay focused on the feature
6. **Preserve consistency** — Match existing naming, style, patterns
7. **Document only essentials** — Don't over-document

---

## What If Something Fails?

| Step | Fails | Action |
|------|-------|--------|
| 1: Architecture | ❌ | Fix code, re-run step 1 |
| 2: Code Quality | ❌ | Refactor, re-run step 2 |
| 3: Tests | ❌ | Fix implementation or tests, re-run step 3 |
| 4: Documentation | ❌ | Add/update docs, continue to step 5 |
| 5: Self-Review | ❌ | Fix issues, re-run step 5 |
| 6: User Approval | ❌ | Get feedback, iterate back to step 2 |
| 7: Commit | ❌ | Fix staging/message, retry step 7 |

**Never skip back.** If step 6 fails, you loop back to step 2 (quality) with user feedback.

---

## Checklist Before Starting

Ensure you have:

- [ ] Feature working (happy path implemented)
- [ ] Tests passing (from Feature Creation)
- [ ] Summary from Feature Creation (shows what was done)
- [ ] Ready to polish (no major unknowns)

---

## Next Step

After commit is merged:

- Feature is **shipped** 🎉
- If API/UI is needed, that's a **separate Feature Creation** task
- If bugs are found, that's a **separate bugfix** task
