"""UI shell - sidebar, dialogs, setup tabs."""
from __future__ import annotations

from nicegui import ui, app

from ..config import BASE_DIR, CONFIG
from ..pipeline import PIPELINE
from ..state import STATE
from ..utils import show_toast, update_progress, get_stage
from ..exporters import export_pipeline_json
from .stage1 import render_stage1_prd, render_stage1_full_view
from .stage2 import render_frs_pipeline
from .stages import render_generic_stage
from .components import (
    _test_ollama, _test_anthropic, _test_openai, _test_gemini,
    _test_azure, _test_groq, _test_cerebras, _test_openrouter,
    _test_nvidia, _test_siliconflow,
)


content_container = None


def build_ui():
    """Build the complete UI shell."""
    global content_container

    # ── Dark mode support ──
    app.add_static_files("/static", BASE_DIR / "static" if (BASE_DIR / "static").exists() else BASE_DIR)

    # ── Sidebar ──
    with ui.left_drawer(value=True, bordered=True).classes("w-[280px] bg-indigo-950 text-white") as drawer:
        drawer.props("width=280")
        with ui.column().classes("w-full h-full"):
            # Header
            with ui.column().classes("p-4 border-b border-indigo-800"):
                ui.label("Pipeline Author").classes("text-xs font-bold uppercase tracking-wider text-indigo-200")
                ui.label("LLM-Assisted Software Dev").classes("text-xs text-indigo-400")

            # Stage list
            with ui.scroll_area().classes("flex-1 w-full"):
                for s in PIPELINE:
                    sid = str(s["id"])
                    sd = STATE.stage_data.get(sid, {})
                    is_active = s["id"] == STATE.current_stage
                    is_completed = sd.get("completed", False)
                    is_gate = s.get("isGate", False)
                    classes = "p-2 px-4 cursor-pointer hover:bg-indigo-800 transition flex items-center gap-2"
                    if is_active:
                        classes += " bg-indigo-700 border-l-4 border-l-indigo-300"
                    if is_completed:
                        classes += " opacity-80"
                    with ui.row().classes(classes).on("click", lambda sid=sid: _go_to_stage(int(sid))):
                        num = "⛔" if is_gate else str(s["id"])
                        ui.label(num).classes(
                            "w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold "
                            + ("bg-green-500" if is_completed else "bg-indigo-600 text-indigo-200")
                        ).style("line-height: 1.5rem; text-align: center;")
                        with ui.column().classes("flex-1 min-w-0 gap-0"):
                            ui.label(s["name"]).classes("text-xs font-medium truncate text-indigo-100")
                            ui.label(f"{s['type']}" + (" GATE" if is_gate else "")).classes("text-[10px] text-indigo-400")
                        ui.label("").classes("w-2 h-2 rounded-full " +
                            ("bg-green-400" if is_completed else "bg-transparent border border-indigo-400"))

            # Footer
            with ui.column().classes("p-3 border-t border-indigo-800 gap-2"):
                done, total = update_progress()
                ui.label(f"Progress: {done} of {total} stages done").classes("text-xs text-indigo-300")
                ui.linear_progress(value=done / total if total > 0 else 0, color="indigo").classes("w-full")
                ui.button("📁 Sessions", on_click=_show_sessions).props("flat dense size=sm").classes("text-indigo-300 w-full")
                ui.button("⚙️ Connection Setup", on_click=_show_setup).props("flat dense size=sm").classes("text-indigo-300 w-full")
                ui.button("💾 Save to Server", on_click=export_pipeline_json).props("flat dense size=sm").classes("text-indigo-300 w-full")

    # ── Main content area ──
    with ui.column().classes("w-full h-full p-0"):
        # Top bar
        with ui.row().classes("w-full items-center gap-4 p-3 bg-white border-b border-gray-200"):
            stage = get_stage()
            badge = f"Stage {stage['id']}"
            with ui.row().classes("items-center gap-1"):
                ui.label(badge).classes("text-xs font-semibold px-3 py-1 rounded-full bg-indigo-100 text-indigo-700") \
                    if not stage.get("isGate") else \
                    ui.label("⛔ Gate").classes("text-xs font-semibold px-3 py-1 rounded-full bg-red-100 text-red-700")
            ui.label(stage.get("name", "")).classes("text-sm font-semibold flex-1")
            ui.label(CONFIG.get_active_model()).classes("text-xs font-mono bg-indigo-50 text-indigo-600 px-2 py-1 rounded-full")
            ui.button("📜 History", on_click=lambda: setattr(STATE, 'history_open', not STATE.history_open)).props("flat dense size=sm")

        # Progress bar
        done, total = update_progress()
        ui.linear_progress(value=done / total if total > 0 else 0, color="indigo").classes("w-full h-1")

        # Scrollable content area
        with ui.scroll_area().classes("flex-1 w-full p-6"):
            content_container = ui.column().classes("w-full")
            with content_container:
                _rebuild_content()

    # ── Setup dialog ──
    with ui.dialog().props("maximized") as setup_dialog:
        STATE._setup_dialog = setup_dialog
        with ui.card().classes("w-full max-w-3xl mx-auto"):
            with ui.column().classes("p-4 gap-4"):
                ui.label("Connection Setup").classes("text-lg font-bold")
                # Provider tabs
                providers = [
                    ("local", "🖥️ Local (Ollama)"), ("cloud", "☁️ Anthropic"),
                    ("openai", "🤖 OpenAI"), ("gemini", "✧ Gemini"),
                    ("azure", "🧱 Azure"), ("groq", "🟥 Groq"),
                    ("cerebras", "🟧 Cerebras"), ("openrouter", "🟡 OpenRouter"),
                    ("nvidia", "🟢 NVIDIA NIM"), ("siliconflow", "🧱 SiliconFlow"),
                ]
                with ui.tabs().classes("w-full") as tabs:
                    for pkey, plabel in providers:
                        ui.tab(pkey, label=plabel)
                with ui.tab_panels(tabs, value="local").classes("w-full"):
                    for pkey, _ in providers:
                        with ui.tab_panel(pkey):
                            _render_setup_tab(pkey, ui.column())
                with ui.row().classes("w-full justify-end gap-2 pt-4"):
                    ui.button("Cancel", on_click=lambda: setup_dialog.close()).props("flat")
                    ui.button("Save & Close", on_click=lambda: _save_setup(setup_dialog)).props("color=primary")

    # ── Sessions dialog ──
    with ui.dialog().props("maximized") as session_dialog:
        STATE._session_dialog = session_dialog
        with ui.card().classes("w-full max-w-3xl mx-auto"):
            with ui.column().classes("p-4 gap-4"):
                ui.label("Pipeline Sessions").classes("text-lg font-bold")
                _render_sessions_list(session_dialog)

    # ── History panel (slide-in) ──
    STATE.history_panel = ui.card().classes("hidden")


