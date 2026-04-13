from dataclasses import dataclass
from typing import Optional
from domain.models import Scenario


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
    pension_value: float = 0.0  # End-of-year pension fund value
    pension_accessible: bool = False  # Whether pension can count toward retirement


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
    pension = scenario.pension.initial_value if scenario.pension else 0.0
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

        # Pension growth (if pension exists)
        pension_accessible = False
        if scenario.pension is not None:
            current_age = scenario.age + year_num - 1
            pension_accessible = (current_age >= scenario.pension.accessible_at_age)
            # Grow pension fund with contributions
            pension = (pension + scenario.pension.monthly_contribution * 12) * (1 + scenario.pension.annual_growth_rate)

        # Portfolio growth
        portfolio = (portfolio + net_savings) * (1 + scenario.return_rate)

        # Compute required capital for retirement
        required_capital = annual_expenses / scenario.withdrawal_rate

        # Detect retirement based on mode
        if retirement_year is None:
            if scenario.retirement_mode == "liquid_only":
                # Original mode: count pension only if accessible
                effective_capital = portfolio
                if pension_accessible:
                    effective_capital += pension
                if effective_capital >= required_capital:
                    retirement_year = year_num

            elif scenario.retirement_mode == "pension_bridged":
                # New mode: can retire if portfolio bridges to pension unlock
                current_age = scenario.age + year_num - 1

                if pension_accessible:
                    # Pension is already unlocked, use traditional check
                    effective_capital = portfolio + pension
                    if effective_capital >= required_capital:
                        retirement_year = year_num
                elif scenario.pension is not None:
                    # Pension is locked. Check if we can bridge to unlock
                    years_to_pension_unlock = scenario.pension.accessible_at_age - current_age
                    annual_expenses_in_retirement = annual_expenses  # Use current year's expenses for calculation

                    # Can we sustain from portfolio until pension unlocks?
                    portfolio_needed_to_bridge = annual_expenses_in_retirement * years_to_pension_unlock

                    # At pension unlock, can we sustain from pension + portfolio?
                    required_capital_at_unlock = annual_expenses_in_retirement / scenario.withdrawal_rate

                    # Simple check: portfolio covers bridge, pension covers after unlock
                    if (portfolio >= portfolio_needed_to_bridge and
                        pension >= required_capital_at_unlock):
                        retirement_year = year_num
                else:
                    # No pension, fall back to liquid_only logic
                    if portfolio >= required_capital:
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
                pension_value=pension,
                pension_accessible=pension_accessible,
            )
        )

    return SimulationResult(
        scenario_name=scenario.name,
        year_data=year_data_list,
        retirement_year=retirement_year,
    )
