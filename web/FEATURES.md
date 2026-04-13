# Finance Planner Web Features

Complete user guide for Finance Planner web application features.

---

## What-If Explorer

Explore financial scenarios in real-time by adjusting sliders and adding one-time events.

### Overview

The What-If Explorer provides an interactive sandbox for testing different financial configurations:
- Adjust income, expenses, growth rate, starting age, and portfolio size
- Add one-time events (bonuses, purchases, inheritances, etc.)
- See results update instantly
- Save your exploration as a named scenario for future reference

### How to Use

1. **Navigate to What-If** — Click "What-If Explorer" in the sidebar
2. **Adjust Sliders** — Move sliders to change:
   - **Monthly Income** (₪) — Regular monthly income amount
   - **Monthly Expenses** (₪) — Regular monthly spending
   - **Growth Rate** (%) — Expected annual investment return
   - **Starting Age** — Your current age
   - **Initial Portfolio** (₪) — Current investment portfolio balance
3. **View Results** — Table shows year-by-year projection including:
   - Age and year
   - Projected portfolio value
   - When you can afford to retire (retirement year highlighted)
4. **Add Events** — Click "Add Event" to include one-time changes:
   - Enter the year it occurs
   - Enter the amount (positive for income/inheritance, negative for expenses)
   - Add a description (e.g., "Bonus from company sale")
   - Toggle events on/off without deleting them
5. **Save as Scenario** — When you've found a configuration you like:
   - Click "Save as Scenario" button
   - Enter a name (e.g., "Conservative Plan" or "2026 Projection")
   - Confirm save
   - Scenario is now available in the Scenarios list

### Retirement Detection

The explorer highlights your **retirement year** — the first year where your portfolio can sustain your living expenses until age 100.

**Example:**
- You can save ₪23,000/month (income - expenses)
- Portfolio grows at 7% annually
- After 11 years, portfolio reaches ₪14M
- This is enough to sustain ₪300,000/year until age 100
- **Retirement year: 11** (at age 52)

If you never accumulate enough to retire, the table shows "No retirement achieved in [years] years".

### Events

One-time portfolio changes that occur in a specific year.

**Examples:**
- Year 5: +₪500,000 (bonus from company exit)
- Year 3: -₪100,000 (car purchase)
- Year 8: +₪1,500,000 (inheritance)

**Features:**
- Add multiple events to the same scenario
- Toggle events on/off with checkboxes to see their impact
- Edit event details by clicking the event row
- Delete events you no longer need
- Events are included when you save the scenario

### Saving Scenarios

Save your What-If configuration as a **named scenario** to:
- Persist it for future reference
- Compare it with other saved scenarios
- Use it as a baseline for variations

**Steps:**
1. Adjust sliders to your desired configuration
2. (Optional) Add one-time events
3. Click "Save as Scenario" button (green button in header)
4. Modal appears asking for scenario name
5. Enter a unique, descriptive name:
   - ✅ "Conservative Plan - 6% growth"
   - ✅ "IPO Exit Year 2"
   - ✅ "Max Savings Scenario"
   - ❌ "Test" (too generic)
6. Click "Save"
7. See success message: "Scenario saved!"

**After Saving:**
- Navigate to **Scenarios** view
- New scenario appears under **"What-If Saves"** run
- Select it to view full year-by-year data
- Use it to compare with other scenarios

### Limitations

