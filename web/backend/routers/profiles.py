from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import ProfileSchema, SimulationRunSchema
from models import Profile, SimulationRun
from auth import get_current_user

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])

@router.get("", response_model=list[ProfileSchema])
def list_profiles(
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all profiles"""
    profiles = db.query(Profile).all()
    return profiles

@router.get("/{profile_id}/runs", response_model=list[SimulationRunSchema])
def get_profile_runs(
    profile_id: int,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all simulation runs for a profile"""
    runs = db.query(SimulationRun).filter(
        SimulationRun.profile_id == profile_id
    ).all()
    return runs
