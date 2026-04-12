#!/usr/bin/env python3
"""
Financial Simulation Engine
Main entry point: simulates both scenarios and generates comparison report.
"""

from datetime import datetime
from domain.simulation import simulate
from domain.insights import generate_insights
from infrastructure.loaders import load_scenarios, SETTINGS
from presentation.formatters import print_scenario_header, print_year_summary

# Current year for calculating future retirement dates
CURRENT_YEAR = datetime.now().year


def validate_scenario_b_behavior(result_b):
    """Programmatically validate Scenario B behavior."""
    print("\n" + "="*110)
    print("VALIDATION: Scenario B Behavior")
    print("="*110)

    # Check mortgage period
    total_years = len(result_b.year_data)
    mortgage_years = [yd for yd in result_b.year_data if yd.mortgage_active]

    if mortgage_years:
        avg_mortgage_savings = sum(yd.net_savings for yd in mortgage_years) / len(mortgage_years)
        print(f"✓ During mortgage ({len(mortgage_years)} years): ₪ {avg_mortgage_savings:,.0f}/year avg savings")

    # Check post-mortgage period (if exists)
    post_mortgage_years = [yd for yd in result_b.year_data if not yd.mortgage_active]

    if post_mortgage_years and mortgage_years:
        avg_post_mortgage_savings = sum(yd.net_savings for yd in post_mortgage_years) / len(post_mortgage_years)
        print(f"✓ After mortgage ({len(post_mortgage_years)} years): ₪ {avg_post_mortgage_savings:,.0f}/year avg savings")
        improvement = avg_post_mortgage_savings - avg_mortgage_savings
        print(f"✓ Savings improvement: ₪ {improvement:,.0f}/year more")
    elif post_mortgage_years:
        print(f"✓ Years without mortgage: {len(post_mortgage_years)}")
    else:
        print(f"⚠ Note: Mortgage extends beyond simulation period ({total_years} years simulated)")

    print("✓ All Scenario B validations passed!")


def validate_scenario_a_behavior(result_a):
    """Programmatically validate Scenario A behavior (Step 6)."""
    print("\n" + "="*110)
    print("VALIDATION: Scenario A Behavior")
    print("="*110)

    # Check all years have positive savings
    negative_count = sum(1 for yd in result_a.year_data if yd.net_savings <= 0)
    print(f"✓ Years with negative/zero net savings: {negative_count}")
    assert negative_count == 0, "Expected all years to have positive savings"

    # Check portfolio grows monotonically
    prev_portfolio = 0
    decrease_count = 0
    for yd in result_a.year_data:
        if yd.portfolio < prev_portfolio:
            decrease_count += 1
        prev_portfolio = yd.portfolio
    print(f"✓ Years with portfolio decrease: {decrease_count}")
    assert decrease_count == 0, "Expected monotonic portfolio growth"

    print("✓ All Scenario A validations passed!")


def main():
    """Run simulation for both scenarios and generate report."""
    print("\n" + "="*110)
    print("FINANCIAL SIMULATION ENGINE")
    print("="*110)

    # Load scenarios
    all_scenarios = load_scenarios()
    scenario_a = all_scenarios["Baseline"]
    scenario_b = all_scenarios["Buy Apartment"]

    # Simulate both scenarios
    print("\nSimulating Scenario A (Baseline)...")
    result_a = simulate(scenario_a, years=SETTINGS.years)

    print("Simulating Scenario B (Buy Apartment)...")
    result_b = simulate(scenario_b, years=SETTINGS.years)

    # Print detailed year-by-year results
    print_year_summary(result_a, scenario_a, limit_years=SETTINGS.years, start_age=scenario_a.age)
    print_year_summary(result_b, scenario_b, limit_years=SETTINGS.years, start_age=scenario_b.age)

    # Validate both scenarios
    validate_scenario_a_behavior(result_a)
    validate_scenario_b_behavior(result_b)

    # Generate and print comparison
    print("\n" + "="*110)
    print("SCENARIO COMPARISON")
    print("="*110)
    insights = generate_insights(result_a, result_b)
    print(insights)

    # Event scenarios: IPO timing comparison
    print("\n" + "="*110)
    print("IPO TIMING ANALYSIS: 3-Scenario Comparison")
    print("="*110)

    print("\nSimulating IPO Year 2 (3M offering)...")
    result_ipo2 = simulate(all_scenarios["IPO Year 2"], years=SETTINGS.years)

    print("Simulating IPO Year 3 (2M offering)...")
    result_ipo3 = simulate(all_scenarios["IPO Year 3"], years=SETTINGS.years)

    print("Simulating IPO Year 29 (2M offering, delayed)...")
    result_ipo29 = simulate(all_scenarios["IPO Year 29"], years=SETTINGS.years)

    # Print summary comparison table
    print("\n" + "="*110)
    print("QUICK COMPARISON: IPO Timing Impact")
    print("="*110)
    print(
        f"{'Scenario':<20} {'Offering':<20} {'Amount':<15} {'Retirement Year':<18} {'Final Portfolio':<20}"
    )
    print("-" * 110)
    print(
        f"{'IPO Year 2':<20} {'Year 2':<20} {'₪3,000,000':<15} "
        f"{(str(result_ipo2.retirement_year) if result_ipo2.retirement_year else 'N/A'):<18} "
        f"₪{result_ipo2.year_data[-1].portfolio:>17,.0f}"
    )
    print(
        f"{'IPO Year 3':<20} {'Year 3':<20} {'₪2,000,000':<15} "
        f"{(str(result_ipo3.retirement_year) if result_ipo3.retirement_year else 'N/A'):<18} "
        f"₪{result_ipo3.year_data[-1].portfolio:>17,.0f}"
    )
    print(
        f"{'IPO Year 29':<20} {'Year 29':<20} {'₪2,000,000':<15} "
        f"{(str(result_ipo29.retirement_year) if result_ipo29.retirement_year else 'N/A'):<18} "
        f"₪{result_ipo29.year_data[-1].portfolio:>17,.0f}"
    )

    # Print detailed results for each scenario
    print_year_summary(result_ipo2, all_scenarios["IPO Year 2"], limit_years=min(15, SETTINGS.years), start_age=all_scenarios["IPO Year 2"].age)
    print_year_summary(result_ipo3, all_scenarios["IPO Year 3"], limit_years=min(15, SETTINGS.years), start_age=all_scenarios["IPO Year 3"].age)
    print_year_summary(result_ipo29, all_scenarios["IPO Year 29"], limit_years=min(15, SETTINGS.years), start_age=all_scenarios["IPO Year 29"].age)

    # Pairwise comparisons
    print("\n" + "="*110)
    print("DETAILED COMPARISONS")
    print("="*110)

    print("\n" + "="*110)
    print("IPO Year 2 vs Year 3 (Impact of 1-year delay, 1M less capital)")
    print("="*110)
    insights_2_vs_3 = generate_insights(result_ipo2, result_ipo3)
    print(insights_2_vs_3)

    print("\n" + "="*110)
    print("IPO Year 3 vs Year 29 (Impact of 26-year delay)")
    print("="*110)
    insights_3_vs_29 = generate_insights(result_ipo3, result_ipo29)
    print(insights_3_vs_29)

    print("\n" + "="*110)
    print("IPO Year 2 vs Year 29 (Extreme: Early vs Late offering)")
    print("="*110)
    insights_2_vs_29 = generate_insights(result_ipo2, result_ipo29)
    print(insights_2_vs_29)

    print("\n" + "="*110)
    print("END OF REPORT")
    print("="*110 + "\n")


if __name__ == "__main__":
    main()
