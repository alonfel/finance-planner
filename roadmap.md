# Roadmap

## Phase 1 — Simulation Engine (Completed)

### Feature: Core Simulation Engine

* Status: done
* Description: Deterministic year-by-year portfolio simulation with income, expenses, mortgage, pension

### Feature: Income & Expense Breakdowns

* Status: done
* Description: Named components for income/expenses with deep-merge overrides in ScenarioNode tree

### Feature: Pension Modeling

* Status: done
* Description: Pension fund accumulation with liquid_only and pension_bridged retirement modes

### Feature: One-Time Deterministic Events

* Status: done
* Description: Portfolio injections (positive or negative) at a specific simulation year

### Feature: Historical Returns Integration

* Status: done
* Description: S&P 500, NASDAQ, Bonds, Russell 2000 actual annual returns (1928–2024) with wrap-around

### Feature: Database Persistence

* Status: done
* Description: SQLite via SQLAlchemy; scenario definitions, results, events, mortgages, pensions

### Feature: What-If Explorer

* Status: done
* Description: Real-time slider playground with save-as-scenario and restore exact state

### Feature: Monte Carlo Engine

* Status: done
* Description: 500-trial lognormal return sampling; p5/p50/p95 fan chart; OAT sensitivity analysis

---

## Phase 2 — Probabilistic Events (Completed)

### Feature: ProbabilisticEvent Domain Model

* Status: done
* Description: New domain types for events with multiple weighted outcomes. Each outcome has a year, probability, and portfolio injection. Probabilities across outcomes must sum to 1.0.
* Layer: domain/models.py

### Feature: Simulation Engine — Probabilistic Event Support

* Status: done
* Description: simulate_branches() for deterministic multi-branch runs; Monte Carlo samples one outcome per event per trial using probability weights.
* Layer: domain/simulation.py, domain/monte_carlo.py

### Feature: Backend API + DB Persistence for Probabilistic Events

* Status: done
* Description: Store and retrieve probabilistic events from SQLite. New DB tables, Pydantic schemas, updated save/load endpoints.
* Layer: web/backend

### Feature: Frontend — Probabilistic Event Builder

* Status: done
* Description: UI in What-If Explorer to add/edit probabilistic events. Live probability validation (must sum to 100%).
* Layer: web/frontend/src/views/WhatIfView.vue

### Feature: Frontend — Multi-Branch Results Display

* Status: done
* Description: Chart overlays one colored line per outcome branch; legend shows outcome name + probability. Graceful fallback to single line when no probabilistic events.
* Layer: web/frontend

### Feature: Unified View/Edit Mode (WhatIfView)

* Status: done
* Description: Consolidated ScenarioDetailView + WhatIfView into a single view with two modes. View mode: grayed-out read-only sidebar, "👁️ View Mode" badge, "✏️ Edit" button. Edit mode: full What-If Explorer. All parameters (sliders, events, prob events, mortgage) in sidebar; chart + metrics in main panel.
* Layer: web/frontend/src/views/WhatIfView.vue

---

## Phase 3 — Insight & Analysis Layer

### Feature: Tax Modeling

* Status: planned
* Description: Progressive income tax brackets applied annually during simulation. Taxes reduce net portfolio growth year-by-year. Optional per scenario (backward compatible).
* Layer: domain/models.py, domain/simulation.py, web/backend/schemas.py, WhatIfView.vue
* Inputs: list of (annual_income_threshold, rate) bracket pairs
* Outputs: annual taxes deducted from portfolio; YearData.annual_taxes field
* Dependencies: none (extends simulation engine)
* Acceptance Criteria:
  * TaxBracket dataclass: annual_income_threshold, rate
  * Scenario.tax_brackets: list[TaxBracket] = [] (optional, backward compatible)
  * simulate() applies tax annually: income above threshold taxed at bracket rate
  * YearData gains annual_taxes field (float)
  * API: tax_brackets field in WhatIfScenarioSchema + SimulateRequest
  * UI: collapsible "Tax Brackets" section in sidebar with add/remove bracket rows
  * Tests: single bracket, multi-bracket progressive, zero income, no regression

### Feature: Trade-Off Analysis

* Status: planned
* Description: Given a target (e.g., retire 2 years earlier), compute the required change in each input (e.g., "need +₪3,000/mo income OR -₪2,000/mo expenses"). Surfaces the cheapest path to a goal.
* Layer: domain/sensitivity.py (extend), web/backend, MonteCarloView.vue or new TradeOffView
* Inputs: target outcome (retire by year N, portfolio threshold), baseline scenario
* Outputs: ranked list of inputs with required delta to hit the target
* Dependencies: Tax Modeling (optional — better with taxes in place)
* Acceptance Criteria:
  * Given target retirement year, compute required income increase and required expense decrease
  * Rank by "effort" (absolute delta)
  * Surface top 3 trade-offs in UI as cards: "Retire 2 years earlier by saving ₪2,500 more/month"
  * Tests: trade-off correctly computed for income and expense knobs

### Feature: Allocation Recommendations

* Status: planned
* Description: Suggest an equity/bond split based on time horizon and risk tolerance. Map the recommendation to an expected return rate and show the impact on retirement year.
* Layer: domain/ (new allocations.py), web/backend, WhatIfView.vue
* Inputs: years_to_retirement, risk_tolerance (conservative/moderate/aggressive)
* Outputs: recommended allocation (e.g., 80/20), mapped return rate, delta vs current
* Dependencies: Trade-Off Analysis (optional — can stand alone)
* Acceptance Criteria:
  * AllocationProfile dataclass: equity_pct, bond_pct, expected_return, volatility
  * Three profiles: conservative, moderate, aggressive
  * UI: segmented control in sidebar maps to return rate; shows "Recommended: Moderate (80/20)"
  * Tests: correct expected_return computed per profile; integration with simulate()

---

## Status Summary

* Done: 14
* In Progress: 0
* Planned: 3
