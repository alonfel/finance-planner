"""
Compare four scenarios:
1. Your baseline (no exit, with surrogacy expense in year 2)
2. Your baseline + ₪2M exit in year 1
3. Your baseline + ₪3M exit in year 1
4. Friend's scenario

Shows year-by-year snapshots at milestones: 1, 5, 10, 15, 20 years
Compares: portfolio, retirement year, annual savings
"""

from models import Scenario, Event, Mortgage
from simulation import simulate


def create_scenarios():
    """Create the four scenarios for comparison."""

    # YOUR BASELINE (no exit)
    your_baseline = Scenario(
        name="Your Baseline (No Exit)",
        monthly_income=45_000,
        monthly_expenses=25_000,
        initial_portfolio=1_400_000,  # ₪900K + ₪500K
        return_rate=0.05,
        withdrawal_rate=0.04,
        currency="ILS",
        age=41,
        mortgage=None,
        events=[
            Event(
                year=2,
                portfolio_injection=-500_000,
                description="Child 2 surrogacy expense"
            )
        ]
    )

    # YOUR BASELINE + EXIT ₪2M YEAR 1
    your_with_exit_2m = Scenario(
        name="You + Exit (₪2M, Year 1)",
        monthly_income=45_000,
        monthly_expenses=25_000,
        initial_portfolio=1_400_000,
        return_rate=0.05,
        withdrawal_rate=0.04,
        currency="ILS",
        age=41,
        mortgage=None,
        events=[
            Event(
                year=1,
                portfolio_injection=2_000_000,
                description="Exit proceeds"
            ),
            Event(
                year=2,
                portfolio_injection=-500_000,
                description="Child 2 surrogacy expense"
            )
        ]
    )

    # YOUR BASELINE + EXIT ₪3M YEAR 1
    your_with_exit_3m = Scenario(
        name="You + Exit (₪3M, Year 1)",
        monthly_income=45_000,
        monthly_expenses=25_000,
        initial_portfolio=1_400_000,
        return_rate=0.05,
        withdrawal_rate=0.04,
        currency="ILS",
        age=41,
        mortgage=None,
        events=[
            Event(
                year=1,
                portfolio_injection=3_000_000,
                description="Exit proceeds"
            ),
            Event(
                year=2,
                portfolio_injection=-500_000,
                description="Child 2 surrogacy expense"
            )
        ]
    )

    # FRIEND'S SCENARIO
    friend_mortgage = Mortgage(
        principal=1_500_000,
        annual_rate=0.04,
        duration_years=30,
        currency="ILS"
    )

    friend_scenario = Scenario(
        name="Friend's Scenario",
        monthly_income=20_000,
        monthly_expenses=12_000,
        initial_portfolio=300_000,
        return_rate=0.05,
        withdrawal_rate=0.04,
        currency="ILS",
        age=35,
        mortgage=friend_mortgage,
        events=[]
    )

    return your_baseline, your_with_exit_2m, your_with_exit_3m, friend_scenario


def get_milestone_years(max_years):
    """Return milestone years to display."""
    return [y for y in [1, 5, 10, 15, 20] if y <= max_years]


def print_scenario_snapshot(name, result, years):
    """Print detailed snapshot for one scenario."""
    print(f"\n{'='*100}")
    print(f"SCENARIO: {name}".center(100))
    print(f"{'='*100}\n")

    # Header
    print(f"{'Year':<6} {'Portfolio':<18} {'Annual':<18} {'Required':<18} {'Retirement':<15}")
    print(f"{'':6} {'Value':<18} {'Savings':<18} {'Capital':<18} {'Status':<15}")
    print("-" * 100)

    milestones = get_milestone_years(years)

    for year_num in milestones:
        if year_num > len(result.year_data):
            continue

        year_data = result.year_data[year_num - 1]
        portfolio = year_data.portfolio
        net_savings = year_data.net_savings
        required_capital = year_data.required_capital

        if result.retirement_year and year_num >= result.retirement_year:
            retirement_status = f"✓ Retired (Y{result.retirement_year})"
        else:
            retirement_status = "Working"

        print(f"{year_num:<6} ₪{portfolio:>16,.0f} ₪{net_savings:>16,.0f} ₪{required_capital:>16,.0f} {retirement_status:<15}")

    # Final summary
    print(f"\n{'SUMMARY':-^100}")
    final_portfolio = result.year_data[-1].portfolio
    retirement_year = result.retirement_year if result.retirement_year else "Never"

    print(f"Final portfolio (year {years}): ₪{final_portfolio:,.0f}")
    print(f"Retirement year: {retirement_year}")

    if result.retirement_year:
        ret_year_data = result.year_data[result.retirement_year - 1]
        print(f"Portfolio at retirement: ₪{ret_year_data.portfolio:,.0f}")
        print(f"Age at retirement: ~{41 + result.retirement_year} years old")


