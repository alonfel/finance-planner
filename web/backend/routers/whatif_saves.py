"""
What-If Scenario Save Router

Handles saving What-If Explorer configurations as new named scenarios.
Provides persistence to both:
  - Disk: scenarios.json file with file locking for concurrency
  - Database: SQLite with new ScenarioResult and YearData rows

Workflow:
  1. Validate scenario name uniqueness
  2. Create Scenario object from request parameters
  3. Run simulation to get year-by-year results
  4. Append to scenarios.json (with file lock)
  5. Create/reuse "What-If Saves" SimulationRun
  6. Store ScenarioResult and YearData in SQLite
"""
import json
from datetime import datetime
import filelock
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import SaveScenarioRequest, SaveScenarioResponse
from models import Profile, SimulationRun, ScenarioResult, YearData
from auth import get_current_user
from domain.models import Scenario, Event, Mortgage
from domain.simulation import simulate
from domain.breakdown import IncomeBreakdown, ExpenseBreakdown
from infrastructure.data_layer import get_scenarios_path

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
      2. Check scenario name uniqueness
      3. Create Scenario domain object from request params
      4. Run simulation to calculate year-by-year results
      5. Persist to scenarios.json (disk) using file lock
      6. Create/reuse "What-If Saves" SimulationRun in SQLite
      7. Store ScenarioResult and YearData rows

    Returns:
      201 Created with scenario_result_id, run_id, retirement_year, final_portfolio

    Errors:
      404 - Profile not found
      409 - Scenario name already exists
    """
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    scenarios_path = get_scenarios_path(profile.name)
    _assert_name_unique(scenarios_path, body.scenario_name)

    mortgage = None
    if body.mortgage:
        mortgage = Mortgage(
            principal=body.mortgage.principal,
            annual_rate=body.mortgage.annual_rate,
            duration_years=body.mortgage.duration_years,
            currency=body.mortgage.currency
        )

    scenario_obj = Scenario(
        name=body.scenario_name,
        monthly_income=IncomeBreakdown(components={"income": body.monthly_income}),
        monthly_expenses=ExpenseBreakdown(components={"expenses": body.monthly_expenses}),
        return_rate=body.return_rate,
        age=body.starting_age,
        initial_portfolio=body.initial_portfolio,
        mortgage=mortgage,
        events=[Event(year=e.year, portfolio_injection=e.portfolio_injection,
                      description=e.description) for e in body.events]
    )
    sim_result = simulate(scenario_obj, years=body.years)

    _append_to_scenarios_json(scenarios_path, body)

    run = _get_or_create_whatif_run(db, profile_id)

    scenario_result = ScenarioResult(run_id=run.id, scenario_name=body.scenario_name,
                                      retirement_year=sim_result.retirement_year)
    db.add(scenario_result)
    db.flush()

    for yd in sim_result.year_data:
        db.add(YearData(result_id=scenario_result.id, year=yd.year, age=yd.age,
                        income=yd.income, expenses=yd.expenses, net_savings=yd.net_savings,
                        portfolio=yd.portfolio, required_capital=yd.required_capital,
                        mortgage_active=yd.mortgage_active, pension_value=yd.pension_value,
                        pension_accessible=yd.pension_accessible))

    db.commit()
    run.num_scenarios = db.query(ScenarioResult).filter(ScenarioResult.run_id == run.id).count()
    db.commit()
    db.refresh(scenario_result)

    final_portfolio = sim_result.year_data[-1].portfolio if sim_result.year_data else 0.0
    return SaveScenarioResponse(scenario_result_id=scenario_result.id, run_id=run.id,
                                 scenario_name=body.scenario_name,
                                 retirement_year=sim_result.retirement_year,
                                 final_portfolio=final_portfolio)


def _assert_name_unique(scenarios_path, name):
    """
    Validate that a scenario name doesn't already exist in scenarios.json.

    Args:
        scenarios_path: Path to scenarios.json file
        name: Scenario name to check

    Raises:
        HTTPException(409): If name already exists in scenarios file
    """
    if not scenarios_path.exists():
        return
    with open(scenarios_path) as f:
        data = json.load(f)
    if name in {s["name"] for s in data.get("scenarios", [])}:
        raise HTTPException(status_code=409, detail=f"A scenario named '{name}' already exists.")


def _append_to_scenarios_json(scenarios_path, body):
    """
    Atomically append a new scenario to scenarios.json using FileLock.

    Uses filelock.FileLock to ensure only one process writes at a time,
    preventing concurrent modification issues on shared filesystems.

    Args:
        scenarios_path: Path to scenarios.json file
        body: SaveScenarioRequest with scenario parameters
    """
    lock_path = str(scenarios_path) + ".lock"
    with filelock.FileLock(lock_path, timeout=5):
        with open(scenarios_path) as f:
            data = json.load(f)

        scenario_entry = {
            "name": body.scenario_name,
            "monthly_income": body.monthly_income,
            "monthly_expenses": body.monthly_expenses,
            "return_rate": body.return_rate,
            "age": body.starting_age,
            "initial_portfolio": body.initial_portfolio,
            "currency": "ILS",
            "events": [{"year": e.year, "portfolio_injection": e.portfolio_injection,
                         "description": e.description} for e in body.events],
            "saved_from": "whatif",
            "saved_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }

        # Add mortgage if it exists
        if body.mortgage:
            scenario_entry["mortgage"] = {
                "principal": body.mortgage.principal,
                "annual_rate": body.mortgage.annual_rate,
                "duration_years": body.mortgage.duration_years,
                "currency": body.mortgage.currency
            }

        data["scenarios"].append(scenario_entry)
        with open(scenarios_path, "w") as f:
            json.dump(data, f, indent=2)


def _get_or_create_whatif_run(db, profile_id):
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
    run = db.query(SimulationRun).filter(SimulationRun.profile_id == profile_id,
                                          SimulationRun.label == WHATIF_SAVES_LABEL).first()
    if run is None:
        run = SimulationRun(profile_id=profile_id,
                             generated_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
                             num_scenarios=0, label=WHATIF_SAVES_LABEL)
        db.add(run)
        db.commit()
        db.refresh(run)
    return run
