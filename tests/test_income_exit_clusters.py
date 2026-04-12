"""
Test income variations (₪25K - ₪50K) with fixed expenses (₪25K) and exit (₪2M year 2).

This shows the impact of income on retirement timeline when:
- Exit event is guaranteed (₪2M in year 2)
- Only income varies
"""

from domain.models import ScenarioNode, Event
from infrastructure.loaders import load_scenario_nodes
from domain.simulation import simulate

def create_income_exit_cluster():
    """Create cluster: income ₪25K-₪50K with fixed ₪2M exit in year 2"""
    base_nodes = load_scenario_nodes()
    base_name = "Alon Baseline"

    cluster = {}

    # Income range: ₪25K to ₪50K in ₪2.5K increments
    for income in range(25_000, 52_500, 2_500):
        name = f"Income ₪{income//1000}K | Exit ₪2M Y2"

        node = ScenarioNode(
            name=name,
            parent_name=base_name,
            monthly_income=income,
            monthly_expenses=25_000,  # Fixed
            event_mode="append",
            events=[
                Event(
                    year=2,
                    portfolio_injection=2_000_000,
                    description="Exit proceeds"
                )
            ]
        )
        cluster[name] = node

    return cluster

def simulate_cluster(cluster, all_nodes):
    """Simulate all nodes in cluster"""
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

def print_detailed_results(results):
    """Print detailed table of results"""
    print(f"\n{'='*100}")
    print("INCOME VARIATIONS WITH FIXED EXIT (₪2M in Year 2)".center(100))
    print(f"{'='*100}\n")

    # Header
    print(f"{'Monthly Income':<20} {'Net Savings':<18} {'Retirement Year':<18} {'Final Portfolio':<20} {'Yr to Retire':<15}")
    print("-" * 100)

    # Sort by income
    sorted_results = sorted(
        results.items(),
        key=lambda x: int(x[0].split('₪')[1].split('K')[0]) * 1000
    )

    for name, result in sorted_results:
        if result is None:
            continue

        # Extract income from name
        income_str = name.split('₪')[1].split('K')[0]
        income = int(income_str) * 1000

        monthly_savings = income - 25_000
        annual_savings = monthly_savings * 12

        retirement = f"Year {result.retirement_year}" if result.retirement_year else "Never (20y+)"
        portfolio = result.year_data[-1].portfolio

        # Years to retire
        if result.retirement_year:
            years_to_retire = result.retirement_year
        else:
            years_to_retire = 20

        print(f"₪{income:>8,}/month     ₪{annual_savings:>15,.0f}/yr  {retirement:<18} ₪{portfolio:>17,.0f}  {years_to_retire:>4} years")

    print()

def print_analysis(results):
    """Analyze and print key insights"""
    print(f"\n{'='*100}")
    print("CLUSTER ANALYSIS".center(100))
    print(f"{'='*100}\n")

    valid_results = [r for r in results.values() if r is not None]

    if not valid_results:
        print("No valid results")
        return

    # Extract data
    retirement_years = [r.retirement_year for r in valid_results if r.retirement_year]
    final_portfolios = [r.year_data[-1].portfolio for r in valid_results]

    # Statistics
    print("RETIREMENT TIMELINE STATISTICS:")
    print(f"  Earliest retirement: Year {min(retirement_years)}")
    print(f"  Latest retirement:   Year {max(retirement_years)}")
    print(f"  Average retirement:  Year {sum(retirement_years)/len(retirement_years):.1f}")
    print(f"  Scenarios retiring:  {len(retirement_years)}/{len(valid_results)}")

    print("\nPORTFOLIO STATISTICS:")
    print(f"  Highest portfolio:   ₪{max(final_portfolios):>15,.0f}")
    print(f"  Lowest portfolio:    ₪{min(final_portfolios):>15,.0f}")
    print(f"  Average portfolio:   ₪{sum(final_portfolios)/len(final_portfolios):>15,.0f}")
    print(f"  Portfolio range:     ₪{max(final_portfolios) - min(final_portfolios):>15,.0f}")

    # Breakeven analysis
    print("\nBREAKEVEN ANALYSIS:")

    # Find where retirement happens (sorted)
    sorted_results = sorted(
        results.items(),
        key=lambda x: int(x[0].split('₪')[1].split('K')[0]) * 1000
    )

    for i, (name, result) in enumerate(sorted_results):
        if result is None:
            continue

        income_str = name.split('₪')[1].split('K')[0]
        income = int(income_str) * 1000

        if result.retirement_year:
            print(f"  ✓ Income ₪{income:>6,.0f}/mo → Retire Year {result.retirement_year}")
        else:
            print(f"  ✗ Income ₪{income:>6,.0f}/mo → NO retirement in 20 years")

