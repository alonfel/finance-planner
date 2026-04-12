# Documentation Index

Quick guide to all documentation in this project.

## Quick Start

Start here if you're new:
1. [README.md](README.md) — Project overview, quick start, 5-minute guide
2. [CLAUDE.md](CLAUDE.md) — How to work with this project (commands, workflows, editing guides)
3. Run: `python scenario_analysis/run_simulations.py` then `python scenario_analysis/run_analysis.py`

## Understanding the System

### Core Concepts
- **[SCENARIO_TREE_GUIDE.md](SCENARIO_TREE_GUIDE.md)** — How scenario inheritance works, why it matters, examples
- **[GRAPH_GUIDE.md](GRAPH_GUIDE.md)** — How to read portfolio graphs, tables, and insights
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — Technical design, data models, extension patterns

### Common Tasks

| Task | Where to Find | How Long |
|------|---|---|
| Run analysis | [CLAUDE.md Quick Start](CLAUDE.md#quick-start) | 2 min read |
| Add a new scenario | [CLAUDE.md Adding New Scenarios](CLAUDE.md#adding-new-scenarios-best-practices) | 5 min |
| Add a new analysis | [CLAUDE.md Configuration-Driven Analysis](CLAUDE.md#configuration-driven-analysis-analysisjson) | 5 min |
| Understand a graph | [GRAPH_GUIDE.md](GRAPH_GUIDE.md) | 10 min |
| Modify simulation logic | [ARCHITECTURE.md Extension Patterns](ARCHITECTURE.md#extension-patterns) | 15 min |
| Create scenario variations | [SCENARIO_TREE_GUIDE.md](SCENARIO_TREE_GUIDE.md) | 15 min |

## File-by-File Overview

### Documentation Files

| File | Purpose | Audience |
|------|---------|----------|
| [README.md](README.md) | Project overview, workflow, quick start, architecture diagram | Everyone |
| [CLAUDE.md](CLAUDE.md) | How to use this project: commands, workflows, editing guides, best practices | Users & developers |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Technical design, data models, algorithms, extension patterns | Developers |
| [SCENARIO_TREE_GUIDE.md](SCENARIO_TREE_GUIDE.md) | Scenario inheritance system, examples, use cases | Users planning scenarios |
| [GRAPH_GUIDE.md](GRAPH_GUIDE.md) | How to read portfolio growth graphs with annotated examples | Everyone |
| [DOCUMENTATION.md](DOCUMENTATION.md) | This file — index of all docs | Everyone |

### Configuration Files

| File | Purpose | Edit When | See Also |
|------|---------|-----------|----------|
| `scenarios.json` | Flat scenario definitions (one-off) | Adding simple, non-inherited scenarios | [CLAUDE.md Scenarios](CLAUDE.md#scenariosjson) |
| `scenario_analysis/scenario_nodes.json` | Scenario tree definitions (inheritance) | Adding scenario variations or multi-level trees | [SCENARIO_TREE_GUIDE.md](SCENARIO_TREE_GUIDE.md) |
| `scenario_analysis/analysis.json` | Analysis definitions | Defining what to analyze without code changes | [CLAUDE.md Analysis](CLAUDE.md#configuration-driven-analysis-analysisjson) |
| `settings.json` | Simulation & output config | Changing return rate, years, display fields | [CLAUDE.md Settings](CLAUDE.md#settingsjson) |

### Code Files

| File | Purpose | Modify When |
|------|---------|-------------|
| `simulation.py` | Core simulation engine (simulate function) | Extending simulation logic (rare) |
| `models.py` | Data models (Scenario, ScenarioNode, Mortgage, etc.) | Adding new scenario fields |
| `scenarios.py` / `scenario_nodes.py` | Load config from JSON | Adding new config options |
| `comparison.py` | Build & format insights | Changing insight types or output |
| `main.py` | Entry point for simple comparison | Changing basic workflow |
| `scenario_analysis/run_simulations.py` | Simulate all scenarios, save cache | Changing cache format (rare) |
| `scenario_analysis/run_analysis.py` | Load cache, run analyses | Adding new analysis types (rare) |

## Workflows

### Two-Step Analysis Workflow (Recommended)

```bash
# Step 1: Simulate (do once when scenarios change)
python scenario_analysis/run_simulations.py

# Step 2: Analyze (do many times for different outputs)
python scenario_analysis/run_analysis.py

# Modify analysis.json and re-run Step 2 — no re-simulation!
```

**When to re-simulate (Step 1):**
- After editing `scenario_nodes.json` (new nodes or parameters)
- After editing `settings.json` (return rate, years, etc.)

**When to just analyze (Step 2):**
- After editing `analysis.json` (different analyses)
- After editing graphs/tables output format
- When iterating on insights and reports

### Simple Comparison (Alternative)

```bash
python main.py
```

Simulates two fixed scenarios (SCENARIO_A and SCENARIO_B in main.py) and compares them.

### Running Tests

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

All 42 tests should pass.

## Architecture Overview

### Data Flow

```
scenarios.json                   scenario_nodes.json
      ↓                                 ↓
scenarios.py                    scenario_nodes.py
      ↓                                 ↓
Scenario objects ←────────────→ ScenarioNode objects
      ↓                                 ↓
      ├─→ simulation.py ←──────────────┘
      │        ↓
      │   SimulationResult
      │        ↓
      └─→ run_simulations.py
           ↓
   simulation_cache.json
           ↓
      run_analysis.py
           ↓
      analysis.json (defines what to analyze)
           ↓
    [Formatted Output]
    - Graphs
    - Tables
    - Insights
```

### Three Key Layers

1. **Simulation Layer** (`simulation.py`)
   - Pure functions, no state
   - Takes Scenario → Returns SimulationResult
   - 42 unit tests, all passing

2. **Analysis Layer** (`run_analysis.py` with caching via `run_simulations.py`)
   - Loads cached results (fast)
   - Falls back to inline simulation if needed (safe)
   - Produces formatted output

3. **Configuration Layer** (JSON files)
   - `scenarios.json` — Flat scenario definitions
   - `scenario_nodes.json` — Inheritance trees
   - `analysis.json` — What to analyze
   - `settings.json` — Simulation & display config

## Key Design Principles

### 1. Configuration-Driven
- Edit JSON to change behavior
- Don't edit Python unless adding new features
- Golden rule: Data changes → JSON edits, Feature changes → Python edits

### 2. Decoupled Simulation & Analysis
- Simulate once (expensive, 2 seconds)
- Analyze many times (fast, 1 second each)
- Cache enables rapid iteration on output format

### 3. Pure Functions
- `simulate(scenario) → SimulationResult` is deterministic
- No global state, no side effects
- Easy to test, easy to parallelize

### 4. Inheritance-Based Composition
- ScenarioNode enables scenario trees
- Child inherits from parent, overrides what changes
- DRY principle: avoid duplication across scenarios

### 5. Separation of Concerns
- Simulation (compute results)
- Analysis (organize results)
- Presentation (format output)
- Each layer can be modified independently

## Common Questions

### Q: When should I use scenarios.json vs scenario_nodes.json?
**A:** Use `scenarios.json` for one-off scenarios. Use `scenario_nodes.json` for scenario variations (inheritance trees). [More info](CLAUDE.md#when-to-use-scenariosjson-vs-scenario_nodesjson)

### Q: How do I add a new analysis?
**A:** Edit `scenario_analysis/analysis.json` and add an analysis block. No Python code needed. [Example](CLAUDE.md#add-a-new-analysis-recommended-edit-json-only)

### Q: How do I interpret the portfolio graphs?
**A:** See [GRAPH_GUIDE.md](GRAPH_GUIDE.md) for detailed walkthrough with examples.

### Q: Can I access the raw simulation results?
**A:** Yes! Load `scenario_analysis/simulation_cache.json` directly as JSON. [More info](DOCUMENTATION.md#decoupled-architecturerun_simulationspy)

### Q: What happens if I delete the cache?
**A:** `run_analysis.py` will simulate scenarios inline (slower). Run `python scenario_analysis/run_simulations.py` to recreate cache.

### Q: How do I extend the simulation with inflation?
**A:** See [ARCHITECTURE.md Extension Pattern 1](ARCHITECTURE.md#pattern-1-add-a-scenario-field).

## Resources

### Tools & Commands

```bash
# Simulate all scenarios, save cache
python scenario_analysis/run_simulations.py

# Run all analyses (uses cache)
python scenario_analysis/run_analysis.py

# Simple two-scenario comparison
python main.py

# Run tests
python -m unittest discover -s tests -p "test_*.py" -v

# Run specific test class
python -m unittest tests.test_simulation.TestMortgage -v
```

### Documentation Files (In Order)

1. **Quick Start** → [README.md](README.md) (5 min)
2. **How to Use** → [CLAUDE.md](CLAUDE.md) (15 min)
3. **Understanding Graphs** → [GRAPH_GUIDE.md](GRAPH_GUIDE.md) (10 min)
4. **Scenario Trees** → [SCENARIO_TREE_GUIDE.md](SCENARIO_TREE_GUIDE.md) (15 min)
5. **Technical Design** → [ARCHITECTURE.md](ARCHITECTURE.md) (20 min)
6. **Navigation** → [DOCUMENTATION.md](DOCUMENTATION.md) (5 min, this file)

## Version & Status

- **Status:** Production-ready
- **Tests:** 42 unit tests, all passing
- **Key Features:**
  - ✅ Decoupled simulation/analysis architecture
  - ✅ Scenario tree inheritance
  - ✅ Configuration-driven analysis
  - ✅ Portfolio growth graphs
  - ✅ Mortgage support
  - ✅ Event support
  - ✅ Multi-currency ready
  - ✅ 100% standard library (no external dependencies)

## Getting Help

- **How do I...?** → Check [CLAUDE.md](CLAUDE.md#common-tasks)
- **I don't understand the graph** → See [GRAPH_GUIDE.md](GRAPH_GUIDE.md)
- **I want to add a feature** → See [ARCHITECTURE.md#extension-patterns](ARCHITECTURE.md#extension-patterns)
- **I'm getting an error** → See [CLAUDE.md#troubleshooting](CLAUDE.md#troubleshooting)
- **I want to understand the design** → See [ARCHITECTURE.md](ARCHITECTURE.md)

---

**Last Updated:** 2026-04-12  
**Documentation Version:** 2.0 (with decoupled architecture & graphs)
