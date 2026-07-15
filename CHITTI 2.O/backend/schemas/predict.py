from typing import Literal
from pydantic import BaseModel


class PredictRequest(BaseModel):
    target_column: str
    feature_columns: list[str] | None = None
    task_type: Literal["auto", "regression", "classification"] = "auto"
    test_size: float = 0.2


class FeatureImportance(BaseModel):
    feature: str
    importance: float


class PredictResponse(BaseModel):
    session_id: str
    task_type: str
    model_name: str
    metrics: dict[str, float]
    feature_importances: list[FeatureImportance]
    plotly_json: dict | None = None
    explanation: str
    model_used: str
