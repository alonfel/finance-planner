from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json
from database import get_db
from schemas import (
    ScenarioResultSchema,
    ScenarioSummarySchema,
    ScenarioCardSchema,
    WhatIfScenarioSchema,
    EventSchema,
    MortgageSchema,
    PensionSchema
)
from models import ScenarioResult, YearData, Profile, SimulationRun, ScenarioDefinition, ScenarioEvent, ScenarioMortgage, ScenarioPension
from auth import get_current_user

router = APIRouter(prefix="/api/v1", tags=["scenarios"])

def _build_definition(db: Session, scenario_id: int):
    """
    Build a complete WhatIfScenarioSchema from a ScenarioDefinition.
    Returns exact values from the database for round-trip accuracy.
    """
    try:
        definition = db.query(ScenarioDefinition).filter(
            ScenarioDefinition.id == scenario_id
        ).first()

        if not definition:
            return None

        # Parse income and expenses JSON and sum the values
        try:
            income_dict = json.loads(definition.monthly_income) if definition.monthly_income else {}
            monthly_income = sum(income_dict.values()) if income_dict else 0.0
        except (json.JSONDecodeError, TypeError):
            monthly_income = 0.0

        try:
            expenses_dict = json.loads(definition.monthly_expenses) if definition.monthly_expenses else {}
            monthly_expenses = sum(expenses_dict.values()) if expenses_dict else 0.0
        except (json.JSONDecodeError, TypeError):
            monthly_expenses = 0.0

        # Get events
        events = []
        event_rows = db.query(ScenarioEvent).filter(
            ScenarioEvent.scenario_id == scenario_id
        ).all()
        for e in event_rows:
            events.append(EventSchema(
                year=e.year,
                portfolio_injection=e.portfolio_injection,
                description=e.description
            ))

        # Get mortgage
        mortgage_data = None
        mortgage = db.query(ScenarioMortgage).filter(
            ScenarioMortgage.scenario_id == scenario_id
        ).first()
        if mortgage:
            mortgage_data = MortgageSchema(
                principal=mortgage.principal,
                annual_rate=mortgage.annual_rate,
                duration_years=mortgage.duration_years,
                currency=mortgage.currency
            )

        # Get pension
        pension_data = None
        pension = db.query(ScenarioPension).filter(
            ScenarioPension.scenario_id == scenario_id
        ).first()
        if pension:
            pension_data = PensionSchema(
                initial_value=pension.initial_value,
                monthly_contribution=pension.monthly_contribution,
                annual_growth_rate=pension.annual_growth_rate,
                accessible_at_age=pension.accessible_at_age
            )

        # Build the full scenario definition schema
        definition_schema = WhatIfScenarioSchema(
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            return_rate=definition.return_rate,
            historical_start_year=definition.historical_start_year,
            withdrawal_rate=definition.withdrawal_rate,
            starting_age=definition.age,
            initial_portfolio=definition.initial_portfolio,
            years=20,  # Default years for What-If (not stored in definition)
            retirement_mode=definition.retirement_mode,
            currency=definition.currency,
            events=events,
            mortgage=mortgage_data,
            pension=pension_data
        )

        return definition_schema
    except Exception as e:
        return None

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
    """Get full scenario result with all year data, events, mortgage, and exact definition"""
    result = db.query(ScenarioResult).filter(
        ScenarioResult.id == result_id
    ).first()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    year_data = db.query(YearData).filter(
        YearData.result_id == result_id
    ).order_by(YearData.year).all()

    # Build full definition from scenario_definition if scenario_id is linked
    definition = None
    events = []
    mortgage = None
    if result.scenario_id:
        definition = _build_definition(db, result.scenario_id)
        if definition:
            # Extract events and mortgage from the definition for backward compatibility
            events = [{"year": e.year, "portfolio_injection": e.portfolio_injection, "description": e.description} for e in definition.events]
            if definition.mortgage:
                mortgage = {"principal": definition.mortgage.principal, "annual_rate": definition.mortgage.annual_rate, "duration_years": definition.mortgage.duration_years, "currency": definition.mortgage.currency}

    return {
        "id": result.id,
        "scenario_name": result.scenario_name,
        "retirement_year": result.retirement_year,
        "year_data": year_data,
        "events": events,
        "mortgage": mortgage,
        "definition": definition
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
