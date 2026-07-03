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
    
    df_utama = repo.get_data_utama_df(**filters)
    df_events = repo.get_events_df(**filters)
    
    df_rank = KpiCalculator.calculate_unit_ranking(df_utama, df_events, metric)
    
    if not df_rank.empty:
        df_rank = df_rank.sort_values(by='value', ascending=(order == 'asc'))
        df_rank = df_rank.head(limit)
        data = df_rank.to_dict('records')
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
    
    df_utama = repo.get_data_utama_df(**filters)
    df_events = repo.get_events_df(**filters)
    
    if df_utama.empty:
        raise HTTPException(status_code=404, detail=f"Unit {unit_code} not found for given filters")
        
    kpi_result = KpiCalculator.summarize_kpi(df_utama, df_events)
    
    events_list = []
    if not df_events.empty:
        for _, row in df_events.iterrows():
            events_list.append({
                "time": str(row.get('Time', '')),
                "status": str(row.get('Status', '')),
                "start": str(row.get('Start', '')),
                "stop": str(row.get('Stop', '')),
                "durasi_jam": float(row.get('Durasi', 0.0))
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
    
    df_utama = repo.get_data_utama_df(**filters)
    df_events = repo.get_events_df(**filters)
    
    results = KpiCalculator.calculate_all_units_kpi(df_utama, df_events)
    return {"data": results}
