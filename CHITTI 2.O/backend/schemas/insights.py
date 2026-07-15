from typing import Literal
from pydantic import BaseModel


class Insight(BaseModel):
    category: Literal["correlation", "outlier", "skewness", "missing_data", "distribution", "duplicate"]
    severity: Literal["info", "warning", "critical"]
    title: str
    description: str
    affected_columns: list[str]
    metric_value: float | None = None


class InsightsResponse(BaseModel):
    session_id: str
    insights: list[Insight]
    total: int
    generated_at: str
