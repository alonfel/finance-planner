# Guided Scenario Generator — Sprint Tasks (GitHub-Ready)

**Epic:** Guided Scenario Generator  
**Status:** Ready for Implementation  
**Target:** Phase 1 (MVP) + Phase 2 + Phase 3  

---

## Phase 1: Core Generator (MVP End-to-End)

### Backend Setup

#### T1.1 Create config directory structure
```
Title: Create backend config directory and files
Type: Setup
Complexity: Trivial
Dependencies: None

Description:
Create web/backend/config/ folder with three JSON config files.

Acceptance Criteria:
- [ ] Folder web/backend/config/ exists
- [ ] questionnaire_config.json exists with 5 questions
- [ ] template_defaults.json exists with Alon defaults
- [ ] evaluation_rules.json exists with success/fail rules
- [ ] All files are valid JSON (can be parsed)
```

#### T1.2 Create ScenarioGeneratorService
```
Title: Implement ScenarioGeneratorService class
Type: Backend
Complexity: Medium
Dependencies: T1.1

Description:
Create web/backend/services/scenario_generator.py with the following classes:
- QuestionnaireConfig: Load and parse questionnaire JSON
- TemplateDefaults: Load and access template defaults
- EvaluationRules: Load and evaluate rules
- ScenarioGeneratorService: Main service coordinating all

Features:
- Load all 3 config files
- Build Scenario from answers + defaults
- Generate scenario names (fallback to timestamp)
- Evaluate results against rules
- Calculate data completeness score

Acceptance Criteria:
- [ ] QuestionnaireConfig class loads questionnaire_config.json
- [ ] get_required_questions() returns correct list
- [ ] calculate_completeness_score(answers) returns 0.0-1.0
- [ ] get_questions_by_section() returns grouped dict
- [ ] TemplateDefaults loads and gets values correctly
- [ ] build_scenario_from_answers() creates valid Scenario
- [ ] Missing answers filled from defaults
- [ ] Mortgage built correctly from answers
- [ ] Pension built correctly from answers
- [ ] Scenario name auto-generated if not provided
- [ ] EvaluationRules evaluates result and returns verdict
- [ ] All rules load and can be evaluated
- [ ] ScenarioGeneratorService.generate() returns dict with scenario, result, completeness, verdict
```

#### T1.3 Create /api/questionnaire/config endpoint
```
Title: Implement GET /api/questionnaire/config endpoint
Type: Backend API
Complexity: Trivial
Dependencies: T1.2

Description:
Create web/backend/routers/generator.py with endpoint to return questionnaire config.

Endpoint:
POST /api/questionnaire/config

Response:
{
  "version": "1.0",
  "questions": [...],
  "sections": {...},
  "scoring": {...}
}

Acceptance Criteria:
- [ ] Endpoint registered in main.py
- [ ] Returns 200 OK with valid config
- [ ] Config matches questionnaire_config.json
- [ ] Response includes version, questions, sections, scoring
```

#### T1.4 Create /api/questionnaire/completeness endpoint
```
Title: Implement POST /api/questionnaire/completeness endpoint
Type: Backend API
Complexity: Trivial
Dependencies: T1.2

Description:
Calculate data completeness score for given answers.

Endpoint:
POST /api/questionnaire/completeness

Request:
{
  "answers": {"age": 42, "monthly_income": 45000},
  "profile": "alon"
}

Response:
{
  "completeness_score": 0.4,
  "percentage": 40,
  "answered_questions": 2,
  "total_required_questions": 5
}

Acceptance Criteria:
- [ ] Endpoint calculates score correctly
- [ ] Returns both decimal (0.0-1.0) and percentage format
- [ ] Returns count of answered vs required questions
```

