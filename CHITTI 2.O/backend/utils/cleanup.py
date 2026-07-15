import shutil
import time
from pathlib import Path


def cleanup_old_sessions(upload_dir: str, ttl_minutes: int) -> None:
    base = Path(upload_dir)
    if not base.exists():
        return
    cutoff = time.time() - ttl_minutes * 60
    for session_dir in base.iterdir():
        if session_dir.is_dir():
            try:
                mtime = session_dir.stat().st_mtime
                if mtime < cutoff:
                    shutil.rmtree(session_dir, ignore_errors=True)
            except Exception:
                pass
