"""
Explore scenario tree with inheritance.

Demonstrates how to:
1. Load a scenario tree
2. Resolve inherited scenarios
3. Simulate and compare variations
4. Understand compounding effects of incremental changes
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scenario_analysis.scenario_nodes import load_scenario_nodes
from simulation import simulate
from comparison import build_insights, format_insights


def main():
    nodes = load_scenario_nodes()

    print("\n" + "=" * 90)
    print("SCENARIO TREE EXPLORATION")
    print("=" * 90)

    # 1. Load and display tree structure
    print("\n[1] TREE STRUCTURE & COMPOSITION")
    print("-" * 90)

    tree_structure = {
        "Alon Baseline": [],
        "Alon - Buy Apartment": ["Alon Baseline"],
        "Alon - Buy Apartment + Exit": ["Alon - Buy Apartment"],
    }

    for node_name, ancestors in tree_structure.items():
        node = nodes[node_name]
        ancestor_str = " ← ".join(ancestors) if ancestors else "ROOT"
        print(f"\n{node_name}")
        print(f"  Ancestors: {ancestor_str}")

        # Show what this node uniquely defines
        resolved = node.resolve(nodes)
        parent_resolved = None
        if node.parent_name:
            parent_resolved = nodes[node.parent_name].resolve(nodes)

        unique_attrs = []
        if node.mortgage:
            unique_attrs.append(
                f"Mortgage ₪{node.mortgage.principal:,.0f} @ {node.mortgage.annual_rate*100}%"
            )
        if node.monthly_income is not None:
            unique_attrs.append(f"Income ₪{node.monthly_income:,.0f}")
        if node.events:
            unique_attrs.append(f"{len(node.events)} event(s) (mode={node.event_mode})")

        if unique_attrs:
            print(f"  Defines: {', '.join(unique_attrs)}")
        else:
            print(f"  Defines: inherits all fields from parent")

    # 2. Simulate each and show results
    print("\n[2] SIMULATIONS (20-year horizon)")
    print("-" * 90)

    results = {}
    for name in ["Alon Baseline", "Alon - Buy Apartment", "Alon - Buy Apartment + Exit"]:
        resolved = nodes[name].resolve(nodes)
        result = simulate(resolved, years=20)
        results[name] = result

        retirement = f"Year {result.retirement_year}" if result.retirement_year else "Never"
        final_portfolio = result.year_data[-1].portfolio

        print(f"\n{name}")
        print(f"  Retirement: {retirement}")
        print(f"  Final portfolio: ₪{final_portfolio:,.0f}")

    # 3. Pairwise comparisons
    print("\n[3] PAIRWISE COMPARISONS (Understanding Tradeoffs)")
    print("-" * 90)

    comparisons = [
        ("Alon Baseline", "Alon - Buy Apartment"),
        ("Alon Baseline", "Alon - Buy Apartment + Exit"),
        ("Alon - Buy Apartment", "Alon - Buy Apartment + Exit"),
    ]

    for name_a, name_b in comparisons:
        print(f"\n{name_a} vs {name_b}")
        print("-" * 90)
        insights = build_insights(results[name_a], results[name_b])
        print(format_insights(insights))

    # 4. Show how to build new variations
    print("\n[4] HOW TO CREATE NEW VARIATIONS (Code Example)")
    print("-" * 90)

    example_code = """
# Example: What if income stays at ₪45K even after exit?
from models import ScenarioNode
from scenario_nodes import load_scenario_nodes

nodes = load_scenario_nodes()

# Create a new variation
new_variation = ScenarioNode(
    name="Buy Apartment + Exit (no salary cut)",
    parent_name="Alon - Buy Apartment",
    monthly_income=45_000,  # Keep original income
    event_mode="replace",
    events=[nodes["Alon - Buy Apartment + Exit"].events[0]],  # Keep exit event
)

# Resolve and simulate
all_nodes = {**nodes, "Buy Apartment + Exit (no salary cut)": new_variation}
resolved = new_variation.resolve(all_nodes)
result = simulate(resolved, years=20)

print(f"With income ₪45K: Retire at year {result.retirement_year}")
    """

    print(example_code)

    print("\n" + "=" * 90)
    print("KEY TAKEAWAY: Inheritance makes it easy to explore 'what-if' scenarios")
    print("by composing small, understandable changes into complex financial models.")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    main()