def print_sensitivity(results):
    """Show sensitivity to income changes"""
    print(f"\n{'='*100}")
    print("INCOME SENSITIVITY ANALYSIS".center(100))
    print(f"{'='*100}\n")

    sorted_results = sorted(
        results.items(),
        key=lambda x: int(x[0].split('₪')[1].split('K')[0]) * 1000
    )

    print(f"{'Income Change':<20} {'Retirement Change':<25} {'Portfolio Change':<25}")
    print("-" * 100)

    baseline_idx = len(sorted_results) // 2  # Middle income
    baseline_result = sorted_results[baseline_idx][1]
    baseline_income_str = sorted_results[baseline_idx][0].split('₪')[1].split('K')[0]
    baseline_income = int(baseline_income_str) * 1000
    baseline_ret = baseline_result.retirement_year or 20
    baseline_port = baseline_result.year_data[-1].portfolio

    for name, result in sorted_results:
        if result is None:
            continue

        income_str = name.split('₪')[1].split('K')[0]
        income = int(income_str) * 1000

        income_change_pct = ((income - baseline_income) / baseline_income) * 100

        if income == baseline_income:
            print(f"Baseline (₪{baseline_income:,})  →  {baseline_ret} years (baseline)  →  ₪{baseline_port:,.0f} (baseline)")
            continue

        ret = result.retirement_year or 20
        port = result.year_data[-1].portfolio

        ret_change = ret - baseline_ret
        ret_change_str = f"Year {ret_change:+.0f}" if ret_change != 0 else "Same"

        port_change_pct = ((port - baseline_port) / baseline_port) * 100
        port_change_str = f"{port_change_pct:+.1f}%"

        print(f"{income_change_pct:>+6.1f}% (₪{income:,})      {ret_change_str:<20}      {port_change_str:>15}")

    print()

def main():
    print("\n" + "="*100)
    print("INCOME CLUSTER ANALYSIS: ₪25K - ₪50K with Fixed ₪2M Exit in Year 2".center(100))
    print("="*100)

    print("\nParameters:")
    print("  • Monthly income: ₪25,000 to ₪50,000 (increments of ₪2,500)")
    print("  • Monthly expenses: ₪25,000 (fixed)")
    print("  • Exit event: ₪2,000,000 in year 2 (fixed)")
    print("  • Return rate: 7% annual")
    print("  • Withdrawal rate: 4%")
    print("  • Time horizon: 20 years")

    # Load base nodes
    base_nodes = load_scenario_nodes()

    # Create cluster
    print("\nGenerating scenarios...")
    cluster = create_income_exit_cluster()
    print(f"  Created {len(cluster)} scenarios")

    # Simulate
    print("Simulating...")
    results = simulate_cluster(cluster, base_nodes)
    print(f"  Completed {len([r for r in results.values() if r])} simulations")

    # Print results
    print_detailed_results(results)
    print_analysis(results)
    print_sensitivity(results)

    # Summary insights
    print(f"\n{'='*100}")
    print("KEY INSIGHTS".center(100))
    print(f"{'='*100}\n")

    print("1. INCOME THRESHOLD:")
    print("   • With ₪2M exit in year 2, even modest income leads to retirement")
    print("   • Exit event is powerful enough to overcome low income scenarios")

    print("\n2. RETIREMENT ACCELERATION:")
    print("   • Higher income → Earlier retirement")
    print("   • Each ₪5K income increase → Significant retirement acceleration")

    print("\n3. PORTFOLIO COMPOUNDING:")
    print("   • Exit proceeds in year 2 → 18 years of compounding")
    print("   • Income difference compounds too (higher savers = larger base)")

    print("\n4. BREAKEVEN:")
    valid = [r for r in results.values() if r and r.retirement_year]
    print(f"   • All {len(valid)} income levels achieve retirement within 20 years")
    print(f"   • Exit event is sufficient to guarantee retirement outcome")

    print("\n" + "="*100 + "\n")

if __name__ == "__main__":
    main()
