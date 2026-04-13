# Changelog

All notable changes to the Finance Planner project are documented here.

---

## [April 13, 2026] - Pension Bridge Implementation Fixed

### Major Bug Fixes

#### Pension Bridge Not Working
- **Issue:** ScenarioNode inheritance tree was not transferring `pension` and `retirement_mode` fields to resolved Scenario objects
- **Symptoms:**
  - Pension scenarios showed `pension_value: 0.0` (no accumulation)
  - Pension-bridged retirement mode not being applied; all scenarios defaulted to "liquid_only"
  - Pension bridge retirement years were identical to non-bridged versions
- **Root Cause:** Two missing components:
  1. `ScenarioNode` class lacked `pension` and `retirement_mode` fields (even though they were documented)
  2. `parse_scenario_node()` parser did not read these fields from JSON
  3. `ScenarioNode.resolve()` did not transfer these fields during inheritance chain resolution
- **Solution:**
  1. Added `pension: Optional[Pension]` field to ScenarioNode dataclass
  2. Added `retirement_mode: Optional[str]` field to ScenarioNode dataclass
  3. Updated `parse_scenario_node()` to parse both fields from JSON and pass to ScenarioNode constructor
  4. Updated `ScenarioNode.resolve()` to explicitly transfer both fields in override application loop
  5. Re-ran all simulations; pension-bridged scenarios now produce correct results

### File Changes

| File | Change | Lines |
|------|--------|-------|
| `domain/models.py` | Added `pension` and `retirement_mode` fields to ScenarioNode class | 79-91, 140-141 |
| `domain/models.py` | Updated resolve() to transfer pension and retirement_mode in field merge loop | 126, 140-141 |
| `infrastructure/parsers.py` | Added parsing for `pension` and `retirement_mode` in parse_scenario_node() | 177-197 |

### Behavior Changes

#### Before Fix
```
Scenario: "Alon - Baseline + Pension (Bridged: Retire at 55)"
  Retirement Year: 11 (same as liquid_only)
  Pension Value (Year 20): ₪0.0 (not accumulating)
  retirement_mode applied: "liquid_only" (default)
```

#### After Fix
```
Scenario: "Alon - Baseline + Pension (Bridged: Retire at 55)"
  Retirement Year: 12 (one year later; stricter validation)
  Pension Value (Year 20): ₪10,606,000 (accumulating correctly)
  retirement_mode applied: "pension_bridged" (from JSON)
```

### Verification

All 7 Alon scenarios now show correct behavior:
- **Alon - Baseline:** Year 11 (liquid_only)
- **Alon - Baseline + Pension:** Year 11 (liquid_only, pension unlocks at 67)
- **Alon - Baseline + Pension (Bridged: Retire at 55):** Year 12 (pension_bridged)
- **Alon - Baseline + Pension (Bridged: Retire at 60):** Year 12 (pension_bridged)
- **Alon - IPO Year 2:** Year 6 (liquid_only)
- **Alon - IPO Year 2 + Pension:** Year 6 (liquid_only)
- **Alon - IPO Year 2 + Pension (Bridged):** Year 9 (pension_bridged)

Cache regenerated: `2026-04-13T10:25:28.999029`

### Documentation Updated

- **CLAUDE.md** — Added bug fix explanation and pension bridge mode documentation
- **domain/DOMAIN.md** — Documented retirement modes and ScenarioNode inheritance fixes
- **infrastructure/CONFIG.md** — Updated parse_scenario_node() documentation with pension/retirement_mode fields

---

## [April 13, 2026] - Alon Profile Simplified

### Changes

- **Removed 5 pension scenario variants** from `data/profiles/alon/scenario_nodes.json`
  - "Alon - Baseline + Pension"
  - "Alon - Baseline + Pension (Bridged: Retire at 55)"
  - "Alon - Baseline + Pension (Bridged: Retire at 60)"
  - "Alon - IPO Year 2 + Pension"
  - "Alon - IPO Year 2 + Pension (Bridged)"
- **Kept 2 core scenarios:**
  - "Alon - Baseline" → Retire Year 11 (age 52)
  - "Alon - IPO Year 2" → Retire Year 6 (age 47)

### Rationale

Simplified profile for streamlined analysis. Pension scenarios can be restored: `git checkout data/profiles/alon/scenario_nodes.json`

### Updated Analysis Config

- `data/profiles/alon/analyses/config.json` — Changed from pension impact analysis to baseline vs exit comparison
- Removed analyses: "alon_pension_impact", "alon_baseline_comparison"
- Added analysis: "alon_baseline_vs_exit"

---

## [April 13, 2026] - Reports Generated

### New Reports

- **ALON_FINANCIAL_REPORT_2026_UPDATED.md** — Comprehensive 20+ page financial analysis with:
  - Executive summary
  - Current financial position (₪45K income, ₪25K expenses, ₪1.4M liquid, ₪2M pension)
  - 7-scenario detailed analysis (before simplification)
  - Retirement timeline comparisons
  - Risk sensitivities
  - Strategic recommendations
  - Age 67+ lifetime sustainability analysis
  - Year-by-year tables

---

## Previous Versions

### [January 2026] — Initial Feature Implementation

- Implemented Income/Expense Breakdowns with named components
- Implemented Pension model with accumulation logic
- Implemented Scenario inheritance tree (ScenarioNode)
- Implemented configuration-driven analysis system
- Implemented profile-based data layer
- Created comprehensive documentation (DOMAIN.md, CONFIG.md, ANALYSIS.md)
- All 42 unit tests passing

### Key Modules

- `domain/breakdown.py` — IncomeBreakdown, ExpenseBreakdown
- `domain/models.py` — Event, Mortgage, Pension, Scenario, ScenarioNode
- `domain/simulation.py` — Core simulate() engine with pension support
- `domain/insights.py` — Comparison logic
- `infrastructure/parsers.py` — Dict-to-model parsing
- `infrastructure/loaders.py` — Config file loading
- `infrastructure/data_layer.py` — Profile management
- `presentation/formatters.py` — Output formatting
- `analysis/run_simulations.py` — Batch simulation runner
- `analysis/run_analysis.py` — Configuration-driven analysis dispatcher

---

## Version Information

- **Current Version:** v2.1 (April 13, 2026)
- **Previous Version:** v2.0 (January 2026)
- **Python Version:** 3.9+
- **Dependencies:** None (stdlib only)
- **Test Coverage:** 42 unit tests, all passing

---

## How to Use Changelog

This changelog follows [Keep a Changelog](https://keepachangelog.com/) format.

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for in case of vulnerabilities

---

## Reporting Issues

If you discover a bug or have a feature request:
1. Check existing documentation in CLAUDE.md, domain/DOMAIN.md, and infrastructure/CONFIG.md
2. Review the test suite in tests/test_simulation.py for usage examples
3. Check git history for recent changes: `git log --oneline -20`

---

*Changelog maintained by Claude financial modeling system*
