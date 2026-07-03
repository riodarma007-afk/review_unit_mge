from fastapi import APIRouter, Query
from typing import Optional
import httpx
import time
from app.core.config import settings

router = APIRouter()

_HAULING_CACHE = {}
CACHE_TTL = 300  # 5 minutes

async def _fetch_hauling_pages(params: dict) -> list:
    """Fetch all pages of hauling data from external API (with caching).
    Uses limit=500 (API max) and concurrent fetching for speed.
    """
    import asyncio

    # Check cache first
    cache_key = str(sorted(params.items()))
    if cache_key in _HAULING_CACHE:
        cached_time, cached_data = _HAULING_CACHE[cache_key]
        if time.time() - cached_time < CACHE_TTL:
            return cached_data

    headers = {"X-API-Key": settings.FUEL_API_KEY}
    PAGE_LIMIT = 500  # API maximum
    
    # Use the FUEL_API_URL as base but replace /fuel with /coal/hauling
    hauling_url = settings.FUEL_API_URL.replace("/fuel", "/coal/hauling")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # First request to get totalPages
        try:
            resp = await client.get(
                hauling_url,
                headers=headers,
                params={**params, "page": 1, "limit": PAGE_LIMIT}
            )
            resp.raise_for_status()
            body = resp.json()
            all_rows = body.get("data", [])
            total_pages = body.get("meta", {}).get("totalPages", 1)
        except Exception as e:
            print(f"Failed to fetch hauling data page 1: {e}")
            return []

        # Fetch remaining pages concurrently
        if total_pages > 1:
            async def fetch_page(p):
                try:
                    r = await client.get(
                        hauling_url,
                        headers=headers,
                        params={**params, "page": p, "limit": PAGE_LIMIT}
                    )
                    r.raise_for_status()
                    return r.json().get("data", [])
                except Exception as e:
                    print(f"Failed to fetch hauling data page {p}: {e}")
                    return []

            results = await asyncio.gather(
                *[fetch_page(p) for p in range(2, total_pages + 1)]
            )
            for page_data in results:
                all_rows.extend(page_data)

    # Save to cache
    _HAULING_CACHE[cache_key] = (time.time(), all_rows)
    return all_rows

_HAULING_RESULT_CACHE = {}

@router.get("/unit")
async def get_hauling_by_unit(
    unit_code: str = Query(..., description="OpTrack unit code, e.g. 'GHT 748'"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """Get hauling summary for a specific unit (e.g. Total Tonase)."""
    # Check result cache first
    result_key = f"{unit_code}|{date_from}|{date_to}"
    if result_key in _HAULING_RESULT_CACHE:
        cached_time, cached_result = _HAULING_RESULT_CACHE[result_key]
        if time.time() - cached_time < CACHE_TTL:
            return cached_result
    
    params = {"search": unit_code}
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to

    rows = await _fetch_hauling_pages(params)
    
    # Filter strict by unit_code since search can be fuzzy
    filtered = [r for r in rows if str(r.get("unit_id", "")).strip().upper() == unit_code.upper()]
    
    from collections import defaultdict
    from datetime import datetime

    total_tonage = 0.0
    trip_count = len(filtered)
    unique_dates = set()
    total_loading_time_minutes = 0.0
    products_breakdown = defaultdict(int)
    
    for r in filtered:
        # Tonage
        try:
            total_tonage += float(r.get("tonage", 0))
        except (ValueError, TypeError):
            pass
            
        # Dates for Avg Ritasi
        dt = r.get("date")
        if dt:
            unique_dates.add(dt.split("T")[0])
            
        # Loading Time (payload_embark_time - payload_arrival_time)
        arr_str = r.get("payload_arrival_time")
        emb_str = r.get("payload_embark_time")
        if arr_str and emb_str:
            try:
                fmt = "%H:%M:%S"
                t1 = datetime.strptime(arr_str, fmt)
                t2 = datetime.strptime(emb_str, fmt)
                diff = (t2 - t1).total_seconds() / 60.0
                if diff < 0:
                    diff += 24 * 60  # Cross midnight
                total_loading_time_minutes += diff
            except Exception:
                pass
                
        # Products Breakdown
        prod = r.get("product")
        if prod:
            products_breakdown[prod] += 1
            
    days_count = len(unique_dates) if len(unique_dates) > 0 else 1
    avg_ritasi_per_day = trip_count / days_count if days_count > 0 else 0
    avg_payload = total_tonage / trip_count if trip_count > 0 else 0
    avg_loading_time = total_loading_time_minutes / trip_count if trip_count > 0 else 0
            
    result = {
        "unit_code": unit_code,
        "total_tonage": round(total_tonage, 2),
        "trip_count": trip_count,
        "avg_ritasi_per_day": round(avg_ritasi_per_day, 1),
        "avg_payload": round(avg_payload, 2),
        "avg_loading_time": round(avg_loading_time, 1),
        "products": dict(products_breakdown)
    }
    _HAULING_RESULT_CACHE[result_key] = (time.time(), result)
    return result
