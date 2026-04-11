#!/usr/bin/env python3
"""
Comprehensive insights analysis: all 5 scenarios with all pairwise comparisons.
Shows how structured insights make it easy to programmatically work with insights.
"""

from datetime import datetime
from scenarios import load_scenarios
from settings import SETTINGS
from simulation import simulate
from comparison import build_insights, format_insights

CURRENT_YEAR = datetime.now().year


def print_scenario_header(scenario, settings):
    """Print scenario input parameters as a header block."""
    from main import get_currency_symbol

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

def main():
    """Load all scenarios, simulate, and show comprehensive pairwise insights."""
    print("\n" + "="*110)
    print("COMPREHENSIVE INSIGHTS: ALL SCENARIOS")
    print("="*110)

    # Load all scenarios
    scenarios = load_scenarios()
    scenario_names = list(scenarios.keys())
    print(f"\nLoaded {len(scenario_names)} scenarios: {', '.join(scenario_names)}\n")

    # Simulate all
    print(f"Simulating {len(scenario_names)} scenarios ({SETTINGS.years} years)...")
    results = {}
    for name in scenario_names:
        results[name] = simulate(scenarios[name], years=SETTINGS.years)
    print("✓ All simulations complete\n")

    # Quick summary table
    print("="*110)
    print("SUMMARY: Quick Overview")
    print("="*110)
    print(f"{'Scenario':<20} {'Retirement':<18} {'Final Portfolio':<20} {'Age at Retirement'}")
    print("-"*110)
    for name in scenario_names:
        result = results[name]
        retirement = str(result.retirement_year) if result.retirement_year else "N/A"
        retirement_age = "N/A"
        if result.retirement_year:
            age = scenarios[name].age
            retirement_age = str(age + result.retirement_year - 1)
        final = result.year_data[-1].portfolio
        print(f"{name:<20} {retirement:<18} ₪{final:>17,.0f}  {retirement_age}")

    # All pairwise insights
    print("\n" + "="*110)
    print("PAIRWISE INSIGHTS: All Scenario Comparisons")
    print("="*110)

    comparisons_shown = 0
    for i, name_a in enumerate(scenario_names):
        for name_b in scenario_names[i+1:]:
            comparisons_shown += 1
            result_a = results[name_a]
            result_b = results[name_b]
            scenario_a = scenarios[name_a]
            scenario_b = scenarios[name_b]

            print(f"\n{'-'*110}")
            print(f"[{comparisons_shown}] {name_a} vs {name_b}")
            print(f"{'-'*110}")

            # Show scenario parameters
            print(f"\nScenario A: {name_a}")
            print_scenario_header(scenario_a, SETTINGS)

            print(f"\nScenario B: {name_b}")
            print_scenario_header(scenario_b, SETTINGS)

            # Build and display insights
            print(f"\nInsights:")
            insights = build_insights(result_a, result_b)
            formatted = format_insights(insights)
            print(formatted)

            # Also show structured data (demonstrating the insights layer)
            print(f"\n[Structured insights ({len(insights)} objects)]")
            for idx, insight in enumerate(insights, 1):
                print(f"  {idx}. {insight.__class__.__name__}")

    print(f"\n{'='*110}")
    print(f"✓ Complete: {len(scenario_names)} scenarios, {comparisons_shown} pairwise comparisons")
    print(f"{'='*110}\n")


if __name__ == "__main__":
    main()
