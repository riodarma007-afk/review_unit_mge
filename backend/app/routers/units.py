from fastapi import APIRouter, Depends, Query, HTTPException

from datetime import date
from typing import Optional

from app.repositories.optrack_repository import OptrackRepository
from app.services.kpi_calculator import KpiCalculator
from app.schemas.unit import UnitRankingResponse, UnitDetailResponse

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

@router.get("/ranking", response_model=UnitRankingResponse)
def get_unit_ranking(
    metric: str = Query("productivity", description="productivity, ritasi, ma_percent, pa_percent, ua_percent, eu_percent"),
    order: str = Query("desc", description="desc atau asc"),
    limit: int = Query(10, description="jumlah limit"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    shift: Optional[str] = None,
    pit: Optional[str] = None,
    activity: Optional[str] = None,
    
):
    filters = _get_filters(date_from, date_to, shift, pit, None, activity)
    repo = OptrackRepository()
    
    data_utama = repo.get_data_utama(**filters)
    events = repo.get_events(**filters)
    
    rank_data = KpiCalculator.calculate_unit_ranking(data_utama, events, metric)
    
    if rank_data:
        # Sort by value
        rank_data.sort(key=lambda x: x.get('value', 0) or 0, reverse=(order != 'asc'))
        # Limit
        data = rank_data[:limit]
    else:
        data = []
        
    return UnitRankingResponse(metric=metric, data=data)

@router.get("/{unit_code}/detail", response_model=UnitDetailResponse)
def get_unit_detail(
    unit_code: str,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    shift: Optional[str] = None,
    pit: Optional[str] = None,
    
):
    filters = _get_filters(date_from, date_to, shift, pit, unit_code, None)
    repo = OptrackRepository()
    
    data_utama = repo.get_data_utama(**filters)
    events = repo.get_events(**filters)
    
    if not data_utama:
        raise HTTPException(status_code=404, detail=f"Unit {unit_code} not found for given filters")
        
    kpi_result = KpiCalculator.summarize_kpi(data_utama, events)
    
    events_list = []
    if events:
        for row in events:
            events_list.append({
                "time": str(row.get('Time', '')),
                "status": str(row.get('Status', '')),
                "start": str(row.get('Start', '')),
                "stop": str(row.get('Stop', '')),
                "durasi_jam": float(row.get('Durasi', 0.0) or 0.0)
            })
            
    return UnitDetailResponse(
        unit_code=unit_code,
        kpi=kpi_result,
        events=events_list
    )

@router.get("/performance")
def get_all_unit_performance(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    shift: Optional[str] = None,
    pit: Optional[str] = None,
    activity: Optional[str] = None
):
    filters = _get_filters(date_from, date_to, shift, pit, None, activity)
    repo = OptrackRepository()
    
    data_utama = repo.get_data_utama(**filters)
    events = repo.get_events(**filters)
    
    results = KpiCalculator.calculate_all_units_kpi(data_utama, events)
    return {"data": results}
