"""
Generic analysis runner: load analysis.json and execute all analyses.

This script interprets analysis.json (pure configuration) and executes the
specified analyses without any Python code changes. New analysis types require
adding a handler function, but new analyses only require JSON updates.

DECOUPLED WORKFLOW:
  1. python run_simulations.py      → Run all scenarios, cache to simulation_cache.json
  2. python run_analysis.py         → Load cache, produce analysis output

This allows fast iteration on analysis/output without re-simulating.
Fallback: If cache doesn't exist, simulates inline (slower but works).
"""

import json
from pathlib import Path
from dataclasses import replace
from typing import Dict, Any, List

from infrastructure.loaders import load_scenario_nodes
from domain.models import ScenarioNode, Event
from domain.simulation import simulate, SimulationResult
from domain.insights import build_insights, format_insights
from infrastructure.cache import load_cache, dict_to_simulation_result
from infrastructure.data_layer import (
    get_analysis_config_path,
    get_cache_path,
    save_run_result,
    DEFAULT_PROFILE,
)


def load_analyses(path: Path) -> List[Dict[str, Any]]:
    """Load analysis definitions from JSON."""
    with open(path) as f:
        data = json.load(f)
    return data.get("analyses", [])


def create_variant_node(
    base_node: ScenarioNode,
    variant_overrides: Dict[str, Any],
    variant_label: str
) -> ScenarioNode:
    """
    Create a variant of a scenario node by applying parameter overrides.

    Args:
        base_node: The base ScenarioNode to variant
        variant_overrides: Dict of field overrides (e.g., {"monthly_income": 50000})
        variant_label: Label for the variant (appended to node name)

    Returns:
        New ScenarioNode with overrides applied
    """
    # Build new fields dict from overrides
    new_fields = {}

    # Apply scalar overrides
    for key in [
        "monthly_income",
        "monthly_expenses",
        "age",
        "initial_portfolio",
        "return_rate",
        "withdrawal_rate",
        "currency",
    ]:
        if key in variant_overrides:
            new_fields[key] = variant_overrides[key]

    # Apply mortgage override if present
    if "mortgage" in variant_overrides:
        new_fields["mortgage"] = variant_overrides["mortgage"]

    # Apply events override if present (replaces, not appends)
    if "events" in variant_overrides:
        new_fields["events"] = variant_overrides["events"]
        new_fields["event_mode"] = "replace"

    # Create new node with updated name and fields
    variant_name = f"{base_node.name} ({variant_label})"

    return replace(base_node, name=variant_name, **new_fields)


def simulate_scenario(
    node: ScenarioNode,
    all_nodes: Dict[str, ScenarioNode],
    cached_results: Dict[str, SimulationResult] = None,
    years: int = 20
) -> SimulationResult:
    """
    Get simulation result for a scenario node.

    Tries to use cached result first; falls back to running simulation.
    """
    # Check cache first
    if cached_results and node.name in cached_results:
        return cached_results[node.name]

    # Fallback: simulate inline
    resolved = node.resolve(all_nodes)
    return simulate(resolved, years=years)


# ============================================================================
# Analysis Handler Functions
# ============================================================================