#### T1.5 Create /api/questionnaire/generate-scenario endpoint
```
Title: Implement POST /api/questionnaire/generate-scenario endpoint
Type: Backend API
Complexity: Medium
Dependencies: T1.2, T1.4

Description:
Generate scenario from questionnaire answers.

Endpoint:
POST /api/questionnaire/generate-scenario

Request:
{
  "answers": {
    "age": 42,
    "monthly_income": 45000,
    "monthly_expenses": 25000,
    ...
  },
  "profile": "alon"
}

Response:
{
  "scenario_id": "gen-123456",
  "name": "My Scenario",
  "retirement_year": 11,
  "final_portfolio": 8200000,
  "monthly_income": 45000,
  "monthly_expenses": 25000,
  "initial_portfolio": 1500000,
  "data_completeness_score": 1.0,
  "verdict": "success",
  "emoji": "✅",
  "message": "You're on track...",
  "hint": "Small changes..."
}

Acceptance Criteria:
- [ ] Validates required answers (age, income, expenses)
- [ ] Returns 400 if required fields missing
- [ ] Builds Scenario from answers + defaults
- [ ] Runs simulation (calls simulate())
- [ ] Evaluates result against rules
- [ ] Returns all required fields
- [ ] Handles mortgage and pension correctly
- [ ] Returns 500 with error message on failure
- [ ] Logs generation (scenario name, retirement year)
```

#### T1.6 Register router in main.py
```
Title: Register generator router in FastAPI app
Type: Backend
Complexity: Trivial
Dependencies: T1.5

Description:
Add generator router to web/backend/main.py

Before:
app = FastAPI()
app.include_router(auth.router)
app.include_router(profiles.router)

After:
app = FastAPI()
app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(generator.router)  # NEW

Acceptance Criteria:
- [ ] Router registered with correct prefix (/api/questionnaire)
- [ ] All three endpoints accessible
- [ ] /api/questionnaire/config returns config
- [ ] /api/questionnaire/completeness calculates score
- [ ] /api/questionnaire/generate-scenario works end-to-end
```

### Frontend UI Components

#### T1.7 Create ScenarioGeneratorModal.vue
```
Title: Implement ScenarioGeneratorModal component
Type: Frontend
Complexity: Medium
Dependencies: None (UI-only)

Description:
Main modal wrapper that manages three-step flow:
1. Questionnaire Form
2. Loading spinner
3. Results screen

Props:
- isOpen: boolean

Emits:
- close
- scenario-saved

Features:
- Load questionnaire config on mount
- Switch between questionnaire/loading/results views
- Handle answer updates (update completeness)
- Call /api/questionnaire/generate-scenario
- Handle save flow (emit to parent)
- Error handling with retry

Acceptance Criteria:
- [ ] Modal renders as overlay with backdrop
- [ ] Config loads when modal opens
- [ ] Three-step flow works (questionnaire → loading → results)
- [ ] Can navigate back to questionnaire from results
- [ ] Closes properly on cancel
- [ ] Loads config from /api/questionnaire/config
- [ ] Calls /api/questionnaire/generate-scenario on "Generate"
- [ ] Shows loading spinner during API call
- [ ] Displays results on success
- [ ] Shows error message on failure, allows retry
- [ ] Emits 'close' on cancel or close button
```

#### T1.8 Create QuestionnaireForm.vue
```
Title: Implement QuestionnaireForm component
Type: Frontend
Complexity: Medium
Dependencies: ScoreBar.vue, QuestionInput.vue

Description:
Displays questionnaire questions grouped by section.

Props:
- config: questionnaire config object
- answers: dict of question_id → value

Emits:
- update-answer: (questionId, value)
- generate: generate scenario from current answers
- close: cancel flow

Features:
- Display questions grouped by section
- Skip-enabled (can generate with incomplete answers)
- Progress bar shows data completeness
- Conditional question visibility
- "Generate Scenario" button (enabled after first question)
- Section headers with descriptions
- Help text under each question

Acceptance Criteria:
- [ ] Questions render grouped by section
- [ ] Sections display in correct order
- [ ] Section headers and descriptions visible
- [ ] Help text displays for all questions
- [ ] Questions are interactive (user can enter values)
- [ ] Score bar updates as answers change
- [ ] Conditional questions hide/show correctly
- [ ] "Generate Scenario" button disabled initially
- [ ] "Generate Scenario" button enabled after first answer
- [ ] "Generate Scenario" button triggers @generate emit
- [ ] Can cancel flow
```

