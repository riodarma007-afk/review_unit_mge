from fastapi import APIRouter, Depends, Query

from datetime import date
from typing import Optional

from app.repositories.optrack_repository import OptrackRepository
from app.services.kpi_calculator import KpiCalculator
from app.schemas.kpi import KpiSummaryResponse, KpiTrendResponse
from app.core.kpi_targets import KPI_TARGETS

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

@router.get("/summary", response_model=KpiSummaryResponse)
def get_kpi_summary(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    shift: Optional[str] = None,
    pit: Optional[str] = None,
    unit_code: Optional[str] = None,
    activity: Optional[str] = None,
    
):
    filters = _get_filters(date_from, date_to, shift, pit, unit_code, activity)
    repo = OptrackRepository()
    
    data_utama = repo.get_data_utama(**filters)
    events = repo.get_events(**filters)
    
    kpi_result = KpiCalculator.summarize_kpi(data_utama, events)
    
    # Calculate period bounds if available
    if data_utama:
        dates = [row.get('Date') for row in data_utama if row.get('Date') is not None]
        d_from = str(min(dates)) if dates else (str(date_from) if date_from else "")
        d_to = str(max(dates)) if dates else (str(date_to) if date_to else "")
        unit_codes = set(row.get('Unit_Code') for row in data_utama if row.get('Unit_Code') is not None)
        unit_count = len(unit_codes)
    else:
        d_from = str(date_from) if date_from else ""
        d_to = str(date_to) if date_to else ""
        unit_count = 0
    
    # Tambahkan total jam operasional
    total_mohh = sum(float(row.get('MOHH', 0) or 0) for row in data_utama) if data_utama else 0
    total_wh = sum(float(row.get('WH', 0) or 0) for row in data_utama) if data_utama else 0
    total_downtime = sum(float(row.get('Downtime', 0) or 0) for row in data_utama) if data_utama else 0
    
    return KpiSummaryResponse(
        period={"date_from": d_from, "date_to": d_to},
        unit_count=unit_count,
        targets=KPI_TARGETS,
        total_mohh=round(total_mohh, 2),
        total_wh=round(total_wh, 2),
        total_downtime=round(total_downtime, 2),
        **kpi_result
    )

@router.get("/trend", response_model=KpiTrendResponse)
def get_kpi_trend(
    group_by: str = Query("date", description="date, shift, atau pit"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    shift: Optional[str] = None,
    pit: Optional[str] = None,
    unit_code: Optional[str] = None,
    activity: Optional[str] = None,
    
):
    filters = _get_filters(date_from, date_to, shift, pit, unit_code, activity)
    repo = OptrackRepository()
    
    data_utama = repo.get_data_utama(**filters)
    events = repo.get_events(**filters)
    
    # Map group_by ke kolom
    gb_map = {"date": "Date", "shift": "Shift", "pit": "PIT"}
    col_group = gb_map.get(group_by.lower(), "Date")
    
    series = KpiCalculator.calculate_trend(data_utama, events, col_group)
    
    return KpiTrendResponse(group_by=group_by.lower(), series=series)
