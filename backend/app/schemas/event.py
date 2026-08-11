from pydantic import BaseModel
from typing import List

class ParetoItem(BaseModel):
    status: str
    code: int
    hours: float
    plan_hours: float = 0.0
    percent: float
    cumulative_percent: float

class DelayParetoResponse(BaseModel):
    total_delay_hours: float
    items: List[ParetoItem]

class FilterOptionsResponse(BaseModel):
    units: List[str]
    pits: List[str]
    shifts: List[str]
    activities: List[str]
    date_range: dict
