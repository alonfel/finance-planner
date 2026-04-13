# Creating a New Profile with a New Simulation

**Purpose:** This guide walks you through creating a complete new profile (multi-user profile) with custom scenarios and analyses from scratch.

---

## Quick Overview

A **profile** is a complete, independent simulation workspace. Each profile contains:
- **Financial data** — scenarios, assumptions, settings
- **Analysis configurations** — how to compare and analyze scenarios
- **Results history** — timestamped analysis runs

This allows multiple people (or multiple "what-if" analyses) to maintain separate simulations under one codebase.

---

## Directory Structure for a New Profile

When you create a profile named `sarah`, the system will create:

```
data/
└── profiles/
    └── sarah/
        ├── profile.json                      # Metadata + creation timestamp
        ├── settings.json                     # Simulation parameters (years, return rate, withdrawal rate)
        ├── scenarios.json                    # Base scenarios (flat, no inheritance)
        ├── scenario_nodes.json               # Scenario trees (inheritance-based)
        └── analyses/
            ├── config.json                   # Analysis definitions (what to compare)
            ├── cache/
            │   └── simulation_cache.json     # Generated: cached simulation results
            └── results/
                ├── 2026-04-12T14_30_00.json  # Generated: timestamped run results
                └── 2026-04-12T15_45_30.json
```

