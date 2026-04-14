# Guided Scenario Generator — Implementation Plan

**Status:** Planning Complete — Ready to Build  
**Phases:** 3 (Phase 1: MVP, Phase 2: Full Questionnaire, Phase 3: Evaluation)  
**Target Users:** Quick-start seekers  
**Success Metric:** User answers 5+ questions → generates + saves scenario in < 3 minutes

---

# Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Frontend (Vue 3)                                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ScenarioGeneratorModal.vue                              │ │
│ │  ├─ QuestionnaireForm.vue (display questions)           │ │
│ │  ├─ ScoreBar.vue (data completeness %)                  │ │
│ │  ├─ ResultsScreen.vue (verdict + hints)                 │ │
│ │  └─ SaveScenarioModal.vue (existing, reuse)             │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Backend (FastAPI)                                           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ routers/generator.py                                    │ │
│ │  └─ POST /api/generate-scenario                         │ │
│ │      (answers + profile → scenario + verdict)           │ │
│ │                                                         │ │
│ │ services/scenario_generator.py                          │ │
│ │  ├─ build_scenario_from_answers()                       │ │
│ │  ├─ evaluate_scenario()                                 │ │
│ │  └─ load_config()                                       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ web/backend/config/ (NEW)                               │ │
│ │  ├─ questionnaire_config.json (5 questions)             │ │
│ │  ├─ template_defaults.json (Alon defaults)              │ │
│ │  └─ evaluation_rules.json (success/fail rules)          │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Domain (Pure Logic)                                         │
│  - Scenario construction (use existing Scenario model)      │
│  - Simulation (use existing simulate())                     │
│  - Insights (use existing insights logic)                   │
└─────────────────────────────────────────────────────────────┘
```

---

# Files to Create / Modify

## **Files to Create**

```
web/backend/
├── config/ (NEW FOLDER)
│   ├── questionnaire_config.json
│   ├── template_defaults.json
│   └── evaluation_rules.json
│
├── routers/
│   └── generator.py (NEW)
│
├── services/ (NEW FOLDER)
│   └── scenario_generator.py (NEW)
│
└── schemas.py (MODIFY — add GeneratorRequest/Response)

web/frontend/src/
├── components/
│   ├── ScenarioGeneratorModal.vue (NEW)
│   ├── QuestionnaireForm.vue (NEW)
│   ├── ScoreBar.vue (NEW)
│   └── ResultsScreen.vue (NEW)
│
└── views/
    └── WhatIfView.vue (MODIFY — add "Generate" button)
