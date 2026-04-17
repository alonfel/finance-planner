import random
from dataclasses import dataclass, replace
from typing import Optional
from domain.models import Scenario, Event, FinancialStory, EventOutcome, ProbabilisticEvent


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
    is_retired: bool = False  # Whether retirement lifestyle is active this year
    active_income: float = 0.0  # Income used in calculation (after retirement adjustments)


@dataclass
class SimulationResult:
    """Result of simulating a single scenario."""
    scenario_name: str
    year_data: list[YearData]
    retirement_year: Optional[int]  # First year where portfolio >= required_capital


def simulate(scenario: Scenario, years: int = 40, rate_sequence_override: Optional[list[float]] = None) -> SimulationResult:
    """
    Simulate a scenario year-by-year.

    Args:
        scenario: The financial scenario to simulate
        years: Number of years to simulate (default 40)
        rate_sequence_override: Optional list of annual returns to use instead of scenario's return_rate or historical data

    Returns:
        SimulationResult with year-by-year data and retirement year
    """
    portfolio = scenario.initial_portfolio
    pension = scenario.pension.initial_value if scenario.pension else 0.0
    retirement_year: Optional[int] = None
    year_data_list: list[YearData] = []

    # Determine which rate sequence to use
    if rate_sequence_override is not None:
        # Override takes highest precedence
        rate_sequence = rate_sequence_override
    elif scenario.historical_start_year is not None:
        # Build historical rate sequence if using historical returns
        from domain.historical_returns import get_historical_rate_sequence, DEFAULT_INDEX
        rate_sequence = get_historical_rate_sequence(
            scenario.historical_start_year,
            years,
            index=scenario.historical_index or DEFAULT_INDEX,
        )
    else:
        rate_sequence = None

    for year_num in range(1, years + 1):
        current_age = scenario.age + year_num

        # Determine active income (apply retirement lifestyle if applicable)
        is_retired = False
        active_income_monthly = scenario.monthly_income.total

        if scenario.retirement_lifestyle_mode and scenario.retirement_lifestyle_age:
            if current_age >= scenario.retirement_lifestyle_age:
                is_retired = True
                if scenario.retirement_lifestyle_mode == "full":
                    active_income_monthly = 0
                elif scenario.retirement_lifestyle_mode == "partial":
                    active_income_monthly = scenario.partial_retirement_income or 0

        annual_income = active_income_monthly * 12

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

        # Portfolio growth — use historical rate if available, else fixed return_rate
        annual_rate = rate_sequence[year_num - 1] if rate_sequence is not None else scenario.return_rate
        portfolio = (portfolio + net_savings) * (1 + annual_rate)

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
                is_retired=is_retired,
                active_income=annual_income,
            )
        )

    return SimulationResult(
        scenario_name=scenario.name,
        year_data=year_data_list,
        retirement_year=retirement_year,
    )


def simulate_branches(
    scenario: Scenario,
    years: int = 40,
) -> list[tuple[str, float, SimulationResult]]:
    """Simulate each probabilistic event outcome branch independently.

    For each ProbabilisticEvent in scenario.probabilistic_events, iterates over
    outcomes and runs a separate simulation with that outcome injected as a
    deterministic Event. Outcomes with probability=0 are skipped.

    If scenario.probabilistic_events is empty, returns a single-element list
    with the plain simulate() result (regression-safe).

    Args:
        scenario: Scenario to simulate; probabilistic_events drives branching
        years: Number of years per simulation (default 40)

    Returns:
        List of (label, probability, SimulationResult) tuples — one per outcome
        branch. For the no-probabilistic-events case, label=scenario.name and
        probability=1.0.
    """
    if not scenario.probabilistic_events:
        result = simulate(scenario, years=years)
        return [(scenario.name, 1.0, result)]

    branches: list[tuple[str, float, SimulationResult]] = []

    # For simplicity, expand all outcome combinations across all probabilistic events.
    # Current scope (roadmap Feature 2): one probabilistic event per scenario in What-If.
    # Multiple events produce a cross-product of branches; each branch injects all
    # sampled outcomes as deterministic Events.
    _expand_branches(scenario, scenario.probabilistic_events, [], 1.0, years, branches)

    return branches


def _expand_branches(
    scenario: Scenario,
    remaining_events: list,
    accumulated_events: list[Event],
    accumulated_probability: float,
    years: int,
    out: list,
) -> None:
    """Recursively expand probabilistic event outcome combinations into branches."""
    if not remaining_events:
        # All events resolved — run the simulation with accumulated injections
        branch_scenario = replace(
            scenario,
            events=list(scenario.events) + accumulated_events,
            probabilistic_events=[],
        )
        result = simulate(branch_scenario, years=years)
        label = " + ".join(e.description or f"Year {e.year}" for e in accumulated_events) if accumulated_events else scenario.name
        out.append((label, accumulated_probability, result))
        return

    current_event = remaining_events[0]
    rest = remaining_events[1:]

    for outcome in current_event.outcomes:
        if outcome.probability == 0:
            continue  # Skip zero-probability branches
        branch_event = Event(
            year=outcome.year,
            portfolio_injection=outcome.portfolio_injection,
            description=outcome.description,
        )
        _expand_branches(
            scenario,
            rest,
            accumulated_events + [branch_event],
            accumulated_probability * outcome.probability,
            years,
            out,
        )


def story_to_branches(
    story: FinancialStory,
    years: int = 40,
) -> list[tuple[str, float, "SimulationResult"]]:
    """Simulate all outcome paths of a FinancialStory.

    Converts StoryEventNode objects into the existing Event / ProbabilisticEvent
    format, then delegates to simulate_branches() for cross-product expansion.
    All deterministic events apply to every branch equally.

    Args:
        story: FinancialStory with base scenario and event nodes
        years: Number of years to simulate per branch (default 40)

    Returns:
        List of (label, probability, SimulationResult) — one entry per leaf
        branch path. Single-path stories return one entry with probability=1.0.
    """
    det_events: list[Event] = []
    prob_events: list[ProbabilisticEvent] = []

    for node in story.events:
        if node.event_type == "deterministic":
            det_events.append(Event(
                year=node.year,
                portfolio_injection=node.portfolio_injection,
                description=node.label,
            ))
        elif node.event_type == "probabilistic":
            prob_events.append(ProbabilisticEvent(
                name=node.label,
                outcomes=[
                    EventOutcome(
                        year=node.year,
                        probability=o.probability,
                        portfolio_injection=o.portfolio_injection,
                        description=o.label,
                    )
                    for o in node.outcomes
                ],
            ))

    scenario = replace(
        story.base_scenario,
        name=story.name,
        events=det_events,
        probabilistic_events=prob_events,
    )
    return simulate_branches(scenario, years=years)


def story_to_scenario(story: FinancialStory) -> Scenario:
    """Flatten a FinancialStory to a single Scenario (deterministic events only).

    Probabilistic event nodes are dropped. Useful for backward-compatible
    callers that expect a plain Scenario rather than branches.

    Args:
        story: FinancialStory to flatten

    Returns:
        Scenario with only deterministic events from the story's event nodes.
        base_scenario.events and .probabilistic_events are replaced entirely.
    """
    det_events = [
        Event(
            year=node.year,
            portfolio_injection=node.portfolio_injection,
            description=node.label,
        )
        for node in story.events
        if node.event_type == "deterministic"
    ]
    return replace(
        story.base_scenario,
        name=story.name,
        events=det_events,
        probabilistic_events=[],
    )
