from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_session_store, get_dataframe
from backend.schemas.ask import AskRequest, AskResponse
from backend.services import llm_service
from backend.services.profiler import profile_dataframe
from backend.config import settings

router = APIRouter(tags=["ask"])


def _build_data_context(df, session_id: str) -> str:
    profile = profile_dataframe(df, session_id)
    sample = df.head(5).to_markdown(index=False) if hasattr(df.head(5), "to_markdown") else df.head(5).to_string()

    lines = [
        f"## Dataset Context",
        f"- **Shape:** {len(df)} rows × {len(df.columns)} columns",
        f"- **Numeric columns:** {profile.numeric_columns}",
        f"- **Categorical columns:** {profile.categorical_columns}",
        "",
        "### Column Statistics (numeric):",
    ]
    for col in profile.columns:
        if col.name in profile.numeric_columns:
            lines.append(
                f"- **{col.name}**: mean={col.mean}, std={col.std}, min={col.min}, max={col.max}"
            )
    lines.append("\n### Sample rows (first 5):")
    lines.append(sample)
    return "\n".join(lines)


@router.post("/ask/{session_id}", response_model=AskResponse)
def ask(
    session_id: str,
    req: AskRequest,
    sessions: dict = Depends(get_session_store),
):
    df = get_dataframe(session_id, sessions)
    data_context = _build_data_context(df, session_id)
    answer = llm_service.answer_question(req.question, data_context, req.conversation_history)
    return AskResponse(session_id=session_id, answer=answer, model_used=settings.CORTEX_MODEL)