def _render_setup_tab(provider: str, panel):
    """Render a provider setup tab inside the dialog."""
    with panel:
        if provider == "local":
            with ui.card().classes("w-full"):
                ui.label("Step 1: Serve this page").classes("text-xs font-semibold")
                ui.label("Browsers block localhost calls from file:// pages. Use the server instead.").classes("text-xs text-gray-500")
            with ui.card().classes("w-full"):
                ui.label("Step 2: Start Ollama with CORS").classes("text-xs font-semibold")
                ui.code('OLLAMA_ORIGINS="*" ollama serve').classes("text-xs")
            with ui.card().classes("w-full"):
                ui.input(label="Ollama API base URL", value=CONFIG.ollama_url).classes("w-full") \
                    .on_value_change(lambda v: setattr(CONFIG, "ollama_url", v))
                ui.input(label="Default Ollama model", value=CONFIG.ollama_model,
                         placeholder="e.g. gemma3:4b").classes("w-full") \
                    .on_value_change(lambda v: setattr(CONFIG, "ollama_model", v))
                ui.button("Test Ollama connection", on_click=_test_ollama).props("outline size=sm")
        elif provider == "cloud":
            ui.input(label="Anthropic API Key", value=CONFIG.api_key, password=True, placeholder="sk-ant-api03-...") \
                .classes("w-full").on_value_change(lambda v: setattr(CONFIG, "api_key", v))
            ui.input(label="Model", value=CONFIG.cloud_model, placeholder="claude-sonnet-4-6").classes("w-full") \
                .on_value_change(lambda v: setattr(CONFIG, "cloud_model", v))
            ui.button("Test API Key", on_click=_test_anthropic).props("outline size=sm")
        elif provider == "openai":
            ui.input(label="OpenAI API Key", value=CONFIG.openai_key, password=True, placeholder="sk-...") \
                .classes("w-full").on_value_change(lambda v: setattr(CONFIG, "openai_key", v))
            ui.input(label="Model", value=CONFIG.openai_model, placeholder="gpt-4o").classes("w-full") \
                .on_value_change(lambda v: setattr(CONFIG, "openai_model", v))
            ui.button("Test API Key", on_click=_test_openai).props("outline size=sm")
        elif provider == "gemini":
            ui.input(label="Gemini API Key", value=CONFIG.gemini_key, password=True, placeholder="AIza...") \
                .classes("w-full").on_value_change(lambda v: setattr(CONFIG, "gemini_key", v))
            ui.input(label="Model", value=CONFIG.gemini_model, placeholder="gemini-2.0-flash").classes("w-full") \
                .on_value_change(lambda v: setattr(CONFIG, "gemini_model", v))
            ui.button("Test API Key", on_click=_test_gemini).props("outline size=sm")
        elif provider == "azure":
            ui.input(label="API Key", value=CONFIG.azure_key, password=True).classes("w-full") \
                .on_value_change(lambda v: setattr(CONFIG, "azure_key", v))
            ui.input(label="Endpoint URL", value=CONFIG.azure_endpoint,
                     placeholder="https://your-resource.openai.azure.com").classes("w-full") \
                .on_value_change(lambda v: setattr(CONFIG, "azure_endpoint", v))
            ui.input(label="Deployment name", value=CONFIG.azure_deployment, placeholder="gpt-4o").classes("w-full") \
                .on_value_change(lambda v: setattr(CONFIG, "azure_deployment", v))
            ui.button("Test Connection", on_click=_test_azure).props("outline size=sm")
        elif provider == "groq":
            ui.input(label="Groq API Key", value=CONFIG.groq_key, password=True, placeholder="gsk_...") \
                .classes("w-full").on_value_change(lambda v: setattr(CONFIG, "groq_key", v))
            ui.input(label="Model", value=CONFIG.groq_model, placeholder="llama3-70b-8192").classes("w-full") \
                .on_value_change(lambda v: setattr(CONFIG, "groq_model", v))
            ui.button("Test API Key", on_click=_test_groq).props("outline size=sm")
        elif provider == "cerebras":
            ui.input(label="Cerebras API Key", value=CONFIG.cerebras_key, password=True, placeholder="csk_...") \
                .classes("w-full").on_value_change(lambda v: setattr(CONFIG, "cerebras_key", v))
            ui.input(label="Model", value=CONFIG.cerebras_model, placeholder="llama-3.1-8b").classes("w-full") \
                .on_value_change(lambda v: setattr(CONFIG, "cerebras_model", v))
            ui.button("Test API Key", on_click=_test_cerebras).props("outline size=sm")
        elif provider == "openrouter":
            ui.input(label="OpenRouter API Key", value=CONFIG.openrouter_key, password=True, placeholder="sk-or-v1-...") \
                .classes("w-full").on_value_change(lambda v: setattr(CONFIG, "openrouter_key", v))
            ui.input(label="Model", value=CONFIG.openrouter_model, placeholder="deepseek/deepseek-chat").classes("w-full") \
                .on_value_change(lambda v: setattr(CONFIG, "openrouter_model", v))
            ui.button("Test API Key", on_click=_test_openrouter).props("outline size=sm")
        elif provider == "nvidia":
            ui.input(label="NVIDIA NIM API Key", value=CONFIG.nvidia_key, password=True, placeholder="nvapi_...") \
                .classes("w-full").on_value_change(lambda v: setattr(CONFIG, "nvidia_key", v))
            ui.input(label="Model", value=CONFIG.nvidia_model, placeholder="minimaxai/minimax-m3").classes("w-full") \
                .on_value_change(lambda v: setattr(CONFIG, "nvidia_model", v))
            ui.button("Test API Key", on_click=_test_nvidia).props("outline size=sm")
        elif provider == "siliconflow":
            ui.input(label="SiliconFlow API Key", value=CONFIG.siliconflow_key, password=True, placeholder="sk-...") \
                .classes("w-full").on_value_change(lambda v: setattr(CONFIG, "siliconflow_key", v))
            ui.input(label="Model", value=CONFIG.siliconflow_model, placeholder="Qwen/Qwen3-32B").classes("w-full") \
                .on_value_change(lambda v: setattr(CONFIG, "siliconflow_model", v))
            ui.button("Test API Key", on_click=_test_siliconflow).props("outline size=sm")


