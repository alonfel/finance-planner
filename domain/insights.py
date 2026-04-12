from dataclasses import dataclass
from typing import Optional, List, Union
from domain.simulation import SimulationResult


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


# --- Structured Insight Types ---

@dataclass
class RetirementInsight:
    """Retirement outcome for a single scenario."""
    scenario_name: str
    retirement_year: Optional[int]
    years_simulated: int


@dataclass
class RetirementDeltaInsight:
    """How scenario B's retirement timing compares to A."""
    scenario_a_name: str
    scenario_b_name: str
    year_difference: int  # B - A; positive = B is later, negative = B is earlier


@dataclass
class PortfolioInsight:
    """Final portfolio comparison between two scenarios."""
    scenario_a_name: str
    scenario_b_name: str
    final_portfolio_a: float
    final_portfolio_b: float
    difference: float  # B - A
    years_simulated: int
    currency_symbol: str = "₪"


@dataclass
class MortgageInsight:
    """Mortgage burden narrative for a single scenario."""
    scenario_name: str
    first_mortgage_year: int
    last_mortgage_year: int
    avg_net_savings_during_mortgage: float
    currency_symbol: str = "₪"


# Union type for any insight
Insight = Union[RetirementInsight, RetirementDeltaInsight, PortfolioInsight, MortgageInsight]


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


def build_insights(result_a: SimulationResult, result_b: SimulationResult) -> List[Insight]:
    """
    Build structured insights from two simulation results.

    Converts raw simulation results into typed insight objects. Each insight
    represents a single observation (retirement timing, portfolio delta, etc.)
    that can be tested, rendered, or consumed programmatically.

    Args:
        result_a: First scenario result
        result_b: Second scenario result

    Returns:
        List of insight objects (order defines output order)
    """
    comparison = compare_scenarios(result_a, result_b)
    insights: List[Insight] = []

    # Retirement insight for scenario A
    insights.append(RetirementInsight(
        scenario_name=comparison.scenario_a_name,
        retirement_year=comparison.retirement_year_a,
        years_simulated=comparison.years_simulated,
    ))

    # Retirement insight for scenario B
    insights.append(RetirementInsight(
        scenario_name=comparison.scenario_b_name,
        retirement_year=comparison.retirement_year_b,
        years_simulated=comparison.years_simulated,
    ))

    # Retirement delta only when both scenarios retire
    if comparison.retirement_year_difference is not None:
        insights.append(RetirementDeltaInsight(
            scenario_a_name=comparison.scenario_a_name,
            scenario_b_name=comparison.scenario_b_name,
            year_difference=comparison.retirement_year_difference,
        ))

    # Portfolio comparison
    insights.append(PortfolioInsight(
        scenario_a_name=comparison.scenario_a_name,
        scenario_b_name=comparison.scenario_b_name,
        final_portfolio_a=comparison.final_portfolio_a,
        final_portfolio_b=comparison.final_portfolio_b,
        difference=comparison.final_portfolio_difference,
        years_simulated=comparison.years_simulated,
    ))

    # Mortgage insight only when scenario B has an active mortgage
    if result_b.year_data and result_b.year_data[0].mortgage_active:
        mortgage_years = [yd for yd in result_b.year_data if yd.mortgage_active]
        if mortgage_years:
            insights.append(MortgageInsight(
                scenario_name=comparison.scenario_b_name,
                first_mortgage_year=mortgage_years[0].year,
                last_mortgage_year=mortgage_years[-1].year,
                avg_net_savings_during_mortgage=sum(yd.net_savings for yd in mortgage_years) / len(mortgage_years),
            ))

    return insights


def format_insights(insights: List[Insight]) -> str:
    """
    Format structured insights into human-readable text.

    Pure function: converts a list of insight objects into formatted string.
    Uses isinstance dispatch to handle different insight types.

    Args:
        insights: List of insight objects

    Returns:
        Multi-line string with formatted insights
    """
    lines = []

    for insight in insights:
        if isinstance(insight, RetirementInsight):
            if insight.retirement_year:
                lines.append(f"{insight.scenario_name} retires at year {insight.retirement_year}.")
            else:
                lines.append(f"{insight.scenario_name} does not reach retirement within {insight.years_simulated} years.")

        elif isinstance(insight, RetirementDeltaInsight):
            if insight.year_difference > 0:
                lines.append(
                    f"{insight.scenario_b_name} delays retirement by {insight.year_difference} years."
                )
            elif insight.year_difference < 0:
                lines.append(
                    f"{insight.scenario_b_name} accelerates retirement by {abs(insight.year_difference)} years."
                )
            else:
                lines.append("Both scenarios reach retirement in the same year.")

        elif isinstance(insight, PortfolioInsight):
            direction = "higher" if insight.difference >= 0 else "lower"
            lines.append(
                f"After {insight.years_simulated} years, {insight.scenario_b_name}'s final portfolio is "
                f"{insight.currency_symbol} {abs(insight.difference):,.0f} {direction} than {insight.scenario_a_name}'s."
            )

        elif isinstance(insight, MortgageInsight):
            lines.append(
                f"During the mortgage period (years {insight.first_mortgage_year}-{insight.last_mortgage_year}), "
                f"{insight.scenario_name}'s average annual net savings is {insight.currency_symbol} {insight.avg_net_savings_during_mortgage:,.0f}."
            )

    return "\n".join(lines)


def generate_insights(result_a: SimulationResult, result_b: SimulationResult) -> str:
    """
    Generate human-readable insights comparing two scenarios.

    Convenience wrapper that builds structured insights and formats them.
    Maintains backward-compatible public API.

    Args:
        result_a: First scenario result
        result_b: Second scenario result

    Returns:
        Multi-line string with insights
    """
    return format_insights(build_insights(result_a, result_b))
