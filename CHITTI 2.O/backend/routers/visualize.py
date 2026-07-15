import json

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from backend.dependencies import get_session_store, get_dataframe
from backend.schemas.visualize import ChartRequest
from backend.services.visualizer import build_chart

router = APIRouter(tags=["visualize"])


@router.post("/visualize/{session_id}")
def create_chart(
    session_id: str,
    req: ChartRequest,
    sessions: dict = Depends(get_session_store),
):
    df = get_dataframe(session_id, sessions)
    plotly_json = build_chart(df, req)
    # Return via JSONResponse so Pydantic never touches the plotly dict
    return JSONResponse(content={
        "session_id": session_id,
        "chart_type": req.chart_type,
        "plotly_json": plotly_json,
    })
