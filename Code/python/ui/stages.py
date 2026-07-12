"""Generic stage renderer for stages 3-9."""
from __future__ import annotations

from nicegui import ui

from ..config import CONFIG
from ..pipeline import PIPELINE
from ..state import STATE
from ..utils import show_toast, get_sd, get_stage


def render_generic_stage():
    """Render generic stages 2-9 (except stage 1 and FRS sub-pipeline)."""
    stage = get_stage()
    sd = get_sd()

    # Stage note
    if stage.get("note"):
        with ui.card().classes("w-full max-w-4xl mx-auto"):
            ui.label(f"ℹ️ Stage note: {stage['note']}").classes("text-sm text-indigo-600")

    # Config warning
    mode = CONFIG.mode
    if mode in ("cloud", "openai", "gemini", "groq", "cerebras", "openrouter", "nvidia", "siliconflow"):
        key_attr = {
            "cloud": "api_key", "openai": "openai_key", "gemini": "gemini_key",
            "groq": "groq_key", "cerebras": "cerebras_key", "openrouter": "openrouter_key",
            "nvidia": "nvidia_key", "siliconflow": "siliconflow_key",
        }
        if not getattr(CONFIG, key_attr.get(mode, ""), ""):
            with ui.card().classes("w-full max-w-4xl mx-auto bg-amber-50 border-amber-200"):
                ui.label(f"⚠️ No {mode} API key configured. Click Connection Setup in sidebar.").classes("text-amber-800 text-sm")

    # Manual deliverables
    if stage.get("manualDeliverables"):
        with ui.card().classes("w-full max-w-4xl mx-auto border-l-4 border-l-amber-400"):
            with ui.card_section():
                ui.label("✍️ Your inputs — manual authoring required").classes(
                    "text-xs font-semibold uppercase tracking-wider text-amber-700")
            for d in stage["manualDeliverables"]:
                did = d["id"]
                label = d["label"]
                placeholder = d.get("placeholder", "")
                with ui.card().classes("w-full"):
                    ui.label(label).classes("text-sm font-medium")
                    val = sd.get("manualInputs", {}).get(did, "")
                    safe_placeholder = placeholder.replace('"', '\\"').replace('\n', ' ')
                    ta = ui.textarea(value=val).props("outlined").classes("w-full").props(f'placeholder="{safe_placeholder}"')
                    ta.on_value_change(lambda v, d_id=did: _save_manual_input(d_id, v))

    # AI deliverables
    if stage.get("aiDeliverables"):
        with ui.card().classes("w-full max-w-4xl mx-auto border-l-4 border-l-emerald-400"):
            with ui.card_section():
                ai_gen = sd.get("aiGenerated", False)
                label_text = "AI-generated outputs"
                if not ai_gen:
                    label_text += " — Click Generate AI Output to populate"
                ui.label("🤖 " + label_text).classes("text-xs font-semibold uppercase tracking-wider text-emerald-700")
            for d in stage["aiDeliverables"]:
                did = d["id"]
                label = d["label"]
                with ui.card().classes("w-full"):
                    ui.label(label).classes("text-sm font-medium")
                    val = sd.get("aiOutputs", {}).get(did, "")
                    if val:
                        ui.markdown(val).classes("text-sm")
                    else:
                        ui.label("Not yet generated").classes("text-xs italic text-gray-400")

    # QA section
    if sd.get("aiGenerated") and sd.get("aiQuestions"):
        with ui.card().classes("w-full max-w-4xl mx-auto border-l-4 border-l-red-300"):
            with ui.card_section():
                ui.label("AI questions & clarifications").classes("text-xs font-semibold uppercase tracking-wider text-red-600")
            for i, q in enumerate(sd.get("aiQuestions", [])):
                with ui.card().classes("w-full"):
                    ui.label(f"Q{i+1}: {q.get('question', '')}").classes("text-sm font-medium text-indigo-700")
                    ta = ui.textarea(value=sd.get("qaAnswers", {}).get(i, "")).props("outlined").classes("w-full")
                    ta.on_value_change(lambda v, idx=i: _save_qa_answer(idx, v))

    # Gate reviews
    if stage.get("gateReviews") and sd.get("aiGenerated"):
        with ui.card().classes("w-full max-w-4xl mx-auto border-l-4 border-l-purple-400"):
            approved = sd.get("completed", False)
            label = "Gate approved — proceed to next stage" if approved else "Gate review — all items must pass"
            ui.label("⚡ " + label).classes("text-xs font-semibold uppercase tracking-wider")
            for r in stage["gateReviews"]:
                rid = r["id"]
                with ui.card().classes("w-full"):
                    ui.label(r["question"]).classes("text-sm font-medium")
                    ans = sd.get("reviewAnswers", {}).get(rid, "")
                    with ui.row():
                        for opt in ["yes", "partial", "no"]:
                            label_map = {"yes": "Yes", "partial": "Partial", "no": "No"}
                            color = "green" if opt == "yes" else "orange" if opt == "partial" else "red"
                            selected = ans == opt
                            ui.button(label_map[opt], on_click=lambda o=opt, r_id=rid: _set_review(r_id, o)) \
                                .props(f'{"outline" if not selected else ""} color="{color}" size="sm"')
                    notes = sd.get("reviewNotes", {}).get(rid, "")
                    ta = ui.textarea(value=notes).props("outlined").classes("w-full")
                    ta.on_value_change(lambda v, r_id=rid: _save_review_note(r_id, v))


def _save_manual_input(did: str, value: str):
    sd = get_sd()
    if "manualInputs" not in sd:
        sd["manualInputs"] = {}
    sd["manualInputs"][did] = value


def _save_qa_answer(idx: int, value: str):
    sd = get_sd()
    if "qaAnswers" not in sd:
        sd["qaAnswers"] = {}
    sd["qaAnswers"][idx] = value


def _save_review_note(rid: str, value: str):
    sd = get_sd()
    if "reviewNotes" not in sd:
        sd["reviewNotes"] = {}
    sd["reviewNotes"][rid] = value


def _set_review(rid: str, value: str):
    sd = get_sd()
    if "reviewAnswers" not in sd:
        sd["reviewAnswers"] = {}
    sd["reviewAnswers"][rid] = value
    # Check gate completion
    stage = get_stage()
    gate_reviews = stage.get("gateReviews", [])
    all_answered = all(sd.get("reviewAnswers", {}).get(r["id"]) for r in gate_reviews)
    all_pass = all(sd.get("reviewAnswers", {}).get(r["id"]) in ("yes", "partial") for r in gate_reviews)
    if all_answered and all_pass:
        sd["completed"] = True
        show_toast("Gate review complete — stage approved ✓", "positive")
        from ..utils import update_progress
        update_progress()