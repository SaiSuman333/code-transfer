from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_session_store, get_dataframe
from backend.schemas.profile import ProfileResponse
from backend.services.profiler import profile_dataframe

router = APIRouter(tags=["profile"])


@router.get("/profile/{session_id}", response_model=ProfileResponse)
def get_profile(session_id: str, sessions: dict = Depends(get_session_store)):
    df = get_dataframe(session_id, sessions)
    try:
        return profile_dataframe(df, session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profiling failed: {str(e)}")
