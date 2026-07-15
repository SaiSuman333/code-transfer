from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_session_store, get_dataframe
from backend.schemas.predict import PredictRequest, PredictResponse
from backend.services.predictor import run_prediction

router = APIRouter(tags=["predict"])


@router.post("/predict/{session_id}", response_model=PredictResponse)
def predict(
    session_id: str,
    req: PredictRequest,
    sessions: dict = Depends(get_session_store),
):
    df = get_dataframe(session_id, sessions)
    try:
        return run_prediction(
            df=df,
            session_id=session_id,
            target_column=req.target_column,
            feature_columns=req.feature_columns,
            task_type=req.task_type,
            test_size=req.test_size,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
