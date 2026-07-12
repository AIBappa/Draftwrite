"""Stage 6 - SDD + Atomic Task Generation."""
from __future__ import annotations

from nicegui import ui

from ..utils import get_sd, get_stage


def render():
    """Render Stage 6 - SDD + Atomic Task Generation."""
    # Uses generic renderer
    from .stages import render_generic_stage
    render_generic_stage()