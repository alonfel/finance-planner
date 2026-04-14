# Guided Scenario Generator — Complete Plan Summary

**Status:** 🟢 Ready for Implementation  
**Created:** April 14, 2026  
**Estimated Effort:** ~70 hours (3 phases)  

---

## What We've Created

A **complete, actionable, 3-phase implementation plan** for a guided questionnaire that generates financial scenarios.

### 4 Deliverable Documents

1. **GUIDED_SCENARIO_GENERATOR_PLAN.md** (Main architectural plan)
   - Feature breakdown by phase
   - Architecture diagram
   - API contract
   - Success criteria
   - Dependencies & critical path

2. **SPRINT_TASKS.md** (GitHub-ready task list)
   - 23 detailed tasks across 3 phases
   - Acceptance criteria for each task
   - Estimated effort (hours)
   - Task dependencies & critical path
   - Definition of Done checklist

3. **UI_FLOW_MOCKUP.md** (Visual & interaction design)
   - ASCII mockups of all 3 screens
   - Interaction flow diagram
   - CSS/styling notes
   - Accessibility guidelines
   - Responsive design notes

4. **This document** (Summary & next steps)

### 5 Code Files (Drafts)

**Backend:**
- `web/backend/config/questionnaire_config.json` — 10 questions, conditional logic, scoring weights
- `web/backend/config/template_defaults.json` — Alon's defaults for all parameters
- `web/backend/config/evaluation_rules.json` — Success/fail verdicts with messages & hints
- `web/backend/services/scenario_generator.py` — Main service logic (400+ lines)
- `web/backend/routers/generator.py` — FastAPI endpoints (4 endpoints)

**Frontend:**
- `web/frontend/src/components/ScenarioGeneratorModal.vue` — Main modal orchestrator
- `web/frontend/src/components/QuestionnaireForm.vue` — Question display & input handling
- `web/frontend/src/components/QuestionInput.vue` — Reusable input component
- `web/frontend/src/components/ScoreBar.vue` — Progress bar with hints
- `web/frontend/src/components/ResultsScreen.vue` — Results display & save flow

---

## The 3-Phase Roadmap

### Phase 1: MVP End-to-End (16 tasks, ~50 hours)
**Goal:** Working questionnaire → scenario generation → save

✅ **What works:**
- User answers 3-5 basic questions (age, income, expenses, retirement age, initial portfolio)
- Score bar shows data completeness (e.g., "60% complete")
- User clicks "Generate" (can happen anytime, even with partial answers)
- Backend fills missing answers from Alon's defaults
- Scenario runs through simulation
- Results show: retirement year, final portfolio, data quality, and simple verdict
- User can save scenario to database
- New scenario appears in Scenarios view

✅ **What doesn't work yet:**
- Mortgage/pension questions (Phase 2)
- Sensitive verdict verdicts (Phase 3)
- AI-powered insights (Future)

### Phase 2: Full Questionnaire + Scoring (4 tasks, ~10 hours)
**Goal:** All 10 questions + progressive scoring

✅ **What we add:**
- Mortgage questions (amount, rate, years) — optional, conditional
- Pension questions (initial value, contribution) — optional, conditional
- Questions hide/show based on user answers (e.g., "Do you have mortgage?" → if Yes, show mortgage details)
- Scoring refined (still equal weights, but handles conditional questions correctly)
- Results display mortgage/pension status if answered

### Phase 3: Evaluation + Insights (4 tasks, ~10 hours)
**Goal:** Simple verdict logic + hints

✅ **What we add:**
- 4 verdict types applied in order:
  - **🎉 Early retirement:** Year ≤ 50
  - **✅ On track:** 50 < Year < 67
  - **⚠️ Warning:** Year ≥ 67
  - **❌ Alert:** Portfolio depleted
- Color-coded verdict cards (green/amber/red)
- Actionable hints for each verdict

---

## Key Design Decisions

### 1. **Configuration-Driven**
All rules, questions, and defaults live in JSON. No hardcoding. Future changes don't require code deployments.

### 2. **Evolutionary Questionnaire**
- Users can **skip questions** (not required to answer all)
- **Scoring shows progress** (e.g., "40% complete")
- **Conditional visibility** (mortgage details only show if "Yes")
- **Easy to expand** — adding new questions is just JSON edits

### 3. **MVP First**
Phase 1 is a complete, standalone product. User can generate, save, and view scenarios. Mortgage/pension are nice-to-haves added in Phase 2.

### 4. **Reuse Existing Code**
- Uses existing `Scenario` model, `simulate()` function, simulation logic
- Saves via existing `/api/whatif-saves` endpoint
- No database schema changes needed (scenarios already have all fields)

### 5. **Equal-Weight Scoring**
5 required questions = 20% each. Simple, fair, transparent to user.

---

## Critical Path (Start Here)

**If you only do 2 tasks:**
1. **T1.1** — Create config folder + 3 JSON files
2. **T1.2** — Create ScenarioGeneratorService class

After that, backend and frontend can proceed in parallel.

