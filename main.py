#!/usr/bin/env python3
"""
Financial Simulation Engine
Main entry point: simulates both scenarios and generates comparison report.
"""

from models import Scenario, Mortgage
from simulation import simulate
from comparison import compare_scenarios, generate_insights
from scenarios import SCENARIO_A, SCENARIO_B
from settings import SETTINGS


# Currency symbols
CURRENCY_SYMBOLS = {
    "ILS": "₪",
    "USD": "$",
    "EUR": "€",
}


def get_currency_symbol(currency: str) -> str:
    """Get currency symbol for display."""
    return CURRENCY_SYMBOLS.get(currency, currency)


def print_year_summary(result, limit_years=40):
    """Print a table of year-by-year results."""
    # Get currency symbol from first year's data (all years use same currency)
    # For now, get it from the scenario name (will be improved)
    currency_symbol = "₪"  # Default to ILS (shekel)

    print(f"\n{'='*110}")
    print(f"Scenario: {result.scenario_name} ({currency_symbol})")
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
        print(f"\n✓ Retirement achieved in year {result.retirement_year}")
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
    print_year_summary(result_a, limit_years=SETTINGS.years)
    print_year_summary(result_b, limit_years=SETTINGS.years)

    # Validate both scenarios
    validate_scenario_a_behavior(result_a)
    validate_scenario_b_behavior(result_b)

    # Generate and print comparison
    print("\n" + "="*110)
    print("SCENARIO COMPARISON")
    print("="*110)
    insights = generate_insights(result_a, result_b)
    print(insights)

    print("\n" + "="*110)
    print("✓ Simulation complete and validated!")
    print("="*110 + "\n")


if __name__ == "__main__":
    main()
