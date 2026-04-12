# Analysis Subsystem: Configuration-Driven Scenario Analysis

This subsystem decouples simulation (expensive, run once) from analysis/output (fast, run many times). Two-step workflow enables 100x faster iteration.

## Architecture

**Principle:** Pure configuration drives analysis. Add new analyses by editing `analysis.json`, not Python.

**Two-step workflow:**
1. **Run simulations** (slow, ~2 seconds for 8 scenarios)
   - `python analysis/run_simulations.py`
   - Executes all scenario nodes
   - Saves results to `simulation_cache.json`

2. **Run analysis** (fast, ~1 second, can repeat many times)
   - `python analysis/run_analysis.py`
   - Loads cache
   - Executes all analyses in `analysis.json`
   - Produces formatted output

## Step 1: Run Simulations (run_simulations.py)

```bash
python analysis/run_simulations.py
```

**What it does:**
1. Load scenario tree from `scenario_nodes.json`
2. Resolve each node (walk inheritance chain)
3. Run `simulate()` for each scenario
4. Convert SimulationResult → dict
5. Save to `scenario_analysis/simulation_cache.json` with metadata

**Output:**
```
================================================================================
SIMULATION RUNNER
================================================================================

Loading scenario tree...
✓ Loaded 8 scenario nodes

Running simulations for 8 scenarios...
[1/8] Alon Baseline                                      → Retire: Year 16      Portfolio: ₪ 10,783,762
[2/8] Alon - Buy Apartment                              → Retire: Never        Portfolio: ₪  3,384,573
[3/8] Alon - Buy Apartment + Exit                       → Retire: Year 12      Portfolio: ₪ 18,405,932
...

✓ Completed 8 simulations

To analyze these results without re-simulating:
  python analysis/run_analysis.py

================================================================================
```

**Cache file** (`scenario_analysis/simulation_cache.json`):
```json
{
  "generated_at": "2026-04-12T08:52:19.653433",
  "num_scenarios": 8,
  "results": {
    "Alon Baseline": {
      "scenario_name": "Alon Baseline",
      "retirement_year": 16,
      "year_data": [
        {"year": 1, "income": 540000, "expenses": 300000, ...},
        ...
      ]
    },
    ...
  }
}
```

## Step 2: Run Analysis (run_analysis.py)

```bash
python analysis/run_analysis.py
```

**What it does:**
1. Load `analysis.json` (analysis definitions)
2. Load `scenario_nodes.json` (scenario tree)
3. Load `simulation_cache.json` (cached results)
4. For each analysis:
   - Dispatch to appropriate handler based on `type`
   - Use cached results (or simulate inline if cache missing)
   - Format and print output

**Output:**
Depends on analyses defined in `analysis.json`. Examples below.

## Configuration: analysis.json

Pure JSON configuration. No Python code changes needed to add analyses.

```json
{
  "analyses": [
    {
      "id": "baseline_vs_exit",
      "title": "Exit Impact: Income Range ₪30K-₪45K",
      "type": "parameter_sweep",
      "base_scenario": "Alon Baseline",
      "parameter": "monthly_income",
      "range": {
        "min": 30000,
        "max": 45000,
        "step": 5000
      },
      "test_variations": [
        {
          "name": "Without Exit",
          "events": []
        },
        {
          "name": "With ₪2M Exit (Year 2)",
          "events": [
            {"year": 2, "portfolio_injection": 2000000}
          ]
        }
      ],
      "metrics": ["retirement_year", "portfolio_final"],
      "outputs": ["detailed_tables", "comparison_table"]
    },
    ...
  ]
}
```

## Analysis Types

| Type | What It Does | Example |
|------|-------------|---------|
| `parameter_pair_comparison` | Compare two parameter values | Income ₪45K vs ₪25K |
| `parameter_sweep` | Vary parameter across range, test multiple variations | Income ₪25K-₪50K, with/without exit |
| `milestone_snapshots` | Show snapshots at specific years | Years 1, 5, 10, 15, 20 |
| `tree_exploration` | Visualize tree structure and comparisons | Show all nodes, pairwise diffs |

### Example: parameter_pair_comparison
```json
{
  "type": "parameter_pair_comparison",
  "title": "Income Comparison: ₪45K vs ₪25K",
  "base_scenario": "Alon Baseline",
  "variations": {
    "High Income": {"monthly_income": 45000},
    "Low Income": {"monthly_income": 25000}
  },
  "pairs": [
    {"var1": "High Income", "var2": "Low Income"}
  ],
  "metrics": ["retirement_year", "portfolio_final"],
  "outputs": ["detailed_tables", "comparison_table"]
}
```