```

## **Files to Modify**

- `web/backend/main.py` — Register `generator` router
- `web/backend/schemas.py` — Add GeneratorRequest + GeneratorResponse
- `web/frontend/src/views/WhatIfView.vue` — Add "Generate Scenario" button

---

# Config File Schemas

## **1. questionnaire_config.json**

```json
{
  "questions": [
    {
      "id": "age",
      "label": "What age are you today?",
      "type": "number",
      "min": 18,
      "max": 80,
      "default": 42,
      "required": true,
      "weight": 0.20
    },
    {
      "id": "monthly_income",
      "label": "What's your monthly income? (₪)",
      "type": "number",
      "min": 0,
      "max": 500000,
      "default": 45000,
      "required": true,
      "weight": 0.20
    },
    {
      "id": "monthly_expenses",
      "label": "What are your monthly expenses? (₪)",
      "type": "number",
      "min": 0,
      "max": 300000,
      "default": 25000,
      "required": true,
      "weight": 0.20
    },
    {
      "id": "retirement_age",
      "label": "At what age do you want to retire?",
      "type": "number",
      "min": 40,
      "max": 85,
      "default": 55,
      "required": false,
      "weight": 0.20
    },
    {
      "id": "initial_portfolio",
      "label": "How much do you have saved today? (₪)",
      "type": "number",
      "min": 0,
      "max": 50000000,
      "default": 1500000,
      "required": false,
      "weight": 0.20
    }
  ],
  "scenarioNameQuestion": {
    "label": "Give your scenario a name (optional)",
    "placeholder": "e.g., 'Early Retirement', 'Beach Life Plan'"
  }
}
```

## **2. template_defaults.json**

```json
{
  "profile": "alon",
  "defaults": {
    "monthly_income": {
      "salary": 36000,
      "freelance": 5000,
      "other": 4000
    },
    "monthly_expenses": {
      "rent": 8000,
      "food": 3500,
      "utilities": 1500,
      "childcare": 4000,
      "other": 8000
    },
    "mortgage": null,
    "pension": {
      "initial_value": 2000000,
      "monthly_contribution": 9000,
      "annual_growth_rate": 0.06,
      "accessible_at_age": 67
    },
    "return_rate": 0.07,
    "historical_index": "sp500",
    "historical_start_year": null,
    "starting_age": 42,
    "currency": "ILS"
  }
}
```

## **3. evaluation_rules.json**

```json
{
  "rules": [
    {
      "id": "early_retirement",
      "condition": "retirement_year <= 50",
      "verdict": "success",
      "message": "🎉 Early retirement path! You could retire before 50.",
      "hint": "Consider if you want even more flexibility (earlier exit, sabbatical)"
    },
    {
      "id": "on_track",
      "condition": "retirement_year > 50 and retirement_year < 67",
      "verdict": "success",
      "message": "✅ You're on track for retirement in your 50s.",
      "hint": "Small changes to income/expenses could bring this earlier"
    },
    {
      "id": "standard_retirement",
      "condition": "retirement_year >= 67",
      "verdict": "warning",
      "message": "⚠️ Retirement likely at or after 67.",
      "hint": "Consider increasing income or reducing expenses to retire sooner"
    },
    {
      "id": "depleted_portfolio",
      "condition": "final_portfolio <= 0",
      "verdict": "fail",
      "message": "❌ Portfolio depletes before age 100.",
      "hint": "You'll need to increase income, reduce expenses, or save more upfront"
    }
  ],
  "default_verdict": {
    "verdict": "success",
    "message": "✅ Scenario generated successfully.",
    "hint": "Adjust sliders in What-If Explorer to explore variations"
  }
}
```

---

# Task Breakdown by Phase

## **PHASE 1: Core Generator (MVP End-to-End)**

**Goal:** Working questionnaire (3-5 Q's) → scenario generation → save  
**Estimated effort:** ~12-15 tasks

### **Backend Setup**
- [ ] **T1.1** Create `web/backend/config/` folder
- [ ] **T1.2** Create `questionnaire_config.json` with 5 questions (equal weights)
- [ ] **T1.3** Create `template_defaults.json` with Alon's defaults
- [ ] **T1.4** Create `evaluation_rules.json` with simple verdict rules
- [ ] **T1.5** Create `web/backend/services/scenario_generator.py`
  - [ ] `load_config()` — Load all 3 config files
  - [ ] `build_scenario_from_answers(answers, defaults)` — Map answers + defaults → Scenario object
  - [ ] `evaluate_scenario(result)` — Apply rules → (verdict, message, hint)
- [ ] **T1.6** Create `web/backend/routers/generator.py`
  - [ ] `POST /api/generate-scenario` endpoint
  - [ ] Input: `GeneratorRequest` (answers dict)
  - [ ] Output: `GeneratorResponse` (scenario data + verdict + hints + redirect to save)
- [ ] **T1.7** Add `GeneratorRequest` + `GeneratorResponse` schemas to `web/backend/schemas.py`
- [ ] **T1.8** Register generator router in `web/backend/main.py`

### **Frontend Modal**
- [ ] **T1.9** Create `web/frontend/src/components/ScenarioGeneratorModal.vue`
  - [ ] Show/hide logic (modal state)
  - [ ] Question display (one at a time)
  - [ ] Answer input (text/number fields)
  - [ ] "Generate now" button (skip-enabled)
  - [ ] Call `/api/generate-scenario`
- [ ] **T1.10** Create `web/frontend/src/components/ScoreBar.vue`
  - [ ] Display data completeness % (calculated from answered questions)
  - [ ] Update on each answer
- [ ] **T1.11** Create `web/frontend/src/components/ResultsScreen.vue`
  - [ ] Show generated scenario name + metrics
  - [ ] Display verdict + message + hint
  - [ ] "Save Scenario" button → triggers save flow
- [ ] **T1.12** Modify `web/frontend/src/views/WhatIfView.vue`
  - [ ] Add "Generate Scenario" button in sidebar
  - [ ] Open ScenarioGeneratorModal on click
- [ ] **T1.13** Modify `web/frontend/src/views/WhatIfView.vue`
  - [ ] After save, close modal + reload scenario list

### **Testing**
- [ ] **T1.14** E2E Test: Answer 3 questions → Generate → Save works end-to-end
- [ ] **T1.15** Backend Test: Verify answers + defaults = valid Scenario object
- [ ] **T1.16** Verify `/api/generate-scenario` response format matches schema

---

## **PHASE 2: Full Questionnaire + Scoring**

**Goal:** All 5 questions + progressive score display  
**Estimated effort:** ~6-8 tasks

### **Questionnaire Enhancement**
- [ ] **T2.1** Update `questionnaire_config.json` — Add remaining 2 questions (mortgage, pension)
  - Note: Keep 5 questions total (replace age/income/expenses if preferred, or expand)
- [ ] **T2.2** Modify `QuestionnaireForm.vue`
  - [ ] Add conditional logic (e.g., mortgage → show sub-questions)
  - [ ] Implement "skip question" logic
  - [ ] Persist answers in component state across questions

### **Scoring Logic**
- [ ] **T2.3** Update `ScoreBar.vue`
  - [ ] Calculate completeness % based on answered questions
  - [ ] Equal weight: each question = 20% (5 questions)
  - [ ] Display: "40% Complete" or similar
- [ ] **T2.4** Update `GeneratorResponse` schema
  - [ ] Include `data_completeness_score: float` in response
- [ ] **T2.5** Update `evaluate_scenario()` in `scenario_generator.py`
  - [ ] Calculate and return completeness score

### **Testing**
- [ ] **T2.6** Test: Answer 2 Q's → score = 40%
- [ ] **T2.7** Test: Answer all 5 Q's → score = 100%
- [ ] **T2.8** Test: Mortgage conditional logic works

---

## **PHASE 3: Evaluation + Insights**

**Goal:** Simple success/fail verdict + hints  
**Estimated effort:** ~5-6 tasks

### **Evaluation Rules**
- [ ] **T3.1** Enhance `evaluation_rules.json`
  - [ ] Add all verdict types (early_retirement, on_track, standard, depleted)
  - [ ] Add default fallback message
- [ ] **T3.2** Implement `evaluate_scenario()` in `scenario_generator.py`
  - [ ] Load rules from config
  - [ ] Check conditions (retirement_year, final_portfolio)
  - [ ] Return matched rule (verdict, message, hint)

### **Results Display**
- [ ] **T3.3** Update `ResultsScreen.vue`
  - [ ] Show verdict emoji + message
  - [ ] Show hint below metrics
  - [ ] Color-code verdict (green=success, yellow=warning, red=fail)
- [ ] **T3.4** Test: Different scenario outcomes show correct verdict
  - [ ] Early retirement (year < 50) → green
  - [ ] On track (year 50-67) → green
  - [ ] Standard (year ≥ 67) → yellow
  - [ ] Depleted (portfolio < 0) → red

### **Polish & Docs**
- [ ] **T3.5** Document evaluation rules in `config/README.md`
- [ ] **T3.6** Add comments to `scenario_generator.py` for future AI agent integration

---

# API Contract (Reference)

## **POST /api/generate-scenario**

**Request:**
```json
{
  "answers": {
    "age": 42,
    "monthly_income": 45000,
    "monthly_expenses": 25000,
    "retirement_age": 55,
    "initial_portfolio": 1500000,
    "mortgage": null,
    "pension": null,
    "scenario_name": "My Quick Start"
  },
  "profile": "alon"
}
```

**Response (Phase 1):**
```json
{
  "scenario_id": "gen-20260414-1234",
  "name": "My Quick Start",
  "retirement_year": 11,
  "final_portfolio": 8200000,
  "monthly_income": 45000,
  "monthly_expenses": 25000,
  "initial_portfolio": 1500000,
  "data_completeness_score": 1.0,
  "verdict": "success",
  "message": "✅ You're on track for retirement in your 50s.",
  "hint": "Small changes to income/expenses could bring this earlier"
}
```

---

# Dependencies & Critical Path

```
Phase 1 CRITICAL PATH:
T1.1 → T1.2/T1.3/T1.4 (parallel) → T1.5 → T1.6 → T1.7 → T1.8 → T1.9 → T1.10/T1.11 (parallel) → T1.12 → T1.13

