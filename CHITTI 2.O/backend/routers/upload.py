from fastapi import APIRouter, UploadFile, File, Depends

from backend.dependencies import get_session_store
from backend.schemas.upload import UploadResponse
from backend.services.file_manager import save_upload, load_dataframe
from backend.utils.validators import validate_file_upload

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    sessions: dict = Depends(get_session_store),
):
    validate_file_upload(file)
    session_id, filename, path = await save_upload(file)
    df = load_dataframe(path)
    sessions[session_id] = df
    return UploadResponse(
        session_id=session_id,
        filename=filename,
        rows=len(df),
        columns=len(df.columns),
        column_names=list(df.columns),
        dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
        file_size_bytes=path.stat().st_size,
    )
