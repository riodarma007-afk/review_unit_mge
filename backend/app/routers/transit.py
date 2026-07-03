from fastapi import APIRouter, Query
from typing import Optional
import httpx
import time
import asyncio
from collections import defaultdict
from app.core.config import settings

router = APIRouter()

_TRANSIT_CACHE = {}
_TRANSIT_RESULT_CACHE = {}
CACHE_TTL = 300  # 5 minutes


async def _fetch_transit_pages(params: dict) -> list:
    """Fetch all pages of transit data from external API (with caching).
    Uses limit=500 (API max) and concurrent fetching for speed.
    """
    cache_key = str(sorted(params.items()))
    if cache_key in _TRANSIT_CACHE:
        cached_time, cached_data = _TRANSIT_CACHE[cache_key]
        if time.time() - cached_time < CACHE_TTL:
            return cached_data

    headers = {"X-API-Key": settings.FUEL_API_KEY}
    PAGE_LIMIT = 500
    transit_url = settings.FUEL_API_URL.replace("/fuel", "/coal/transit")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # First request to get totalPages
        try:
            resp = await client.get(
                transit_url,
                headers=headers,
                params={**params, "page": 1, "limit": PAGE_LIMIT}
            )
            resp.raise_for_status()
            body = resp.json()
            all_rows = body.get("data", [])
            total_pages = body.get("meta", {}).get("totalPages", 1)
        except Exception as e:
            print(f"Failed to fetch transit data page 1: {e}")
            return []

        # Fetch remaining pages concurrently
        if total_pages > 1:
            async def fetch_page(p):
                try:
                    r = await client.get(
                        transit_url,
                        headers=headers,
                        params={**params, "page": p, "limit": PAGE_LIMIT}
                    )
                    r.raise_for_status()
                    return r.json().get("data", [])
                except Exception as e:
                    print(f"Failed to fetch transit data page {p}: {e}")
                    return []

            results = await asyncio.gather(
                *[fetch_page(p) for p in range(2, total_pages + 1)]
            )
            for page_data in results:
                all_rows.extend(page_data)

    _TRANSIT_CACHE[cache_key] = (time.time(), all_rows)
    return all_rows


@router.get("/unit")
async def get_transit_by_unit(
    unit_code: str = Query(..., description="OpTrack unit code, e.g. 'GHT 748'"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """Get coal transit (ritasi) summary for a specific unit."""
    # Check result cache
    result_key = f"{unit_code}|{date_from}|{date_to}"
    if result_key in _TRANSIT_RESULT_CACHE:
        cached_time, cached_result = _TRANSIT_RESULT_CACHE[result_key]
        if time.time() - cached_time < CACHE_TTL:
            return cached_result

    params = {"search": unit_code}
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to

    rows = await _fetch_transit_pages(params)

    # Filter strict by unit_code (ignoring spaces and case)
    search_unit = unit_code.replace(" ", "").replace("-", "").upper()
    filtered = [
        r for r in rows 
        if str(r.get("unit_code", "")).replace(" ", "").replace("-", "").upper() == search_unit
    ]

    total_ritasi = 0
    total_netto = 0.0
    unique_dates = set()
    products = defaultdict(lambda: {"ritasi": 0, "netto": 0.0})
    pits = defaultdict(int)
    hourly = defaultdict(int)  # h1..h12

    for r in filtered:
        rit = r.get("total", 0) or 0
        total_ritasi += rit

        netto_val = 0.0
        try:
            netto_val = float(r.get("netto", 0) or 0)
            total_netto += netto_val
        except (ValueError, TypeError):
            pass

        dt = r.get("date")
        if dt:
            unique_dates.add(dt.split("T")[0])

        prod = r.get("product_code")
        if prod:
            products[prod]["ritasi"] += rit
            products[prod]["netto"] += netto_val

        pit = r.get("pit")
        if pit:
            pits[pit] += rit

        # Accumulate hourly distribution
        for h in range(1, 13):
            val = r.get(f"h{h}") or 0
            hourly[h] += val

    days_count = max(len(unique_dates), 1)
    avg_ritasi_per_day = total_ritasi / days_count
    avg_netto_per_rit = total_netto / total_ritasi if total_ritasi > 0 else 0

    result = {
        "unit_code": unit_code,
        "total_ritasi": total_ritasi,
        "total_netto": round(total_netto, 2),
        "avg_ritasi_per_day": round(avg_ritasi_per_day, 1),
        "avg_netto_per_rit": round(avg_netto_per_rit, 2),
        "days_count": days_count,
        "products": dict(products),
        "pits": dict(pits),
        "hourly": {f"h{k}": v for k, v in sorted(hourly.items())},
    }

    _TRANSIT_RESULT_CACHE[result_key] = (time.time(), result)
    return result
