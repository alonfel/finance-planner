"""
What-If Scenario Save Router

Handles saving What-If Explorer configurations as new named scenarios.
Provides persistence to both:
  - Database: SQLite with ScenarioDefinition, ScenarioResult, and YearData rows
  - Disk: scenarios.json file (read-only backup, updated for portability)

Workflow:
  1. Validate scenario name uniqueness (query scenario_definitions table)
  2. Create Scenario object from request parameters
  3. Run simulation to get year-by-year results
  4. Insert into scenario_definitions + scenario_events + scenario_mortgages
  5. Create/reuse "What-If Saves" SimulationRun
  6. Store ScenarioResult and YearData in SQLite
"""
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import SaveScenarioRequest, SaveScenarioResponse
from models import (
    Profile, SimulationRun, ScenarioResult, YearData,
    ScenarioDefinition, ScenarioEvent, ScenarioMortgage, ScenarioPension
)
from auth import get_current_user
from domain.models import Scenario, Event, Mortgage, Pension
from domain.simulation import simulate
from domain.breakdown import IncomeBreakdown, ExpenseBreakdown

WHATIF_SAVES_LABEL = "What-If Saves"  # Special run label for all what-if saves in a profile
router = APIRouter(prefix="/api/v1/profiles", tags=["whatif-saves"])

@router.post("/{profile_id}/saved-scenarios", response_model=SaveScenarioResponse, status_code=201)
def save_whatif_scenario(profile_id: int, body: SaveScenarioRequest,
                          username: str = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    """
    Save a What-If Explorer configuration as a named scenario.

    Workflow:
      1. Validate profile exists
      2. Check scenario name uniqueness (query database)
      3. Create Scenario domain object from request params
      4. Run simulation to calculate year-by-year results
      5. Insert into scenario_definitions, scenario_events, scenario_mortgages
      6. Create/reuse "What-If Saves" SimulationRun in SQLite
      7. Store ScenarioResult and YearData rows
      8. Optionally export to scenarios.json for portability

    Returns:
      201 Created with scenario_result_id, run_id, retirement_year, final_portfolio

    Errors:
      404 - Profile not found
      409 - Scenario name already exists
    """
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    _assert_name_unique(db, profile_id, body.scenario_name)

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

    scenario_obj = Scenario(
        name=body.scenario_name,
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
        events=[Event(year=e.year, portfolio_injection=e.portfolio_injection,
                      description=e.description) for e in body.events]
    )

    try:
        sim_result = simulate(scenario_obj, years=body.years)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Insert into scenario_definitions
    definition = ScenarioDefinition(
        profile_id=profile_id,
        name=body.scenario_name,
        monthly_income=json.dumps({"income": body.monthly_income}),
        monthly_expenses=json.dumps({"expenses": body.monthly_expenses}),
        initial_portfolio=body.initial_portfolio,
        age=body.starting_age,
        currency=body.currency,
        return_rate=body.return_rate,
        historical_start_year=body.historical_start_year,
        historical_index=body.historical_index,
        withdrawal_rate=body.withdrawal_rate,
        retirement_mode=body.retirement_mode,
        saved_from="whatif",
        saved_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
    )
    db.add(definition)
    db.flush()

    # Insert events
    for event in scenario_obj.events:
        db.add(ScenarioEvent(
            scenario_id=definition.id,
            year=event.year,
            portfolio_injection=event.portfolio_injection,
            description=event.description,
        ))

    # Insert mortgage if present
    if body.mortgage:
        db.add(ScenarioMortgage(
            scenario_id=definition.id,
            principal=body.mortgage.principal,
            annual_rate=body.mortgage.annual_rate,
            duration_years=body.mortgage.duration_years,
            currency=body.mortgage.currency,
        ))

    # Insert pension if present
    if body.pension:
        db.add(ScenarioPension(
            scenario_id=definition.id,
            initial_value=body.pension.initial_value,
            monthly_contribution=body.pension.monthly_contribution,
            annual_growth_rate=body.pension.annual_growth_rate,
            accessible_at_age=body.pension.accessible_at_age,
        ))

    db.flush()

    # Create/reuse "What-If Saves" run
    run = _get_or_create_whatif_run(db, profile_id)

    # Insert ScenarioResult
    scenario_result = ScenarioResult(
        run_id=run.id,
        scenario_id=definition.id,
        scenario_name=body.scenario_name,
        retirement_year=sim_result.retirement_year
    )
    db.add(scenario_result)
    db.flush()

    # Insert YearData
    for yd in sim_result.year_data:
        db.add(YearData(
            result_id=scenario_result.id,
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
        ))

    db.commit()
    run.num_scenarios = db.query(ScenarioResult).filter(ScenarioResult.run_id == run.id).count()
    db.commit()
    db.refresh(scenario_result)

    final_portfolio = sim_result.year_data[-1].portfolio if sim_result.year_data else 0.0
    return SaveScenarioResponse(
        scenario_result_id=scenario_result.id,
        run_id=run.id,
        scenario_name=body.scenario_name,
        retirement_year=sim_result.retirement_year,
        final_portfolio=final_portfolio
    )


def _assert_name_unique(db: Session, profile_id: int, name: str) -> None:
    """
    Validate that a scenario name doesn't already exist for this profile.

    Args:
        db: SQLAlchemy session
        profile_id: Profile ID
        name: Scenario name to check

    Raises:
        HTTPException(409): If name already exists in scenario_definitions
    """
    existing = db.query(ScenarioDefinition).filter(
        ScenarioDefinition.profile_id == profile_id,
        ScenarioDefinition.name == name
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail=f"A scenario named '{name}' already exists.")


def _get_or_create_whatif_run(db: Session, profile_id: int) -> SimulationRun:
    """
    Get or create the "What-If Saves" SimulationRun for a profile.

    All what-if saved scenarios for a profile are grouped under a single
    special SimulationRun with label "What-If Saves". This allows users
    to view all saved what-if scenarios together in the Scenarios view.

    Args:
        db: SQLAlchemy session
        profile_id: Profile ID

    Returns:
        SimulationRun: Existing or newly created what-if saves run
    """
    run = db.query(SimulationRun).filter(
        SimulationRun.profile_id == profile_id,
        SimulationRun.label == WHATIF_SAVES_LABEL
    ).first()

    if run is None:
        run = SimulationRun(
            profile_id=profile_id,
            generated_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
            num_scenarios=0,
            label=WHATIF_SAVES_LABEL
        )
        db.add(run)
        db.commit()
        db.refresh(run)

    return run
