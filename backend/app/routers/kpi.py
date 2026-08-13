from fastapi import APIRouter, Depends, Query

from datetime import date
from typing import Optional

from app.repositories.optrack_repository import OptrackRepository
from app.services.kpi_calculator import KpiCalculator
from app.schemas.kpi import KpiSummaryResponse, KpiTrendResponse
from app.core.kpi_targets import KPI_TARGETS

router = APIRouter()

def _get_dynamic_targets(repo: OptrackRepository, filters: dict, date_from: Optional[date], date_to: Optional[date]):
    # Default targets
    t = {"ma": KPI_TARGETS["ma"], "pa": KPI_TARGETS["pa"], "ua": KPI_TARGETS["ua"], "eu": KPI_TARGETS["eu"]}
    
    if not date_from and not date_to:
        return t
        
    start_date = date_from or date_to
    end_date = date_to or date_from
    
    # Generate list of year, month for the date range
    from datetime import timedelta
    current_date = start_date
    periods = set()
    while current_date <= end_date:
        periods.add((current_date.year, current_date.month))
        # advance to next month
        days_in_month = 32 - (current_date.replace(day=1) + timedelta(days=31)).day
        next_month = current_date + timedelta(days=days_in_month)
        next_month = next_month.replace(day=1)
        if current_date.month == end_date.month and current_date.year == end_date.year:
            break
        current_date = next_month
        
    activity_filter = filters.get("activity")
    pit_filter = filters.get("pit")
    
    # Fetch all targets
    all_targets = repo.get_target_settings()
    
    matching_pa = []
    matching_ua = []
    
    for y, m in periods:
        # Find best match for this period
        best_match = None
        for plan in all_targets:
            if plan['year'] == y and plan['month'] == m:
                match_activity = not activity_filter or plan['activity'] == 'All' or plan['activity'] == activity_filter
                match_pit = not pit_filter or plan['pit'] == 'All' or plan['pit'] == pit_filter
                
                if match_activity and match_pit:
                    if not best_match:
                        best_match = plan
                    else:
                        # Prefer more specific plans over 'All'
                        if plan['activity'] != 'All' and best_match['activity'] == 'All':
                            best_match = plan
                        elif plan['pit'] != 'All' and best_match['pit'] == 'All':
                            best_match = plan
                            
        if best_match:
            matching_pa.append(best_match['pa_target'])
            matching_ua.append(best_match['ua_target'])
            
    if matching_pa:
        t["pa"] = sum(matching_pa) / len(matching_pa)
    if matching_ua:
        t["ua"] = sum(matching_ua) / len(matching_ua)
        
    return t

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
    
    # Calculate dynamic targets
    dynamic_targets = _get_dynamic_targets(repo, filters, date_from, date_to)
    
    return KpiSummaryResponse(
        period={"date_from": d_from, "date_to": d_to},
        unit_count=unit_count,
        targets=dynamic_targets,
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