**Key Points:**
- `profile.json` is auto-created and contains metadata
- **You create:** settings.json, scenarios.json, scenario_nodes.json, analyses/config.json
- **System generates:** cache files and result files (don't edit these manually)

---

## Step 1: Create Profile Metadata

**File:** `data/profiles/{profile_name}/profile.json`

The system auto-creates this on first run, but you can create it manually for clarity.

**Minimum example (Sarah's profile):**
```json
{
  "name": "sarah",
  "description": "Sarah's retirement planning scenarios",
  "created_at": "2026-04-12T14:00:00"
}
```

**Fields:**
- `name` — Profile identifier (used in file paths, must be lowercase alphanumeric + underscore)
- `description` — Human-readable purpose (optional)
- `created_at` — ISO timestamp when profile was created (optional, system adds if missing)

---

## Step 2: Define Simulation Settings

**File:** `data/profiles/{profile_name}/settings.json`

Controls global simulation parameters that apply to all scenarios in the profile.

**Example:**
```json
{
  "simulation": {
    "years": 25,
    "return_rate": 0.06,
    "withdrawal_rate": 0.04
  },
  "output": {
    "show_fields": [
      "income_expenses",
      "mortgage_details",
      "events",
      "rates_settings"
    ]
  }
}
```

**Simulation settings:**
- `years` — How many years to simulate (integer, 10-50 typical)
- `return_rate` — Annual portfolio return assumption (0.03 = 3%, decimal format)
- `withdrawal_rate` — Safe withdrawal rate for retirement calculation (0.04 = 4%, decimal format)

**Output settings:**
- `show_fields` — Which sections to print during output
  - `income_expenses` — Monthly income/expenses summary
  - `mortgage_details` — Mortgage amortization details
  - `events` — One-time events (injections, expenses)
  - `rates_settings` — Simulation parameters used

Leave as shown above unless you want to hide certain output sections.

---

## Step 3: Define Base Scenarios

**File:** `data/profiles/{profile_name}/scenarios.json`

Base scenarios are simple, standalone scenario definitions. Use this for:
- **Simple scenarios** with no inheritance (standalone definitions)
- **Reference scenarios** that other scenarios inherit from

**Example for Sarah (a software engineer):**
```json
{
  "scenarios": [
    {
      "name": "Baseline",
      "monthly_income": 25000,
      "monthly_expenses": 15000,
      "currency": "USD",
      "initial_portfolio": 500000,
      "mortgage": null,
      "age": 35,
      "events": []
    },
    {
      "name": "With House Purchase",
      "monthly_income": 25000,
      "monthly_expenses": 15000,
      "currency": "USD",
      "initial_portfolio": 100000,
      "mortgage": {
        "principal": 400000,
        "annual_rate": 0.065,
        "duration_years": 30,
        "currency": "USD"
      },
      "age": 35,
      "events": [
        {
          "year": 1,
          "portfolio_injection": -50000,
          "description": "Closing costs and inspection"
        }
      ]
    },
    {
      "name": "Job Change Year 3",
      "monthly_income": 25000,
      "monthly_expenses": 15000,
      "currency": "USD",
      "initial_portfolio": 500000,
      "mortgage": null,
      "age": 35,
      "events": [
        {
          "year": 3,
          "portfolio_injection": 200000,
          "description": "Signing bonus (new job)"
        }
      ]
    }
  ]
}
```

**Core fields (required for all scenarios):**
- `name` — Unique scenario identifier (used in analyses)
- `monthly_income` — Gross monthly income (in cents: 25000 = $250, or actual amount like 45000 = ₪45K)
- `monthly_expenses` — Monthly burn rate (same units as income)
- `currency` — Three-letter code (USD, ILS, EUR, etc.)
- `initial_portfolio` — Starting portfolio value (same units as income)
- `age` — Current age (integer)
- `mortgage` — Null if no mortgage, or a mortgage object (see below)
- `events` — List of one-time portfolio events (injections or withdrawals)

**Mortgage object (if applicable):**
```json
{
  "principal": 400000,           // Total loan amount
  "annual_rate": 0.065,         // Interest rate (6.5% = 0.065)
  "duration_years": 30,         // Loan term
  "currency": "USD"             // Must match scenario currency
}
```

**Event object:**
```json
{
  "year": 3,                     // Which year (1 = first year)
  "portfolio_injection": 200000, // Positive = add to portfolio, negative = withdraw
  "description": "Signing bonus" // Human-readable label
}
```

---

## Step 4: Define Scenario Trees (Inheritance)

**File:** `data/profiles/{profile_name}/scenario_nodes.json`

Scenario nodes are inheritance-based variations. Use this for:
- **Modifying parent scenarios** (override specific fields)
- **Building scenario families** (baseline → variations → more specific)
- **Reducing duplication** (inherit 90% of settings, only specify changes)

**Example for Sarah's scenario tree:**
```json
{
  "scenario_nodes": [
    {
      "name": "Sarah Baseline",
      "base_scenario": "Baseline",
      "monthly_income": 25000,
      "monthly_expenses": 15000,
      "age": 35,
      "event_mode": "append",
      "events": []
    },
    {
      "name": "Sarah - With House",
      "parent": "Sarah Baseline",
      "mortgage": {
        "principal": 400000,
        "annual_rate": 0.065,
        "duration_years": 30,
        "currency": "USD"
      },
      "event_mode": "append",
      "events": [
        {
          "year": 1,
          "portfolio_injection": -50000,
          "description": "Closing costs"
        }
      ]
    },
    {
      "name": "Sarah - With House + Early Retirement",
      "parent": "Sarah - With House",
      "monthly_income": 0,
      "monthly_expenses": 20000,
      "event_mode": "append",
      "events": []
    },
    {
      "name": "Sarah - High Income (₪35K)",
      "parent": "Sarah Baseline",
      "monthly_income": 35000,
      "event_mode": "replace",
      "events": [
        {
          "year": 5,
          "portfolio_injection": 150000,
          "description": "Promotion raise accumulated"
        }
      ]
    },
    {
      "name": "Sarah - High Income + House",
      "parent": "Sarah - High Income (₪35K)",
      "mortgage": {
        "principal": 500000,
        "annual_rate": 0.065,
        "duration_years": 30,
        "currency": "USD"
      },
      "event_mode": "append",
      "events": [
        {
          "year": 1,
          "portfolio_injection": -50000,
          "description": "Closing costs"
        }
      ]
    }
  ]
}
```

**Node fields:**

**For root nodes (inheriting from base_scenario):**
- `name` — Unique node identifier
- `base_scenario` — Which scenario from scenarios.json to inherit from
- Fields to override (monthly_income, monthly_expenses, age, return_rate, etc.)
- `event_mode` — How to combine inherited events: "append" (add to parent's) or "replace" (use only these)
- `events` — List of event objects

**For child nodes (inheriting from another node via parent):**
- `name` — Unique node identifier
- `parent` — Name of parent scenario_node to inherit from
- Fields to override (only include what differs from parent)
- `event_mode` — "append" or "replace"
- `events` — List of event objects

**event_mode behavior:**
- `"append"` — Child's events are added AFTER parent's inherited events
- `"replace"` — Child's events REPLACE parent's (parent's events discarded)

**Example of inheritance chain:**
```
Base scenarios.json
  ↓ inherits from
Sarah Baseline (root node) ← base_scenario: "Baseline"
  ├─ Sarah - With House ← parent: Sarah Baseline (adds mortgage)
  │   ├─ Sarah - With House + Early Retirement ← parent: Sarah - With House (changes income to 0)
  │
  ├─ Sarah - High Income ← parent: Sarah Baseline (overrides income)
  │   └─ Sarah - High Income + House ← parent: Sarah - High Income (adds mortgage)
```

---

## Step 5: Define Analyses

**File:** `data/profiles/{profile_name}/analyses/config.json`

Analyses define what comparisons and explorations to run. This is where you specify:
- Which scenarios to compare
- What variations to apply
- Which metrics to show

**Example analysis configuration:**
```json
{
  "analyses": [
    {
      "id": "income_comparison",
      "title": "Income Impact: $25K vs $35K",
      "description": "Compare retirement outcomes at different income levels",
      "type": "parameter_pair_comparison",
      "scenarios": [
        "Sarah Baseline",
        "Sarah - With House"
      ],
      "variations": {
        "low_income": {
          "monthly_income": 25000
        },
        "high_income": {
          "monthly_income": 35000
        }
      },
      "pairs": [
        {
          "var1": "low_income",
          "var2": "high_income"
        }
      ],
      "metrics": [
        "retirement_year",
        "age_at_retirement",
        "portfolio_year_10",
        "portfolio_final",
        "annual_savings"
      ],
      "outputs": [
        "pair_comparison",
        "summary_table",
        "insights"
      ]
    },
    {
      "id": "house_impact",
      "title": "House Purchase Impact",
      "description": "Baseline vs With House scenarios",
      "type": "parameter_pair_comparison",
      "scenarios": [
        "Sarah Baseline"
      ],
      "variations": {
        "no_house": {
          "mortgage": null
        },
        "with_house": {
          "mortgage": {
            "principal": 400000,
            "annual_rate": 0.065,
            "duration_years": 30,
            "currency": "USD"
          }
        }
      },
      "pairs": [
        {
          "var1": "no_house",
          "var2": "with_house"
        }
      ],
      "metrics": [
        "retirement_year",
        "portfolio_final"
      ],
      "outputs": [
        "pair_comparison",
        "insights"
      ]
    },
    {
      "id": "scenario_tree",
      "title": "Complete Scenario Tree",
      "description": "Explore all scenarios in the inheritance tree",
      "type": "tree_exploration",
      "root_scenario": "Sarah Baseline",
      "outputs": [
        "tree_visualization",
        "pairwise_comparison"
      ]
    }
  ]
}
```

**Analysis types:**

### 1. `parameter_pair_comparison` — Compare two variations
Compare the SAME scenario under two different parameter sets.

**Fields:**
- `id` — Unique identifier for this analysis
- `title` — Display title
- `description` — What this analysis explores
- `type` — Must be "parameter_pair_comparison"
- `scenarios` — Which scenario(s) to analyze (can be one or multiple)
- `variations` — Dict of parameter sets (var1, var2, etc.)
  - Each variation specifies which fields to override
  - Can override: monthly_income, monthly_expenses, mortgage, return_rate, events, etc.
- `pairs` — List of comparisons to make (each pair has var1 and var2)
- `metrics` — Which metrics to calculate:
  - `retirement_year` — Year when portfolio depleted
  - `age_at_retirement` — Age at retirement
  - `portfolio_year_10` — Portfolio value at year 10
  - `portfolio_final` — Final portfolio value (year 20/25/etc)
  - `annual_savings` — Average annual savings
- `outputs` — What to display:
  - `pair_comparison` — Side-by-side var1 vs var2
  - `summary_table` — Formatted comparison table
  - `insights` — Calculated insights and deltas

### 2. `tree_exploration` — Visualize scenario inheritance
Show all scenarios in the tree and their pairwise comparisons.

**Fields:**
- `id`, `title`, `description` — Standard
- `type` — Must be "tree_exploration"
- `root_scenario` — Starting scenario node name
- `outputs` — Display options:
  - `tree_visualization` — Shows the inheritance hierarchy
  - `pairwise_comparison` — Compares all pairs in the tree

### 3. `parameter_sweep` — Vary parameter across a range
Vary a parameter from min to max and show how retirement changes.

**Example:**
```json
{
  "id": "income_sweep",
  "title": "Income Sweep: $20K to $50K",
  "type": "parameter_sweep",
  "scenarios": ["Sarah Baseline"],
  "parameter": "monthly_income",
  "range": {
    "min": 20000,
    "max": 50000,
    "step": 5000
  },
  "metrics": ["retirement_year", "portfolio_final"],
  "outputs": ["line_chart", "table"]
}
```

### 4. `milestone_snapshots` — Show values at specific years
Capture portfolio snapshots at key milestones.

**Example:**
```json
{
  "id": "milestones",
  "title": "Portfolio at Key Ages",
  "type": "milestone_snapshots",
  "scenarios": ["Sarah Baseline", "Sarah - With House"],
  "milestones": [
    {"year": 5, "label": "Age 40"},
    {"year": 10, "label": "Age 45"},
    {"year": 15, "label": "Age 50"}
  ],
  "metrics": ["portfolio_value", "annual_income", "annual_expenses"],
  "outputs": ["snapshot_table", "growth_chart"]
}
```

---

## Step 6: Run the Simulation

Once you have all files in place, run the simulations and analyses.

### Generate Simulation Cache

```bash
cd /Users/alon/Documents/finance_planner

# Specify which profile to simulate
export FINANCE_PROFILE=sarah

python analysis/run_simulations.py
```

**What happens:**
- System loads all scenarios from your profile
- Runs 20+ year simulation for each scenario
- Caches results in `data/profiles/sarah/analyses/cache/simulation_cache.json`
- All results available instantly for analysis

**Output:**
```
Simulating Sarah Baseline...
Simulating Sarah - With House...
Simulating Sarah - With House + Early Retirement...
...
Cache saved to: data/profiles/sarah/analyses/cache/simulation_cache.json
14 scenarios cached
```

### Run Analyses

```bash
export FINANCE_PROFILE=sarah

python analysis/run_analysis.py
```

**What happens:**
- Loads cached simulation results
- Runs each analysis defined in config.json
- Displays comparisons and insights
- Saves timestamped result file in `data/profiles/sarah/analyses/results/`

**Output:**
```
=== Income Impact: $25K vs $35K ===
...comparison table...
...insights...

=== House Purchase Impact ===
...comparison table...

=== Complete Scenario Tree ===
...tree visualization...
...pairwise comparisons...

Results saved to: data/profiles/sarah/analyses/results/2026-04-12T14_35_22.json
```

---

## Complete Example: Create Profile from Scratch

Let's create a profile for "john" (a consultant with variable income):

### File 1: `data/profiles/john/profile.json`
```json
{
  "name": "john",
  "description": "John's retirement planning with variable consulting income",
  "created_at": "2026-04-12T15:00:00"
}
```

### File 2: `data/profiles/john/settings.json`
```json
{
  "simulation": {
    "years": 30,
    "return_rate": 0.055,
    "withdrawal_rate": 0.04
  },
  "output": {
    "show_fields": [
      "income_expenses",
      "events",
      "rates_settings"
    ]
  }
}
```

### File 3: `data/profiles/john/scenarios.json`
```json
{
  "scenarios": [
    {
      "name": "Baseline",
      "monthly_income": 30000,
      "monthly_expenses": 18000,
      "currency": "USD",
      "initial_portfolio": 750000,
      "mortgage": null,
      "age": 38,
      "events": []
    }
  ]
}
```

### File 4: `data/profiles/john/scenario_nodes.json`
```json
{
  "scenario_nodes": [
    {
      "name": "John Baseline",
      "base_scenario": "Baseline",
      "monthly_income": 30000,
      "monthly_expenses": 18000,
      "age": 38,
      "event_mode": "append",
      "events": []
    },
    {
      "name": "John - Good Year (₪45K)",
      "parent": "John Baseline",
      "monthly_income": 45000,
      "event_mode": "append",
      "events": []
    },
    {
      "name": "John - Slow Year (₪15K)",
      "parent": "John Baseline",
      "monthly_income": 15000,
      "event_mode": "append",
      "events": []
    },
    {
      "name": "John - Acquisition",
      "parent": "John Baseline",
      "monthly_income": 0,
      "event_mode": "replace",
      "events": [
        {
          "year": 5,
          "portfolio_injection": 1000000,
          "description": "Company acquisition payout"
        }
      ]
    }
  ]
}
```

### File 5: `data/profiles/john/analyses/config.json`
```json
{
  "analyses": [
    {
      "id": "income_sensitivity",
      "title": "Income Sensitivity Analysis",
      "description": "How does retirement change with different income levels?",
      "type": "parameter_pair_comparison",
      "scenarios": ["John Baseline"],
      "variations": {
        "average": {
          "monthly_income": 30000
        },
        "good_year": {
          "monthly_income": 45000
        },
        "slow_year": {
          "monthly_income": 15000
        }
      },
      "pairs": [
        {"var1": "slow_year", "var2": "average"},
        {"var1": "average", "var2": "good_year"}
      ],
      "metrics": [
        "retirement_year",
        "age_at_retirement",
        "portfolio_final",
        "annual_savings"
      ],
      "outputs": [
        "pair_comparison",
        "summary_table",
        "insights"
      ]
    },
    {
      "id": "acquisition_impact",
      "title": "Acquisition Impact",
      "description": "Effect of potential company acquisition on retirement timeline",
      "type": "parameter_pair_comparison",
      "scenarios": ["John Baseline"],
      "variations": {
        "baseline": {
          "events": []
        },
        "with_acquisition": {
          "monthly_income": 0,
          "events": [
            {
              "year": 5,
              "portfolio_injection": 1000000,
              "description": "Acquisition payout"
            }
          ]
        }
      },
      "pairs": [
        {"var1": "baseline", "var2": "with_acquisition"}
      ],
      "metrics": [
        "retirement_year",
        "portfolio_final"
      ],
      "outputs": [
        "pair_comparison",
        "insights"
      ]
    },
    {
      "id": "scenario_tree",
      "title": "Consulting Income Scenarios",
      "description": "Explore all John's income scenarios",
      "type": "tree_exploration",
      "root_scenario": "John Baseline",
      "outputs": [
        "tree_visualization"
      ]
    }
  ]
}
```

### Create the Profile

**Manually create the directory structure:**
```bash
mkdir -p data/profiles/john/analyses/cache
mkdir -p data/profiles/john/analyses/results
```

**Then create each JSON file** with the content above.

### Run Simulations and Analyses

```bash
# Simulate
python analysis/run_simulations.py

# Analyze
python analysis/run_analysis.py
```

---

## Data Requirements Checklist

### Required Files
- ✅ `data/profiles/{name}/settings.json` — Simulation parameters
- ✅ `data/profiles/{name}/scenarios.json` — Base scenarios (at least one)
- ✅ `data/profiles/{name}/scenario_nodes.json` — Scenario trees (at least one root node)
- ✅ `data/profiles/{name}/analyses/config.json` — Analysis definitions (at least one analysis)

### Optional Files
- ⚪ `data/profiles/{name}/profile.json` — Auto-created if missing, but can be created manually

### Auto-Generated Files (Don't Create)
- 🚫 `data/profiles/{name}/analyses/cache/simulation_cache.json` — Created by `run_simulations.py`
- 🚫 `data/profiles/{name}/analyses/results/*.json` — Created by `run_analysis.py`

---

## Common Data Patterns

### Income Events
```json
{
  "year": 2,
  "portfolio_injection": 100000,
  "description": "Salary bonus"
}
```

### Major Expenses
```json
{
  "year": 1,
  "portfolio_injection": -50000,
  "description": "Car purchase"
}
```

### Windfall (Inheritance, Sale, etc.)
```json
{
  "year": 7,
  "portfolio_injection": 500000,
  "description": "Inheritance from parent"
}
```

### Multi-Year Variable Income (Use Separate Events)
```json
[
  {"year": 1, "portfolio_injection": 50000, "description": "Year 1 bonus"},
  {"year": 2, "portfolio_injection": 75000, "description": "Year 2 bonus"},
  {"year": 3, "portfolio_injection": 100000, "description": "Year 3 bonus"}
]
```

### Mortgage with Down Payment from Portfolio
```json
{
  "mortgage": {
    "principal": 400000,
    "annual_rate": 0.065,
    "duration_years": 30,
    "currency": "USD"
  },
  "events": [
    {
      "year": 1,
      "portfolio_injection": -100000,
      "description": "Down payment (20%)"
    },
    {
      "year": 1,
      "portfolio_injection": -10000,
      "description": "Closing costs and inspections"
    }
  ]
}
```

---

## Validation Rules

Before running simulations, ensure:

1. **Unique names** — All scenario and scenario_node names are unique within their files
2. **Parent references** — Every parent in scenario_nodes.json refers to an existing node
3. **Base scenario references** — Every base_scenario refers to an existing scenario in scenarios.json
4. **Currencies match** — All events and mortgage in a scenario use the same currency
5. **Scenario references in analyses** — All scenarios in analysis configs exist
6. **Valid JSON** — No trailing commas, all quotes matched, valid number formats
7. **Positive values** — Income and expenses should be positive (use negative events for withdrawals)

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'domain'"
```bash
cd /Users/alon/Documents/finance_planner
python analysis/run_simulations.py
```

### "FileNotFoundError: data/profiles/sarah/..."
Ensure all required files exist in the correct directory structure.

### "JSON decode error" in scenarios.json
Check for:
- Trailing commas after last item in arrays
- Missing quotes around strings
- Unmatched braces/brackets

### Stale cache
```bash
rm data/profiles/sarah/analyses/cache/simulation_cache.json
python analysis/run_simulations.py
```

### Want to reset a profile
```bash
rm -rf data/profiles/sarah/
# Then recreate the files
```

---

## Best Practices

1. **Keep scenarios.json simple** — Use only for base, standalone scenarios
2. **Use scenario_nodes.json for variations** — Inheritance reduces duplication by 90%
3. **One analysis per business question** — "Income sensitivity", "House impact", not "All analyses"
4. **Use meaningful descriptions** — Future you (or your team) will thank you
5. **Test with one scenario first** — Create minimal profile, run simulations, verify output before adding complexity
6. **Use consistent naming** — "Sarah - Baseline", "Sarah - With House" (pattern: "Name - Variation")
7. **Document assumptions** — Include assumption values in scenario names where not obvious

---

## Next Steps

1. **Copy this guide** and customize for your use case
2. **Create the directory structure** for your profile
3. **Start with one base scenario** in scenarios.json
4. **Create one root node** in scenario_nodes.json
5. **Run simulations:** `python analysis/run_simulations.py`
6. **Create one simple analysis** (parameter_pair_comparison)
7. **Run analysis:** `python analysis/run_analysis.py`
8. **Expand gradually** — Add more scenarios, analyses, variations

---

## Need Help?

- See [CLAUDE.md](CLAUDE.md) for quick start and common tasks
- See [analysis/ANALYSIS.md](analysis/ANALYSIS.md) for analysis configuration details
- See [domain/DOMAIN.md](domain/DOMAIN.md) for financial modeling details