def handle_parameter_pair_comparison(analysis: Dict[str, Any], all_nodes: Dict[str, ScenarioNode], cached_results: Dict[str, SimulationResult] = None):
    """
    Handle parameter_pair_comparison analysis.

    Compares scenarios at two different parameter values (e.g., ₪45K vs ₪25K income).
    """
    title = analysis.get("title", "Parameter Pair Comparison")
    scenario_names = analysis.get("scenarios", [])
    variations = analysis.get("variations", {})
    pairs = analysis.get("pairs", [])
    metrics = analysis.get("metrics", [])
    outputs = analysis.get("outputs", [])

    print(f"\n{'='*120}")
    print(title.center(120))
    print(f"{'='*120}\n")

    # For each pair, compare scenarios
    for pair in pairs:
        var1_label = pair.get("var1")
        var2_label = pair.get("var2")
        var1_overrides = variations.get(var1_label, {})
        var2_overrides = variations.get(var2_label, {})

        # Simulate all scenarios for both variations
        for scenario_name in scenario_names:
            base_node = all_nodes[scenario_name]

            # Create variants
            node_var1 = create_variant_node(base_node, var1_overrides, var1_label)
            node_var2 = create_variant_node(base_node, var2_overrides, var2_label)

            # Create temporary all_nodes dict with variants
            temp_nodes = {
                **all_nodes,
                node_var1.name: node_var1,
                node_var2.name: node_var2,
            }

            # Simulate both
            result_var1 = simulate_scenario(node_var1, temp_nodes, cached_results)
            result_var2 = simulate_scenario(node_var2, temp_nodes, cached_results)

            # Print scenario comparison
            print(f"\n{scenario_name}")
            print(f"{'='*120}\n")

            # Print yearly portfolio growth graph
            comparison_results = {
                var1_label: result_var1,
                var2_label: result_var2,
            }
            plot_scenarios_graph(comparison_results)

            print_metric_comparison(result_var1, result_var2, metrics, var1_label, var2_label)

            # Print insights if requested
            if "insights" in outputs:
                print(f"\nInsights:")
                insights = build_insights(result_var1, result_var2)
                for line in format_insights(insights).split("\n"):
                    print(f"  {line}")


def handle_parameter_sweep(analysis: Dict[str, Any], all_nodes: Dict[str, ScenarioNode], cached_results: Dict[str, SimulationResult] = None):
    """
    Handle parameter_sweep analysis.

    Sweeps a parameter across a range and tests variations.
    Example: income ₪25K-₪50K, with/without exit event.
    """
    title = analysis.get("title", "Parameter Sweep")
    base_scenario_name = analysis.get("base_scenario")
    parameter = analysis.get("parameter")
    param_range = analysis.get("range", {})
    test_variations = analysis.get("test_variations", [])
    metrics = analysis.get("metrics", [])
    outputs = analysis.get("outputs", [])

    min_val = param_range.get("min")
    max_val = param_range.get("max")
    step = param_range.get("step")

    print(f"\n{'='*120}")
    print(title.center(120))
    print(f"{'='*120}\n")

    # Collect results for all parameter values and variations
    results = {}  # {param_value: {variation_name: result}}

    param_values = []
    current = min_val
    while current <= max_val:
        param_values.append(current)
        current += step

    # Simulate all combinations
    for param_value in param_values:
        results[param_value] = {}
        param_override = {parameter: param_value}

        for variation in test_variations:
            var_name = variation.get("name")
            var_events = variation.get("events", [])

            # Create variant
            base_node = all_nodes[base_scenario_name]
            var_overrides = {
                **param_override,
                "events": [Event(**e) for e in var_events] if var_events else [],
                "event_mode": "replace" if var_events else "append"
            }

            variant_node = create_variant_node(base_node, var_overrides, f"{var_name} @ {parameter}={param_value}")

            temp_nodes = {**all_nodes, variant_node.name: variant_node}
            result = simulate_scenario(variant_node, temp_nodes, cached_results)
            results[param_value][var_name] = result

    # Print graphs for each variation
    print("\n[YEARLY PORTFOLIO GROWTH BY INCOME LEVEL]")
    print("="*120)
    for variation in test_variations:
        var_name = variation.get("name")
        print(f"\n{var_name}")
        print("-"*120)

        # Collect results for this variation across all income levels
        variation_results = {}
        for param_value in param_values:
            if param_value in results and var_name in results[param_value]:
                label = f"₪{param_value//1000}K"
                variation_results[label] = results[param_value][var_name]

        if variation_results:
            plot_scenarios_graph(variation_results)

    # Print detailed tables
    if "detailed_tables" in outputs:
        print_sweep_detailed_tables(results, test_variations, parameter, param_values, metrics)

    # Print comparison table
    if "comparison_table" in outputs:
        print_sweep_comparison_table(results, test_variations, parameter, param_values)

    # Print impact analysis
    if "impact_analysis" in outputs:
        print_sweep_impact_analysis(results, test_variations, parameter, param_values)


