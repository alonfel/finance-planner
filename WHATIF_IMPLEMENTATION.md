# What-If Explorer Implementation

**Status:** ✅ Complete and Tested  
**Date:** April 13, 2026

## Overview

Added a new "What-If Explorer" playground feature to the Finance Planner web app. Users can adjust three sliders (income, expenses, growth rate) in real-time and see portfolio projections updated instantly alongside the original scenario.

## Key Features

- **Real-time simulation**: POST requests debounced at 300ms for instant feedback
- **Side-by-side comparison**: Original scenario vs. What-If scenario in ComparisonChart
- **Temporary playground**: No persistence—results are temporary for exploration
- **Slider controls**:
  - Monthly Income: ₪15K–150K (step ₪1K)
  - Monthly Expenses: ₪10K–100K (step ₪1K)
  - Annual Growth Rate: 2%–15% (step 0.5%)

## Files Created/Modified

### Backend

**1. `web/backend/main.py`**
- Added `sys.path.insert()` to enable domain module imports
- Imported and registered `simulate` router
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from routers import simulate
app.include_router(simulate.router)
```

**2. `web/backend/schemas.py`**
- Added `SimulateRequest` model (monthly_income, monthly_expenses, return_rate, starting_age, initial_portfolio, years)
- Added `SimulateResponse` model (scenario_name, retirement_year, final_portfolio, total_savings, year_data)

**3. `web/backend/routers/simulate.py` (NEW)**
- Created POST `/api/v1/simulate` endpoint
- Takes slider values, builds Scenario object, calls `domain.simulation.simulate()`
- Returns year-by-year financial data

### Frontend

**4. `web/frontend/src/router/index.js`**
- Added WhatIfView import
- Added route: `/profiles/:profileId/whatif` → WhatIfView

**5. `web/frontend/src/views/WhatIfView.vue` (NEW)**
- 500+ line Vue component with full What-If Explorer UI
- Sections: Run selector, scenario selector, sliders, comparison chart, metrics cards
- Logic:
  - Fetch runs on mount
  - On run change: fetch scenarios for that run
  - On scenario select: fetch full scenario data, initialize sliders, run initial simulation
  - On slider change: debounce 300ms, POST /simulate, update whatIfResult
  - ComparisonChart receives [originalScenario, whatIfResult] for side-by-side display

**6. `web/frontend/src/views/ScenariosView.vue`**
- Added "🔮 What-If Explorer" button next to "📊 Compare Scenarios"
- Added `goToWhatIf()` method to navigate to What-If page

## Bug Fixes

### Initial Portfolio Calculation (Fixed Apr 13, 2026)

**Problem:** WhatIfView was incorrectly calculating the initial portfolio when initializing sliders from scenario data.

**Original code:**
```js
sliders.value.initialPortfolio = (firstYear.portfolio / 1.07) - (firstYear.net_savings / 12)
```

**Issue:** `firstYear.net_savings` is **ANNUAL**, not monthly. Dividing by 12 created invalid starting portfolio values, causing simulation failures.

**Fixed code:**
```js
sliders.value.initialPortfolio = (firstYear.portfolio / 1.07) - firstYear.net_savings
```

**Why:** Back-calculating portfolio start: `portfolio_start = (portfolio_end / (1 + rate)) - net_savings`  
The annual net_savings should not be divided by 12.

## Architecture

```
User moves slider
  ↓ (300ms debounce)
  ↓
POST /api/v1/simulate {monthly_income, monthly_expenses, return_rate, starting_age, initial_portfolio, years}
  ↓
Backend: Build Scenario → Call simulate() → Return year_data[]
  ↓
Frontend: Store as whatIfResult
  ↓
ComparisonChart renders: [originalScenario, whatIfResult]
  ↓
Metrics cards show side-by-side retirement year and final portfolio
```

## API Endpoint

**POST /api/v1/simulate**

Request:
```json
{
  "monthly_income": 45000,
  "monthly_expenses": 22000,
  "return_rate": 0.07,
  "starting_age": 41,
  "initial_portfolio": 1700000,
  "years": 20
}
```

Response:
```json
{
  "scenario_name": "What-If",
  "retirement_year": 9,
  "final_portfolio": 18685252.38,
  "total_savings": 5520000.0,
  "year_data": [
    {
      "year": 1,
      "age": 42,
      "income": 540000.0,
      "expenses": 264000.0,
      "net_savings": 276000.0,
      "portfolio": 2114320.0,
      "required_capital": 6600000.0,
      "mortgage_active": false,
      "pension_value": 0.0,
      "pension_accessible": false
    },
    ...
  ]
}
```

## Testing Checklist

- ✅ Backend /api/v1/simulate endpoint works (tested with curl + bearer token)
- ✅ Frontend can login and navigate to What-If Explorer
- ✅ Run selector fetches simulation runs
- ✅ Scenario selector populates and loads scenario data
- ✅ Sliders initialize from scenario first year
- ✅ Slider movement triggers debounced simulation
- ✅ ComparisonChart renders both scenarios with correct data
- ✅ Metrics cards display original vs. what-if retirement year and final portfolio
- ✅ Initial portfolio calculation fixed (was dividing annual by 12)

## Usage

1. Navigate: Dashboard → Profile → Scenarios → "🔮 What-If Explorer"
2. Select a simulation run
3. Select a base scenario
4. Sliders auto-initialize from the scenario's first year
5. Move sliders to explore different outcomes
6. Chart updates in real-time (~300ms after slider stops moving)
7. No save functionality—results are temporary for exploration

## Notes

- Uses existing `ComparisonChart` component (no modifications needed)
- Auth token automatically included via `axios.defaults.headers.common['Authorization']`
- Playground philosophy: Temporary exploration, not persistence
- Growth rate slider shows 2–15% (good range for different portfolio strategies)
