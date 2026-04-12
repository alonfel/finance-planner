# Infrastructure Layer: Configuration & Loading

This layer handles all external input: loading JSON configs, parsing to domain models, caching simulation results.

## Overview

Three main responsibilities:
1. **Parsers** — Convert JSON dicts → domain objects
2. **Loaders** — Load JSON files → in-memory objects + singletons
3. **Cache** — Serialize/deserialize simulation results for decoupled analysis

## Parsers (parsers.py)

Consolidated dict-to-model parsing. Eliminates duplication across scenarios.py and scenario_nodes.py.

### parse_mortgage(d: dict) → Mortgage | None
```python
mortgage_dict = {
    "principal": 2_250_000,
    "annual_rate": 0.04,
    "duration_years": 25,
    "currency": "ILS"  # optional, defaults to "ILS"
}
mortgage = parse_mortgage(mortgage_dict)
```

### parse_pension(d: dict) → Pension | None
```python
pension_dict = {
    "initial_value": 2_000_000,
    "monthly_contribution": 9_000,
    "annual_growth_rate": 0.06,
    "accessible_at_age": 67  # optional, defaults to 67
}
pension = parse_pension(pension_dict)
```

**Returns None if dict is empty or None.** Used in parse_scenario to handle optional pension field.

### parse_events(event_list: list) → list[Event]
```python
events_list = [
    {"year": 2, "portfolio_injection": 2_000_000, "description": "Exit"},
    {"year": 5, "portfolio_injection": -500_000, "description": "Wedding"}
]
events = parse_events(events_list)
```

### parse_scenario(d: dict, default_return_rate, default_withdrawal_rate) → Scenario
Parses a flat scenario dict from scenarios.json. Uses provided defaults for rates if not in dict.

```python
scenario_dict = {
    "name": "Baseline",
    "monthly_income": 45_000,
    "monthly_expenses": 25_000,
    "mortgage": {...},             # optional
    "pension": {...},              # optional
    "events": [...],               # optional
    "return_rate": 0.07,           # optional
    "withdrawal_rate": 0.04,       # optional
    "currency": "ILS",             # optional
    "age": 41,                     # optional
    "initial_portfolio": 0.0       # optional
}
scenario = parse_scenario(scenario_dict, default_return_rate=0.07, default_withdrawal_rate=0.04)
```

**Pension field** (added in v2): Optional pension dict is parsed via `parse_pension()`. If not present, scenario.pension is None.

### parse_scenario_node(d: dict, all_scenarios: dict) → ScenarioNode
Parses a tree node from scenario_nodes.json. Resolves base_scenario names against all_scenarios dict.

```python
node_dict = {
    "name": "Alon - Buy Apartment",
    "parent": "Alon Baseline",     # Root: use "base_scenario" instead
    "mortgage": {...},
    "event_mode": "append",        # or "replace"
    "events": [...]
}
node = parse_scenario_node(node_dict, all_scenarios)
```

## Loaders (loaders.py)

Consolidated loading of all config files with default paths.

### Settings & OutputConfig Dataclasses
```python
@dataclass
class OutputConfig:
    show_fields: List[str] = [
        "income_expenses",
        "mortgage_details",
        "events",
        "rates_settings"
    ]

@dataclass
class Settings:
    years: int = 40
    return_rate: float = 0.07
    withdrawal_rate: float = 0.04
    output: OutputConfig = OutputConfig()
```

### load_settings(path=) → Settings
Loads settings.json. Merges JSON values with defaults.

```json
{
  "simulation": {
    "years": 20,
    "return_rate": 0.07,
    "withdrawal_rate": 0.04
  },
  "output": {
    "show_fields": ["income_expenses", "mortgage_details"]
  }
}
```

**Result:** `SETTINGS = load_settings()` — singleton loaded at import time.

### load_scenarios(path=) → dict[str, Scenario]
Loads scenarios.json. Returns dict keyed by scenario name.

```json
{
  "scenarios": [
    {
      "name": "Baseline",
      "monthly_income": 45_000,
      "monthly_expenses": 25_000,
      ...
    },
    {
      "name": "Buy Apartment",
      ...
    }
  ]
}
```

**Usage:**
```python
scenarios = load_scenarios()
baseline = scenarios["Baseline"]
```

### load_scenario_nodes(path=) → dict[str, ScenarioNode]
Loads scenario_nodes.json, validates tree structure, returns dict keyed by node name.

**Validation checks:**
- All parent_name references exist
- No cycles (walk ancestor chains)
- All root nodes have base_scenario set

**Raises:** ValueError if validation fails.

### _validate_nodes(nodes: dict) → None
Internal validation. Called by load_scenario_nodes.

## Cache (cache.py)

Serializes SimulationResult to JSON for decoupled analysis workflow.

### Serialization

**year_data_to_dict(year_data) → dict**
Converts YearData object to plain dict with 9 fields (including pension_value, pension_accessible).

**simulation_result_to_dict(result) → dict**
Converts SimulationResult to dict: scenario_name, retirement_year, year_data list.

### Deserialization

**dict_to_simulation_result(data: dict) → SimulationResult**
Reconstructs SimulationResult from cached dict. Inverse of serialization.

**Backward compatible:** If cache doesn't have pension fields (old format), defaults to 0.0 and False.

### File I/O

**save_cache(results: dict, path: Path) → None**
Writes cache JSON with metadata:
```json
{
  "generated_at": "2026-04-12T08:52:19",
  "num_scenarios": 8,
  "results": {
    "Alon Baseline": {...},
    "Alon - Buy Apartment": {...}
  }
}
```