def handle_milestone_snapshots(analysis: Dict[str, Any], all_nodes: Dict[str, ScenarioNode], cached_results: Dict[str, SimulationResult] = None):
    """
    Handle milestone_snapshots analysis.

    Shows scenario snapshots at specific years (milestones).
    """
    title = analysis.get("title", "Milestone Snapshots")
    scenarios = analysis.get("scenarios", [])
    milestones = analysis.get("milestones", [1, 5, 10, 15, 20])
    metrics = analysis.get("metrics", [])
    outputs = analysis.get("outputs", [])

    print(f"\n{'='*120}")
    print(title.center(120))
    print(f"{'='*120}\n")

    # Simulate all scenarios
    results = {}
    for scenario_info in scenarios:
        label = scenario_info.get("label")
        node_name = scenario_info.get("node")
        node = all_nodes[node_name]
        result = simulate_scenario(node, all_nodes, cached_results)
        results[label] = result

    # Print yearly portfolio growth graph
    plot_scenarios_graph(results)

    # Print milestone table
    if "milestone_table" in outputs:
        print_milestone_table(results, milestones, metrics)

    # Print comparison summary
    if "comparison_summary" in outputs:
        print_milestone_summary(results)


def handle_tree_exploration(analysis: Dict[str, Any], all_nodes: Dict[str, ScenarioNode], cached_results: Dict[str, SimulationResult] = None):
    """
    Handle tree_exploration analysis.

    Shows tree structure, simulations, and pairwise comparisons.
    """
    title = analysis.get("title", "Scenario Tree Exploration")
    scenario_names = analysis.get("scenarios", [])
    outputs = analysis.get("outputs", [])

    print(f"\n{'='*120}")
    print(title.center(120))
    print(f"{'='*120}\n")

    # Print tree structure
    if "tree_structure" in outputs:
        print("[1] TREE STRUCTURE")
        print("-" * 120)
        for name in scenario_names:
            node = all_nodes[name]
            ancestors = []
            current = node
            while current.parent_name:
                ancestors.insert(0, current.parent_name)
                current = all_nodes[current.parent_name]

            ancestor_str = " ← ".join(ancestors) if ancestors else "ROOT"
            print(f"\n{name}")
            print(f"  Ancestors: {ancestor_str}")

            # Show what this node defines
            unique_attrs = []
            if node.mortgage:
                unique_attrs.append(f"Mortgage ₪{node.mortgage.principal:,.0f}")
            if node.monthly_income is not None:
                unique_attrs.append(f"Income ₪{node.monthly_income:,.0f}")
            if node.events:
                unique_attrs.append(f"{len(node.events)} event(s)")

            if unique_attrs:
                print(f"  Defines: {', '.join(unique_attrs)}")
            else:
                print(f"  Defines: inherits all fields from parent")

    # Simulate all scenarios
    results = {}
    for name in scenario_names:
        result = simulate_scenario(all_nodes[name], all_nodes, cached_results)
        results[name] = result

    # Print yearly portfolio growth graph
    plot_scenarios_graph(results)

    # Print simulations
    if "simulations" in outputs:
        print("\n[2] SIMULATIONS (20-year horizon)")
        print("-" * 120)
        for name, result in results.items():
            retirement = f"Year {result.retirement_year}" if result.retirement_year else "Never"
            final_portfolio = result.year_data[-1].portfolio
            print(f"\n{name}")
            print(f"  Retirement: {retirement}")
            print(f"  Final portfolio: ₪{final_portfolio:,.0f}")

    # Print pairwise comparisons
    if "pairwise_comparisons" in outputs:
        print("\n[3] PAIRWISE COMPARISONS")
        print("-" * 120)
        for i, name_a in enumerate(scenario_names):
            for name_b in scenario_names[i+1:]:
                print(f"\n{name_a} vs {name_b}")
                insights = build_insights(results[name_a], results[name_b])
                for line in format_insights(insights).split("\n"):
                    print(f"  {line}")


# ============================================================================
# Output Formatting Helper Functions
# ============================================================================