#### T1.9 Create QuestionInput.vue
```
Title: Implement QuestionInput component
Type: Frontend
Complexity: Small
Dependencies: None

Description:
Reusable input component for different question types.

Props:
- question: question object from config
- value: current answer value

Emits:
- update: new value

Supports:
- type: 'number' (with unit display)
- type: 'text'
- type: 'boolean' (toggle Yes/No buttons)

Features:
- Renders appropriate input based on question.type
- Shows unit suffix for numbers (e.g., "₪", "years")
- Toggle buttons for boolean questions
- "Optional" label for non-required fields
- Help text display
- Input validation (min, max for numbers)

Acceptance Criteria:
- [ ] Number input with min/max validation
- [ ] Unit displays correctly (right-aligned)
- [ ] Text input for text questions
- [ ] Toggle buttons for boolean questions
- [ ] "Optional" label shows for optional questions
- [ ] Help text displays below input
- [ ] Placeholder/default value displays
- [ ] @update emitted on input change
- [ ] Numbers parsed correctly
- [ ] Focus styles visible
```

#### T1.10 Create ScoreBar.vue
```
Title: Implement ScoreBar component
Type: Frontend
Complexity: Small
Dependencies: None

Description:
Data completeness progress bar.

Props:
- completenessScore: float 0.0-1.0

Features:
- Visual progress bar
- Percentage display
- Helpful hint text that changes with score level

Score levels:
- 0%: "Answer a few questions to get started"
- 0-40%: "You can generate with this..."
- 40-80%: "Good progress! Answer a few more..."
- 80-100%: "Almost there! Complete remaining..."
- 100%: "Perfect! You're ready to generate"

Acceptance Criteria:
- [ ] Progress bar renders and fills correctly
- [ ] Percentage displays correctly (rounded to int)
- [ ] Hint text updates based on score
- [ ] Animates when score changes
- [ ] Styled with blue gradient
```

#### T1.11 Create ResultsScreen.vue
```
Title: Implement ResultsScreen component
Type: Frontend
Complexity: Medium
Dependencies: None

Description:
Display generated scenario results with verdict and metrics.

Props:
- generationResult: result object from API
- completenessScore: data completeness 0.0-1.0

Emits:
- save: (scenarioName)
- back: go back to questionnaire

Features:
- Large verdict card with emoji, message, hint
- Verdict color-coded (success=green, warning=yellow, fail=red)
- Metrics grid showing 6 key values:
  - Scenario name
  - Retirement year
  - Final portfolio
  - Monthly net (income - expenses)
  - Data completeness %
  - Initial portfolio
- Formatted numbers with thousands separator
- Save button opens nested save modal
- Back button returns to questionnaire

Acceptance Criteria:
- [ ] Verdict card displays with correct emoji
- [ ] Message and hint display
- [ ] Color coding matches verdict
- [ ] Metrics grid displays all 6 values
- [ ] Numbers formatted with ₪ and commas (e.g., ₪1,500,000)
- [ ] Years display as "Year X" format
- [ ] Save button opens nested modal
- [ ] Back button emits @back
- [ ] Save modal pre-fills scenario name
- [ ] Save modal allows editing name
- [ ] Save button in modal calls API and closes
```

#### T1.12 Create SaveScenarioModal.vue (or reuse existing)
```
Title: Integrate save scenario flow
Type: Frontend
Complexity: Small
Dependencies: T1.11

Description:
Allow user to name and save generated scenario.

Note: This may reuse existing save logic from What-If Explorer.
If existing SaveScenarioModal exists, reuse it. Otherwise, create new.

Acceptance Criteria:
- [ ] Accepts scenario name input
- [ ] Pre-fills with generated name
- [ ] Allows editing before save
- [ ] Calls /api/whatif-saves endpoint
- [ ] Handles success (closes modal, updates scenario list)
- [ ] Handles error (shows message, allows retry)
- [ ] Closes on cancel
```

