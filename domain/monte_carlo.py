"""Monte Carlo simulation engine for probabilistic financial planning."""

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np

from domain.models import Scenario
from domain.simulation import simulate


@dataclass
class MonteCarloResult:
    """Result of a Monte Carlo simulation run."""
    percentile_p5: list[float]
    percentile_p50: list[float]
    percentile_p95: list[float]
    retirement_probability: float  # 0.0 to 1.0
    survival_probability: float    # 0.0 to 1.0
    years: int
    ages: list[int]


def _generate_lognormal_returns(
    return_rate: float,
    sigma: float,
    years: int,
    n_trials: int,
    random_state: Optional[int] = None
) -> np.ndarray:
    """
    Generate lognormal-distributed annual returns for Monte Carlo trials.

    Each trial gets a sequence of `years` annual returns. The lognormal distribution
    is parameterized so that E[e^X - 1] = return_rate (the arithmetic mean matches input).

    Args:
        return_rate: Target arithmetic mean return (e.g., 0.07 for 7%)
        sigma: Volatility parameter (e.g., 0.15 for 15%)
        years: Number of years per trial
        n_trials: Number of trials to generate
        random_state: Optional numpy random seed for reproducibility

    Returns:
        ndarray of shape (n_trials, years) with annual returns (can be negative but > -1.0)
    """
    if random_state is not None:
        np.random.seed(random_state)

    # For lognormal distribution: if X ~ Lognormal(μ, σ), then E[e^X] = exp(μ + σ²/2)
    # We want E[e^X - 1] = return_rate, so E[e^X] = 1 + return_rate
    # Therefore: exp(μ + σ²/2) = 1 + return_rate
    # Taking ln: μ + σ²/2 = ln(1 + return_rate)
    # So: μ = ln(1 + return_rate) - σ²/2
    mu = math.log(1 + return_rate) - (sigma ** 2) / 2

    # Generate lognormal samples, convert to returns
    returns_matrix = np.random.lognormal(
        mean=mu,
        sigma=sigma,
        size=(n_trials, years)
    ) - 1.0

    return returns_matrix


def _sample_probabilistic_events(scenario: Scenario) -> Scenario:
    """Return a copy of scenario with one outcome sampled per probabilistic event.

    For each ProbabilisticEvent, draws one outcome using probability weights and
    injects it as a deterministic Event. The returned scenario has
    probabilistic_events=[] so simulate() treats it as a normal scenario.

    Args:
        scenario: Scenario with zero or more probabilistic_events

    Returns:
        New Scenario with sampled outcomes added to events and probabilistic_events cleared
    """
    import random
    from dataclasses import replace
    from domain.models import Event

    if not scenario.probabilistic_events:
        return scenario

    sampled_events = list(scenario.events)
    for prob_event in scenario.probabilistic_events:
        if not prob_event.outcomes:
            continue
        outcomes = prob_event.outcomes
        weights = [o.probability for o in outcomes]
        chosen = random.choices(outcomes, weights=weights, k=1)[0]
        if chosen.portfolio_injection != 0.0:
            sampled_events.append(Event(
                year=chosen.year,
                portfolio_injection=chosen.portfolio_injection,
                description=chosen.description,
            ))

    return replace(scenario, events=sampled_events, probabilistic_events=[])


def _run_trials(
    scenario: Scenario,
    returns_matrix: np.ndarray,
    years: int
) -> list:
    """
    Run simulate() once per trial, each with a distinct return sequence.

    If scenario has probabilistic_events, each trial independently samples one
    outcome per event using probability weights before simulating.

    Args:
        scenario: Base scenario
        returns_matrix: ndarray shape (n_trials, years) with return sequences
        years: Number of years (should match returns_matrix.shape[1])

    Returns:
        List of SimulationResult objects, one per trial
    """
    from dataclasses import replace

    results = []
    n_trials = returns_matrix.shape[0]

    for trial_idx in range(n_trials):
        trial_returns = returns_matrix[trial_idx].tolist()

        # Sample one outcome per probabilistic event for this trial
        trial_scenario = _sample_probabilistic_events(scenario)
        result = simulate(trial_scenario, years=years, rate_sequence_override=trial_returns)
        results.append(result)

    return results


def _compute_percentiles(trials_results: list, years: int) -> tuple[list[float], list[float], list[float]]:
    """
    Compute p5, p50, p95 portfolio values across all trials for each year.

    Args:
        trials_results: List of SimulationResult objects
        years: Number of years in simulation

    Returns:
        Tuple of (p5_list, p50_list, p95_list) each of length years
    """
    # Extract portfolio values across all trials for each year
    # Shape: (n_trials, years)
    portfolios_by_year = np.array([
        [trial.year_data[year_idx].portfolio for year_idx in range(years)]
        for trial in trials_results
    ])

    # Compute percentiles per year
    p5 = np.percentile(portfolios_by_year, 5, axis=0).tolist()
    p50 = np.percentile(portfolios_by_year, 50, axis=0).tolist()
    p95 = np.percentile(portfolios_by_year, 95, axis=0).tolist()

    return p5, p50, p95


def _compute_success_metrics(trials_results: list) -> tuple[float, float]:
    """
    Compute retirement and survival probabilities.

    Retirement probability: % of trials where retirement_year is not None
    Survival probability: % of trials where final portfolio > 0

    Args:
        trials_results: List of SimulationResult objects

    Returns:
        Tuple of (retirement_probability, survival_probability) each in [0.0, 1.0]
    """
    n_trials = len(trials_results)

    # Count trials where retirement was achieved
    retired_count = sum(1 for result in trials_results if result.retirement_year is not None)
    retirement_probability = retired_count / n_trials if n_trials > 0 else 0.0

    # Count trials where portfolio survived (> 0 at end)
    survived_count = sum(
        1 for result in trials_results
        if result.year_data[-1].portfolio > 0
    )
    survival_probability = survived_count / n_trials if n_trials > 0 else 0.0

    return retirement_probability, survival_probability


def run_monte_carlo(
    scenario: Scenario,
    n_trials: int = 500,
    years: int = 40,
    sigma: float = 0.15
) -> MonteCarloResult:
    """
    Run a Monte Carlo simulation of the scenario.

    Generates n_trials independent return sequences from a lognormal distribution,
    simulates each trial, and aggregates results into percentile bands and success metrics.

    Args:
        scenario: Scenario to simulate
        n_trials: Number of Monte Carlo trials (default 500)
        years: Number of years to simulate (default 40)
        sigma: Volatility of return distribution (default 0.15 for 15%)

    Returns:
        MonteCarloResult with percentile bands, success probabilities, and ages
    """
    returns_matrix = _generate_lognormal_returns(
        return_rate=scenario.return_rate,
        sigma=sigma,
        years=years,
        n_trials=n_trials
    )

    trials_results = _run_trials(scenario, returns_matrix, years)
    p5, p50, p95 = _compute_percentiles(trials_results, years)
    retirement_prob, survival_prob = _compute_success_metrics(trials_results)
    ages = [scenario.age + year_num for year_num in range(1, years + 1)]

    return MonteCarloResult(
        percentile_p5=p5,
        percentile_p50=p50,
        percentile_p95=p95,
        retirement_probability=retirement_prob,
        survival_probability=survival_prob,
        years=years,
        ages=ages
    )
