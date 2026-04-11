from dataclasses import dataclass
from typing import Optional
from simulation import SimulationResult


@dataclass
class ComparisonResult:
    """Result of comparing two simulation outcomes."""
    scenario_a_name: str
    scenario_b_name: str
    retirement_year_a: Optional[int]
    retirement_year_b: Optional[int]
    retirement_year_difference: Optional[int]  # B - A; None if either never retires
    final_portfolio_a: float
    final_portfolio_b: float
    final_portfolio_difference: float  # B - A
    years_simulated: int


def compare_scenarios(result_a: SimulationResult, result_b: SimulationResult) -> ComparisonResult:
    """
    Compare two simulation results.

    Args:
        result_a: First scenario result
        result_b: Second scenario result

    Returns:
        ComparisonResult with key differences
    """
    final_a = result_a.year_data[-1].portfolio
    final_b = result_b.year_data[-1].portfolio

    # Compute retirement difference
    retirement_diff: Optional[int] = None
    if result_a.retirement_year is not None and result_b.retirement_year is not None:
        retirement_diff = result_b.retirement_year - result_a.retirement_year

    return ComparisonResult(
        scenario_a_name=result_a.scenario_name,
        scenario_b_name=result_b.scenario_name,
        retirement_year_a=result_a.retirement_year,
        retirement_year_b=result_b.retirement_year,
        retirement_year_difference=retirement_diff,
        final_portfolio_a=final_a,
        final_portfolio_b=final_b,
        final_portfolio_difference=final_b - final_a,
        years_simulated=len(result_a.year_data),
    )


def generate_insights(result_a: SimulationResult, result_b: SimulationResult) -> str:
    """
    Generate human-readable insights comparing two scenarios.

    Args:
        result_a: First scenario result
        result_b: Second scenario result

    Returns:
        Multi-line string with insights
    """
    comparison = compare_scenarios(result_a, result_b)

    # Currency symbol (default to ILS)
    currency_symbol = "₪"

    lines = []

    # Retirement timing for A
    if comparison.retirement_year_a:
        lines.append(f"{comparison.scenario_a_name} retires at year {comparison.retirement_year_a}.")
    else:
        lines.append(f"{comparison.scenario_a_name} does not reach retirement within {comparison.years_simulated} years.")

    # Retirement timing for B
    if comparison.retirement_year_b:
        lines.append(f"{comparison.scenario_b_name} retires at year {comparison.retirement_year_b}.")
    else:
        lines.append(f"{comparison.scenario_b_name} does not reach retirement within {comparison.years_simulated} years.")

    # Retirement difference
    if comparison.retirement_year_difference is not None:
        if comparison.retirement_year_difference > 0:
            lines.append(
                f"{comparison.scenario_b_name} delays retirement by {comparison.retirement_year_difference} years."
            )
        elif comparison.retirement_year_difference < 0:
            lines.append(
                f"{comparison.scenario_b_name} accelerates retirement by {abs(comparison.retirement_year_difference)} years."
            )
        else:
            lines.append("Both scenarios reach retirement in the same year.")

    # Portfolio comparison
    if comparison.final_portfolio_difference >= 0:
        direction = "higher"
    else:
        direction = "lower"
    lines.append(
        f"After {comparison.years_simulated} years, {comparison.scenario_b_name}'s final portfolio is "
        f"{currency_symbol} {abs(comparison.final_portfolio_difference):,.0f} {direction} than {comparison.scenario_a_name}'s."
    )

    # Mortgage burden narrative (if B has mortgage)
    if result_b.year_data[0].mortgage_active:
        # Find first and last years with mortgage
        mortgage_years = [yd for yd in result_b.year_data if yd.mortgage_active]
        if mortgage_years:
            first_mortgage_year = mortgage_years[0].year
            last_mortgage_year = mortgage_years[-1].year
            avg_net_savings_during_mortgage = sum(yd.net_savings for yd in mortgage_years) / len(mortgage_years)
            lines.append(
                f"During the mortgage period (years {first_mortgage_year}-{last_mortgage_year}), "
                f"{comparison.scenario_b_name}'s average annual net savings is {currency_symbol} {avg_net_savings_during_mortgage:,.0f}."
            )

    return "\n".join(lines)