Phase 2: Independent, builds on T1.9/T1.10
Phase 3: Builds on T1.6/T1.5 (evaluate_scenario)
```

---

# Success Criteria (Definition of Done)

### **Phase 1 Done**
- [ ] User can answer 3+ questions
- [ ] Scenario generates from answers + defaults
- [ ] Scenario saves to database
- [ ] E2E test passes
- [ ] No console errors

### **Phase 2 Done**
- [ ] All 5 questions appear (skip-enabled)
- [ ] Score bar updates correctly
- [ ] Equal weighting: each Q = 20%
- [ ] Score test passes

### **Phase 3 Done**
- [ ] Verdict appears on results screen
- [ ] All 4 verdict types work
- [ ] Hint text displays
- [ ] Color coding works (green/yellow/red)

---

# Notes for Implementation

1. **Scenario naming:** If user doesn't provide name, auto-generate:
   ```
   "Quick Start - {date} {time}"  # e.g., "Quick Start - April 14, 2026 2:45 PM"
   ```

2. **Equal weighting:** With 5 questions, each = 20%. If user answers 3, score = 60%.

3. **Conditional logic:** Mortgage & Pension should be optional:
   - If user skips mortgage → use `mortgage: null` from defaults
   - If user skips pension → use pension from defaults (or null)

4. **Reuse existing saves:** Call `/api/whatif-saves` endpoint (existing) to save generated scenario. No new save logic needed.

5. **Future AI integration (Phase 3+):**
   - Current evaluation rules are hardcoded
   - Future: Replace `evaluate_scenario()` with AI agent call
   - Keep rule config file format for agent to extend

---

# Questions Before Starting

1. **Phase 1 questions (5 total):** Should all 5 be required in MVP, or allow early exit?
   - Answer: Allow early exit (user can generate with 3 Q's)

2. **Mortgage sub-questions:** If user says "yes" to mortgage, what details do we ask?
   - Loan amount?
   - Annual rate?
   - Years remaining?
   - Or skip mortgage in Phase 1, add in Phase 2?

3. **Pension sub-questions:** Same — if user says "yes", what details?
   - Or use Alon's defaults + add customization in Phase 2?

4. **Ready to implement Phase 1?** Should I:
   - Create a detailed sprint task list (Jira/Linear format)?
   - Draft the actual code files?
   - Create a UI mockup?

---

**This plan is ready to hand to a developer. All ambiguity resolved, all files defined, all tasks clear.**