def print_metric_comparison(result_a: SimulationResult, result_b: SimulationResult,
                           metrics: List[str], label_a: str, label_b: str):
    """Print metric comparison between two scenarios."""
    print(f"{'Metric':<40} {f'{label_a}':<35} {f'{label_b}':<35}")
    print("-" * 120)

    for metric in metrics:
        if metric == "retirement_year":
            ret_a = f"Year {result_a.retirement_year}" if result_a.retirement_year else "Never"
            ret_b = f"Year {result_b.retirement_year}" if result_b.retirement_year else "Never"
            print(f"{'Retirement Year':<40} {ret_a:<35} {ret_b:<35}")

        elif metric == "age_at_retirement":
            if result_a.retirement_year:
                age_a = 41 + result_a.retirement_year
                print(f"{'Age at Retirement':<40} {age_a:<35} {'':<35}")
            if result_b.retirement_year:
                age_b = 41 + result_b.retirement_year
                if result_a.retirement_year:
                    age_diff = age_b - age_a
                    print(f"{'Age Difference':<40} {'':<35} {f'(+{age_diff} years)':<35}")

        elif metric == "portfolio_year_10":
            if len(result_a.year_data) > 9:
                port_a = result_a.year_data[9].portfolio
                port_b = result_b.year_data[9].portfolio
                print(f"{'Portfolio at Year 10':<40} ₪{port_a:>33,.0f} ₪{port_b:>33,.0f}")
                diff = port_b - port_a
                print(f"{'  Difference':<40} {'':<35} ₪{diff:>33,.0f}")

        elif metric == "portfolio_final":
            port_a = result_a.year_data[-1].portfolio
            port_b = result_b.year_data[-1].portfolio
            print(f"{'Portfolio at Year 20':<40} ₪{port_a:>33,.0f} ₪{port_b:>33,.0f}")
            diff = port_b - port_a
            print(f"{'  Difference':<40} {'':<35} ₪{diff:>33,.0f}")

        elif metric == "annual_savings":
            savings_a = result_a.year_data[0].net_savings
            savings_b = result_b.year_data[0].net_savings
            print(f"{'Annual Savings (Year 1)':<40} ₪{savings_a:>33,.0f} ₪{savings_b:>33,.0f}")
            diff = savings_b - savings_a
            print(f"{'  Difference':<40} {'':<35} ₪{diff:>33,.0f}")


def print_sweep_detailed_tables(results: Dict, test_variations: List[Dict],
                               parameter: str, param_values: List[float],
                               metrics: List[str]):
    """Print detailed tables for parameter sweep."""
    for variation in test_variations:
        var_name = variation.get("name")

        print(f"\n{'='*100}")
        print(f"SCENARIO: {var_name}".center(100))
        print(f"{'='*100}\n")

        print(f"{'Monthly Income':<20} {'Retirement Year':<20} {'Final Portfolio':<25}")
        print("-" * 100)

        for param_value in param_values:
            if param_value in results and var_name in results[param_value]:
                result = results[param_value][var_name]
                param_label = f"₪{param_value//1000}K"
                ret = f"Year {result.retirement_year}" if result.retirement_year else "Never (20y+)"
                portfolio = result.year_data[-1].portfolio

                print(f"{param_label:<20} {ret:<20} ₪{portfolio:>21,.0f}")

        print()


