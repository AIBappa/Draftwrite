#!/usr/bin/env python3
"""
Pipeline Author — LLM-Assisted Software Development
===================================================
Unified production-grade application built with NiceGUI.
Modular architecture: stages, LLM providers, session persistence, export.

Containerized deployment via Coolify:
    python Code/python/main.py   # binds 0.0.0.0:8080
"""

from nicegui import ui

from .config import BASE_DIR, CONFIG
from .state import STATE
from .exporters import export_pipeline_json
from .ui.shell import build_ui
from .ui.stages import render_generic_stage
from .ui.components import (
    _test_ollama, _test_anthropic, _test_openai, _test_gemini,
    _test_azure, _test_groq, _test_cerebras, _test_openrouter,
    _test_nvidia, _test_siliconflow
)


def main():
    print("\U0001f680 Pipeline Author server starting...")
    print(f"\U0001f4c1 Sessions: {BASE_DIR / 'sessions'}")
    print(f"\U0001f4e6 Exports: {BASE_DIR / 'exports'}")
    print(f"\U0001f50c Ollama proxy: {CONFIG.ollama_url}")
    print(f"\U0001f4bb Binds: 0.0.0.0:8080")
    print(f"\u2757 NICEGUI_RELOAD=false (production mode)")
    print()

    build_ui()

    ui.run(
        host="0.0.0.0",
        port=8080,
        show=False,
        reload=False,
        title="Pipeline Author",
        favicon="\u2699",
    )


if __name__ == "__main__":
    main()