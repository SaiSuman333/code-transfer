import pandas as pd
from fastapi import HTTPException

# In-memory session store: session_id -> DataFrame
_sessions: dict[str, pd.DataFrame] = {}


def get_session_store() -> dict[str, pd.DataFrame]:
    return _sessions


def get_dataframe(session_id: str, sessions: dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = sessions.get(session_id)
    if df is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found. Please upload a file first.")
    return df
