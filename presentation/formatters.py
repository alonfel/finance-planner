"""Formatting functions for displaying scenario data and simulation results."""

from domain.models import Scenario
from domain.simulation import SimulationResult
from infrastructure.loaders import Settings
from presentation.constants import get_currency_symbol


def print_scenario_header(scenario: Scenario, settings: Settings) -> None:
    """Print scenario input parameters as a header block.

    Displays fields configured in settings.output.show_fields. This function
    is deduplicated from main.py and compare_all_scenarios.py where it appeared
    identically.

    Args:
        scenario: The scenario to display
        settings: Global settings containing output configuration
    """
    currency_symbol = get_currency_symbol(scenario.currency)
    fields = settings.output.show_fields

    print(f"\n{'─'*110}")
    print(f"  Scenario Parameters: {scenario.name}")
    print(f"{'─'*110}")

    if "income_expenses" in fields:
        income = scenario.monthly_income
        expenses = scenario.monthly_expenses
        net = income.total - expenses.total

        print(f"  Income:   {currency_symbol} {income.total:>10,.0f}/month")
        if len(income.components) > 1:
            for label, amt in income.components.items():
                print(f"    {label:<22} {currency_symbol} {amt:>10,.0f}/month")

        print(f"  Expenses: {currency_symbol} {expenses.total:>10,.0f}/month")
        if len(expenses.components) > 1:
            for label, amt in expenses.components.items():
                print(f"    {label:<22} {currency_symbol} {amt:>10,.0f}/month")

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


def print_year_summary(result: SimulationResult, scenario: Scenario, limit_years: int = 40, start_age: int = 30) -> None:
    """Print a table of year-by-year results with scenario header.

    Args:
        result: SimulationResult object containing year-by-year data
        scenario: Original Scenario object (for parameter display)
        limit_years: Maximum number of years to display (default 40)
        start_age: Starting age for retirement age calculation (default 30)
    """
    # Get currency symbol from scenario
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

    print()
    if result.retirement_year:
        retirement_age = start_age + result.retirement_year - 1
        print(f"✓ Retires at year {result.retirement_year} (age {retirement_age})")
    else:
        print(f"✗ Does not retire within {limit_years} years")
