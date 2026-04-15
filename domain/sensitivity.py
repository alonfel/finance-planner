"""One-at-a-time sensitivity analysis for Monte Carlo results."""

from dataclasses import dataclass, replace

from domain.breakdown import IncomeBreakdown
from domain.monte_carlo import run_monte_carlo
from domain.models import Scenario


@dataclass
class DriverResult:
    """Result for one OAT sensitivity variant."""
    name: str  # e.g., "Return Rate", "Monthly Income", "Time Horizon"
    direction: str  # "+" or "-"
    delta: float  # Change in retirement probability (e.g., +0.12 for +12%)
    variant_retirement_probability: float  # Retirement probability for this variant


@dataclass
class SensitivityResult:
    """Result of OAT sensitivity analysis."""
    drivers: list[DriverResult]


def _create_oat_variants(
    base_scenario: Scenario,
    base_years: int
) -> list[tuple[str, Scenario, int]]:
    """
    Generate OAT variants for sensitivity analysis.

    Creates 6 variants:
    - Return rate: +2pp and -2pp
    - Monthly income: +20% and -20%
    - Time horizon: +5 years and -5 years

    Args:
        base_scenario: Scenario to vary
        base_years: Base simulation duration

    Returns:
        List of (label, variant_scenario, variant_years) tuples
    """
    variants = []

    # Return rate variants (±2pp, clamped to [0.001, 1.0])
    high_return_rate = min(1.0, base_scenario.return_rate + 0.02)
    low_return_rate = max(0.001, base_scenario.return_rate - 0.02)

    variants.append((
        "Return Rate (+2pp)",
        replace(base_scenario, return_rate=high_return_rate),
        base_years
    ))
    variants.append((
        "Return Rate (-2pp)",
        replace(base_scenario, return_rate=low_return_rate),
        base_years
    ))

    # Monthly income variants (±20%, proportional scaling of all components)
    income_high = IncomeBreakdown(components={
        k: v * 1.2 for k, v in base_scenario.monthly_income.components.items()
    })
    income_low = IncomeBreakdown(components={
        k: v * 0.8 for k, v in base_scenario.monthly_income.components.items()
    })

    variants.append((
        "Monthly Income (+20%)",
        replace(base_scenario, monthly_income=income_high),
        base_years
    ))
    variants.append((
        "Monthly Income (-20%)",
        replace(base_scenario, monthly_income=income_low),
        base_years
    ))

    # Time horizon variants (±5 years)
    high_years = base_years + 5
    low_years = max(1, base_years - 5)

    variants.append((
        "Time Horizon (+5yr)",
        base_scenario,
        high_years
    ))
    variants.append((
        "Time Horizon (-5yr)",
        base_scenario,
        low_years
    ))

    return variants


def run_oat_sensitivity(
    scenario: Scenario,
    n_trials: int = 500,
    years: int = 40
) -> SensitivityResult:
    """
    Run OAT sensitivity analysis on a scenario.

    Generates base Monte Carlo result, then 6 variant runs (return ±2pp, income ±20%, horizon ±5yr).
    Computes delta in retirement probability for each variant vs base.
    Returns results sorted by absolute delta (largest impact first).

    Args:
        scenario: Scenario to analyze
        n_trials: Number of Monte Carlo trials per run (default 500)
        years: Base simulation duration (default 40)

    Returns:
        SensitivityResult with 6 drivers sorted by impact
    """
    # Run base case to get baseline retirement probability
    base_result = run_monte_carlo(scenario, n_trials=n_trials, years=years)
    base_retirement_prob = base_result.retirement_probability

    # Generate OAT variants
    variants = _create_oat_variants(scenario, years)

    # Run Monte Carlo for each variant and compute delta
    drivers = []
    for label, variant_scenario, variant_years in variants:
        variant_result = run_monte_carlo(
            variant_scenario,
            n_trials=n_trials,
            years=variant_years
        )
        delta = variant_result.retirement_probability - base_retirement_prob

        # Extract direction from label
        if "(+" in label:
            direction = "+"
        else:
            direction = "-"

        drivers.append(DriverResult(
            name=label.replace(" (+2pp)", "").replace(" (-2pp)", "")
                      .replace(" (+20%)", "").replace(" (-20%)", "")
                      .replace(" (+5yr)", "").replace(" (-5yr)", ""),
            direction=direction,
            delta=delta,
            variant_retirement_probability=variant_result.retirement_probability
        ))

    # Sort by absolute delta (descending), then by name alphabetically
    drivers.sort(key=lambda d: (-abs(d.delta), d.name))

    return SensitivityResult(drivers=drivers)