def _save_setup(dialog):
    dialog.close()
    show_toast(f"{CONFIG.get_provider_label()} mode active", "positive")


def _show_setup():
    if hasattr(STATE, "_setup_dialog"):
        STATE._setup_dialog.open()


def _show_sessions():
    if hasattr(STATE, "_session_dialog"):
        _render_sessions_list(STATE._session_dialog)
        STATE._session_dialog.open()


def _render_sessions_list(dialog):
    """Render the list of sessions."""
    # Stub: implement session browser as needed
    with ui.column().classes("w-full"):
        ui.label("Session browser coming soon").classes("text-sm text-gray-500")


def _rebuild_content():
    """Clear and rebuild the main content area based on the current stage."""
    content_container.clear()
    with content_container:
        stage = get_stage()
        if stage.get("isStage1PRD"):
            render_stage1_full_view()
            return

        if stage.get("hasFrsSubPipeline"):
            render_frs_pipeline()
            return

        render_generic_stage()


def _go_to_stage(stage_id: int):
    """Navigate to a specific stage."""
    if stage_id < 1 or stage_id > len(PIPELINE):
        return
    # Reset Stage 1 question list to ensure fresh load
    if stage_id == 1:
        STATE.s1_flat_questions = []
    STATE.current_stage = stage_id
    _rebuild_content()
    ui.navigate.reload()
    show_toast(f"Stage {stage_id}", "info")
