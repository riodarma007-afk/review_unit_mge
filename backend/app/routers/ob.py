from fastapi import APIRouter, Query
from typing import Optional
import httpx
import time
import asyncio
from collections import defaultdict
from app.core.config import settings

router = APIRouter()

_OB_CACHE = {}
_OB_RESULT_CACHE = {}
CACHE_TTL = 300  # 5 minutes

async def _fetch_pages(endpoint: str, params: dict) -> list:
    cache_key = f"{endpoint}|{str(sorted(params.items()))}"
    if cache_key in _OB_CACHE:
        cached_time, cached_data = _OB_CACHE[cache_key]
        if time.time() - cached_time < CACHE_TTL:
            return cached_data

    headers = {"X-API-Key": settings.FUEL_API_KEY}
    PAGE_LIMIT = 500
    url = settings.FUEL_API_URL.replace("/fuel", endpoint)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(
                url,
                headers=headers,
                params={**params, "page": 1, "limit": PAGE_LIMIT}
            )
            resp.raise_for_status()
            body = resp.json()
            all_rows = body.get("data", [])
            total_pages = body.get("meta", {}).get("totalPages", 1)
        except Exception as e:
            print(f"Failed to fetch {endpoint} data page 1: {e}")
            return []

        if total_pages > 1:
            async def fetch_page(p):
                try:
                    r = await client.get(
                        url,
                        headers=headers,
                        params={**params, "page": p, "limit": PAGE_LIMIT}
                    )
                    r.raise_for_status()
                    return r.json().get("data", [])
                except Exception as e:
                    print(f"Failed to fetch {endpoint} data page {p}: {e}")
                    return []

            results = await asyncio.gather(
                *[fetch_page(p) for p in range(2, total_pages + 1)]
            )
            for page_data in results:
                all_rows.extend(page_data)

    _OB_CACHE[cache_key] = (time.time(), all_rows)
    return all_rows

@router.get("/unit")
async def get_ob_by_unit(
    unit_code: str = Query(..., description="OpTrack unit code, e.g. 'GMT 714'"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """Get OB summary for a specific unit (e.g. Total BCM)."""
    result_key = f"{unit_code}|{date_from}|{date_to}"
    if result_key in _OB_RESULT_CACHE:
        cached_time, cached_result = _OB_RESULT_CACHE[result_key]
        if time.time() - cached_time < CACHE_TTL:
            return cached_result
    
    params = {"search": unit_code}
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to

    # Fetch both OB and Inpit concurrently
    ob_task = _fetch_pages("/overburden/ob", params)
    inpit_task = _fetch_pages("/overburden/inpit", params)
    
    ob_rows, inpit_rows = await asyncio.gather(ob_task, inpit_task)
    
    # Filter strict by hauler
    search_unit = unit_code.replace(" ", "").replace("-", "").upper()
    ob_filtered = [r for r in ob_rows if str(r.get("hauler", "")).replace(" ", "").replace("-", "").upper() == search_unit]
    inpit_filtered = [r for r in inpit_rows if str(r.get("hauler", "")).replace(" ", "").replace("-", "").upper() == search_unit]
    
    total_volume = 0.0
    trip_count = 0
    unique_dates = set()
    
    ob_total_bcm = 0.0
    ob_trip_count = 0
    inpit_total_bcm = 0.0
    inpit_trip_count = 0
    
    # Structure for pits: { "Pit Name": { "ob_bcm": 0, "ob_trip": 0, "inpit_bcm": 0, "inpit_trip": 0 } }
    pits_data = defaultdict(lambda: {"ob_bcm": 0, "ob_trip": 0, "inpit_bcm": 0, "inpit_trip": 0})
    
    def process_rows(rows, source_type):
        nonlocal total_volume, trip_count, ob_total_bcm, ob_trip_count, inpit_total_bcm, inpit_trip_count
        for r in rows:
            vol = 0.0
            try:
                vol = float(r.get("volume", 0) or 0)
                total_volume += vol
                if source_type == "ob":
                    ob_total_bcm += vol
                else:
                    inpit_total_bcm += vol
            except (ValueError, TypeError):
                pass
                
            trip = 0
            try:
                trip = int(r.get("trip", 0) or 0)
                trip_count += trip
                if source_type == "ob":
                    ob_trip_count += trip
                else:
                    inpit_trip_count += trip
            except (ValueError, TypeError):
                pass

            dt = r.get("date")
            if dt:
                unique_dates.add(dt.split("T")[0])
                    
            pit_name = (r.get("pit") or "Unknown").strip().upper()
            if source_type == "ob":
                pits_data[pit_name]["ob_bcm"] += vol
                pits_data[pit_name]["ob_trip"] += trip
            else:
                pits_data[pit_name]["inpit_bcm"] += vol
                pits_data[pit_name]["inpit_trip"] += trip

    process_rows(ob_filtered, "ob")
    process_rows(inpit_filtered, "inpit")
            
    days_count = len(unique_dates) if len(unique_dates) > 0 else 1
    avg_ritasi_per_day = trip_count / days_count if days_count > 0 else 0
    avg_payload = total_volume / trip_count if trip_count > 0 else 0
            
    result = {
        "unit_code": unit_code,
        "total_bcm": round(total_volume, 2),
        "trip_count": trip_count,
        "ob_bcm": round(ob_total_bcm, 2),
        "ob_trip": ob_trip_count,
        "inpit_bcm": round(inpit_total_bcm, 2),
        "inpit_trip": inpit_trip_count,
        "avg_ritasi_per_day": round(avg_ritasi_per_day, 1),
        "avg_payload": round(avg_payload, 2),
        "pits": {k: {
            "ob_bcm": round(v["ob_bcm"], 2),
            "ob_trip": v["ob_trip"],
            "inpit_bcm": round(v["inpit_bcm"], 2),
            "inpit_trip": v["inpit_trip"]
        } for k, v in pits_data.items()}
    }
    _OB_RESULT_CACHE[result_key] = (time.time(), result)
    return result
