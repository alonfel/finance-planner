from fastapi import APIRouter, Depends, HTTPException
from domain.models import Scenario, Event, Mortgage, Pension, ProbabilisticEvent, EventOutcome
from domain.simulation import simulate, simulate_branches
from domain.breakdown import IncomeBreakdown, ExpenseBreakdown
from schemas import SimulateRequest, SimulateResponse, YearDataSchema, BranchResultSchema
from auth import get_current_user

router = APIRouter(prefix="/api/v1", tags=["simulate"])

@router.post("/simulate", response_model=SimulateResponse)
def run_simulation(body: SimulateRequest, username: str = Depends(get_current_user)):
    """
    Run a real-time simulation with provided parameters.
    Used by What-If Explorer playground for instant portfolio updates.
    """
    mortgage = None
    if body.mortgage:
        mortgage = Mortgage(
            principal=body.mortgage.principal,
            annual_rate=body.mortgage.annual_rate,
            duration_years=body.mortgage.duration_years,
            currency=body.mortgage.currency
        )

    pension = None
    if body.pension:
        pension = Pension(
            initial_value=body.pension.initial_value,
            monthly_contribution=body.pension.monthly_contribution,
            annual_growth_rate=body.pension.annual_growth_rate,
            accessible_at_age=body.pension.accessible_at_age
        )

    prob_events = [
        ProbabilisticEvent(
            name=pe.name,
            outcomes=[
                EventOutcome(
                    year=o.year,
                    probability=o.probability,
                    portfolio_injection=o.portfolio_injection,
                    description=o.description,
                )
                for o in pe.outcomes
            ],
        )
        for pe in body.probabilistic_events
    ]

    scenario = Scenario(
        name="What-If",
        monthly_income=IncomeBreakdown(components={"income": body.monthly_income}),
        monthly_expenses=ExpenseBreakdown(components={"expenses": body.monthly_expenses}),
        return_rate=body.return_rate,
        historical_start_year=body.historical_start_year,
        historical_index=body.historical_index,
        withdrawal_rate=body.withdrawal_rate,
        age=body.starting_age,
        initial_portfolio=body.initial_portfolio,
        currency=body.currency,
        retirement_mode=body.retirement_mode,
        mortgage=mortgage,
        pension=pension,
        events=[Event(year=e.year, portfolio_injection=e.portfolio_injection, description=e.description)
                for e in body.events],
        probabilistic_events=prob_events,
        retirement_lifestyle_mode=body.retirement_lifestyle.mode if body.retirement_lifestyle else None,
        retirement_lifestyle_age=body.retirement_lifestyle.age if body.retirement_lifestyle else None,
        partial_retirement_income=body.retirement_lifestyle.partial_income if body.retirement_lifestyle else None
    )

    try:
        branches = simulate_branches(scenario, years=body.years)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # The first branch is always the base (or only) result — use it for top-level fields
    _, _, primary_result = branches[0]

    def _to_year_data_schemas(year_data):
        return [
            YearDataSchema(
                year=yd.year, age=yd.age, income=yd.income, expenses=yd.expenses,
                net_savings=yd.net_savings, portfolio=yd.portfolio,
                required_capital=yd.required_capital, mortgage_active=yd.mortgage_active,
                pension_value=yd.pension_value, pension_accessible=yd.pension_accessible,
                is_retired=yd.is_retired, active_income=yd.active_income,
            )
            for yd in year_data
        ]

    total_savings = sum(yd.net_savings for yd in primary_result.year_data)
    final_portfolio = primary_result.year_data[-1].portfolio if primary_result.year_data else 0.0

    # Build branch list (empty when no probabilistic events — single branch is the base result)
    branch_schemas: list[BranchResultSchema] = []
    if prob_events:
        for label, probability, branch_result in branches:
            branch_schemas.append(BranchResultSchema(
                label=label,
                probability=probability,
                retirement_year=branch_result.retirement_year,
                final_portfolio=branch_result.year_data[-1].portfolio if branch_result.year_data else 0.0,
                year_data=_to_year_data_schemas(branch_result.year_data),
            ))

    return SimulateResponse(
        scenario_name="What-If",
        retirement_year=primary_result.retirement_year,
        final_portfolio=final_portfolio,
        total_savings=total_savings,
        year_data=_to_year_data_schemas(primary_result.year_data),
        branches=branch_schemas,
    )
