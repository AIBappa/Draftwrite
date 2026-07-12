"""Stage 8 - Local Task-by-Task Code Generation."""
from __future__ import annotations

from nicegui import ui

from ..utils import get_sd, get_stage


def render():
    """Render Stage 8 - Local Task-by-Task Code Generation."""
    # Uses generic renderer
    from .stages import render_generic_stage
    render_generic_stage()