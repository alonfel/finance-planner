"""
API Router for Guided Scenario Generator

Endpoints:
  POST /api/questionnaire/config - Get questionnaire configuration
  POST /api/questionnaire/completeness - Calculate data completeness score
  POST /api/generate-scenario - Generate scenario from answers
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

from services.scenario_generator import get_service
from database import get_db
from models import ScenarioDefinition, SimulationRun, ScenarioResult, YearData

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/questionnaire", tags=["questionnaire"])


# ============ REQUEST/RESPONSE MODELS ============

class QuestionnaireAnswersRequest(BaseModel):
    """Answers to questionnaire questions."""
    answers: Dict[str, Any]
    profile: str = "alon"


class QuestionnaireCompletenessResponse(BaseModel):
    """Data completeness score response."""
    completeness_score: float  # 0.0 to 1.0
    percentage: int  # 0 to 100
    answered_questions: int
    total_required_questions: int


class GenerateScenarioResponse(BaseModel):
    """Generated scenario response."""
    scenario_id: str
    name: str
    retirement_year: int
    final_portfolio: float
    monthly_income: float
    monthly_expenses: float
    initial_portfolio: float
    data_completeness_score: float
    verdict: str  # 'success', 'warning', 'fail'
    emoji: str
    message: str
    hint: str


class QuestionnaireConfigResponse(BaseModel):
    """Questionnaire configuration response."""
    version: str
    questions: list
    sections: dict
    scoring: dict


# ============ ENDPOINTS ============

@router.post("/config", response_model=QuestionnaireConfigResponse)
async def get_questionnaire_config():
    """
    Get questionnaire configuration.

    Returns all questions, sections, and scoring rules.
    Client uses this to render the question flow.
    """
    service = get_service()
    return {
        'version': service.questionnaire.version,
        'questions': service.questionnaire.data['questions'],
        'sections': service.questionnaire.data.get('sections', {}),
        'scoring': service.questionnaire.data.get('scoring', {})
    }


@router.post("/completeness", response_model=QuestionnaireCompletenessResponse)
async def calculate_completeness(request: QuestionnaireAnswersRequest):
    """
    Calculate data completeness score for given answers.

    Endpoint is used by frontend to update progress bar as user answers questions.
    """
    service = get_service()
    score = service.questionnaire.calculate_completeness_score(request.answers)
    required = service.questionnaire.get_required_questions()
    answered = sum(
        1 for q_id in required
        if q_id in request.answers and request.answers[q_id] is not None
    )

    return {
        'completeness_score': score,
        'percentage': int(score * 100),
        'answered_questions': answered,
        'total_required_questions': len(required)
    }


@router.post("/generate-scenario", response_model=GenerateScenarioResponse)
async def generate_scenario(
    request: QuestionnaireAnswersRequest,
    db=Depends(get_db)
):
    """
    Generate a scenario from questionnaire answers.

    Process:
    1. Validate answers
    2. Fill missing answers from template defaults
    3. Build Scenario object
    4. Run simulation
    5. Evaluate results against rules
    6. Save to database (optional)
    7. Return results

    The returned scenario can then be saved via /api/whatif-saves endpoint.
    """
    try:
        service = get_service()

        # Validate that at least required questions are answered
        required = service.questionnaire.get_required_questions()
        missing = [q for q in required if q not in request.answers or request.answers[q] is None]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required answers: {missing}"
            )

        # Generate scenario
        generation_result = service.generate(request.answers, profile=request.profile)

        scenario = generation_result['scenario']
        result = generation_result['result']
        completeness = generation_result['completeness_score']
        verdict = generation_result['verdict']

        # Build response
        response = GenerateScenarioResponse(
            scenario_id=f"gen-{id(scenario)}",  # Temp ID until saved
            name=scenario.name,
            retirement_year=result.retirement_year,
            final_portfolio=result.year_data[-1].portfolio if result.year_data else 0,
            monthly_income=scenario.monthly_income.total,
            monthly_expenses=scenario.monthly_expenses.total,
            initial_portfolio=scenario.initial_portfolio,
            data_completeness_score=completeness,
            verdict=verdict['verdict'],
            emoji=verdict.get('emoji', ''),
            message=verdict['message'],
            hint=verdict['hint']
        )

        logger.info(f"Generated scenario: {scenario.name} (retirement_year={result.retirement_year})")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ UTILITY ENDPOINTS ============

@router.post("/visible-questions")
async def get_visible_questions(request: QuestionnaireAnswersRequest):
    """
    Get list of questions that should be visible given current answers.

    Used by frontend to determine which questions to display next based on
    conditional visibility rules.
    """
    service = get_service()
    visible = service.questionnaire.get_visible_questions(request.answers)
    return {'visible_questions': visible}
