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

## Phase 3 — UI Fixes & Polish

### Feature: Delete Scenario Bug Fix

* Status: planned
* Description: Can't delete seeded scenarios (e.g. "Alon - IPO Year 2") from the Scenarios screen. Root cause: backend delete endpoint restricts to "What-If Saves" run label only, rejecting seeded scenarios with 403. Secondary issue: list_scenarios returns scenario_id (definition ID) as the card ID instead of result.id, causing ID mismatch for both navigation and delete on What-If saved scenarios.
* Layer: web/backend/routers/scenarios.py, web/frontend/src/views/ScenariosView.vue
* Acceptance Criteria:
  * Any scenario can be soft-deleted regardless of run label
  * list_scenarios always returns result.id as the card ID
  * Delete flow completes without error for seeded and What-If saved scenarios

### Feature: Sidebar Full-Height Layout

* Status: planned
* Description: The scenario parameters sidebar only fills ~55% of vertical space; user must scroll to reach bottom controls. Root cause: .sliders-section has max-height: 55vh hard-coded. The sidebar container already scrolls — removing the cap lets the sidebar fill top-to-bottom naturally.
* Layer: web/frontend/src/views/WhatIfView.vue (CSS)
* Acceptance Criteria:
  * Sidebar parameters use full available vertical space
  * Sidebar scrolls smoothly when content overflows
  * No layout regression on different screen sizes

### Feature: Branch Color & Event Label Differentiation

* Status: planned
* Description: When probabilistic events produce branches, all cards look identical with no visual tie between branch and event name. Branch label (e.g. "Success") doesn't show which event it belongs to. Fix: show the event name prominently in each branch card and match the card's left-border color to its chart line color so users can visually trace branch → chart line.
* Layer: web/frontend/src/views/WhatIfView.vue
* Acceptance Criteria:
  * Each branch metric card has a colored left border matching its chart line
  * Event name is shown as a distinct header inside the card (parsed from label)
  * Single-event and multi-event cross-product cases both display correctly

### Feature: Scenarios Screen Cleanup

* Status: planned
* Description: The Scenarios screen has redundant/broken action buttons cluttering the header: "🔮 What-If Explorer" (redundant — users navigate via card clicks) and "✨ Guided Scenario Generator" (non-functional). Remove both; keep "📊 Compare Scenarios" which is the only unique action.
* Layer: web/frontend/src/views/ScenariosView.vue
* Acceptance Criteria:
  * "What-If Explorer" button removed from Scenarios screen
  * "Guided Scenario Generator" button removed from Scenarios screen
  * "Compare Scenarios" button retained
  * No dead imports or unused refs left in the component

---

## Phase 4 — Financial Story Builder

A `FinancialStory` is a tree-structured narrative object: a saveable entity that makes the simulation branching structure explicit. The root is a Scenario (base parameters); events hang off the timeline as nodes — deterministic events continue the single path, probabilistic events split the tree into weighted branches. Long-term this replaces the flat `events`/`probabilistic_events` lists on `Scenario`.

**MVP scope:** All events apply to all branches equally (no branch-specific sub-events). Probabilistic splits are captured explicitly in the tree; cross-product branching matches current `simulate_branches()` behavior.

### Feature: FinancialStory Domain Model

* Status: done
* Description: New domain dataclasses (`StoryOutcome`, `StoryEventNode`, `FinancialStory`) + two converter functions. `story_to_branches()` produces `[(label, probability, Scenario)]` for simulation; `story_to_scenario()` flattens to a single Scenario for backward compat.
* Layer: domain/models.py, domain/simulation.py
* Inputs: `FinancialStory` with base scenario params + ordered `StoryEventNode` list
* Outputs: branch list via `story_to_branches()`; flat `Scenario` via `story_to_scenario()`
* Dependencies: none
* Acceptance Criteria:
  * `StoryOutcome`: label, probability, portfolio_injection
  * `StoryEventNode`: node_id, label, year, event_type ("deterministic"|"probabilistic"), portfolio_injection, outcomes: list[StoryOutcome]
  * `FinancialStory`: name, base_scenario (no events), events: list[StoryEventNode], story_id
  * `ProbabilisticEvent.__post_init__` validation reused for outcome probability sums
  * `story_to_branches()` cross-products probabilistic nodes, applies all deterministic events to every branch
  * `story_to_scenario()` returns flat Scenario (deterministic events only) for backward compat
  * Tests: deterministic-only story, single probabilistic split, two-event cross-product (4 branches), probability validation

### Feature: Story DB Persistence

* Status: planned
* Description: SQLite tables and Pydantic schemas to save/load `FinancialStory`. Stories are owned by a profile, have a name, and store base scenario params + the full event node tree.
* Layer: web/backend/models.py, web/backend/schemas.py, web/backend/routers/stories.py
* Dependencies: FinancialStory Domain Model
* Acceptance Criteria:
  * `financial_stories` table: id, profile_id, name, base_scenario_params (JSON), created_at, updated_at
  * `story_event_nodes` table: id, story_id, node_id, label, year, event_type, portfolio_injection, sort_order
  * `story_outcomes` table: id, node_id, label, probability, portfolio_injection
  * CRUD endpoints: `POST /api/v1/stories`, `GET /api/v1/stories`, `GET /api/v1/stories/{id}`, `PUT /api/v1/stories/{id}`, `DELETE /api/v1/stories/{id}`
  * Round-trip: save → load restores identical `FinancialStory`

### Feature: Story Simulation API

* Status: planned
* Description: Simulate a saved story — converts it to branches via `story_to_branches()` and returns the same `branches[]` response format already used by the What-If simulate endpoint.
* Layer: web/backend/routers/stories.py (extend)
* Dependencies: Story DB Persistence, FinancialStory Domain Model
* Acceptance Criteria:
  * `POST /api/v1/stories/{id}/simulate` accepts optional `years` param
  * Returns `{ branches: [{ label, probability, result }] }` — same schema as WhatIf simulate
  * Single-path stories (no probabilistic nodes) return one branch with probability=1.0
  * Reuses existing `BranchResultSchema`

### Feature: Story Builder UI

* Status: planned
* Description: New `StoryView.vue` — visual timeline editor. Root card shows scenario base params; events appear as timeline nodes. Deterministic nodes show as single cards; probabilistic nodes render as a split with probability badges on each branch. Users can add/remove/reorder nodes and trigger simulation to see the multi-branch chart.
* Layer: web/frontend/src/views/StoryView.vue (new), web/frontend/src/router/index.js
* Dependencies: Story Simulation API
* Acceptance Criteria:
  * Route `/stories` lists saved stories; `/stories/new` opens builder; `/stories/:id` opens existing
  * Timeline shows root scenario → event nodes in year order
  * Probabilistic node renders as a visual split (N branches, probability badge per branch)
  * "Add event" button inserts deterministic or probabilistic node (type picker)
  * "Simulate" runs `POST /stories/{id}/simulate`; shows multi-branch chart + metric cards (reuses existing branch display components)
  * Save/load round-trip works end-to-end

---

## Phase 5 — Insight & Analysis Layer

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

* Done: 15
* In Progress: 0
* Planned: 10
