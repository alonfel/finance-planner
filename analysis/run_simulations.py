"""
Run all scenarios and cache results to JSON.

This decouples simulation (expensive) from analysis/output (fast iteration).

Workflow:
  1. python run_simulations.py    → Runs all scenarios, saves to simulation_cache.json
  2. python run_analysis.py       → Reads cache, produces analysis output
  3. Modify analysis.json and re-run step 2 → No re-simulation needed!

Benefits:
  - Fast iteration on analysis/output formats
  - Consistent results across multiple analysis runs
  - Easy to add new analyses without re-simulating
  - Cache survives across sessions
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from infrastructure.loaders import load_scenario_nodes
from domain.simulation import simulate
from infrastructure.cache import simulation_result_to_dict, save_cache, load_cache
from infrastructure.data_layer import get_cache_path, ACTIVE_PROFILE


def run_all_simulations(all_nodes: Dict, years: int = 20) -> Dict[str, Dict[str, Any]]:
    """
    Run all scenario nodes and return results as dicts.

    Returns:
        {scenario_name: simulation_result_dict}
    """
    results = {}

    print(f"\nRunning simulations for {len(all_nodes)} scenarios...")
    print("-" * 80)

    for i, (name, node) in enumerate(sorted(all_nodes.items()), 1):
        resolved = node.resolve(all_nodes)
        result = simulate(resolved, years=years)
        results[name] = simulation_result_to_dict(result)

        retirement_str = f"Year {result.retirement_year}" if result.retirement_year else "Never"
        final_portfolio = result.year_data[-1].portfolio
        print(f"[{i:2d}/{len(all_nodes)}] {name:<50} → Retire: {retirement_str:<15} Portfolio: ₪{final_portfolio:>12,.0f}")

    print("-" * 80)
    print(f"✓ Completed {len(results)} simulations\n")

    return results


def main():
    # Cache file location from profile-based data layer
    cache_file = get_cache_path(ACTIVE_PROFILE)
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print("SIMULATION RUNNER".center(80))
    print("=" * 80)

    # Load scenario tree
    print("\nLoading scenario tree...")
    all_nodes = load_scenario_nodes()
    print(f"✓ Loaded {len(all_nodes)} scenario nodes")

    # Run all simulations
    results = run_all_simulations(all_nodes, years=20)

    # Save cache
    save_cache(results, cache_file)

    print("\n" + "=" * 80)
    print("To analyze these results without re-simulating:".center(80))
    print("  python analysis/run_analysis.py".center(80))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
