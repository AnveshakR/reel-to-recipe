import logging
import os
import subprocess
import sys
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

_current_proc: subprocess.Popen | None = None


class RunRequest(BaseModel):
    url: str


@app.post("/run")
async def run_pipeline(req: RunRequest):
    """Start the recipe pipeline for a given video URL.

    Args:
        req: Request body containing the video URL.

    Returns:
        Dict with 'status', 'pid', 'url', and 'log' keys.
    """
    global _current_proc

    if not req.url.strip():
        raise HTTPException(status_code=400, detail="url is required")

    if _current_proc is not None and _current_proc.poll() is None:
        raise HTTPException(status_code=409, detail="A pipeline is already running. Try again later.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(LOGS_DIR, f"run_{timestamp}.log")

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    with open(log_path, "w") as log_file:
        _current_proc = subprocess.Popen(
            [sys.executable, os.path.join(os.path.dirname(__file__), "reel_to_recipe.py"), req.url],
            stdout=log_file,
            stderr=log_file,
            env=env,
        )

    log.info(f"Started pipeline for {req.url} — PID {_current_proc.pid}, log: {log_path}")
    return {
        "status": "started",
        "pid": _current_proc.pid,
        "url": req.url,
        "log": log_path,
    }


@app.get("/health")
async def health():
    """Return server health status.

    Returns:
        Dict with 'status' key set to 'ok'.
    """
    return {"status": "ok"}