#### T1.13 Add "Generate Scenario" button to WhatIfView
```
Title: Add Generate Scenario button to What-If Explorer sidebar
Type: Frontend
Complexity: Small
Dependencies: T1.7

Description:
Add button to open ScenarioGeneratorModal.

Location: WhatIfView.vue sidebar (near "Save as Scenario" button)

Button:
- Text: "✨ Generate Scenario" or "Generate Scenario"
- Opens: ScenarioGeneratorModal
- Icon: Sparkle or lightbulb

Acceptance Criteria:
- [ ] Button visible in sidebar
- [ ] Opens ScenarioGeneratorModal on click
- [ ] Modal imports and uses generator modal
- [ ] Close button closes modal
- [ ] Can be clicked multiple times
```

### Integration & Testing

#### T1.14 End-to-End Test: Happy Path
```
Title: E2E test - Answer 3 questions → Generate → Save
Type: Test
Complexity: Medium
Dependencies: All of T1

Description:
Manual test (can be automated later):
1. Click "Generate Scenario" button
2. Modal opens, load config
3. Answer: age = 35
4. Answer: income = 50000
5. Answer: expenses = 30000
6. Click "Generate Scenario"
7. Wait for loading
8. See results screen with verdict
9. Click "Save Scenario"
10. Enter name "Test Scenario"
11. Click "Save"
12. Modal closes
13. New scenario appears in Scenarios list

Acceptance Criteria:
- [ ] Modal opens successfully
- [ ] Config loads (questions visible)
- [ ] Answers are accepted
- [ ] Completeness score updates
- [ ] Generate button enabled
- [ ] API call succeeds (/api/questionnaire/generate-scenario)
- [ ] Results display with metrics
- [ ] Verdict shows (success/warning/fail)
- [ ] Save flow works
- [ ] Scenario persisted to database
- [ ] Scenario appears in Scenarios view
- [ ] No console errors
```

#### T1.15 Backend Test: Scenario Building
```
Title: Unit test - build_scenario_from_answers
Type: Test
Complexity: Small
Dependencies: T1.2

Description:
Test that answers + defaults produce valid Scenario.

Test case:
answers = {
  'age': 35,
  'monthly_income': 50000,
  'monthly_expenses': 30000
}

Result should:
- Scenario.age = 35
- Scenario.monthly_income.total = 50000
- Scenario.monthly_expenses.total = 30000
- Scenario.initial_portfolio = 1500000 (from defaults)
- Scenario.return_rate = 0.07 (from defaults)
- Scenario.pension is set (from defaults)

Acceptance Criteria:
- [ ] Test passes
- [ ] Scenario object valid
- [ ] Simulation can run on result
```

#### T1.16 Backend Test: Evaluation Rules
```
Title: Unit test - evaluate_scenario
Type: Test
Complexity: Small
Dependencies: T1.2

Description:
Test that rules are applied correctly.

Test cases:
1. retirement_year = 11 → verdict = "success", message contains "on track"
2. retirement_year = 70 → verdict = "warning", message contains "67"
3. final_portfolio = -1 → verdict = "fail", message contains "depleted"

Acceptance Criteria:
- [ ] All test cases pass
- [ ] Verdict object has required fields
- [ ] Rules load and evaluate correctly
```

---

## Phase 2: Full Questionnaire + Scoring

#### T2.1 Add mortgage and pension questions to config
```
Title: Expand questionnaire with mortgage & pension questions
Type: Config
Complexity: Small
Dependencies: Phase 1 complete

Description:
Update questionnaire_config.json to include:
- has_mortgage (boolean)
- mortgage_amount (number)
- mortgage_annual_rate (number)
- mortgage_years (number)
- has_pension (boolean)
- pension_initial (number)
- pension_monthly_contribution (number)

All mortgage/pension questions conditional (visible_when rules).

Acceptance Criteria:
- [ ] 5 new questions added
- [ ] visible_when conditions correct
- [ ] Weights updated (equal distribution)
- [ ] Config is valid JSON
```

