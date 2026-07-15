from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_session_store, get_dataframe
from backend.schemas.insights import InsightsResponse
from backend.services.insight_engine import generate_insights

router = APIRouter(tags=["insights"])


@router.get("/insights/{session_id}", response_model=InsightsResponse)
def get_insights(session_id: str, sessions: dict = Depends(get_session_store)):
    df = get_dataframe(session_id, sessions)
    try:
        return generate_insights(df, session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insight generation failed: {str(e)}")
