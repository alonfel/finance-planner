# What-If Explorer — Event Controls

**Status:** ✅ Complete  
**Date:** April 13, 2026  
**Commit:** `e195b9f`

## Overview

Extended What-If Explorer with full event management. Users can now add, adjust, and toggle one-time events (windfalls and expenses) in real-time, seeing immediate portfolio and retirement year changes.

## Features

**Add Events:**
- `[+ Add Windfall]` — Creates event: Year 5, +₪500K, "Stock Windfall"
- `[+ Add Expense]` — Creates event: Year 5, -₪300K, "Major Expense"

**Adjust Events:**
- **Description** — Text input to label event (e.g., "IPO Bonus", "Home Repair")
- **Year Slider** — Range 1–20, step 1 (which simulation year the event occurs)
- **Amount Slider** — Range -₪3M to +₪5M, step ₪50K (portfolio injection)
- **Display Format** — Shows "+₪500K" (windfall) or "-₪300K" (expense)

**Toggle / Remove:**
- **Checkbox** — Enable/disable event without deleting (event excluded from simulation when unchecked)
- **🗑 Button** — Delete event permanently

**Real-Time Updates:**
- All changes debounced 300ms
- Chart updates instantly with event effects
- Retirement year recalculates as events change
- Final portfolio shows impact of all active events

## Architecture

```
User adds/adjusts event
  ↓ (300ms debounce)
  ↓
POST /api/v1/simulate { ...sliders, events: [{year, portfolio_injection, description}] }
  ↓
Backend maps to domain.Event objects → Scenario(events=[...])
  ↓
simulate() applies injection at year N before portfolio growth
  ↓
Event compounds with market returns: portfolio grows from injection amount too
  ↓
Chart shows both scenarios + metrics update
```

## Implementation

### Backend (2 files modified)

**`schemas.py`**
```python
class EventSchema(BaseModel):
    year: int
    portfolio_injection: float  # Positive = windfall, negative = expense
    description: str = ""

class SimulateRequest(BaseModel):
    # ... existing fields ...
    events: List[EventSchema] = []  # NEW
```

**`routers/simulate.py`**
```python
from domain.models import Event

# Map events in scenario construction:
events=[
    Event(year=e.year, portfolio_injection=e.portfolio_injection, description=e.description)
    for e in body.events
]
```

### Frontend (1 file modified)

**`WhatIfView.vue`**

**State:**
```js
const events = ref([])  // Each item: {year, amount, description, enabled}
```

**Helper Functions:**
```js
const addEvent = (type) => {
  events.value.push({
    year: 5,
    amount: type === 'windfall' ? 500000 : -300000,
    description: type === 'windfall' ? 'Stock Windfall' : 'Major Expense',
    enabled: true
  })
  onSliderChange()
}

const removeEvent = (index) => {
  events.value.splice(index, 1)
  onSliderChange()
}

const formatEventAmount = (amount) => {
  const prefix = amount >= 0 ? '+' : '-'
  return prefix + '₪' + Math.round(Math.abs(amount) / 1000) + 'K'
}
```

**Updated runSimulation:**
```js
events: events.value
  .filter(e => e.enabled)
  .map(e => ({ year: e.year, portfolio_injection: e.amount, description: e.description }))
```

**Reset on Scenario Change:**
```js
events.value = []  // Clear events when selecting new scenario
```

### UI Layout

```
┌──────────────── One-Time Events ──────────────────────────┐
│  [+ Add Windfall]  [+ Add Expense]                        │
│                                                           │
│  ☑  [Stock Windfall ] Year [━●──] 5  ₪[━━━●──] +500K  [🗑] │
│  ☑  [Major Expense  ] Year [━━●─] 8  ₪[━━●───] -300K  [🗑] │
└───────────────────────────────────────────────────────────┘
```

Positioned between sliders and comparison chart.

## Event Behavior

**Timing in Simulation:**
- Events applied **before** portfolio growth each year
- Injection compounds with annual return rate
- Example: Year 2 +₪500K windfall at 7% return grows with rest of portfolio

**Toggle vs. Delete:**
- **Unchecked** (disabled) → Event ignored in POST request
- **Checked** (enabled) → Event included in simulation
- **Deleted** → Event removed from list

**Reset Behavior:**
- When switching base scenarios, events list clears
- Each scenario starts with fresh event state (playground philosophy)

## Testing

### Backend Test
```bash
curl -X POST http://localhost:8000/api/v1/simulate \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "monthly_income": 45000,
    "monthly_expenses": 22000,
    "return_rate": 0.07,
    "starting_age": 41,
    "initial_portfolio": 1700000,
    "years": 20,
    "events": [
      {"year": 2, "portfolio_injection": 500000, "description": "IPO Windfall"}
    ]
  }'
```

**Result:** Retirement year 8 (vs. 9 without event), final portfolio ₪20.5M (vs. ₪18.7M without)

### Frontend Test
1. Navigate to What-If Explorer
2. Select scenario → Sliders initialize
3. Click `[+ Add Windfall]` → Event row appears with Year=5, Amount=+₪500K
4. Move Year slider to 2 → Chart updates, portfolio shows windfall effect
5. Move Amount slider to +₪1M → Chart updates, retirement year may shift earlier
6. Add expense event: `[+ Add Expense]` → Shows -₪300K default
7. Uncheck windfall event → Chart reverts to single-event state
8. Check windfall again → Chart shows both events
9. Delete expense → Event removed, chart updates
10. Change scenario → Events reset to empty list

## Edge Cases Handled

✅ Empty events list → "No events added" message, no POST overhead
✅ Disabled events → Not sent in POST, but state preserved if re-enabled
✅ Multiple events same year → Both applied (stacked)
✅ Events at boundary years (1, 20) → Work correctly
✅ Very large amounts (±₪5M) → No validation errors, let user decide
✅ Scenario switching → Events cleared automatically (no cross-scenario bleed)

## CSS Styling

- Green buttons for windfalls: `#27ae60` → `#229954` on hover
- Red buttons for expenses: `#e74c3c` → `#c0392b` on hover
- Event rows: Light background `#f9f9f9`, border `#e0e0e0`
- Sliders match existing What-If style (blue `#667eea`)
- Remove button (🗑) scales on hover

## Notes

- **No validation** on event year/amount ranges (user can set whatever they want)
- **Description is optional** but encouraged for clarity
- **Events persist in component state** across slider adjustments (independent system)
- **Debounce applies to all changes** (checkbox, description, sliders) = smooth interaction
- **Domain layer unchanged** — `Event` dataclass and `simulate()` already fully support this

## Future Enhancements (not implemented)

- Event type enum (Windfall vs. Expense vs. other) with icons
- Event recurrence (annual events, one-time only)
- Event history from base scenario (load events from original run)
- Probability/confidence sliders (e.g., "IPO 60% chance")
- Event templates (pre-built common scenarios)