#### T2.2 Update QuestionnaireForm conditional logic
```
Title: Implement conditional question visibility
Type: Frontend
Complexity: Small
Dependencies: T2.1

Description:
Enhance isQuestionVisible() to handle conditional questions.

Visibility rules:
- mortgage_amount shows only if has_mortgage === true
- mortgage_annual_rate shows only if has_mortgage === true
- mortgage_years shows only if has_mortgage === true
- pension_initial shows only if has_pension === true
- pension_monthly_contribution shows only if has_pension === true

Acceptance Criteria:
- [ ] Mortgage questions hidden by default
- [ ] Mortgage questions show when user selects "Yes"
- [ ] Mortgage questions hide when user selects "No"
- [ ] Pension questions conditional
- [ ] Questions animate in/out (slide transition)
- [ ] Logic handles nested conditions
```

#### T2.3 Verify scoring with all 10 questions
```
Title: Test equal-weight scoring with full questionnaire
Type: Test
Complexity: Small
Dependencies: T2.1, T2.2

Description:
Test scenarios:
- Answer 1 question → 10% score
- Answer 5 questions → 50% score
- Answer all 10 → 100% score
- Skip mortgage/pension sub-questions → still 100% if required parent answered

Acceptance Criteria:
- [ ] Scoring tests pass
- [ ] Percentage displays correctly
- [ ] Completeness endpoint returns correct score
```

#### T2.4 Update ResultsScreen to show all metrics
```
Title: Display additional metrics in results
Type: Frontend
Complexity: Small
Dependencies: T2.3

Description:
If user answered mortgage/pension questions, display:
- Has mortgage: yes/no
- Has pension: yes/no
- (Optionally mortgage payment, pension value at retirement)

Acceptance Criteria:
- [ ] Metrics grid shows mortgage/pension status if provided
- [ ] Formatted cleanly
```

---

## Phase 3: Evaluation + Insights

#### T3.1 Implement evaluation rule matching
```
Title: Complete evaluate_scenario() logic
Type: Backend
Complexity: Small
Dependencies: Phase 1 complete

Description:
Test all 4 verdict types:
- early_retirement (retirement_year <= 50)
- on_track (50 < retirement_year < 67)
- standard_retirement (retirement_year >= 67)
- depleted_portfolio (final_portfolio <= 0)

Acceptance Criteria:
- [ ] All 4 rules evaluate correctly
- [ ] First matching rule returns
- [ ] Default verdict if no rules match
- [ ] Verdict object has emoji, message, hint
```

#### T3.2 Update ResultsScreen color coding
```
Title: Implement verdict color-coding in UI
Type: Frontend
Complexity: Small
Dependencies: T3.1

Description:
Color code verdict cards:
- success (green #16a34a): Early retirement, on track
- warning (amber #f59e0b): Standard retirement
- fail (red #dc2626): Depleted portfolio

Acceptance Criteria:
- [ ] Background color changes by verdict
- [ ] Text color readable on all backgrounds
- [ ] Emoji visible
- [ ] Message and hint display clearly
```

#### T3.3 Add hint text to results
```
Title: Display actionable hints in results
Type: Frontend
Complexity: Trivial
Dependencies: T3.1

Description:
Show hint text below verdict message.

Example hints:
- "Consider increasing income or reducing expenses"
- "Small changes to income/expenses could bring this earlier"

Acceptance Criteria:
- [ ] Hint displays under message
- [ ] Font size smaller than message
- [ ] Color distinct (gray)
- [ ] Actionable language
```

#### T3.4 Test all verdict paths
```
Title: E2E test - All verdict types
Type: Test
Complexity: Medium
Dependencies: T3

Description:
Create scenarios that hit each verdict type:
1. Early retirement: Age 40, income ₪60k, expenses ₪20k
   → Should show "Success! Early retirement"
2. On track: Age 42, income ₪45k, expenses ₪25k
   → Should show "You're on track"
3. Standard: Age 50, income ₪30k, expenses ₪28k
   → Should show "Warning. Standard retirement age"
4. Depleted: Age 55, income ₪20k, expenses ₪25k
   → Should show "Alert. Portfolio depleted"

Acceptance Criteria:
- [ ] All 4 verdicts show correct message
- [ ] Color coding matches verdict type
- [ ] Hints are relevant and actionable
```

