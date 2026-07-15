from typing import Any
from pydantic import BaseModel


class UploadResponse(BaseModel):
    session_id: str
    filename: str
    rows: int
    columns: int
    column_names: list[str]
    dtypes: dict[str, str]
    file_size_bytes: int