def print_sweep_comparison_table(results: Dict, test_variations: List[Dict],
                                 parameter: str, param_values: List[float]):
    """Print side-by-side comparison of variations."""
    print(f"\n{'='*140}")
    print("COMPARISON TABLE: WITH EXIT vs WITHOUT EXIT".center(140))
    print(f"{'='*140}\n")

    if len(test_variations) >= 2:
        var_without = test_variations[0].get("name")
        var_with = test_variations[1].get("name")

        print(f"{'Income':<12} | {f'WITHOUT {var_with}':<35} | {f'WITH {var_with}':<35} | {'Exit Impact':<35}")
        print(f"{'':12} | {'Retirement':<12} {'Portfolio':<22} | {'Retirement':<12} {'Portfolio':<22} | {'Years Saved':<12} {'Portfolio +':<22}")
        print("-" * 140)

        for param_value in param_values:
            if param_value in results:
                param_label = f"₪{param_value//1000}K"

                result_without = results[param_value].get(var_without)
                result_with = results[param_value].get(var_with)

                if result_without and result_with:
                    ret_without = f"Year {result_without.retirement_year}" if result_without.retirement_year else "Never"
                    ret_with = f"Year {result_with.retirement_year}" if result_with.retirement_year else "Never"

                    port_without = result_without.year_data[-1].portfolio
                    port_with = result_with.year_data[-1].portfolio

                    if result_without.retirement_year and result_with.retirement_year:
                        years_saved = result_without.retirement_year - result_with.retirement_year
                        years_str = f"{years_saved:+.0f} years"
                    else:
                        years_str = "N/A"

                    port_diff = port_with - port_without
                    port_diff_pct = (port_diff / port_without) * 100 if port_without > 0 else 0
                    port_diff_str = f"₪{port_diff:+,.0f} ({port_diff_pct:+.1f}%)"

                    print(f"{param_label:<12} | {ret_without:<12} ₪{port_without:>17,.0f} | {ret_with:<12} ₪{port_with:>17,.0f} | {years_str:<12} {port_diff_str:<22}")


def print_sweep_impact_analysis(results: Dict, test_variations: List[Dict],
                               parameter: str, param_values: List[float]):
    """Print impact analysis of variations."""
    print(f"\n{'='*100}")
    print("EXIT EVENT IMPACT ANALYSIS".center(100))
    print(f"{'='*100}\n")

    if len(test_variations) >= 2:
        var_without = test_variations[0].get("name")
        var_with = test_variations[1].get("name")

        impacts = []
        for param_value in param_values:
            if param_value in results:
                result_without = results[param_value].get(var_without)
                result_with = results[param_value].get(var_with)

                if result_without and result_with:
                    ret_without = result_without.retirement_year
                    ret_with = result_with.retirement_year

                    if ret_without and ret_with:
                        years_saved = ret_without - ret_with
                    else:
                        years_saved = None

                    port_without = result_without.year_data[-1].portfolio
                    port_with = result_with.year_data[-1].portfolio
                    port_increase = port_with - port_without
                    port_increase_pct = (port_increase / port_without) * 100 if port_without > 0 else 0

                    impacts.append({
                        'param': param_value,
                        'label': f"₪{param_value//1000}K",
                        'years_saved': years_saved,
                        'port_increase': port_increase,
                        'port_increase_pct': port_increase_pct,
                    })

        print(f"{'Income':<12} | {'Retirement Without':<20} | {'Retirement With':<20} | {'Years Saved':<15} | {'Portfolio Impact':<25}")
        print("-" * 100)

        for impact in impacts:
            years_str = f"{impact['years_saved']} years" if impact['years_saved'] else "N/A"
            port_str = f"₪{impact['port_increase']:+,.0f} ({impact['port_increase_pct']:+.1f}%)"
            print(f"{impact['label']:<12} | {'':<20} | {'':<20} | {years_str:<15} | {port_str:<25}")


def print_milestone_table(results: Dict, milestones: List[int], metrics: List[str]):
    """Print milestone snapshot table."""
    print("[MILESTONE SNAPSHOTS]")
    print("-" * 120)

    # Build header
    header = "Year".ljust(8)
    for label in results.keys():
        header += f" | {label:<35}"
    print(header)
    print("-" * 120)

    # Print each milestone
    for milestone in milestones:
        row = f"{milestone:<8}"
        for label, result in results.items():
            if milestone <= len(result.year_data):
                year_data = result.year_data[milestone - 1]
                portfolio = year_data.portfolio
                row += f" | ₪{portfolio:>30,.0f}"
            else:
                row += f" | {'N/A':<35}"
        print(row)