def print_comparison_table(results, years):
    """Print side-by-side comparison."""
    print(f"\n\n{'='*140}")
    print("SIDE-BY-SIDE COMPARISON".center(140))
    print(f"{'='*140}\n")

    milestones = get_milestone_years(years)

    # Header
    print(f"{'Year':<6}", end="")
    for scenario_name, _ in results:
        print(f" | {scenario_name:<30} Portfolio", end="")
    print()

    print(f"{'':6}", end="")
    for _ in results:
        print(f" | {'Portfolio':<30}", end="")
    print()
    print("-" * 140)

    # Data rows
    for year_num in milestones:
        print(f"{year_num:<6}", end="")
        for scenario_name, result in results:
            if year_num > len(result.year_data):
                print(f" | {'N/A':<30}", end="")
            else:
                year_data = result.year_data[year_num - 1]
                portfolio = year_data.portfolio
                print(f" | ₪{portfolio:>28,.0f}", end="")
        print()

    # Retirement summary
    print(f"\n{'RETIREMENT YEAR':-^140}")
    print(f"{'Scenario':<50} {'Retirement Year':<30} {'Final Portfolio':<30}")
    print("-" * 140)

    for scenario_name, result in results:
        retirement_year = result.retirement_year if result.retirement_year else "Never"
        final_portfolio = result.year_data[-1].portfolio
        print(f"{scenario_name:<50} {str(retirement_year):<30} ₪{final_portfolio:>28,.0f}")


def print_key_differences(results, years):
    """Print key differences between scenarios."""
    print(f"\n\n{'='*100}")
    print("KEY DIFFERENCES".center(100))
    print(f"{'='*100}\n")

    scenario_names = [name for name, _ in results]
    scenario_results = [result for _, result in results]

    your_baseline = scenario_results[0]
    your_with_exit = scenario_results[1]
    friend_result = scenario_results[2]

    # Baseline vs Exit
    print("1. YOUR BASELINE vs YOU + EXIT")
    print("-" * 100)

    baseline_ret = your_baseline.retirement_year if your_baseline.retirement_year else "Never"
    exit_ret = your_with_exit.retirement_year if your_with_exit.retirement_year else "Never"
    baseline_final = your_baseline.year_data[-1].portfolio
    exit_final = your_with_exit.year_data[-1].portfolio

    print(f"Retirement year:    {baseline_ret} → {exit_ret}", end="")
    if your_baseline.retirement_year and your_with_exit.retirement_year:
        diff = your_baseline.retirement_year - your_with_exit.retirement_year
        print(f" ({diff:+d} years)")
    else:
        print()

    print(f"Final portfolio:    ₪{baseline_final:,.0f} → ₪{exit_final:,.0f}")
    print(f"Portfolio gain:     ₪{exit_final - baseline_final:+,.0f}")

    # Baseline vs Friend
    print(f"\n2. YOUR BASELINE vs FRIEND")
    print("-" * 100)

    friend_ret = friend_result.retirement_year if friend_result.retirement_year else "Never"
    friend_final = friend_result.year_data[-1].portfolio

    print(f"Retirement year:    {baseline_ret} vs {friend_ret}")
    print(f"Final portfolio:    ₪{baseline_final:,.0f} vs ₪{friend_final:,.0f}")
    print(f"Portfolio gap:      ₪{baseline_final - friend_final:+,.0f}")

    # Year 10 snapshot
    if 10 <= years:
        print(f"\n3. PORTFOLIO AT YEAR 10")
        print("-" * 100)

        baseline_y10 = your_baseline.year_data[9].portfolio
        exit_y10 = your_with_exit.year_data[9].portfolio
        friend_y10 = friend_result.year_data[9].portfolio

        print(f"Your baseline:      ₪{baseline_y10:,.0f}")
        print(f"You + exit:         ₪{exit_y10:,.0f} ({exit_y10 - baseline_y10:+,.0f})")
        print(f"Friend:             ₪{friend_y10:,.0f} ({friend_y10 - baseline_y10:+,.0f})")


