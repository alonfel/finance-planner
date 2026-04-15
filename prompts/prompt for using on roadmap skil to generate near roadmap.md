You are a senior system architect and product thinker.

You are helping design a major extension to a financial planning system.

---

## Context

The system currently includes:

* A UI for financial inputs and "what-if" exploration
* Basic financial logic

Missing components:

* Monte Carlo Simulation Engine
* Insight Engine

We are building both from scratch.

---

## Goal

Design an MVP roadmap that enables:

* Probability of success estimation
* Identification of key drivers (return, savings, time)
* Clear insights per user

---

## IMPORTANT — Workflow Integration

This roadmap will NOT be executed directly.

It will be:

1. Converted into roadmap.md
2. Managed using a **Roadmap Manager Skill**
3. Executed via:

   * Feature Creation Skill
   * Feature Completion Skill (feature-finish-cycle)

---

## Your Responsibility

Design the roadmap so it is:

* Compatible with roadmap.md structure
* Easily breakable into features (1–3 days each)
* Aligned with system architecture
* Executable step-by-step using the skills

---

## Process (STRICT)

### Step 1 — Clarify

Ask 5–10 critical questions.

Focus on:

* Existing financial logic
* Data structures
* Expected simulation fidelity
* Time granularity (monthly / yearly)
* Performance expectations
* UI expectations

Do NOT propose solutions yet.

Wait for answers.

---

### Step 2 — Define MVP

Define a **clear MVP**:

Include:

* Minimal Monte Carlo engine
* OAT-based Insight Engine

Exclude:

* Multi-asset allocation
* Optimization
* ML

Define:

* Scope
* Success criteria

---

### Step 3 — Architecture

Define components:

1. Simulation Engine
2. Sensitivity Layer
3. Insight Engine

For each:

* Responsibility
* Inputs / Outputs
* Interfaces

---

### Step 4 — Monte Carlo Design

Provide a minimal design:

* Return model (simple distribution)
* Time steps
* Cash flow modeling
* Portfolio evolution

Keep it simple and replaceable.

---

### Step 5 — Roadmap (Phases)

Create phases aligned with system evolution:

* Phase 1: Simulation Engine
* Phase 2: Insight Engine
* Phase 3: (Optional) Extensions

Each phase includes:

* Goal
* Deliverables
* Risks

---

### Step 6 — Feature-Oriented Roadmap (CRITICAL)

Break phases into features.

Each feature MUST:

* Be 1–3 days of work
* Be independently executable
* Map to a real system component
* Fit Feature Creation + Completion workflow

Include:

* Name
* Description
* Inputs / Outputs
* Dependencies
* Acceptance Criteria
* Status: planned

---

### Step 7 — roadmap.md Compatibility

Ensure output can be directly converted into roadmap.md.

Use consistent structure:

* Phases
* Features
* Status

---

### Step 8 — Handoff to Roadmap Manager Skill

Explicitly structure the roadmap so that:

* A roadmap manager can track it
* Features can be selected sequentially
* Progress can be updated incrementally

---

## Constraints

* Do NOT over-engineer
* Keep simulation simple
* Focus on enabling insights
* Respect architectural layering:
  simulation → insight → decision

---

## Output Format

1. Questions
2. MVP Definition
3. Architecture
4. Monte Carlo Design
5. Roadmap (phases)
6. Features (ready for execution)
7. Notes for roadmap manager

---

## Goal

Produce a roadmap that:

* Can be directly executed using roadmap-manager skill
* Supports iterative development
* Maintains architectural integrity

---

Start with Step 1: Ask your questions only.
