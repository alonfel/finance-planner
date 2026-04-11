"""
Test multiple scenario clusters to explore different financial outcomes.

Creates variations along different axes:
  - Income levels (₪30K, ₪45K, ₪60K)
  - Mortgage sizes (none, ₪1.5M, ₪2.5M)
  - Exit timing (year 2, 3, 5) and size (₪3M, ₪5M, ₪7M)
  - Event combinations

Generates clusters and shows comparative outcomes.
"""

from models import ScenarioNode, Mortgage, Event
from scenario_analysis.scenario_nodes import load_scenario_nodes
from simulation import simulate
from comparison import build_insights, format_insights
import json

def generate_income_cluster(base_node_name, base_nodes):
    """Create cluster: vary income levels"""
    base = base_nodes[base_node_name]
    cluster = {}

    for income in [30_000, 40_000, 45_000, 50_000, 60_000]:
        name = f"Income ₪{income//1000}K"
        node = ScenarioNode(
            name=name,
            parent_name=base_node_name,
            monthly_income=income,
        )
        cluster[name] = node

    return cluster

def generate_mortgage_cluster(base_node_name, base_nodes):
    """Create cluster: vary mortgage amounts"""
    base = base_nodes[base_node_name]
    cluster = {}

    # No mortgage
    cluster["No Mortgage"] = ScenarioNode(
        name="No Mortgage",
        parent_name=base_node_name,
        mortgage=None,
        event_mode="append",
        events=[]
    )

    # Different mortgage sizes
    for principal in [1_000_000, 1_500_000, 2_000_000, 2_500_000]:
        name = f"Mortgage ₪{principal//1_000_000}M"
        node = ScenarioNode(
            name=name,
            parent_name=base_node_name,
            mortgage=Mortgage(principal, 0.04, 25),
            event_mode="append",
            events=[Event(year=1, portfolio_injection=-200_000, description="Down payment fees")]
        )
        cluster[name] = node

    return cluster

def generate_exit_cluster(base_node_name, base_nodes):
    """Create cluster: vary exit timing and size"""
    cluster = {}

    # No exit
    cluster["No Exit"] = ScenarioNode(
        name="No Exit",
        parent_name=base_node_name,
        event_mode="append",
        events=[]
    )

    # Different exit scenarios
    for year in [2, 3, 5]:
        for amount in [3_000_000, 5_000_000, 7_000_000]:
            name = f"Exit Year {year} (₪{amount//1_000_000}M)"
            node = ScenarioNode(
                name=name,
                parent_name=base_node_name,
                event_mode="append",
                events=[Event(year=year, portfolio_injection=amount, description="Company exit")]
            )
            cluster[name] = node

    return cluster

def simulate_cluster(cluster, all_nodes):
    """Simulate all nodes in a cluster and return results"""
    results = {}
    for name, node in cluster.items():
        try:
            resolved = node.resolve({**all_nodes, **cluster})
            result = simulate(resolved, years=20)
            results[name] = result
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            results[name] = None

    return results

def print_cluster_results(cluster_name, results):
    """Print summary of cluster results"""
    print(f"\n{'='*80}")
    print(f"{cluster_name} CLUSTER RESULTS".center(80))
    print(f"{'='*80}\n")

    # Header
    print(f"{'Scenario':<40} {'Retirement':<15} {'Portfolio':<20}")
    print("-" * 80)

    # Sort by retirement year (None last)
    sorted_results = sorted(
        results.items(),
        key=lambda x: (x[1].retirement_year is None, x[1].retirement_year or 999)
    )

    for name, result in sorted_results:
        if result is None:
            print(f"{name:<40} {'ERROR':<15}")
            continue

        retirement = f"Year {result.retirement_year}" if result.retirement_year else "Never"
        portfolio = result.year_data[-1].portfolio

        print(f"{name:<40} {retirement:<15} ₪{portfolio:>17,.0f}")

    print()

