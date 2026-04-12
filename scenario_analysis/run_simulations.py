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

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from scenario_analysis.scenario_nodes import load_scenario_nodes
from simulation import simulate


def year_data_to_dict(year_data) -> Dict[str, Any]:
    """Convert YearData object to a serializable dict."""
    return {
        "year": year_data.year,
        "income": year_data.income,
        "expenses": year_data.expenses,
        "net_savings": year_data.net_savings,
        "portfolio": year_data.portfolio,
        "required_capital": year_data.required_capital,
        "mortgage_active": year_data.mortgage_active,
    }


def simulation_result_to_dict(result) -> Dict[str, Any]:
    """Convert SimulationResult to a serializable dict."""
    return {
        "scenario_name": result.scenario_name,
        "retirement_year": result.retirement_year,
        "year_data": [year_data_to_dict(yd) for yd in result.year_data],
    }


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


def save_cache(results: Dict[str, Dict[str, Any]], path: Path) -> None:
    """Save simulation results to cache file."""
    cache_data = {
        "generated_at": datetime.now().isoformat(),
        "num_scenarios": len(results),
        "results": results,
    }

    with open(path, "w") as f:
        json.dump(cache_data, f, indent=2)

    print(f"✓ Cache saved to {path.name}")
    print(f"  Generated: {cache_data['generated_at']}")
    print(f"  Scenarios: {cache_data['num_scenarios']}")


def load_cache(path: Path) -> Dict[str, Dict[str, Any]]:
    """Load simulation results from cache file."""
    if not path.exists():
        return None

    with open(path) as f:
        cache_data = json.load(f)

    return cache_data.get("results", {})


def main():
    cache_file = Path(__file__).parent / "simulation_cache.json"

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
    print("  python scenario_analysis/run_analysis.py".center(80))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