**Sequential tasks (can't skip):**
1. Config folder (T1.1)
2. Service class (T1.2)
3. API endpoints (T1.3-T1.5)
4. Router registration (T1.6)
5. All UI components (T1.7-T1.11 in parallel)
6. Integration (T1.12-T1.13)
7. Testing (T1.14-T1.16)

---

## File Locations (Ready to Use)

### Already Created
```
✅ web/backend/config/questionnaire_config.json
✅ web/backend/config/template_defaults.json
✅ web/backend/config/evaluation_rules.json
✅ web/backend/services/scenario_generator.py
✅ web/backend/routers/generator.py
✅ web/frontend/src/components/ScenarioGeneratorModal.vue
✅ web/frontend/src/components/QuestionnaireForm.vue
✅ web/frontend/src/components/QuestionInput.vue
✅ web/frontend/src/components/ScoreBar.vue
✅ web/frontend/src/components/ResultsScreen.vue
```

### Needs Updates
```
web/backend/main.py           — Add router registration
web/frontend/src/views/WhatIfView.vue — Add "Generate" button + import modal
```

---

## How to Use These Documents

### For Architecture Review
👉 **Read:** `GUIDED_SCENARIO_GENERATOR_PLAN.md`
- Understand the full system
- Review API contract
- Check dependencies

### For Implementation
👉 **Read:** `SPRINT_TASKS.md`
- Start with Phase 1 tasks
- Each task has clear acceptance criteria
- Follow dependencies
- Check off tasks as complete

### For UI/UX
👉 **Read:** `UI_FLOW_MOCKUP.md`
- See all 3 screens (mockups)
- Understand user flow
- CSS/styling guidance
- Accessibility notes

### For Code
👉 **Review:** Code files listed above
- Drafts are ~80% complete
- Some imports may need adjusting
- Follow same pattern for remaining components

---

## Questions to Ask Before Starting

1. **Mortgage sub-questions:** Do we want to collect:
   - Loan amount (required)
   - Interest rate (required)
   - Years remaining (optional, assume 20 default?)

2. **Pension sub-questions:** Same — what details do we need?

3. **Scenario naming:** Auto-generate or user input?
   - Current plan: Auto-generate fallback, user can edit

4. **Error handling:** What if simulation fails?
   - Current: Show error message, allow retry

5. **Logging:** Do we need to log all generated scenarios?
   - Recommended: Yes, for analytics

---

## Success Metrics

### Phase 1 Done When:
- ✅ User can answer 3+ questions
- ✅ Scenario generates from answers + defaults
- ✅ Scenario saves to database
- ✅ New scenario appears in Scenarios view
- ✅ No console errors
- ✅ Manual E2E test passes

### Phase 2 Done When:
- ✅ All 10 questions load
- ✅ Mortgage/pension questions show/hide correctly
- ✅ Scoring displays correct percentage
- ✅ Tests pass

### Phase 3 Done When:
- ✅ All 4 verdict types show correct message
- ✅ Color coding works
- ✅ Hints display
- ✅ E2E tests pass

---

## Future Enhancements (Tickets to Open)

1. **Multi-profile support** — Ask user's name, load different defaults per profile
2. **Scenario comparison** — Generate side-by-side variations (Conservative/Balanced/Aggressive)
3. **What-If integration** — Go directly to sliders after generation
4. **AI insights** — Replace hardcoded rules with AI agent discovery
5. **Export** — Save generated scenario as PDF report
6. **Share** — Generate shareable link to scenario
7. **History** — Show user's past generated scenarios
8. **A/B testing** — Track which question sequences lead to saves

---

## Time Breakdown

```
Phase 1 (MVP):
├── Backend config       2 hours (T1.1)
├── Service logic       8 hours (T1.2)
├── API endpoints       8 hours (T1.3-T1.5)
├── Router register     1 hour  (T1.6)
├── Frontend components 25 hours (T1.7-T1.11)
├── Integration         4 hours  (T1.12-T1.13)
└── Testing             2 hours  (T1.14-T1.16)
    Total Phase 1: ~50 hours

Phase 2:
├── Config expansion    2 hours (T2.1)
├── Form logic          3 hours (T2.2)
├── Scoring test        2 hours (T2.3)
└── Results update      3 hours (T2.4)
    Total Phase 2: ~10 hours

Phase 3:
├── Rules logic         2 hours (T3.1)
├── Color coding        2 hours (T3.2)
├── Hints               1 hour  (T3.3)
└── E2E testing         3 hours (T3.4)
    Total Phase 3: ~8 hours

Documentation: ~4-6 hours

Grand Total: ~70-80 hours (assume 1.5-week sprint)
```

---

## Next Steps

1. **Review this plan** — Ask questions, flag concerns
2. **Decide on phase** — Do Phase 1 first, Phase 2+3 can wait
3. **Assign tasks** — Pick from SPRINT_TASKS.md
4. **Use code drafts** — Refine existing code rather than rewrite
5. **Track progress** — Use GitHub Projects or Linear to track tasks
6. **Test continuously** — E2E test after Phase 1, unit tests for each phase

---

## Summary

You now have:
- ✅ Complete architecture
- ✅ 3 phases with clear milestones  
- ✅ 23 actionable tasks with acceptance criteria
- ✅ 10 code file drafts (80% complete)
- ✅ UI mockups and flow diagrams
- ✅ Configuration format and evolution strategy
- ✅ Time estimates

**You're ready to build. 🚀**

---

## Questions?

Refer to the appropriate document:
- **"How do I build it?"** → SPRINT_TASKS.md
- **"What's the architecture?"** → GUIDED_SCENARIO_GENERATOR_PLAN.md
- **"What should it look like?"** → UI_FLOW_MOCKUP.md
- **"What's the code?"** → Individual .py/.vue files

Good luck! 🎉
