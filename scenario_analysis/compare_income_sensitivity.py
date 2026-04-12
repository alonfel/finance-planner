"""
Income Sensitivity Analysis: ₪45K vs ₪25K

Shows how your three core scenarios differentiate when income decreases:
1. Baseline (no exit)
2. Baseline + ₪2M exit
3. Baseline + ₪3M exit

Compares retirement timing and portfolio growth at both income levels.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scenario_analysis.scenario_nodes import load_scenario_nodes
from simulation import simulate


def print_scenario_pair(scenario_45k, scenario_25k, result_45k, result_25k, years):
    """Compare two income versions of the same scenario."""
    print(f"\n{'='*120}")
    print(f"SCENARIO: {scenario_45k.split(' - ')[0].strip()}")
    print(f"{'='*120}\n")

    # Header
    print(f"{'Metric':<40} {'At ₪45K Income':<35} {'At ₪25K Income':<35}")
    print(f"{'':40} {'(Current)':<35} {'(Low Income)':<35}")
    print("-" * 120)

    # Retirement year
    ret_45k = result_45k.retirement_year if result_45k.retirement_year else "Never (20+ years)"
    ret_25k = result_25k.retirement_year if result_25k.retirement_year else "Never (20+ years)"
    print(f"{'Retirement Year':<40} {str(ret_45k):<35} {str(ret_25k):<35}")

    # Age at retirement (if applicable)
    if result_45k.retirement_year:
        age_45k = 41 + result_45k.retirement_year
        print(f"{'Age at Retirement':<40} {age_45k:<35} {'(N/A if never retires)':<35}")
    if result_25k.retirement_year:
        age_25k = 41 + result_25k.retirement_year
        if result_45k.retirement_year:
            age_diff = age_25k - age_45k
            print(f"{'Age Difference':<40} {'':<35} {f'(+{age_diff} years later)':<35}")

    # Portfolio at year 10
    port_45k_y10 = result_45k.year_data[9].portfolio if 10 <= years else "N/A"
    port_25k_y10 = result_25k.year_data[9].portfolio if 10 <= years else "N/A"
    if isinstance(port_45k_y10, (int, float)):
        print(f"{'Portfolio at Year 10':<40} ₪{port_45k_y10:>33,.0f} ₪{port_25k_y10:>33,.0f}")
        diff_y10 = port_45k_y10 - port_25k_y10
        print(f"{'  Difference':<40} {'':<35} ₪{diff_y10:>33,.0f}")

    # Final portfolio at year 20
    port_45k_final = result_45k.year_data[-1].portfolio
    port_25k_final = result_25k.year_data[-1].portfolio
    print(f"{'Portfolio at Year 20':<40} ₪{port_45k_final:>33,.0f} ₪{port_25k_final:>33,.0f}")
    diff_final = port_45k_final - port_25k_final
    print(f"{'  Difference':<40} {'':<35} ₪{diff_final:>33,.0f}")

    # Annual savings
    savings_45k = result_45k.year_data[0].net_savings
    savings_25k = result_25k.year_data[0].net_savings
    print(f"{'Annual Savings (Year 1)':<40} ₪{savings_45k:>33,.0f} ₪{savings_25k:>33,.0f}")
    diff_savings = savings_45k - savings_25k
    print(f"{'  Difference':<40} {'':<35} ₪{diff_savings:>33,.0f}")

    # Impact of retirement delay
    if result_45k.retirement_year and result_25k.retirement_year:
        delay = result_25k.retirement_year - result_45k.retirement_year
        print(f"\n{'RETIREMENT DELAY':<40} {delay} year(s) {'for ₪25K income':<25}")

        if delay > 0:
            print(f"{'  Years of extra work':<40} {delay}x (₪20K savings/year less)")
    elif result_45k.retirement_year and not result_25k.retirement_year:
        print(f"\n{'RETIREMENT IMPACT':<40} {'Can retire at ₪45K':<35} {'Cannot retire at ₪25K in 20 years':<35}")


def main():
    print("\n" + "="*120)
    print("INCOME SENSITIVITY ANALYSIS: ₪45K vs ₪25K Income")
    print("="*120)

    print("\nScenario Parameters:")
    print("="*120)
    print("\n₪45K INCOME SCENARIOS (Current):")
    print("  • Monthly income: ₪45,000")
    print("  • Monthly expenses: ₪25,000")
    print("  • Monthly savings: ₪20,000")
    print("  • Initial portfolio: ₪1,400,000")

    print("\n₪25K INCOME SCENARIOS (Low Income):")
    print("  • Monthly income: ₪25,000")
    print("  • Monthly expenses: ₪25,000")
    print("  • Monthly savings: ₪0 (break-even)")
    print("  • Initial portfolio: ₪1,400,000")

    print("\nEvents (both income levels):")
    print("  • Year 2: Child 2 surrogacy (₪500K)")
    print("  • ₪2M/₪3M exit variants: Exit proceeds in year 1")

    print("\n" + "="*120)
    print("LOADING SCENARIO TREE AND SIMULATING...")
    print("="*120 + "\n")

    nodes = load_scenario_nodes()
    years = 20

    # Simulate all 6 scenarios
    scenarios = [
        ("Alon Baseline", "Alon Baseline - Low Income (₪25K)"),
        ("Alon Baseline + ₪2M Exit (from compare script)", "Alon - Low Income + ₪2M Exit"),
        ("Alon Baseline + ₪3M Exit (from compare script)", "Alon - Low Income + ₪3M Exit"),
    ]

    results = []
    for node_45k_name, node_25k_name in scenarios:
        # For the high-income scenarios with exits, we need to get them from the direct Scenario creation
        # since they're not in the tree. Let me use the tree nodes that exist.

        # Resolve the 25K scenarios (they exist in the tree)
        if "₪2M" in node_45k_name:
            # Create from tree node
            result_25k = simulate(nodes[node_25k_name].resolve(nodes), years=years)
            # For 45K scenario, we'll simulate inline
            from models import Scenario, Event
            scenario_45k = Scenario(
                name="Baseline + ₪2M Exit (₪45K)",
                monthly_income=45_000,
                monthly_expenses=25_000,
                initial_portfolio=1_400_000,
                return_rate=0.05,
                withdrawal_rate=0.04,
                currency="ILS",
                age=41,
                mortgage=None,
                events=[
                    Event(year=1, portfolio_injection=2_000_000, description="Exit proceeds"),
                    Event(year=2, portfolio_injection=-500_000, description="Child 2 surrogacy expense")
                ]
            )
            result_45k = simulate(scenario_45k, years=years)
        elif "₪3M" in node_45k_name:
            # Create from tree node
            result_25k = simulate(nodes[node_25k_name].resolve(nodes), years=years)
            # For 45K scenario, we'll simulate inline
            from models import Scenario, Event
            scenario_45k = Scenario(
                name="Baseline + ₪3M Exit (₪45K)",
                monthly_income=45_000,
                monthly_expenses=25_000,
                initial_portfolio=1_400_000,
                return_rate=0.05,
                withdrawal_rate=0.04,
                currency="ILS",
                age=41,
                mortgage=None,
                events=[
                    Event(year=1, portfolio_injection=3_000_000, description="Exit proceeds"),
                    Event(year=2, portfolio_injection=-500_000, description="Child 2 surrogacy expense")
                ]
            )
            result_45k = simulate(scenario_45k, years=years)
        else:
            # Baseline
            result_25k = simulate(nodes[node_25k_name].resolve(nodes), years=years)
            from models import Scenario, Event
            scenario_45k = Scenario(
                name="Baseline (₪45K)",
                monthly_income=45_000,
                monthly_expenses=25_000,
                initial_portfolio=1_400_000,
                return_rate=0.05,
                withdrawal_rate=0.04,
                currency="ILS",
                age=41,
                mortgage=None,
                events=[
                    Event(year=2, portfolio_injection=-500_000, description="Child 2 surrogacy expense")
                ]
            )
            result_45k = simulate(scenario_45k, years=years)

        results.append((node_45k_name, result_45k, result_25k))

    # Display comparisons
    for label, result_45k, result_25k in results:
        print_scenario_pair(label, "", result_45k, result_25k, years)

    # Summary table
    print(f"\n\n{'='*120}")
    print("SUMMARY TABLE")
    print(f"{'='*120}\n")

    print(f"{'Scenario':<45} {'₪45K Retirement':<25} {'₪25K Retirement':<25} {'Retirement Delay':<20}")
    print("-" * 120)

    for label, result_45k, result_25k in results:
        ret_45k = result_45k.retirement_year if result_45k.retirement_year else "Never"
        ret_25k = result_25k.retirement_year if result_25k.retirement_year else "Never"

        if isinstance(ret_45k, int) and isinstance(ret_25k, int):
            delay = ret_25k - ret_45k
            delay_str = f"{delay} years"
        else:
            delay_str = "N/A"

        scenario_label = label.replace(" (from compare script)", "").replace("₪", "").strip()
        print(f"{scenario_label:<45} {str(ret_45k):<25} {str(ret_25k):<25} {delay_str:<20}")

    print("\n" + "="*120)
    print("KEY INSIGHTS")
    print("="*120 + "\n")

    ret_baseline_45k = results[0][1].retirement_year
    ret_baseline_25k = results[0][2].retirement_year

    print("1. BASELINE SCENARIO (No Exit):")
    if ret_baseline_45k and ret_baseline_25k:
        delay = ret_baseline_25k - ret_baseline_45k
        print(f"   • At ₪45K: Retire year {ret_baseline_45k} (age ~{41 + ret_baseline_45k})")
        print(f"   • At ₪25K: Retire year {ret_baseline_25k} (age ~{41 + ret_baseline_25k})")
        print(f"   • Income impact: {delay} year(s) delay")
    elif ret_baseline_45k and not ret_baseline_25k:
        print(f"   • At ₪45K: Retire year {ret_baseline_45k}")
        print(f"   • At ₪25K: Cannot retire in 20 years (portfolio stalls)")
        print(f"   • Critical insight: Lower income + surrogacy expense = no retirement")

    print("\n2. WITH EXITS (₪2M and ₪3M):")
    for i in [1, 2]:
        label, result_45k, result_25k = results[i]
        ret_45k = result_45k.retirement_year
        ret_25k = result_25k.retirement_year
        exit_amt = "₪2M" if "₪2M" in label else "₪3M"

        if ret_45k and ret_25k:
            delay = ret_25k - ret_45k
            print(f"   • {exit_amt} exit @ ₪45K: Year {ret_45k}")
            print(f"   • {exit_amt} exit @ ₪25K: Year {ret_25k} ({delay:+d} years)")
        elif ret_45k and not ret_25k:
            print(f"   • {exit_amt} exit @ ₪45K: Year {ret_45k}")
            print(f"   • {exit_amt} exit @ ₪25K: Year {ret_25k}")

    print("\n3. BREAK-EVEN ANALYSIS:")
    print("   • At ₪25K income = ₪25K expenses: Zero monthly savings")
    print("   • Retirement depends entirely on:")
    print("     - Initial portfolio (₪1.4M)")
    print("     - Investment returns (5% annually)")
    print("     - One-time events (exits, surrogacy)")
    print("   • Without exits: Portfolio barely grows, retirement unfeasible")
    print("   • With exits: Exit proceeds are critical to retirement timeline")

    print("\n" + "="*120 + "\n")


if __name__ == "__main__":
    main()
