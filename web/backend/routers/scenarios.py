import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import (
    ScenarioResultSchema,
    ScenarioSummarySchema,
    ScenarioCardSchema
)
from models import ScenarioResult, YearData, Profile, SimulationRun
from auth import get_current_user
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from infrastructure.data_layer import get_scenarios_path

router = APIRouter(prefix="/api/v1", tags=["scenarios"])

def _get_scenario_events(profile_name: str, scenario_name: str):
    """Load events from scenarios.json for a specific scenario."""
    try:
        scenarios_path = get_scenarios_path(profile_name)
        if not scenarios_path.exists():
            return []

        with open(scenarios_path) as f:
            data = json.load(f)

        for scenario in data.get("scenarios", []):
            if scenario.get("name") == scenario_name:
                events = scenario.get("events", [])
                # Convert to EventSchema format (year, portfolio_injection, description)
                return [
                    {
                        "year": e.get("year"),
                        "portfolio_injection": e.get("portfolio_injection", 0),
                        "description": e.get("description", "")
                    }
                    for e in events
                ]
        return []
    except Exception:
        return []

@router.get("/runs/{run_id}/scenarios", response_model=list[ScenarioCardSchema])
def list_scenarios(
    run_id: int,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all scenarios for a simulation run"""
    results = db.query(ScenarioResult).filter(
        ScenarioResult.run_id == run_id
    ).all()

    cards = []
    for result in results:
        final_year = db.query(YearData).filter(
            YearData.result_id == result.id
        ).order_by(YearData.year.desc()).first()

        final_portfolio = final_year.portfolio if final_year else 0.0
        cards.append({
            "id": result.id,
            "scenario_name": result.scenario_name,
            "retirement_year": result.retirement_year,
            "final_portfolio": final_portfolio
        })

    return cards

@router.get("/scenarios/{result_id}", response_model=ScenarioResultSchema)
def get_scenario_detail(
    result_id: int,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full scenario result with all year data and original events"""
    result = db.query(ScenarioResult).filter(
        ScenarioResult.id == result_id
    ).first()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    year_data = db.query(YearData).filter(
        YearData.result_id == result_id
    ).order_by(YearData.year).all()

    # Get the profile name for this scenario via the SimulationRun
    events = []
    sim_run = db.query(SimulationRun).filter(SimulationRun.id == result.run_id).first()
    if sim_run:
        profile = db.query(Profile).filter(Profile.id == sim_run.profile_id).first()
        if profile:
            events = _get_scenario_events(profile.name, result.scenario_name)

    return {
        "id": result.id,
        "scenario_name": result.scenario_name,
        "retirement_year": result.retirement_year,
        "year_data": year_data,
        "events": events
    }

@router.get("/scenarios/{result_id}/summary", response_model=ScenarioSummarySchema)
def get_scenario_summary(
    result_id: int,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get scenario summary (retirement year, final portfolio, etc)"""
    result = db.query(ScenarioResult).filter(
        ScenarioResult.id == result_id
    ).first()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    year_data = db.query(YearData).filter(
        YearData.result_id == result_id
    ).order_by(YearData.year).all()

    if not year_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    final_year = year_data[-1]
    first_year = year_data[0]

    retirement_age = None
    if result.retirement_year:
        # retirement_year is 1-indexed, so age = first_year.age + (retirement_year - 1)
        retirement_age = first_year.age + (result.retirement_year - 1)

    return {
        "scenario_name": result.scenario_name,
        "retirement_year": result.retirement_year,
        "final_portfolio": final_year.portfolio,
        "years_simulated": len(year_data),
        "retirement_age": retirement_age
    }
