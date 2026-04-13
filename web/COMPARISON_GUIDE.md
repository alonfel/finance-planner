# Scenario Comparison Guide

## Overview

The Finance Planner now includes a **side-by-side scenario comparison view** that lets you analyze multiple scenarios together to understand the impact of different decisions (like IPO timing).

## How to Use

### Step 1: Navigate to Scenarios
1. Open http://localhost:5173
2. Login with `alon / alon123`
3. Click on the "Alon" profile card
4. Click "View Scenarios"

### Step 2: Open Comparison View
On the Scenarios page, you'll see a **"📊 Compare Scenarios"** button next to the run selector.

Click it to open the comparison view.

### Step 3: Select Scenarios
1. Choose the simulation run from the dropdown (date-based)
2. Check the boxes for scenarios you want to compare
3. You must select **at least 2 scenarios**
4. Click **"Compare Selected"** button

### Step 4: View Results

The comparison displays three sections:

#### A) Portfolio Growth Chart
- **Line chart** showing portfolio trajectories for all selected scenarios
- **Different colors** for each scenario
- **X-axis:** Years (1-20)
- **Y-axis:** Portfolio value in ₪M
- **Hover** over points to see exact values

**What to look for:**
- Which scenario reaches retirement threshold first?
- How much higher is the final portfolio in IPO scenarios?
- When does each scenario cross the required capital line?

#### B) Comparison Metrics
Cards showing key metrics for each scenario:
- **Retirement Year** — When each scenario hits the retirement threshold
- **Retirement Age** — Age at retirement
- **Final Portfolio** — Portfolio value at end of simulation
- **Total Savings** — Sum of all net savings over the period

**What to compare:**
- Retirement year delta (how many years earlier with IPO?)
- Final portfolio difference (wealth impact of timing)
- Total accumulated savings

#### C) Year-by-Year Table
Side-by-side table of all years (1-20) for each scenario.

**Columns per scenario:**
- **Portfolio** — End-of-year portfolio value (₪M)
- **Age** — Your age that year
- **Savings** — Net savings that year (₪K)

**Hover rows** to highlight across all scenarios.

---

## Example: Comparing Alon's Scenarios

### Baseline vs IPO Year 2

| Metric | Baseline | IPO Year 2 | Difference |
|--------|----------|-----------|-----------|
| **Retirement Year** | 11 | 6 | **-5 years earlier** |
| **Retirement Age** | 52 | 47 | **5 years younger** |
| **Final Portfolio** | ₪13.22M | ₪18.27M | **+₪5.05M (+38%)** |
| **Total Savings** | ₪6.17M | ₪7.18M | **+₪1.01M** |

**Insight:** An IPO in Year 2 lets you retire 5 years earlier with 38% more wealth.

### Baseline vs IPO Year 3

| Metric | Baseline | IPO Year 3 | Difference |
|--------|----------|-----------|-----------|
| **Retirement Year** | 11 | 5 | **-6 years earlier** |
| **Retirement Age** | 52 | 46 | **6 years younger** |
| **Final Portfolio** | ₪13.22M | ₪20.44M | **+₪7.22M (+55%)** |
| **Total Savings** | ₪6.17M | ₪7.19M | **+₪1.02M** |

**Insight:** An IPO in Year 3 (vs Year 2) adds just 1 more year of retirement gains, but compounds to ₪2.22M more.

---

## Technical Details

### Chart Features
- **Multiple color palette** — Up to 5 scenarios with distinct colors
- **Interactive legend** — Click legend items to toggle scenarios on/off
- **Tooltip on hover** — Shows exact values for each year
- **Responsive** — Works on different screen sizes

### Table Features
- **Year anchored** — Left column stays visible when scrolling
- **Scenario columns** — Each scenario gets its own column group
- **Row colors** — Alternating backgrounds for readability
- **Mobile-friendly** — Horizontal scroll on smaller screens

### Data Sources
- Pulls from cached simulation results
- Real-time API calls (no stale data)
- Uses same calculation engine as CLI

---

## Component Architecture

```
ComparisonView.vue (page)
├── ComparisonChart.vue (multi-scenario line chart)
├── ComparisonTable.vue (side-by-side year data)
└── Selection Panel (checkboxes + run selector)
```

### ComparisonChart.vue
- Vue wrapper around Chart.js
- Handles 1-5 scenarios simultaneously
- Color palette auto-rotates
- Responsive height (400px fixed)

### ComparisonTable.vue
- Scrollable comparison grid
- Year index (sticky left)
- Portfolio values for each scenario
- Age and savings breakouts

---

## Future Enhancements

- [ ] Export comparison to PDF
- [ ] Save comparison as a note/analysis
- [ ] Add "what-if" toggles (change one parameter, see impact)
- [ ] Highlight retirement year row across all scenarios
- [ ] Add a "rank scenarios" button
- [ ] Show difference bars (scenario A vs B)
- [ ] Download comparison as CSV
- [ ] Share comparison URL with others

---

## Tips & Tricks

### Comparing More Than 3 Scenarios
The interface supports up to 5 scenarios in one comparison. Colors auto-cycle.

### Looking at Specific Years
Scroll the table to see any year (1-20). The year column stays sticky.

### Understanding the Chart
- **Steep slope** = high annual savings
- **Flat line** = portfolio plateauing (near retirement spending)
- **Crossing lines** = scenarios converge (timing matters less later)

### When to Use Comparison
✅ Deciding between IPO timing options  
✅ Understanding salary increase impact  
✅ Evaluating early retirement scenarios  
✅ Showing others your financial plan  

❌ NOT for detailed tax analysis (use Python CLI for that)  
❌ NOT for adjusting parameters (Phase 1 will add input forms)  

---

## Known Limitations (MVP)

- Read-only (no parameter editing in comparison view)
- Up to 20 years only (matches simulation window)
- Can't compare across different runs (must select same run)
- No statistical analysis (max/min/avg)
- No scenario weighting/probability

---

## API Behind the Scenes

The comparison view uses these endpoints:

```
GET /api/v1/profiles/{profileId}/runs
→ List available simulation runs

GET /api/v1/runs/{runId}/scenarios
→ Get scenarios in a run (includes final portfolio)

GET /api/v1/scenarios/{resultId}/summary
→ Get summary metrics (retirement year, age, final portfolio)

GET /api/v1/scenarios/{resultId}
→ Get full year-by-year data for charting
```

All data flows through the same API as the single-scenario detail view.

---

## Troubleshooting

### Chart not showing
- Make sure you've selected at least 2 scenarios
- Click "Compare Selected" button
- Check browser console for errors (F12)

### Table is empty
- Ensure the run has scenarios
- Reload the page

### Performance is slow
- Comparing more than 4 scenarios on older devices may be slower
- Reduce scenarios and compare again

---

**Happy comparing! 📊**

For questions, check the main README or open an issue.