**load_cache(path: Path) → dict | None**
Loads cache JSON, returns results dict or None if missing.

## Workflow: Decoupled Simulation & Analysis

**Step 1:** Simulate all scenarios once, save results
```bash
python analysis/run_simulations.py
# Creates: scenario_analysis/simulation_cache.json
```

**Step 2:** Load cache, run analysis many times
```bash
python analysis/run_analysis.py
# Reads: scenario_analysis/simulation_cache.json
# No re-simulation!
```

**Step 3:** Modify analysis.json, re-run Step 2
```bash
python analysis/run_analysis.py
# Same cached results, new output format!
```

**Benefits:**
- 100x faster iteration on analysis/output
- Consistent results across runs
- Easy to add new analyses (edit JSON only)

## Profile-Based Data Layer (data_layer.py)

Supports multiple profiles (e.g., default, alon, daniel) with separate configurations and caches.

### Profile Directory Structure
```
data/profiles/{profile_name}/
├── profile.json                    # Metadata (name, description, created_at)
├── settings.json                   # Simulation settings
├── scenarios.json                  # Scenario definitions
├── scenario_nodes.json             # Scenario tree (inheritance)
└── analyses/
    ├── config.json                 # Analysis definitions
    ├── cache/
    │   └── simulation_cache.json    # Generated by run_simulations.py
    └── results/
        └── 2026-04-12T...json      # Generated by run_analysis.py
```

### Switching Profiles with Environment Variable

```bash
# Use default profile (Daniel)
python analysis/run_simulations.py

# Switch to alon profile
FINANCE_PROFILE=alon python analysis/run_simulations.py
FINANCE_PROFILE=alon python analysis/run_analysis.py

# Use any other profile
FINANCE_PROFILE=custom_profile python analysis/run_simulations.py
```

**Default:** If FINANCE_PROFILE is not set, uses `default` profile.

### Profile Helper Functions (data_layer.py)
- `get_profile_dir(profile)` — Root directory for a profile
- `get_settings_path(profile)` — Path to settings.json
- `get_scenarios_path(profile)` — Path to scenarios.json
- `get_scenario_nodes_path(profile)` — Path to scenario_nodes.json
- `get_analysis_config_path(profile)` — Path to analyses/config.json
- `get_cache_path(profile)` — Path to analyses/cache/simulation_cache.json
- `get_results_dir(profile)` — Path to analyses/results/
- `profile_exists(profile)` — Check if profile directory exists

### Active Profile in Loaders
```python
from infrastructure.data_layer import ACTIVE_PROFILE

# ACTIVE_PROFILE is read from FINANCE_PROFILE env var at module load time
# All loaders.py functions use ACTIVE_PROFILE for file paths
scenarios = load_scenarios()  # Loads from ACTIVE_PROFILE, not hard-coded default
```

## Usage Examples

### Load all scenarios
```python
from infrastructure.loaders import load_scenarios, SETTINGS
from domain.simulation import simulate

scenarios = load_scenarios()
result = simulate(scenarios["Baseline"], years=SETTINGS.years)
```

### Load scenario tree
```python
from infrastructure.loaders import load_scenario_nodes
from domain.simulation import simulate

nodes = load_scenario_nodes()
resolved = nodes["Alon - Buy Apartment + Exit"].resolve(nodes)
result = simulate(resolved, years=20)
```

### Load with profile switching
```bash
# Set environment variable before running
export FINANCE_PROFILE=alon

# Then Python code loads from alon profile automatically
python your_script.py
```

```python
# Inside your_script.py:
from infrastructure.loaders import load_scenario_nodes
from infrastructure.data_layer import ACTIVE_PROFILE

print(f"Using profile: {ACTIVE_PROFILE}")  # Prints: "alon"
nodes = load_scenario_nodes()               # Loads from data/profiles/alon/scenario_nodes.json
```

### Use cached results
```python
from infrastructure.cache import load_cache, dict_to_simulation_result

cache = load_cache(Path("scenario_analysis/simulation_cache.json"))
result = dict_to_simulation_result(cache["Alon Baseline"])
# No simulation needed!
```

## Configuration Files (JSON)

All config files are now **profile-specific** under `data/profiles/{profile}/`.

### scenarios.json
Located at `data/profiles/{profile}/scenarios.json`. Flat scenario definitions. Can include `pension` field for optional pension modeling.

**Example with pension:**
```json
{
  "scenarios": [
    {
      "name": "Baseline with Pension",
      "monthly_income": 45000,
      "monthly_expenses": 25000,
      "initial_portfolio": 1400000,
      "age": 41,
      "pension": {
        "initial_value": 2000000,
        "monthly_contribution": 9000,
        "annual_growth_rate": 0.06,
        "accessible_at_age": 67
      }
    }
  ]
}
```

### scenario_nodes.json
Located at `data/profiles/{profile}/scenario_nodes.json`. Tree nodes for scenario inheritance.

### analysis.json (analyses/config.json)
Located at `data/profiles/{profile}/analyses/config.json`. Analysis definitions.

### simulation_cache.json
Generated by `analysis/run_simulations.py`. Stores all simulation results.

## Key Design Principles

1. **Consolidation:** Eliminate parsing duplication (Mortgage/Event in both scenarios.py and scenario_nodes.py)
2. **Validation:** Validate tree structure at load time, not resolve time
3. **Defaults:** Settings provide sensible defaults; JSON overrides as needed
4. **Singletons:** SETTINGS loaded at import time (cached)
5. **Pure parsing:** Parsers have no side effects, no I/O
6. **Decoupled:** Cache enables analysis without re-simulation