def analyze_cluster(cluster_name, results):
    """Analyze patterns in cluster"""
    print(f"\n{cluster_name} ANALYSIS")
    print("="*80)

    valid_results = [r for r in results.values() if r is not None]
    if not valid_results:
        print("No valid results")
        return

    retirement_years = [r.retirement_year for r in valid_results if r.retirement_year]
    final_portfolios = [r.year_data[-1].portfolio for r in valid_results]

    if retirement_years:
        print(f"  Retirement: {min(retirement_years)} - {max(retirement_years)} years")
        print(f"  Average: {sum(retirement_years)/len(retirement_years):.1f} years")
    else:
        print(f"  Retirement: None within 20 years (all scenarios)")

    print(f"  Portfolio range: ₪{min(final_portfolios):,.0f} - ₪{max(final_portfolios):,.0f}")
    print(f"  Average: ₪{sum(final_portfolios)/len(final_portfolios):,.0f}")

    # Find best/worst
    by_portfolio = sorted([(name, r.year_data[-1].portfolio) for name, r in results.items() if r], key=lambda x: x[1])
    print(f"\n  Best outcome: {by_portfolio[-1][0]} (₪{by_portfolio[-1][1]:,.0f})")
    print(f"  Worst outcome: {by_portfolio[0][0]} (₪{by_portfolio[0][1]:,.0f})")

def main():
    print("\n" + "="*80)
    print("SCENARIO CLUSTER ANALYSIS")
    print("="*80)

    # Load base nodes
    base_nodes = load_scenario_nodes()
    base_name = "Alon Baseline"

    print(f"\nBase node: {base_name}")
    print(f"Creating clusters around this baseline...\n")

    # Cluster 1: Income variations
    print("📊 Cluster 1: Income Variations")
    income_cluster = generate_income_cluster(base_name, base_nodes)
    income_results = simulate_cluster(income_cluster, base_nodes)
    print_cluster_results("Income Variations", income_results)
    analyze_cluster("Income Variations", income_results)

    # Cluster 2: Mortgage variations
    print("\n📊 Cluster 2: Mortgage Variations")
    mortgage_cluster = generate_mortgage_cluster(base_name, base_nodes)
    mortgage_results = simulate_cluster(mortgage_cluster, base_nodes)
    print_cluster_results("Mortgage Variations", mortgage_results)
    analyze_cluster("Mortgage Variations", mortgage_results)

    # Cluster 3: Exit variations
    print("\n📊 Cluster 3: Exit Event Variations")
    exit_cluster = generate_exit_cluster(base_name, base_nodes)
    exit_results = simulate_cluster(exit_cluster, base_nodes)
    print_cluster_results("Exit Events", exit_results)
    analyze_cluster("Exit Events", exit_results)

    # Summary statistics
    print("\n" + "="*80)
    print("CROSS-CLUSTER SUMMARY".center(80))
    print("="*80)

    all_results = {
        "Income": income_results,
        "Mortgage": mortgage_results,
        "Exit": exit_results,
    }

    for cluster_name, results in all_results.items():
        valid = [r for r in results.values() if r is not None]
        retired = [r for r in valid if r.retirement_year]
        portfolios = [r.year_data[-1].portfolio for r in valid]

        print(f"\n{cluster_name:12} | Scenarios: {len(valid):2} | Retire: {len(retired):2}/{len(valid)} | Avg Portfolio: ₪{sum(portfolios)/len(portfolios):>12,.0f}")

    # Key insights
    print("\n" + "="*80)
    print("KEY INSIGHTS".center(80))
    print("="*80)

    print("\n1. INCOME IMPACT:")
    inc_never_retire = len([r for r in income_results.values() if r and not r.retirement_year])
    print(f"   {inc_never_retire} income levels don't achieve retirement in 20 years")

    print("\n2. MORTGAGE IMPACT:")
    mort_never_retire = len([r for r in mortgage_results.values() if r and not r.retirement_year])
    print(f"   {mort_never_retire} mortgage scenarios don't achieve retirement in 20 years")

    print("\n3. EXIT IMPACT:")
    exit_scenarios = len(exit_results)
    exit_retire = len([r for r in exit_results.values() if r and r.retirement_year])
    print(f"   {exit_retire}/{exit_scenarios} exit scenarios achieve retirement")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()
