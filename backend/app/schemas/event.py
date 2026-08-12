from pydantic import BaseModel
from typing import List, Optional

class ParetoItem(BaseModel):
    status: str
    code: int
    hours: float
    plan_hours: float = 0.0
    percent: float
    cumulative_percent: float
    category: Optional[str] = None

class DelayParetoResponse(BaseModel):
    total_delay_hours: float
    total_idle: float = 0.0
    total_delay: float = 0.0
    total_downtime: float = 0.0
    items: List[ParetoItem]

class FilterOptionsResponse(BaseModel):
    units: List[str]
    pits: List[str]
    shifts: List[str]
    activities: List[str]
    date_range: dict
