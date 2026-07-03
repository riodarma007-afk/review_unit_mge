from fastapi import APIRouter, Depends


from app.repositories.optrack_repository import OptrackRepository
from app.schemas.event import FilterOptionsResponse

router = APIRouter()

@router.get("/options", response_model=FilterOptionsResponse)
def get_filter_options():
    repo = OptrackRepository()
    options = repo.get_filter_options()
    return options
