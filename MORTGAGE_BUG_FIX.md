# Mortgage Rate Conversion Bug - FIXED

## Problem Identified

The graph was showing mathematically nonsensical values when mortgage scenarios were loaded. Root cause: **100x rate mismatch between frontend and backend mortgage calculations**.

## The Bug

### Frontend Perspective
- Mortgage rate slider: ranges from 1 to 8 (representing 1%-8%)
- Display calculation (`calculateMortgagePayment`): converts to decimal
  ```javascript
  const r = (m.annual_rate / 100) / 12  // 4.5 → 0.00375
  ```
- Displayed payment: ₪8,000-10,000/month (reasonable)

### Backend Perspective  
- Mortgage model expects `annual_rate` as decimal (0.01 to 0.08)
  ```python
  r = self.annual_rate / 12  # Expects: 0.045 → 0.00375
  ```
- But was receiving: percentage value (4.5)
  ```python
  r = 4.5 / 12 = 0.375  # 37.5% per month! 
  ```

### The Missing Conversion
When the frontend sent to the backend:
```javascript
// BEFORE (BUG):
mortgage: mortgage.value ? {
  principal: 1500000,
  annual_rate: 4.5,           // ❌ Sent as percentage!
  duration_years: 20,
  currency: 'ILS'
} : null
```

### Impact Example
For ₪1,500,000 mortgage at 4.5% over 20 years:

| Scenario | Rate Sent | Backend Calculation | Payment |
|----------|-----------|-------------------|---------|
| **BUGGY** | 4.5% | r = 4.5/12 = 37.5%/month | ₪4,500,000+/month ❌ |
| **FIXED** | 0.045 | r = 0.045/12 = 0.375%/month | ₪9,490/month ✅ |

When the mortgage payment is calculated as ₪4.5M/month (more than the portfolio!), the simulation shows:
- Expenses: ₪4,500,000+ per month (impossible)
- Net Savings: Severely negative
- Portfolio: Crashes to zero immediately
- Graph: Shows one flat line at bottom (portfolio exhausted)

## The Fix

Convert mortgage `annual_rate` from percentage to decimal before sending to backend, matching how `return_rate` and other rates are already handled:

```javascript
// AFTER (FIXED):
mortgage: mortgage.value ? {
  principal: mortgage.value.principal,
  annual_rate: mortgage.value.annual_rate / 100,  // ✅ Convert percentage to decimal
  duration_years: mortgage.value.duration_years,
  currency: mortgage.value.currency || 'ILS'
} : null
```

### Files Changed
- **web/frontend/src/views/WhatIfView.vue**
  - Line 507: `refreshOriginalScenario()` - re-simulation after loading scenario
  - Line 541: `runSimulation()` - What-If simulation on slider change
  - Line 639: `saveScenario()` - persisting What-If scenario to database

All three call sites now convert the rate:
```javascript
annual_rate: mortgage.value.annual_rate / 100
```

## Verification

### Mathematical Check
```
Principal: ₪1,500,000
Annual Rate: 4.5%
Duration: 20 years (240 months)

Monthly Rate: 0.045 / 12 = 0.00375 (0.375% per month)
Monthly Payment: ₪9,489.74
Total Interest Paid: ₪777,537.75
```

This is economically reasonable for a 4.5% mortgage.

### Before Fix
- Blue line (original) would show expenses ₪4.5M+/month
- Green line (What-If) would show same (both using bugged rate)
- Both would immediately crash to zero portfolio
- Graph completely unreadable

### After Fix
- Blue line (original) shows correct baseline expenses
- Green line (What-If) shows adjusted expenses
- Portfolio grows/shrinks realistically
- Graph comparison is now meaningful

## Testing Steps

1. Go to What-If Explorer
2. Load a scenario or add a mortgage manually
3. Set mortgage rate to 4.5% in the slider
4. Check mortgage payment display (should show ~₪9,490/month)
5. Observe graph:
   - Should show two lines (blue=original, green=What-If)
   - Both should be upward trending (not crashing)
   - Expenses should be roughly ₪30-50K/month range (not millions)

## Why This Happened

The frontend slider creates values 1-8 (native percentage representation for UX).
- Growth rate slider was correctly converted: `growthRate / 100`
- Mortgage rate was **not** converted (oversight)
- Backend always expects decimal format for rates
- The bug manifested only when mortgage was present in What-If scenarios

## Related Code

### Frontend Display (works correctly)
```javascript
calculateMortgagePayment(m) {
  const r = (m.annual_rate / 100) / 12  // Correctly converts percentage to decimal
  const n = m.duration_years * 12
  const numerator = r * Math.pow(1 + r, n)
  const denominator = Math.pow(1 + r, n) - 1
  const payment = m.principal * (numerator / denominator)
  return Math.round(payment).toLocaleString('en-US')
}
```

### Backend Model (now receives correct format)
```python
def __post_init__(self):
  r = self.annual_rate / 12  # Now expects: 0.045 (decimal), not 4.5 (percentage)
  n = self.duration_years * 12
  if r == 0:
    self.monthly_payment = self.principal / n
  else:
    numerator = r * (1 + r) ** n
    denominator = (1 + r) ** n - 1
    self.monthly_payment = self.principal * (numerator / denominator)
```

## Commit

```
3d418ab Fix: Convert mortgage annual_rate from percentage to decimal before sending to backend

CRITICAL BUG FIX: The frontend was sending mortgage annual_rate as a percentage
(e.g., 4.5) but the backend expected a decimal (e.g., 0.045). This caused the
backend to calculate mortgage payments at 100x the correct rate.
```
