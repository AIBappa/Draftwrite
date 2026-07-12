"""Utility helper functions."""
from __future__ import annotations

from typing import Optional

from nicegui import ui
from .config import CONFIG
from .pipeline import PIPELINE
from .state import STATE


def esc_html(s) -> str:
    """Escape HTML special characters."""
    if not s:
        return ""
    return (str(s)
            .replace("&", "&")
            .replace("<", "<")
            .replace(">", ">")
            .replace('"', "&#34;"))


def show_toast(msg: str, color: str = "info"):
    """Show a toast notification."""
    ui.notify(msg, type=color, position="bottom-right", timeout=3000)


def get_sd() -> dict:
    """Get current stage data."""
    return STATE.stage_data.get(str(STATE.current_stage), {})


def get_stage() -> dict:
    """Get current stage definition."""
    return PIPELINE[STATE.current_stage - 1]


def update_progress():
    """Update progress and return (done, total)."""
    done = sum(1 for s in PIPELINE if STATE.stage_data.get(str(s["id"]), {}).get("completed"))
    total = len(PIPELINE)
    return done, total