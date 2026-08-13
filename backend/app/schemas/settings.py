from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TargetSettingBase(BaseModel):
    activity: str = Field(..., description="Activity type e.g. Coal, OB, All")
    pit: str = Field(..., description="PIT location e.g. Jetty, North JO GAM, All")
    year: int = Field(..., description="Year of the plan")
    month: int = Field(..., ge=1, le=12, description="Month of the plan 1-12")
    pa_target: float = Field(..., ge=0, le=100, description="Planned PA percentage")
    ua_target: float = Field(..., ge=0, le=100, description="Planned UA percentage")

class TargetSettingCreate(TargetSettingBase):
    pass

class TargetSettingUpdate(TargetSettingBase):
    pass

class TargetSettingResponse(TargetSettingBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
