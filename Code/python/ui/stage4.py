"""Stage 4 - Software Requirements Document (Architecture + Contracts)."""
from __future__ import annotations

from nicegui import ui

from ..utils import get_sd, get_stage


def render():
    """Render Stage 4 - Software Requirements Document."""
    # Uses generic renderer
    from .stages import render_generic_stage
    render_generic_stage()