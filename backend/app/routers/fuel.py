from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
import httpx
from app.core.config import settings

router = APIRouter()

def optrack_to_fuel(unit_code: str) -> str:
    """Convert OpTrack unit_code format to fuel API format.
    OpTrack: 'GHT 701' -> Fuel: 'GHT-701'
    """
    return unit_code.replace(' ', '-')


def fuel_to_optrack(unit_code: str) -> str:
    """Convert fuel API unit_code format to OpTrack format.
    Fuel: 'GHT-701' -> OpTrack: 'GHT 701'
    """
    # Fuel unit_fix already uses space format like OpTrack
    return unit_code


import time

_FUEL_CACHE = {}
CACHE_TTL = 300  # 5 minutes

async def _fetch_fuel_pages(params: dict) -> list:
    """Fetch all pages of fuel data from external API (with caching).
    Uses limit=500 (API max) and concurrent fetching for speed.
    """
    import asyncio

    # Check cache first
    cache_key = str(sorted(params.items()))
    if cache_key in _FUEL_CACHE:
        cached_time, cached_data = _FUEL_CACHE[cache_key]
        if time.time() - cached_time < CACHE_TTL:
            return cached_data

    headers = {"X-API-Key": settings.FUEL_API_KEY}
    PAGE_LIMIT = 500  # API maximum

    async with httpx.AsyncClient(timeout=30.0) as client:
        # First request to get totalPages
        try:
            resp = await client.get(
                settings.FUEL_API_URL,
                headers=headers,
                params={**params, "page": 1, "limit": PAGE_LIMIT}
            )
            resp.raise_for_status()
            body = resp.json()
            all_rows = body.get("data", [])
            total_pages = body.get("meta", {}).get("totalPages", 1)
        except Exception as e:
            print(f"Failed to fetch fuel data page 1: {e}")
            return []

        # Fetch remaining pages concurrently
        if total_pages > 1:
            async def fetch_page(p):
                try:
                    r = await client.get(
                        settings.FUEL_API_URL,
                        headers=headers,
                        params={**params, "page": p, "limit": PAGE_LIMIT}
                    )
                    r.raise_for_status()
                    return r.json().get("data", [])
                except Exception as e:
                    print(f"Failed to fetch fuel data page {p}: {e}")
                    return []

            results = await asyncio.gather(
                *[fetch_page(p) for p in range(2, total_pages + 1)]
            )
            for page_data in results:
                all_rows.extend(page_data)

    # Save to cache
    _FUEL_CACHE[cache_key] = (time.time(), all_rows)
    return all_rows
_FUEL_RESULT_CACHE = {}

