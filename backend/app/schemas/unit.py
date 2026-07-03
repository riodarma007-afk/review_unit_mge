from pydantic import BaseModel
from typing import List, Optional

class UnitRankingItem(BaseModel):
    unit_code: str
    value: Optional[float]

class UnitRankingResponse(BaseModel):
    metric: str
    data: List[UnitRankingItem]

class UnitKpi(BaseModel):
    ma_percent: Optional[float]
    pa_percent: Optional[float]
    ua_percent: Optional[float]
    eu_percent: Optional[float]
    ritasi: int

class UnitEvent(BaseModel):
    time: str
    status: str
    start: str
    stop: str
    durasi_jam: float

class UnitDetailResponse(BaseModel):
    unit_code: str
    kpi: UnitKpi
    events: List[UnitEvent]
