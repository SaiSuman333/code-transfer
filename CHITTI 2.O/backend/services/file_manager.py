import shutil
import uuid
from pathlib import Path

import pandas as pd
from fastapi import UploadFile, HTTPException

from backend.config import settings


async def save_upload(file: UploadFile) -> tuple[str, str, Path]:
    session_id = str(uuid.uuid4())
    upload_dir = Path(settings.UPLOAD_DIR) / session_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = file.filename or "upload"
    dest = upload_dir / filename

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {settings.MAX_FILE_SIZE_MB} MB.",
        )

    dest.write_bytes(content)
    return session_id, filename, dest


def load_dataframe(path: Path) -> pd.DataFrame:
    ext = path.suffix.lower()
    try:
        if ext == ".csv":
            return pd.read_csv(path)
        elif ext in {".xlsx", ".xls"}:
            return pd.read_excel(path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")


def remove_session(session_id: str, sessions: dict) -> None:
    sessions.pop(session_id, None)
    session_dir = Path(settings.UPLOAD_DIR) / session_id
    shutil.rmtree(session_dir, ignore_errors=True)
