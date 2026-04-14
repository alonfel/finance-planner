from fastapi import APIRouter, Depends, HTTPException
from domain.models import Scenario, Event, Mortgage, Pension
from domain.simulation import simulate
from domain.breakdown import IncomeBreakdown, ExpenseBreakdown
from schemas import SimulateRequest, SimulateResponse, YearDataSchema
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
                for e in body.events]
    )

    try:
        result = simulate(scenario, years=body.years)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Convert domain YearData to schema format
    year_data_schemas = []
    for yd in result.year_data:
        schema = YearDataSchema(
            year=yd.year,
            age=yd.age,
            income=yd.income,
            expenses=yd.expenses,
            net_savings=yd.net_savings,
            portfolio=yd.portfolio,
            required_capital=yd.required_capital,
            mortgage_active=yd.mortgage_active,
            pension_value=yd.pension_value,
            pension_accessible=yd.pension_accessible
        )
        year_data_schemas.append(schema)

    # Calculate total savings (sum of all annual net savings)
    total_savings = sum(yd.net_savings for yd in result.year_data)

    # Get final portfolio value
    final_portfolio = result.year_data[-1].portfolio if result.year_data else 0.0

    return SimulateResponse(
        scenario_name="What-If",
        retirement_year=result.retirement_year,
        final_portfolio=final_portfolio,
        total_savings=total_savings,
        year_data=year_data_schemas
    )
