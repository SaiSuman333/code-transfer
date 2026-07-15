from fastapi import APIRouter, Depends

from backend.dependencies import get_session_store, get_dataframe
from backend.schemas.explain import ExplainRequest, ExplainResponse
from backend.services.insight_engine import generate_insights
from backend.services import llm_service

router = APIRouter(tags=["explain"])


@router.post("/explain/{session_id}", response_model=ExplainResponse)
def explain(
    session_id: str,
    req: ExplainRequest,
    sessions: dict = Depends(get_session_store),
):
    df = get_dataframe(session_id, sessions)
    insights_resp = generate_insights(df, session_id)

    if not insights_resp.insights:
        return ExplainResponse(
            session_id=session_id,
            explanation="No significant insights were found in this dataset. The data looks clean and ready for analysis.",
            model_used="template-engine",
        )

    profile_summary = (
        f"Rows: {len(df)}, Columns: {len(df.columns)}\n"
        f"Numeric columns: {list(df.select_dtypes(include='number').columns)}\n"
        f"Categorical columns: {list(df.select_dtypes(include='object').columns)}"
    )

    explanation = llm_service.explain_insights(
        insights_resp.insights, profile_summary, req.detail_level
    )
    return ExplainResponse(
        session_id=session_id,
        explanation=explanation,
        model_used="template-engine",
    )
