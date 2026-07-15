from typing import Literal
from pydantic import BaseModel


class ExplainRequest(BaseModel):
    detail_level: Literal["brief", "detailed"] = "brief"


class ExplainResponse(BaseModel):
    session_id: str
    explanation: str
    model_used: str