def plot_scenarios_graph(results: Dict):
    """Create ASCII graph showing yearly portfolio values for all scenarios."""
    if not results:
        return

    # Get all year data
    scenarios = {}
    max_years = 0
    for label, result in results.items():
        portfolios = [yd.portfolio for yd in result.year_data]
        scenarios[label] = portfolios
        max_years = max(max_years, len(portfolios))

    if max_years == 0:
        return

    # Find min/max portfolio values for scaling
    all_portfolios = []
    for portfolios in scenarios.values():
        all_portfolios.extend(portfolios)

    min_val = min(all_portfolios)
    max_val = max(all_portfolios)

    # Add some padding
    range_val = max_val - min_val
    min_val = max(0, min_val - range_val * 0.05)
    max_val = max_val + range_val * 0.05

    # Create graph dimensions
    graph_height = 15
    graph_width = max_years

    # Create grid
    grid = [[' ' for _ in range(graph_width)] for _ in range(graph_height)]

    # Plot each scenario with a different character
    chars = ['█', '▓', '▒', '░', '●', '○', '◆', '◇', '■', '□']
    scenario_chars = {label: chars[i % len(chars)] for i, label in enumerate(sorted(scenarios.keys()))}

    for label, portfolios in scenarios.items():
        char = scenario_chars[label]
        for year_idx, portfolio in enumerate(portfolios):
            if year_idx < graph_width:
                # Scale portfolio to grid height
                if max_val > min_val:
                    normalized = (portfolio - min_val) / (max_val - min_val)
                else:
                    normalized = 0.5

                row = int((1 - normalized) * (graph_height - 1))
                row = max(0, min(graph_height - 1, row))

                # Plot character
                if grid[row][year_idx] == ' ':
                    grid[row][year_idx] = char
                else:
                    grid[row][year_idx] = '+'  # Overlap indicator

    # Print graph
    print("\n[YEARLY PORTFOLIO GROWTH]")
    print("-" * (graph_width + 15))

    # Print Y-axis labels and grid
    y_labels = []
    for i in range(graph_height):
        normalized = 1 - (i / (graph_height - 1))
        value = min_val + normalized * (max_val - min_val)
        y_labels.append(value)

    for row_idx in range(graph_height):
        # Y-axis label
        value = y_labels[row_idx]
        label = f"₪{value/1_000_000:>4.1f}M"

        # Grid content
        line = ''.join(grid[row_idx])
        print(f"{label} │{line}")

    # X-axis
    print("      ├" + "─" * graph_width)

    # X-axis labels (years)
    x_labels = "      │"
    for year in range(1, max_years + 1):
        if year % 2 == 1:
            x_labels += str(year % 10)
        else:
            x_labels += " "
    print(x_labels)

    # Legend
    print("\n[LEGEND]")
    for label in sorted(scenarios.keys()):
        char = scenario_chars[label]
        final_port = scenarios[label][-1] if scenarios[label] else 0
        print(f"  {char} {label:<40} → ₪{final_port:>12,.0f}")


def print_milestone_summary(results: Dict):
    """Print milestone summary with key metrics."""
    print("\n[SUMMARY]")
    print("-" * 120)

    for label, result in results.items():
        retirement_str = f"Year {result.retirement_year}" if result.retirement_year else "Never (20y+)"
        final_portfolio = result.year_data[-1].portfolio

        print(f"\n{label}")
        print(f"  Retirement: {retirement_str}")
        print(f"  Final Portfolio: ₪{final_portfolio:,.0f}")


# ============================================================================
# Main Entry Point
# ============================================================================


def print_assumptions():
    """Display key assumptions used in all analyses."""
    print(f"\n{'='*120}")
    print("IMPORTANT ASSUMPTIONS".center(120))
    print(f"{'='*120}\n")

    print("Scenario Parameters:")
    print("  • Base Income: ₪45,000/month")
    print("  • Base Expenses: ₪25,000/month")
    print("  • Monthly Savings: ₪20,000")
    print("  • Initial Portfolio: ₪1,400,000 (₪900K + ₪500K)")
    print("  • Current Age: 41 years old")

    print("\nSimulation Assumptions:")
    print("  • Time Horizon: 20 years")
    print("  • Investment Return Rate: 5% annually")
    print("  • Safe Withdrawal Rate: 4% (retirement threshold)")
    print("  • Currency: Israeli Shekel (₪)")

    print("\nLife Events (Baseline):")
    print("  • Year 2: Surrogacy expense -₪500,000 (one-time)")

    print("\nExit Events (when applicable):")
    print("  • ₪2M Exit: Company exit proceeds ₪2,000,000 (year 1)")
    print("  • ₪3M Exit: Company exit proceeds ₪3,000,000 (year 1)")

    print("\nRetirement Definition:")
    print("  • Portfolio ≥ (Annual Expenses / Withdrawal Rate)")
    print("  • Example: ₪300K expenses ÷ 0.04 = ₪7.5M threshold")

    print("\nMortgage (when applicable):")
    print("  • Principal: ₪2,250,000")
    print("  • Interest Rate: 4% annually")
    print("  • Duration: 25 years")
    print("  • Monthly Payment: ~₪11,323")

    print("\n" + "="*120 + "\n")


