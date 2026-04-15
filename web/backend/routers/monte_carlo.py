"""Monte Carlo simulation endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from domain.monte_carlo import run_monte_carlo
from domain.sensitivity import run_oat_sensitivity
from domain.breakdown import IncomeBreakdown, ExpenseBreakdown
from domain.models import Scenario, Mortgage, Pension, Event
from auth import get_current_user
from database import get_db
from models import Profile, ScenarioDefinition
from schemas import MonteCarloRequest, MonteCarloResponse, PercentileBandsSchema, DriverRankSchema


router = APIRouter(prefix="/api/v1", tags=["monte-carlo"])


def _build_scenario_from_definition(
    definition: ScenarioDefinition
) -> Scenario:
    """
    Reconstruct a Scenario domain object from a ScenarioDefinition database row.

    Preserves income/expense components for OAT sensitivity analysis.
    """
    import json

    # Parse income/expenses from JSON strings to preserve components
    income_dict = json.loads(definition.monthly_income) if isinstance(definition.monthly_income, str) else definition.monthly_income
    expense_dict = json.loads(definition.monthly_expenses) if isinstance(definition.monthly_expenses, str) else definition.monthly_expenses

    # Handle both flat numbers and component dicts
    if isinstance(income_dict, (int, float)):
        monthly_income = IncomeBreakdown(components={"income": income_dict})
    else:
        monthly_income = IncomeBreakdown(components=income_dict)

    if isinstance(expense_dict, (int, float)):
        monthly_expenses = ExpenseBreakdown(components={"expenses": expense_dict})
    else:
        monthly_expenses = ExpenseBreakdown(components=expense_dict)

    # Reconstruct optional fields
    mortgage = None
    if definition.mortgage:
        m = definition.mortgage
        mortgage = Mortgage(
            principal=m.principal,
            annual_rate=m.annual_rate / 100,  # Convert from percentage to decimal
            duration_years=m.duration_years,
            currency=m.currency
        )

    pension = None
    if definition.pension:
        p = definition.pension
        pension = Pension(
            initial_value=p.initial_value,
            monthly_contribution=p.monthly_contribution,
            annual_growth_rate=p.annual_growth_rate,
            accessible_at_age=p.accessible_at_age
        )

    # Reconstruct events
    events = []
    if definition.events:
        for e in definition.events:
            events.append(Event(
                year=e.year,
                portfolio_injection=e.portfolio_injection,
                description=e.description
            ))

    # Build scenario
    return Scenario(
        name=definition.name,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        initial_portfolio=definition.initial_portfolio,
        return_rate=definition.return_rate,
        historical_start_year=definition.historical_start_year,
        historical_index=definition.historical_index,
        withdrawal_rate=definition.withdrawal_rate,
        currency=definition.currency,
        age=definition.age,
        events=events,
        mortgage=mortgage,
        pension=pension,
        retirement_mode=definition.retirement_mode,
        retirement_lifestyle_mode=definition.retirement_lifestyle_mode,
        retirement_lifestyle_age=definition.retirement_lifestyle_age,
        partial_retirement_income=definition.partial_retirement_income
    )


@router.post("/monte-carlo", response_model=MonteCarloResponse)
async def monte_carlo(
    request: MonteCarloRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run a Monte Carlo simulation for a saved scenario.

    Generates 500 lognormal trials (configurable), computes p5/p50/p95 percentile bands,
    retirement and survival probabilities, and OAT sensitivity rankings.

    Args:
        request: MonteCarloRequest with scenario_id, n_trials, years
        current_user: Authenticated user
        db: Database session

    Returns:
        MonteCarloResponse with percentile bands, success metrics, and driver rankings
    """
    # Load scenario from database
    definition = db.query(ScenarioDefinition).filter(
        ScenarioDefinition.id == request.scenario_id,
        ScenarioDefinition.profile_id == request.profile_id,
        ScenarioDefinition.is_deleted == False
    ).first()

    if not definition:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Reconstruct scenario domain object
    scenario = _build_scenario_from_definition(definition)

    # Run Monte Carlo
    mc_result = run_monte_carlo(
        scenario,
        n_trials=request.n_trials,
        years=request.years
    )

    # Run sensitivity analysis
    sensitivity_result = run_oat_sensitivity(
        scenario,
        n_trials=request.n_trials,
        years=request.years
    )

    # Format response
    percentile_bands = PercentileBandsSchema(
        p5=mc_result.percentile_p5,
        p50=mc_result.percentile_p50,
        p95=mc_result.percentile_p95
    )

    driver_rankings = [
        DriverRankSchema(
            name=driver.name,
            direction=driver.direction,
            delta=driver.delta
        )
        for driver in sensitivity_result.drivers
    ]

    return MonteCarloResponse(
        scenario_name=scenario.name,
        retirement_probability=mc_result.retirement_probability,
        survival_probability=mc_result.survival_probability,
        percentile_bands=percentile_bands,
        driver_rankings=driver_rankings,
        ages=mc_result.ages
    )