@router.get("/unit")
async def get_fuel_by_unit(
    unit_code: str = Query(..., description="OpTrack unit code, e.g. 'GHT 701'"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """Get fuel refueling data for a specific unit within a date range.
    Converts OpTrack unit naming to fuel API naming automatically.
    Returns total refueling (liters), refueling count, and daily breakdown.
    """
    # Check result cache first (instant return for repeated requests)
    result_key = f"{unit_code}|{date_from}|{date_to}"
    if result_key in _FUEL_RESULT_CACHE:
        cached_time, cached_result = _FUEL_RESULT_CACHE[result_key]
        if time.time() - cached_time < CACHE_TTL:
            return cached_result

    fuel_unit_code = optrack_to_fuel(unit_code)

    params = {"search": fuel_unit_code}
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to

    rows = await _fetch_fuel_pages(params)

    # Also fetch lookback data (30 days before date_from) for delta calculation
    lookback_rows = []
    if date_from:
        from datetime import timedelta
        lookback_start = (datetime.strptime(date_from, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
        lookback_end = (datetime.strptime(date_from, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        lookback_params = {"search": fuel_unit_code, "date_from": lookback_start, "date_to": lookback_end}
        lookback_rows = await _fetch_fuel_pages(lookback_params)

    # Merge and deduplicate by id
    seen_ids = set()
    combined = []
    for r in lookback_rows + rows:
        rid = r.get("id")
        if rid not in seen_ids:
            seen_ids.add(rid)
            combined.append(r)

    # Filter to exact unit match (search is fuzzy)
    all_history = [r for r in combined if r.get("unit_code") == fuel_unit_code]

    # Parse datetime for sorting
    for r in all_history:
        dt_str = r.get("date", "")[:10]
        tm_str = r.get("time", "00:00:00")
        try:
            r["_dt"] = datetime.strptime(f"{dt_str} {tm_str}", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            r["_dt"] = datetime.min

    # Sort ascending
    all_history.sort(key=lambda x: x["_dt"])
    
    # Calculate Sequential Metrics for ALL history
    prev_record = None
    for row in all_history:
        liters = float(row.get("refueling", 0) or 0)
        current_km = float(row.get("km") or 0) if row.get("km") is not None else None
        current_hm = float(row.get("hm") or 0) if row.get("hm") is not None else None
        
        distance_km = None
        hm_used = None
        km_per_liter = None
        liter_per_hm = None
        warning = None
        
        if prev_record:
            prev_km = prev_record["km"]
            prev_hm = prev_record["hm"]
            
            if current_km is not None and prev_km is not None:
                distance_km = current_km - prev_km
                if distance_km < 0:
                    warning = "KM turun, cek odometer"
                    distance_km = None
            
            if current_hm is not None and prev_hm is not None:
                hm_used = current_hm - prev_hm
                if hm_used <= 0:
                    warning = "HM tidak bertambah"
                    hm_used = None
            
            if liters > 0:
                if distance_km is not None:
                    km_per_liter = distance_km / liters
                if hm_used is not None:
                    liter_per_hm = liters / hm_used
            else:
                warning = "Invalid refueling liter"
        else:
            warning = "First record for this unit"
            
        row["metrics"] = {
            "distance_km": round(distance_km, 1) if distance_km is not None else None,
            "hm_used": round(hm_used, 1) if hm_used is not None else None,
            "km_per_liter": round(km_per_liter, 2) if km_per_liter is not None else None,
            "liter_per_hm": round(liter_per_hm, 2) if liter_per_hm is not None else None,
            "warning": warning
        }
        
        prev_record = {
            "km": current_km,
            "hm": current_hm
        }

    # Now filter the results based on the requested date range
    filtered = []
    
    # Convert query strings to dates for comparison
    filter_start = datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None
    filter_end = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None
    
    total_liters = 0.0
    total_distance = 0.0
    total_hm_used = 0.0
    
    for row in all_history:
        row_date = row["_dt"].date()
        
        # Check date range
        if filter_start and row_date < filter_start:
            continue
        if filter_end and row_date > filter_end:
            continue
            
        filtered.append(row)
        
        liters = float(row.get("refueling", 0) or 0)
        total_liters += liters
        
        m = row["metrics"]
        if m["distance_km"] is not None:
            total_distance += m["distance_km"]
        if m["hm_used"] is not None:
            total_hm_used += m["hm_used"]

    avg_km_per_liter = (total_distance / total_liters) if total_liters > 0 and total_distance > 0 else None
    avg_liter_per_hm = (total_liters / total_hm_used) if total_hm_used > 0 else None

    result = {
        "unit_code": unit_code,
        "fuel_unit_code": fuel_unit_code,
        "total_liters": round(total_liters, 1),
        "refuel_count": len(filtered),
        "total_distance_km": round(total_distance, 1),
        "total_hm_used": round(total_hm_used, 1),
        "average_km_per_liter": round(avg_km_per_liter, 2) if avg_km_per_liter is not None else None,
        "average_liter_per_hm": round(avg_liter_per_hm, 2) if avg_liter_per_hm is not None else None,
    }

    # Cache the result
    _FUEL_RESULT_CACHE[result_key] = (time.time(), result)
    return result


@router.get("/summary")
async def get_fuel_summary(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    """Get fuel summary for all MGE units (GHT + GMT).
    Returns per-unit totals matched to OpTrack naming.
    """
    params = {}
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to

    # Fetch GHT and GMT data
    ght_params = {**params, "search": "GHT"}
    gmt_params = {**params, "search": "GMT"}

    ght_rows = await _fetch_fuel_pages(ght_params)
    gmt_rows = await _fetch_fuel_pages(gmt_params)

    all_rows = ght_rows + gmt_rows

    # Filter only exact GHT-xxx and GMT-xxx units
    filtered = [r for r in all_rows if (r.get("unit_code", "").startswith("GHT-") or r.get("unit_code", "").startswith("GMT-"))]

    # Aggregate per unit
    units = {}
    total_liters = 0.0
    total_count = len(filtered)

    for row in filtered:
        uc = row.get("unit_code", "")
        liters = float(row.get("refueling", 0) or 0)
        total_liters += liters

        optrack_name = uc.replace("-", " ")  # GHT-701 -> GHT 701
        if optrack_name not in units:
            units[optrack_name] = {"unit_code": optrack_name, "total_liters": 0.0, "count": 0}
        units[optrack_name]["total_liters"] += liters
        units[optrack_name]["count"] += 1

    units_list = sorted(units.values(), key=lambda x: x["unit_code"])

    return {
        "total_liters": round(total_liters, 1),
        "total_refuel_count": total_count,
        "unit_count": len(units_list),
        "units": units_list,
    }
