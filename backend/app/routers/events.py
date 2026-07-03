from fastapi import APIRouter, Depends

from datetime import date
from typing import Optional

from app.repositories.optrack_repository import OptrackRepository
from app.services.delay_analysis import DelayAnalysisService
from app.schemas.event import DelayParetoResponse

router = APIRouter()

def _get_filters(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    shift: Optional[str] = None,
    pit: Optional[str] = None,
    unit_code: Optional[str] = None,
    activity: Optional[str] = None
):
    return {
        "date_from": date_from, "date_to": date_to, "shift": shift,
        "pit": pit, "unit_code": unit_code, "activity": activity
    }

@router.get("/pareto", response_model=DelayParetoResponse)
def get_delay_pareto(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    shift: Optional[str] = None,
    pit: Optional[str] = None,
    unit_code: Optional[str] = None,
    activity: Optional[str] = None,
    
):
    filters = _get_filters(date_from, date_to, shift, pit, unit_code, activity)
    repo = OptrackRepository()
    
    events = repo.get_events(**filters)
    
    result = DelayAnalysisService.calculate_pareto(events)
    return DelayParetoResponse(**result)
