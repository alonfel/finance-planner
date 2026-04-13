from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import (
    ScenarioResultSchema,
    ScenarioSummarySchema,
    ScenarioCardSchema
)
from models import ScenarioResult, YearData, Profile, SimulationRun, ScenarioDefinition, ScenarioEvent, ScenarioMortgage
from auth import get_current_user

router = APIRouter(prefix="/api/v1", tags=["scenarios"])

def _get_scenario_data(db: Session, scenario_id: int):
    """Load events and mortgage from database for a specific scenario definition."""
    try:
        definition = db.query(ScenarioDefinition).filter(
            ScenarioDefinition.id == scenario_id
        ).first()

        if not definition:
            return [], None

        # Get events
        events = db.query(ScenarioEvent).filter(
            ScenarioEvent.scenario_id == scenario_id
        ).all()
        events_list = [
            {
                "year": e.year,
                "portfolio_injection": e.portfolio_injection,
                "description": e.description
            }
            for e in events
        ]

        # Get mortgage
        mortgage = db.query(ScenarioMortgage).filter(
            ScenarioMortgage.scenario_id == scenario_id
        ).first()
        mortgage_data = None
        if mortgage:
            mortgage_data = {
                "principal": mortgage.principal,
                "annual_rate": mortgage.annual_rate,
                "duration_years": mortgage.duration_years,
                "currency": mortgage.currency
            }

        return events_list, mortgage_data
    except Exception:
        return [], None

@router.get("/runs/{run_id}/scenarios", response_model=list[ScenarioCardSchema])
def list_scenarios(
    run_id: int,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all scenarios for a simulation run"""
    results = db.query(ScenarioResult).filter(
        ScenarioResult.run_id == run_id,
        ScenarioResult.is_deleted == False
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
    """Get full scenario result with all year data, events, and mortgage"""
    result = db.query(ScenarioResult).filter(
        ScenarioResult.id == result_id
    ).first()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    year_data = db.query(YearData).filter(
        YearData.result_id == result_id
    ).order_by(YearData.year).all()

    # Get events and mortgage from database if scenario_id is linked
    events = []
    mortgage = None
    if result.scenario_id:
        events, mortgage = _get_scenario_data(db, result.scenario_id)

    return {
        "id": result.id,
        "scenario_name": result.scenario_name,
        "retirement_year": result.retirement_year,
        "year_data": year_data,
        "events": events,
        "mortgage": mortgage
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

@router.delete("/scenarios/{result_id}", status_code=204)
def delete_scenario(
    result_id: int,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft-delete a scenario (only What-If Saves scenarios)"""
    result = db.query(ScenarioResult).filter(
        ScenarioResult.id == result_id
    ).first()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Get the run to check if it's a What-If Saves run
    run = db.query(SimulationRun).filter(SimulationRun.id == result.run_id).first()
    if not run or run.label != "What-If Saves":
        raise HTTPException(status_code=403, detail="Can only delete What-If Saves scenarios")

    # Mark as deleted in both result and definition
    result.is_deleted = True
    db.add(result)

    # Also mark the definition as deleted if linked
    if result.scenario_id:
        definition = db.query(ScenarioDefinition).filter(
            ScenarioDefinition.id == result.scenario_id
        ).first()
        if definition:
            definition.is_deleted = True
            db.add(definition)

    db.commit()
