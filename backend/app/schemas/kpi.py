from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date

class Period(BaseModel):
    date_from: str
    date_to: str

class Targets(BaseModel):
    ma: float
    pa: float
    ua: float
    eu: float

class KpiSummaryResponse(BaseModel):
    period: Period
    ma_percent: Optional[float]
    pa_percent: Optional[float]
    ua_percent: Optional[float]
    eu_percent: Optional[float]
    total_ritasi: int
    productivity_rit_per_hour: Optional[float]
    unit_count: int
    targets: Targets
    total_mohh: Optional[float] = 0
    total_wh: Optional[float] = 0
    total_downtime: Optional[float] = 0

class TrendSeriesPoint(BaseModel):
    label: str
    ma_percent: Optional[float]
    pa_percent: Optional[float]
    ua_percent: Optional[float]
    eu_percent: Optional[float]

class KpiTrendResponse(BaseModel):
    group_by: str
    series: List[TrendSeriesPoint]
