from typing import Any
from pydantic import BaseModel


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    non_null_count: int
    null_count: int
    null_percentage: float
    unique_count: int
    mean: float | None = None
    median: float | None = None
    std: float | None = None
    min: float | None = None
    max: float | None = None
    q25: float | None = None
    q75: float | None = None
    skewness: float | None = None
    kurtosis: float | None = None
    top_values: list[dict[str, Any]] | None = None


class ProfileResponse(BaseModel):
    session_id: str
    rows: int
    total_columns: int
    memory_usage_mb: float
    duplicate_rows: int
    numeric_columns: list[str]
    categorical_columns: list[str]
    datetime_columns: list[str]
    columns: list[ColumnProfile]
