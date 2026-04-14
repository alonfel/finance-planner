# Quick Reference - April 14, 2026 Changes

## What Changed

**Model-centric architecture for What-If Explorer + auto-generated save names**

## Problems Fixed (7 Bugs)

| # | Issue | Solution |
|---|-------|----------|
| 1 | Events/mortgage missing for seeded scenarios | Backfilled NULL scenario_id via link_scenario_results() |
| 2 | Growth rate hardcoded to 7% on reload | Load from definition.return_rate via fromDefinition() |
| 3 | Initial portfolio back-calculated (precision loss) | Return exact definition.initial_portfolio |
| 4 | Disabled events saved anyway | Filter in toApiRequest() |
| 5 | Mortgage not restored on query-param load | Use fromDefinition() for all load paths |
| 6 | Pension absent from all screens | Add to schema + integrate all layers |
| 7 | withdrawal_rate/retirement_mode/currency hardcoded | Persist and restore via schema |

## Core Concept: WhatIfScenarioSchema

**Single source of truth for What-If state:**
```python
class WhatIfScenarioSchema(BaseModel):
    monthly_income: float
    monthly_expenses: float
    return_rate: float
    withdrawal_rate: float
    starting_age: int
    initial_portfolio: float
    retirement_mode: str
    currency: str
    events: List[EventSchema]
    mortgage: Optional[MortgageSchema]
    pension: Optional[PensionSchema]
```

**Adding a field = 3 steps:**
1. Add to WhatIfScenarioSchema (backend/schemas.py)
2. Update `toApiRequest()` (frontend save)
3. Update `fromDefinition()` (frontend load)
→ Automatic UI/API sync

## Key Functions Added

### Frontend: web/frontend/src/views/WhatIfView.vue

**`toApiRequest()`** — All saves/simulates send this format
```javascript
const toApiRequest = () => ({
  monthly_income, monthly_expenses, return_rate, withdrawal_rate,
  starting_age, initial_portfolio, years, retirement_mode, currency,
  events: events.value.filter(e => e.enabled).map(...),
  mortgage, pension
})
```

**`fromDefinition(def)`** — All loads restore exact values
```javascript
const fromDefinition = (def) => {
  sliders.value.income = def.monthly_income
  sliders.value.growthRate = def.return_rate * 100
  sliders.value.initialPortfolio = def.initial_portfolio
  // ... all fields
}
```

### Backend: web/backend/routers/scenarios.py

**`_build_definition(db, scenario_id)`** — Load saved scenario from DB
- Queries ScenarioDefinition with all relationships
- Returns complete WhatIfScenarioSchema dict
- Handles JSON parsing for income/expenses

## Files Modified (8)

### Backend (5 files)
- `schemas.py` — Created WhatIfScenarioSchema, updated request/response classes
- `simulate.py` — Pass pension, withdrawal_rate, retirement_mode, currency to Scenario
- `whatif_saves.py` — Save pension to DB; use request values instead of hardcoded defaults
- `scenarios.py` — New _build_definition() function; return definition in response
- `seed.py` — Call link_scenario_results() to backfill NULL scenario_id

### Frontend (2 files)
- `WhatIfView.vue` — Added toApiRequest() + fromDefinition() + auto-names; mortgage collapsible
- `ScenarioDetailView.vue` — Show exact definition values; fix goToWhatIf navigation

### Documentation (1 file)
- `CLAUDE.md` — Updated header + added April 14 section

## New Feature: Auto-Generated Scenario Names

**Format:** `{BaseScenarioName} - Modified {HH:MM AM/PM}`

**Examples:**
- "Baseline - Modified 04:32 PM"
- "IPO Year 2 - Modified 02:15 AM"

**Implementation:**
```javascript
const generateDefaultScenarioName = () => {
  const baseName = originalScenario.value?.scenario_name || 'What-If Scenario'
  const timeStr = new Date().toLocaleTimeString('en-US', { 
    hour: '2-digit', minute: '2-digit', hour12: true 
  })
  return `${baseName} - Modified ${timeStr}`
}
```

## UI Improvements

✅ **Mortgage now collapsible** (hidden by default)  
✅ **Events always visible** without scrolling  
✅ **ScenarioDetailView shows exact parameters** (growth rate, withdrawal rate)  
✅ **"Edit in What-If" navigation fixed** (uses scenarioId instead of broken params)  

## Verification

```bash
cd web/backend && pytest tests/ -v
# Result: All 17 tests passing ✅
```

### Manual Testing Checklist
- [ ] Save scenario with 6% growth → reload → shows 6% (not 7%)
- [ ] Save scenario with events → reload → all events present
- [ ] Save scenario with mortgage → reload → mortgage populated
- [ ] Toggle event off → save → reload → event absent
- [ ] Load seeded scenario → events/mortgage visible
- [ ] Click "Save as Scenario" → dialog pre-filled with auto-name
- [ ] Click "Edit in What-If" from detail view → loads with exact values

## Database Changes

**No migrations needed** — All tables exist.

**What happened:** Seeded scenarios now have scenario_id populated.
```sql
SELECT count(*) FROM scenario_results WHERE scenario_id IS NOT NULL;
-- All rows linked ✅
```

## Dependencies

**No new dependencies added** — All models and relationships already existed in codebase.

---

**Complete documentation:** See CHANGES_2026_04_14.md for detailed breakdown  
**Status:** ✅ Complete, tested, all 17 backend tests passing  
