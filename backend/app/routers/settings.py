from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.schemas.settings import TargetSettingCreate, TargetSettingUpdate, TargetSettingResponse
from app.repositories.optrack_repository import OptrackRepository

router = APIRouter()
repo = OptrackRepository()

@router.get("/targets", response_model=List[TargetSettingResponse])
def get_targets(activity: str = None, pit: str = None, year: int = None, month: int = None):
    filters = {}
    if activity: filters['activity'] = activity
    if pit: filters['pit'] = pit
    if year: filters['year'] = year
    if month: filters['month'] = month
    
    records = repo.get_target_settings(**filters)
    return records

@router.post("/targets", response_model=TargetSettingResponse)
def create_target(setting: TargetSettingCreate):
    setting_data = setting.model_dump()
    new_id = repo.create_target_setting(setting_data)
    
    # Return the newly created record
    records = repo.get_target_settings()
    for rec in records:
        if rec['id'] == new_id:
            return rec
    raise HTTPException(status_code=500, detail="Failed to retrieve created target setting")

@router.put("/targets/{setting_id}", response_model=TargetSettingResponse)
def update_target(setting_id: int, setting: TargetSettingUpdate):
    setting_data = setting.model_dump()
    repo.update_target_setting(setting_id, setting_data)
        
    records = repo.get_target_settings()
    for rec in records:
        if rec['id'] == setting_id:
            return rec
    raise HTTPException(status_code=404, detail="Target setting not found")

@router.delete("/targets/{setting_id}")
def delete_target(setting_id: int):
    deleted = repo.delete_target_setting(setting_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Target setting not found")
    return {"message": "Target setting deleted successfully"}
