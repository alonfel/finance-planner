from dataclasses import dataclass
from typing import Optional
from domain.models import Scenario


@dataclass
class YearData:
    """Annual snapshot of financial state during simulation."""
    year: int  # 1-indexed
    age: int  # Age at end of year
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
        annual_income = scenario.monthly_income.total * 12

        # Compute annual expenses
        annual_expenses = scenario.monthly_expenses.total * 12
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
            current_age = scenario.age + year_num
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
                # Pension-bridged retirement: ensure lifetime sustainability (retirement to age 100)
                current_age = scenario.age + year_num

                if pension_accessible:
                    # Pension is already unlocked, use traditional check
                    effective_capital = portfolio + pension
                    if effective_capital >= required_capital:
                        retirement_year = year_num
                elif scenario.pension is not None:
                    # Pension is locked. Two-phase check:
                    # Phase 1: Can portfolio sustain until pension unlocks?
                    # Phase 2: Will portfolio + pension sustain until end of life (age 100)?

                    years_to_pension_unlock = scenario.pension.accessible_at_age - current_age
                    years_from_unlock_to_age_100 = 100 - scenario.pension.accessible_at_age
                    annual_expenses_in_retirement = annual_expenses

                    # Phase 1: Portfolio covers bridge (conservative: assumes no growth during bridge)
                    portfolio_needed_to_bridge = annual_expenses_in_retirement * years_to_pension_unlock

                    # Phase 2: Project what portfolio + pension will be at pension unlock
                    # Conservative: portfolio after 'years_to_unlock' of withdrawals (assuming minimal growth)
                    # In reality portfolio grows, so this is conservative
                    portfolio_at_unlock = portfolio - (annual_expenses_in_retirement * years_to_pension_unlock)

                    # Pension grows at its rate, so current pension value is conservative estimate
                    # (actual pension at unlock will be higher due to contributions + growth)
                    pension_at_unlock_conservative = pension

                    # Total capital needed from unlock to age 100
                    capital_needed_after_unlock = annual_expenses_in_retirement * years_from_unlock_to_age_100

                    # Retirement is viable if:
                    # 1. Portfolio survives the bridge phase (portfolio_at_unlock > 0)
                    # 2. Portfolio + pension at unlock can sustain to age 100
                    if (portfolio >= portfolio_needed_to_bridge and
                        portfolio_at_unlock >= 0 and
                        (portfolio_at_unlock + pension_at_unlock_conservative) >= capital_needed_after_unlock):
                        retirement_year = year_num
                else:
                    # No pension, fall back to liquid_only logic
                    if portfolio >= required_capital:
                        retirement_year = year_num

        # Record year data
        current_age = scenario.age + year_num
        year_data_list.append(
            YearData(
                year=year_num,
                age=current_age,
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
