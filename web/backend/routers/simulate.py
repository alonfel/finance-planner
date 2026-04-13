from fastapi import APIRouter, Depends
from domain.models import Scenario
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
    scenario = Scenario(
        name="What-If",
        monthly_income=IncomeBreakdown(components={"income": body.monthly_income}),
        monthly_expenses=ExpenseBreakdown(components={"expenses": body.monthly_expenses}),
        return_rate=body.return_rate,
        age=body.starting_age,
        initial_portfolio=body.initial_portfolio
    )

    result = simulate(scenario, years=body.years)

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