---

## Cross-Phase Tasks

#### T-Config Documentation
```
Title: Document config file formats and evolution strategy
Type: Documentation
Complexity: Small
Dependencies: All phases

Description:
Create web/backend/config/README.md explaining:
- questionnaire_config.json format and how to add questions
- template_defaults.json format and how to add profiles
- evaluation_rules.json format and how to add rules
- Future: how to add new question types
- Future: how to support conditional sub-questions
- Future: how to add multi-language support

Acceptance Criteria:
- [ ] README covers all 3 config files
- [ ] Examples provided for adding new questions
- [ ] Change scenarios documented (e.g., changing question type)
- [ ] Notes on evolutionary design
```

#### T-API Documentation
```
Title: Document API endpoints
Type: Documentation
Complexity: Small
Dependencies: All API endpoints

Description:
Add OpenAPI/Swagger documentation to /api/questionnaire/config, /completeness, /generate-scenario endpoints.

Acceptance Criteria:
- [ ] Endpoints documented in OpenAPI schema
- [ ] Request/response examples provided
- [ ] Error codes documented
- [ ] Visible in /docs page
```

---

# Task Dependencies & Critical Path

```
Legend: ▓ = Critical path, → = depends on

PHASE 1 CRITICAL PATH:
T1.1 (Create config) → T1.2 (Service) → T1.3/T1.4/T1.5 (APIs) → T1.6 (Register) ✓

Parallel after T1.1:
T1.7 (ScenarioGeneratorModal) + T1.8 (QuestionnaireForm) + T1.9 (QuestionInput) + T1.10 (ScoreBar) + T1.11 (ResultsScreen)

Final integration:
T1.12 (Save flow) → T1.13 (Add button to What-If) → T1.14 (E2E test)

PHASE 2:
T2.1 (Expand config) → T2.2 (Update form) → T2.3 (Test) → T2.4 (Results)

PHASE 3:
T3.1 (Rules) → T3.2 (Colors) → T3.3 (Hints) → T3.4 (E2E test)
```

# Estimation

| Phase | Tasks | Estimated Hours | Notes |
|-------|-------|-----------------|-------|
| 1     | 13    | 40-50           | MVP, most work in backend + Vue |
| 2     | 4     | 10-12           | Config + conditional logic |
| 3     | 4     | 8-10            | Rules + styling |
| Docs  | 2     | 4-6             | Config + API docs |
| **Total** | **23** | **62-78** | ~2 weeks for 1 developer |

---

# Acceptance Criteria (Definition of Done)

## Phase 1 Complete
- [ ] All 6 backend tasks done (config + service + 3 APIs + registration)
- [ ] All 7 frontend tasks done (modal + form + inputs + score + results)
- [ ] Integration task done (button in sidebar)
- [ ] All tests passing (backend unit tests + E2E test)
- [ ] No console errors, no warnings
- [ ] Manual test successful (generate + save works end-to-end)

## Phase 2 Complete
- [ ] Questionnaire expanded to 10 questions
- [ ] Conditional logic working (mortgage/pension show/hide)
- [ ] Scoring correct (equal weights)
- [ ] Results display mortgage/pension info if provided
- [ ] All tests passing

## Phase 3 Complete
- [ ] All 4 verdict types working
- [ ] Results screen color-coded
- [ ] Hints display and are actionable
- [ ] All E2E tests passing

---

# Notes for Implementation

1. **Start with Phase 1** — It's a complete vertical slice (backend + frontend working together)
2. **Config-first approach** — Spend time getting the JSON structure right. Changes later are cheap.
3. **Evolutionary design** — Mortgage/pension questions are optional in Phase 1; add in Phase 2
4. **Reuse existing code** — Use existing Scenario model, simulate(), insights
5. **Error handling** — Show user-friendly error messages, allow retry
6. **Logging** — Log scenario generation (for monitoring)
7. **Testing** — Manual E2E test first, automate later if needed

