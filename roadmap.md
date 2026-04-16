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

## Phase 2 — Probabilistic Events

### Feature: ProbabilisticEvent Domain Model

* Status: done
* Description: New domain types for events with multiple weighted outcomes. Each outcome has a year, probability, and portfolio injection. Probabilities across outcomes must sum to 1.0.
* Layer: domain/models.py
* Inputs: list of (year, probability, amount, description) tuples
* Outputs: ProbabilisticEvent + EventOutcome dataclasses; Scenario.probabilistic_events field
* Dependencies: none (foundation)
* Acceptance Criteria:
  * EventOutcome dataclass: year, probability (float 0–1), portfolio_injection, description
  * ProbabilisticEvent dataclass: name, outcomes (list[EventOutcome])
  * Validation raises ValueError if probabilities don't sum to 1.0 (within 0.001 tolerance)
  * Scenario gains probabilistic_events: list[ProbabilisticEvent] = field(default_factory=list)
  * Unit tests: valid event, bad probabilities, zero outcomes, single outcome

### Feature: Simulation Engine — Probabilistic Event Support

* Status: done
* Description: Extend simulate() and run_monte_carlo() to handle probabilistic events. Deterministic mode runs one simulation per outcome branch (returned as parallel result sets). Monte Carlo mode samples one outcome per event per trial using probability weights.
* Layer: domain/simulation.py, domain/monte_carlo.py
* Inputs: Scenario with probabilistic_events
* Outputs:
  * simulate(): returns list of (outcome_label, SimulationResult) — one per outcome branch
  * run_monte_carlo(): each trial draws one outcome per event; fan chart captures full distribution
* Dependencies: ProbabilisticEvent Domain Model
* Acceptance Criteria:
  * simulate() with 3-branch IPO event returns 3 SimulationResults (one per outcome)
  * Branch with probability=0 is omitted
  * Monte Carlo trial sampling: outcome drawn proportional to probabilities
  * Regression: simulate() with probabilistic_events=[] behaves identically to before
  * Unit tests: 3-branch event produces 3 results; MC distributes outcomes ~proportionally (200 trials)

### Feature: Backend API + DB Persistence for Probabilistic Events

* Status: done
* Description: Store and retrieve probabilistic events from SQLite. New DB tables, Pydantic schemas, and updated save/load endpoints.
* Layer: web/backend
* Inputs: ProbabilisticEventSchema in SaveScenarioRequest / SimulateRequest
* Outputs: scenario_probabilistic_events + scenario_event_outcomes tables; round-trip save/load
* Dependencies: ProbabilisticEvent Domain Model
* Acceptance Criteria:
  * New tables: scenario_probabilistic_events (id, scenario_id, name), scenario_event_outcomes (id, event_id, year, probability, portfolio_injection, description)
  * whatif_saves.py: saves all probabilistic events and outcomes on scenario save
  * scenarios.py: returns probabilistic events when loading a saved scenario definition
  * simulate.py: accepts and passes probabilistic events to domain layer
  * Migration is idempotent (safe to re-run)

### Feature: Frontend — Probabilistic Event Builder

* Status: done
* Description: UI in What-If Explorer to add/edit probabilistic events. Shows one card per event with all outcome branches. Live probability validation (must sum to 100%).
* Layer: web/frontend/src/views/WhatIfView.vue
* Inputs: user-defined event name + N outcome branches (year, %, amount)
* Outputs: probabilistic_events array passed to simulate/save API
* Dependencies: Backend API + DB Persistence for Probabilistic Events
* Acceptance Criteria:
  * Collapsible "Probabilistic Events" section below deterministic events
  * "Add Event" creates a named event with at least 2 outcome rows
  * Each outcome row: year input, probability % input, amount input, description input
  * Live validation: red warning if total probability ≠ 100%; Run button disabled
  * "Add Outcome" / "Remove Outcome" buttons per event
  * "Remove Event" removes entire event
  * State included in toApiRequest() and fromDefinition() for save/load round-trip

### Feature: Frontend — Multi-Branch Results Display

* Status: done
* Description: When probabilistic events are present, the comparison chart overlays one simulation line per outcome branch (instead of a single What-If line). Each branch is labeled with outcome name + probability.
* Layer: web/frontend/src/components/ComparisonChart.vue, WhatIfView.vue
* Inputs: array of (label, year_data[]) from the simulate API
* Outputs: chart with N colored lines (one per branch) + legend showing probability
* Dependencies: Frontend Probabilistic Event Builder
* Acceptance Criteria:
  * Each outcome branch rendered as a distinct colored line on the chart
  * Legend entry format: "IPO ₪1.5M (60%)" with matching color
  * Baseline (original scenario) always shown as reference line
  * Tooltip on hover shows all branch values at that year
  * Retirement year marker shown per branch (if applicable)
  * Graceful fallback: if no probabilistic events, chart shows single What-If line (existing behavior)

---

## Phase 3 — Future Extensions

Placeholder for:
- Allocation recommendations (equity/bond split optimization)
- Trade-off analysis (e.g., "retire 2 years earlier vs ₪500k less spending")
- Scenario comparison view (side-by-side multiple saved scenarios)
- Tax modeling (progressive brackets applied annually)

---

## Status Summary

* Done: 13
* In Progress: 0
* Planned: 0
