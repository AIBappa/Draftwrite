"""Session persistence (save/load/delete)."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

from .config import BASE_DIR

SESSIONS_DIR = BASE_DIR / "sessions"
EXPORTS_DIR = BASE_DIR / "exports"


def list_sessions() -> list:
    sessions = []
    for f in sorted(SESSIONS_DIR.glob("*.json"), key=os.path.getmtime, reverse=True):
        if f.name == "config.json":
            continue
        try:
            data = json.loads(f.read_text("utf-8"))
            sessions.append({
                "id": data.get("id", f.stem),
                "name": data.get("name", "Untitled Session"),
                "description": data.get("description", ""),
                "createdAt": data.get("createdAt", ""),
                "updatedAt": data.get("updatedAt", ""),
                "currentStage": data.get("currentStage", 1),
                "completed": data.get("completed", 0),
                "totalStages": data.get("totalStages", 9),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return sessions


def load_session(session_id: str) -> Optional[dict]:
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_session(session_id: str, data: dict):
    path = SESSIONS_DIR / f"{session_id}.json"
    data["id"] = session_id
    data["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    path.write_text(json.dumps(data, indent=2), "utf-8")


def delete_session(session_id: str) -> bool:
    path = SESSIONS_DIR / f"{session_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False