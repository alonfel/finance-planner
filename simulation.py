from dataclasses import dataclass
from typing import Optional
from models import Scenario


@dataclass
class YearData:
    """Annual snapshot of financial state during simulation."""
    year: int  # 1-indexed
    income: float  # Annual gross income
    expenses: float  # Annual expenses (including mortgage if active)
    net_savings: float  # income - expenses
    portfolio: float  # End-of-year portfolio value after growth
    required_capital: float  # Annual expenses / withdrawal_rate
    mortgage_active: bool  # Whether mortgage payment was included this year


@dataclass
class SimulationResult:
    """Result of simulating a single scenario."""
    scenario_name: str
    year_data: list[YearData]
    retirement_year: Optional[int]  # First year where portfolio >= required_capital


def simulate(scenario: Scenario, years: int = 40) -> SimulationResult:
    """
    Simulate a scenario year-by-year.

    Args:
        scenario: The financial scenario to simulate
        years: Number of years to simulate (default 40)

    Returns:
        SimulationResult with year-by-year data and retirement year
    """
    portfolio = scenario.initial_portfolio
    retirement_year: Optional[int] = None
    year_data_list: list[YearData] = []

    for year_num in range(1, years + 1):
        # Compute annual income
        annual_income = scenario.monthly_income * 12

        # Compute annual expenses
        annual_expenses = scenario.monthly_expenses * 12
        mortgage_active = False

        if scenario.mortgage is not None:
            if year_num <= scenario.mortgage.duration_years:
                annual_expenses += scenario.mortgage.monthly_payment * 12
                mortgage_active = True

        # Compute net savings
        net_savings = annual_income - annual_expenses

        # Apply one-time events (stock offerings, bonuses, emergencies, etc.)
        for event in scenario.events:
            if event.year == year_num:
                portfolio += event.portfolio_injection

        # Portfolio growth
        portfolio = (portfolio + net_savings) * (1 + scenario.return_rate)

        # Compute required capital for retirement
        required_capital = annual_expenses / scenario.withdrawal_rate

        # Detect retirement (first year where portfolio >= required_capital)
        if retirement_year is None and portfolio >= required_capital:
            retirement_year = year_num

        # Record year data
        year_data_list.append(
            YearData(
                year=year_num,
                income=annual_income,
                expenses=annual_expenses,
                net_savings=net_savings,
                portfolio=portfolio,
                required_capital=required_capital,
                mortgage_active=mortgage_active,
            )
        )

    return SimulationResult(
        scenario_name=scenario.name,
        year_data=year_data_list,
        retirement_year=retirement_year,
    )
