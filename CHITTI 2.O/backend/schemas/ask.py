from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str
    conversation_history: list[dict[str, str]] = []


class AskResponse(BaseModel):
    session_id: str
    answer: str
    model_used: str