def main():
    # Use profile-based data layer (fixes path mismatch bug)
    analysis_file = get_analysis_config_path(DEFAULT_PROFILE)
    cache_file = get_cache_path(DEFAULT_PROFILE)

    print("\n" + "="*120)
    print("SCENARIO ANALYSIS RUNNER".center(120))
    print("="*120)

    # Load analyses
    analyses = load_analyses(analysis_file)
    print(f"\nLoaded {len(analyses)} analysis/analyses from {analysis_file.name}")

    # Try to load cache first (fast path)
    cached_results = load_cache(cache_file)

    if cached_results:
        print(f"✓ Using cached simulation results from {cache_file.name}")
        cache_meta = json.load(open(cache_file))
        print(f"  Generated: {cache_meta.get('generated_at', 'unknown')}")
        print(f"  Scenarios: {cache_meta.get('num_scenarios', len(cached_results))}")

        # Convert cached dicts to SimulationResult objects
        all_cached_results = {
            name: dict_to_simulation_result(data)
            for name, data in cached_results.items()
        }

        # For handlers that need scenario nodes (tree_exploration), load them
        all_nodes = load_scenario_nodes()
        print(f"Loaded {len(all_nodes)} scenario nodes from scenario_nodes.json")

    else:
        print(f"⚠️  No cache found at {cache_file.name}")
        print("   Run: python scenario_analysis/run_simulations.py")
        print("   Falling back to inline simulation (slower)...\n")

        # Fallback: load nodes and simulate inline
        all_nodes = load_scenario_nodes()
        print(f"Loaded {len(all_nodes)} scenario nodes from scenario_nodes.json")

        # Simulate all scenarios
        all_cached_results = {}
        for name, node in all_nodes.items():
            resolved = node.resolve(all_nodes)
            result = simulate(resolved, years=20)
            all_cached_results[name] = result

    # Print assumptions
    print_assumptions()

    # Dispatch to handlers based on analysis type
    handlers = {
        "parameter_pair_comparison": handle_parameter_pair_comparison,
        "parameter_sweep": handle_parameter_sweep,
        "milestone_snapshots": handle_milestone_snapshots,
        "tree_exploration": handle_tree_exploration,
    }

    for analysis in analyses:
        analysis_type = analysis.get("type")
        analysis_id = analysis.get("id", "unknown")

        if analysis_type not in handlers:
            print(f"⚠️  Unknown analysis type: {analysis_type} (id={analysis_id})")
            continue

        try:
            handler = handlers[analysis_type]
            # Pass cached results instead of nodes (handlers will use them)
            handler(analysis, all_nodes, all_cached_results)
        except Exception as e:
            print(f"\n❌ Error running analysis '{analysis_id}': {e}")
            import traceback
            traceback.print_exc()

    # Save run result with metadata
    analyses_run = [a.get("id", "unknown") for a in analyses]
    cache_generated_at = cache_meta.get("generated_at", "unknown") if 'cache_meta' in locals() else "inline"
    save_run_result(DEFAULT_PROFILE, {
        "analyses_run": analyses_run,
        "cache_generated_at": cache_generated_at,
        "num_scenarios": len(all_cached_results),
    })

    print(f"\n{'='*120}")
    print("Analysis complete".center(120))
    print("="*120 + "\n")


if __name__ == "__main__":
    main()
