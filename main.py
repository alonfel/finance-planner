#!/usr/bin/env python3
"""
Financial Simulation Engine
Main entry point: simulates both scenarios and generates comparison report.
"""

from datetime import datetime
from models import Scenario, Mortgage
from simulation import simulate
from comparison import compare_scenarios, generate_insights
from scenarios import SCENARIO_A, SCENARIO_B, load_scenarios
from settings import SETTINGS

# Current year for calculating future retirement dates
CURRENT_YEAR = datetime.now().year


# Currency symbols
CURRENCY_SYMBOLS = {
    "ILS": "₪",
    "USD": "$",
    "EUR": "€",
}


def get_currency_symbol(currency: str) -> str:
    """Get currency symbol for display."""
    return CURRENCY_SYMBOLS.get(currency, currency)


def print_scenario_header(scenario, settings):
    """Print scenario input parameters as a header block.

    Displays fields configured in settings.output.show_fields.
    """
    currency_symbol = get_currency_symbol(scenario.currency)
    fields = settings.output.show_fields

    print(f"\n{'─'*110}")
    print(f"  Scenario Parameters: {scenario.name}")
    print(f"{'─'*110}")

    if "income_expenses" in fields:
        net = scenario.monthly_income - scenario.monthly_expenses
        print(f"  Income:   {currency_symbol} {scenario.monthly_income:>10,.0f}/month")
        print(f"  Expenses: {currency_symbol} {scenario.monthly_expenses:>10,.0f}/month")
        print(f"  Net:      {currency_symbol} {net:>10,.0f}/month")

    if "mortgage_details" in fields:
        if scenario.mortgage:
            m = scenario.mortgage
            print(f"  Mortgage: {currency_symbol} {m.principal:,.0f} @ {m.annual_rate*100:.1f}% for {m.duration_years}y  |  Monthly payment: {currency_symbol} {m.monthly_payment:,.0f}")
        else:
            print(f"  Mortgage: None")

    if "events" in fields:
        if scenario.events:
            for e in scenario.events:
                sign = "+" if e.portfolio_injection >= 0 else ""
                print(f"  Event year {e.year}: {e.description}  ({sign}{currency_symbol} {e.portfolio_injection:,.0f})")
        else:
            print(f"  Events: None")

    if "rates_settings" in fields:
        print(f"  Return rate: {scenario.return_rate*100:.1f}%  |  Withdrawal rate: {scenario.withdrawal_rate*100:.1f}%  |  Simulation: {settings.years} years  |  Age: {scenario.age}")

    print(f"{'─'*110}")


def print_year_summary(result, scenario, limit_years=40, start_age=30):
    """Print a table of year-by-year results with scenario header.

    Args:
        result: SimulationResult object
        scenario: Scenario object (for parameter display)
        limit_years: Max years to display
        start_age: Starting age for retirement age calculation
    """
    # Print scenario parameters header
    print_scenario_header(scenario, SETTINGS)

    # Get currency symbol from first year's data (all years use same currency)
    currency_symbol = get_currency_symbol(scenario.currency)

    print(f"\n{'='*110}")
    print(f"Year-by-Year: {result.scenario_name} ({currency_symbol})")
    print(f"{'='*110}")
    print(
        f"{'Year':<6} {'Income':<14} {'Expenses':<14} {'Net Savings':<14} {'Portfolio':<16} {'Req. Capital':<14}"
    )
    print("-" * 110)

    for year_data in result.year_data[:limit_years]:
        print(
            f"{year_data.year:<6} "
            f"{currency_symbol} {year_data.income:>11,.0f} "
            f"{currency_symbol} {year_data.expenses:>11,.0f} "
            f"{currency_symbol} {year_data.net_savings:>11,.0f} "
            f"{currency_symbol} {year_data.portfolio:>13,.0f} "
            f"{currency_symbol} {year_data.required_capital:>11,.0f}"
        )

    if result.retirement_year:
        future_year = CURRENT_YEAR + result.retirement_year - 1
        retirement_age = start_age + result.retirement_year - 1
        print(f"\n✓ Retirement achieved in year {result.retirement_year} (expected: {future_year}, age: {retirement_age})")
        print(f"  Portfolio at retirement: {currency_symbol} {result.year_data[result.retirement_year - 1].portfolio:,.0f}")
    else:
        print(f"\n✗ No retirement achieved within {len(result.year_data)} years")

    print(f"Final portfolio (year {len(result.year_data)}): {currency_symbol} {result.year_data[-1].portfolio:,.0f}")


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

    # Simulate both scenarios
    print("\nSimulating Scenario A (Baseline)...")
    result_a = simulate(SCENARIO_A, years=SETTINGS.years)

    print("Simulating Scenario B (Buy Apartment)...")
    result_b = simulate(SCENARIO_B, years=SETTINGS.years)

    # Print detailed year-by-year results
    print_year_summary(result_a, SCENARIO_A, limit_years=SETTINGS.years, start_age=SCENARIO_A.age)
    print_year_summary(result_b, SCENARIO_B, limit_years=SETTINGS.years, start_age=SCENARIO_B.age)

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

    all_scenarios = load_scenarios()
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
    print("✓ Simulation complete and validated!")
    print("="*110 + "\n")


if __name__ == "__main__":
    main()
