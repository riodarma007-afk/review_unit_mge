from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

from app.routers import kpi, units, events, filters, fuel, hauling, transit, ob

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for OPTRACK Dashboard",
    version="1.0.0"
)

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(kpi.router, prefix="/api/v1/kpi", tags=["kpi"])
app.include_router(units.router, prefix="/api/v1/units", tags=["units"])
app.include_router(events.router, prefix="/api/v1/delay", tags=["delay"])
app.include_router(filters.router, prefix="/api/v1/filters", tags=["filters"])
app.include_router(fuel.router, prefix="/api/v1/fuel", tags=["fuel"])
app.include_router(hauling.router, prefix="/api/v1/hauling", tags=["hauling"])
app.include_router(transit.router, prefix="/api/v1/transit", tags=["transit"])
app.include_router(ob.router, prefix="/api/v1/ob", tags=["ob"])

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/v1/cache/clear")
def clear_all_caches():
    """Force clear all in-memory caches so next request fetches fresh data from portal."""
    import time as _time
    
    # Clear fuel caches
    fuel._FUEL_CACHE.clear()
    fuel._FUEL_RESULT_CACHE.clear()
    
    # Clear hauling caches
    hauling._HAULING_CACHE.clear()
    hauling._HAULING_RESULT_CACHE.clear()
    
    # Clear transit caches
    transit._TRANSIT_CACHE.clear()
    transit._TRANSIT_RESULT_CACHE.clear()
    
    # Clear OB caches
    ob._OB_CACHE.clear()
    ob._OB_RESULT_CACHE.clear()
    
    return {"status": "ok", "message": "All caches cleared", "timestamp": _time.time()}