def main():
    print("\n" + "="*100)
    print("COMPARISON: YOUR BASELINE vs YOU+EXIT (₪2M/₪3M) vs FRIEND".center(100))
    print("="*100)

    print("\nScenario Parameters:")
    print("="*100)
    print("\nYOUR BASELINE:")
    print("  • Monthly income: ₪45,000")
    print("  • Monthly expenses: ₪25,000")
    print("  • Initial portfolio: ₪1,400,000 (₪900K + ₪500K)")
    print("  • Mortgage: None")
    print("  • Event: Child 2 surrogacy (₪500K) in year 2")
    print("  • Return rate: 5%")

    print("\nYOU + EXIT (₪2M, YEAR 1):")
    print("  • Same as baseline, but:")
    print("  • Exit event: ₪2,000,000 in year 1")

    print("\nYOU + EXIT (₪3M, YEAR 1):")
    print("  • Same as baseline, but:")
    print("  • Exit event: ₪3,000,000 in year 1")

    print("\nFRIEND'S SCENARIO:")
    print("  • Monthly income: ₪20,000")
    print("  • Monthly expenses: ₪12,000")
    print("  • Initial portfolio: ₪300,000")
    print("  • Mortgage: ₪1,500,000 @ 4% for 30 years (~₪7,164/month)")
    print("  • Return rate: 5%")

    print("\n" + "="*100)
    print("RUNNING SIMULATIONS...")
    print("="*100)

    # Create scenarios
    your_baseline, your_with_exit_2m, your_with_exit_3m, friend_scenario = create_scenarios()

    # Simulate (20 years)
    years = 20
    print(f"\nSimulating {years} years...\n")

    baseline_result = simulate(your_baseline, years=years)
    exit_2m_result = simulate(your_with_exit_2m, years=years)
    exit_3m_result = simulate(your_with_exit_3m, years=years)
    friend_result = simulate(friend_scenario, years=years)

    results = [
        (your_baseline.name, baseline_result),
        (your_with_exit_2m.name, exit_2m_result),
        (your_with_exit_3m.name, exit_3m_result),
        (friend_scenario.name, friend_result)
    ]

    # Print detailed snapshots
    print_scenario_snapshot(your_baseline.name, baseline_result, years)
    print_scenario_snapshot(your_with_exit_2m.name, exit_2m_result, years)
    print_scenario_snapshot(your_with_exit_3m.name, exit_3m_result, years)
    print_scenario_snapshot(friend_scenario.name, friend_result, years)

    # Print comparison table
    print_comparison_table(results, years)

    # Print key differences
    print_key_differences(results, years)

    # Conclusions
    print(f"\n\n{'='*100}")
    print("STRATEGIC INSIGHTS".center(100))
    print(f"{'='*100}\n")

    print("1. YOUR SITUATION:")
    print("   • You are in a strong position: ₪20K/month surplus")
    baseline_ret = baseline_result.retirement_year or "20+"
    print(f"   • Retirement is feasible even without exit (Year {baseline_ret})")
    if baseline_result.retirement_year and exit_2m_result.retirement_year:
        acceleration_2m = baseline_result.retirement_year - exit_2m_result.retirement_year
        print(f"   • Exit with ₪2M accelerates retirement by {acceleration_2m} years")
    if baseline_result.retirement_year and exit_3m_result.retirement_year:
        acceleration_3m = baseline_result.retirement_year - exit_3m_result.retirement_year
        print(f"   • Exit with ₪3M accelerates retirement by {acceleration_3m} years")

    print("\n2. FRIEND'S SITUATION:")
    print("   • Tight finances: ₪8K/month savings before mortgage")
    print("   • Mortgage is significant: ~₪7.2K/month for 30 years")
    friend_ret_status = f"Year {friend_result.retirement_year}" if friend_result.retirement_year else "Does not retire in 20 years"
    print(f"   • Retirement status: {friend_ret_status}")

    print("\n3. COMPARISON:")
    portfolio_gap = baseline_result.year_data[-1].portfolio - friend_result.year_data[-1].portfolio
    print(f"   • Portfolio gap at year 20: ₪{portfolio_gap:,.0f}")
    print(f"   • This gap is due to:")
    print(f"     - Income difference: ₪25K/month vs ₪8K/month = ₪204K/year more")
    print(f"     - Initial portfolio: ₪1.4M vs ₪300K = ₪1.1M head start")
    print(f"     - Mortgage burden: Friend has ₪7.2K/month expense you don't")

    print("\n" + "="*100 + "\n")


if __name__ == "__main__":
    main()