### Example: parameter_sweep
```json
{
  "type": "parameter_sweep",
  "title": "Exit Impact Across Income Range",
  "base_scenario": "Alon Baseline",
  "parameter": "monthly_income",
  "range": {"min": 25000, "max": 50000, "step": 5000},
  "test_variations": [
    {"name": "No Exit", "events": []},
    {"name": "With Exit", "events": [{"year": 2, "portfolio_injection": 2000000}]}
  ],
  "metrics": ["retirement_year", "portfolio_final"],
  "outputs": ["detailed_tables", "comparison_table"]
}
```

### Example: milestone_snapshots
```json
{
  "type": "milestone_snapshots",
  "title": "Scenario Comparison at Key Milestones",
  "scenarios": ["Alon Baseline", "Alon - Buy Apartment", "Alon - Buy Apartment + Exit"],
  "milestones": [1, 5, 10, 15, 20],
  "metrics": ["retirement_year", "portfolio_final"],
  "outputs": ["milestone_table", "graph"]
}
```

### Example: tree_exploration
```json
{
  "type": "tree_exploration",
  "title": "Scenario Tree Structure",
  "outputs": ["tree_structure", "pairwise_comparisons"]
}
```

## Adding a New Analysis

**Before:** Create new Python script, copy-paste analysis logic, rename variables.

**Now:** Edit `analysis.json`:

```json
{
  "id": "my_analysis",
  "title": "My Custom Analysis",
  "type": "parameter_sweep",
  "base_scenario": "Alon Baseline",
  "parameter": "monthly_income",
  "range": {"min": 30000, "max": 50000, "step": 5000},
  "test_variations": [
    {"name": "Scenario A", "events": []},
    {"name": "Scenario B", "events": [{"year": 2, "portfolio_injection": 1000000}]}
  ],
  "metrics": ["retirement_year", "portfolio_final"],
  "outputs": ["detailed_tables", "comparison_table"]
}
```

Then:
```bash
python analysis/run_analysis.py
# Your new analysis appears in output!
```

## Workflow Benefits

| Benefit | How |
|---------|-----|
| **Fast iteration** | Run simulations once (2s), then analyses (1s each). Edit JSON, re-run in 1s. |
| **Consistent results** | Same cache used across multiple analyses. No variance from re-simulation. |
| **Easy to add** | New analyses require only JSON edits. No code changes. No side effects. |
| **Fallback safety** | If cache missing, simulates inline (slower but works). |
| **Transparent** | Cache is human-readable JSON. Inspect raw data if needed. |

## When to Re-Simulate

**Re-run `run_simulations.py` when:**
- Adding new scenario nodes to `scenario_nodes.json`
- Changing scenario parameters (income, expenses, mortgage, events)
- Modifying simulation settings (return_rate, withdrawal_rate, years)
- Needing fresh results after upstream changes

**Don't re-simulate when:**
- Changing analysis output format
- Adding new analyses (same scenarios, different groupings)
- Modifying graph/table display
- Editing `analysis.json`

## File Locations

| File | Purpose | Location |
|------|---------|----------|
| `scenario_nodes.json` | Scenario tree definitions | `scenario_analysis/scenario_nodes.json` |
| `analysis.json` | Analysis configurations | `scenario_analysis/analysis.json` |
| `simulation_cache.json` | Cached simulation results | `scenario_analysis/simulation_cache.json` (generated) |

## Storage Hierarchy

```
scenario_nodes.json  (scenario definitions)
      ↓
run_simulations.py   (resolve + simulate all)
      ↓
simulation_cache.json (raw results, JSON-serialized)
      ↓
run_analysis.py      (load cache, execute analyses)
      ↓
analysis.json        (define what to analyze)
```

Each layer is independent: changing analysis doesn't require re-simulation.

## Example Commands

```bash
# One-time simulation
python analysis/run_simulations.py

# First analysis run (uses cache)
python analysis/run_analysis.py

# Edit analysis.json to add new analyses
vim scenario_analysis/analysis.json

# Re-run analysis (same cache, new output)
python analysis/run_analysis.py

# Later, refresh scenarios
python analysis/run_simulations.py
python analysis/run_analysis.py
```

## Key Design Principles

1. **Decoupling:** Simulation and analysis are independent. Enables fast iteration.
2. **Configuration-driven:** JSON defines what to analyze, not Python code.
3. **Cacheable:** Raw results are serialized to JSON for reuse.
4. **Fallback safe:** If cache missing, falls back to inline simulation.
5. **Extensible:** Adding new analysis types requires a handler function in run_analysis.py, but new analyses only require JSON edits.

## Future Extensions

Current analysis types cover common scenarios. To add a new type:

1. **Define handler** in `run_analysis.py`:
   ```python
   def handle_my_new_type(analysis, all_nodes, cached_results):
       # Implementation
   ```

2. **Register handler** in dispatch table (run_analysis.py)

3. **Use in analysis.json**:
   ```json
   {
     "type": "my_new_type",
     "title": "My Analysis",
     ...
   }
   ```

No code duplication across analyses — shared utilities in run_analysis.py.