- Scenario names must be unique (can't save two with the same name)
- Scenarios are profile-specific (private to your profile)
- Saved scenarios are persisted to disk and SQLite database
- Growth rate is stored per-scenario (allows different scenarios to have different return assumptions)

---

## Scenarios View

Browse and compare saved scenarios.

### Overview

The Scenarios view shows all available scenarios organized by simulation run, with detailed year-by-year data for each.

### Navigation

1. **Select Profile** — Choose which financial profile to view (Daniel, Alon, etc.)
2. **Select Run** — Scenarios are grouped by simulation run:
   - Pre-simulated runs (created by analysis team)
   - "What-If Saves" run (your saved What-If explorations)
3. **Select Scenario** — Click a scenario card to view its details

### Scenario Details

Once you select a scenario, you see:
- **Scenario Name** — User-friendly name
- **Retirement Year** — When you can afford to retire
- **Final Portfolio** — Portfolio value at end of simulation
- **Year-by-Year Data** — Table with:
  - Year number (1 = first year)
  - Age at year-end
  - Monthly income and expenses
  - Portfolio value
  - Required capital to sustain until age 100
  - Whether mortgage is active (if applicable)
  - Pension value (if applicable)

### Comparing Scenarios

To compare two scenarios:
1. View the first scenario (note retirement year and final portfolio)
2. Select a different scenario from the run list
3. Compare the year-by-year trajectories

**Example comparison:**
| | Conservative | Aggressive |
|---|---|---|
| Retirement Year | 15 | 10 |
| Final Portfolio (20 years) | ₪12.5M | ₪18.5M |
| Max Risk | Lower | Higher |

### Finding Your Saved Scenarios

Your "Save as Scenario" saves go to the **"What-If Saves"** run:
1. Navigate to Scenarios
2. Select your profile
3. Look for "What-If Saves" in the runs list
4. Your saved scenarios appear here

---

## Profiles

Manage multiple financial profiles.

### Overview

A profile represents your complete financial context:
- Income, expenses, portfolio size
- Life events (mortgage, inheritance, etc.)
- Assumptions (growth rate, retirement age target)
- Scenarios (pre-built or What-If saved)

### Available Profiles

**Daniel** — Default profile with sample scenarios

**Alon** — Comprehensive personal financial plan with:
- Baseline scenario (stable employment)
- IPO Exit Year 2 scenario (company exit in 2 years)

### Switching Profiles

1. Click profile selector in sidebar
2. View that profile's:
   - Scenarios
   - What-If Saves
   - Simulation runs

### Profile Isolation

- Each profile has separate:
  - Scenarios
  - What-If Saves
  - Simulation results
- Saved scenarios in one profile don't appear in another
- Data is private to each profile

---

## Technical Features

### Real-Time Calculation

What-If changes calculate instantly with no server latency:
- Sliders update immediately
- Results refresh within milliseconds
- No "loading" state (purely client-side math)

### Data Persistence

What-If Saves:
1. **Written to Disk** — Persisted to `scenarios.json` with timestamp
2. **Recorded in Database** — Stored in SQLite for retrieval
3. **Immediately Available** — Appear in Scenarios list without app restart

### Authentication

- Login required to access profile data
- Token-based (JWT) authentication
- Session automatically managed by app

### Input Validation

- Negative values prevented (age, income, portfolio)
- Scenario names validated (1-100 characters, must be unique)
- Growth rate range-checked (0-100%)

---

## Common Workflows

### Workflow: Test Different Growth Rate Assumptions

1. Start with your baseline scenario parameters
2. Set Growth Rate to 5%
3. Note retirement year
4. Adjust Growth Rate to 7%
5. Note retirement year again
6. Compare impact on retirement timeline

### Workflow: Plan for Major Event

1. Go to What-If Explorer
2. Set income/expenses to normal levels
3. Add event: Year 3, amount +₪1,500,000 (inheritance)
4. See how it accelerates retirement
5. Save as "Inheritance Scenario"
6. Go back and remove event
7. Save as "Without Inheritance"
8. Compare the two in Scenarios view

### Workflow: Try Conservative vs Aggressive Plans

**Conservative Plan:**
1. Set Monthly Expenses high (₪28,000)
2. Set Growth Rate low (5%)
3. Save as "Conservative"

**Aggressive Plan:**
1. Set Monthly Expenses low (₪20,000)
2. Set Growth Rate high (9%)
3. Save as "Aggressive"

**Compare:**
- Navigate to Scenarios
- View both runs
- Note the difference in retirement years

### Workflow: Sensitivity Analysis

Test how each parameter affects retirement:

1. Start with baseline (50K income, 25K expenses, 7% growth)
2. Save baseline: "Baseline"
3. Increase income to 60K: "Income +20%"
4. Reset income, decrease expenses to 20K: "Expenses -20%"
5. Reset expenses, increase growth to 9%: "Growth 9%"
6. View Scenarios, compare all four
7. Determine which parameter has biggest impact

---

## Troubleshooting

### "Scenario name already exists"

You're trying to save a scenario with a name that's already in use.

**Solution:** Enter a different name or delete the existing scenario before re-saving.

### No What-If Saves appearing

You haven't saved any scenarios yet.

**Solution:**
1. Go to What-If Explorer
2. Adjust sliders to your desired config
3. Click "Save as Scenario"
4. Enter a name and confirm
5. Check Scenarios → "What-If Saves" run

### Retirement year changed after saving

This shouldn't happen — a saved scenario shows the same retirement year as when you saved it.

If different: You may be viewing a different scenario. Check the scenario name.

### Browser losing What-If changes

If you refresh the page mid-exploration, your slider values reset.

**Solution:** Save your scenario before refreshing, or use browser's back button.

### Can't save scenario without logging in

Authentication is required for all features.

**Solution:** Login with your username and password first.

---

## Related Documentation

- [Backend API Reference](backend/API.md) — Technical API endpoint details
- [Backend README](backend/README.md) — Server setup and architecture
- [Main Project Guide](../CLAUDE.md) — Overall project structure
