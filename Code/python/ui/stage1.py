"""Stage 1 PRD - Wizard mode, Full view, D4/D5 generation."""
from __future__ import annotations

import json
import re
from typing import Optional

from nicegui import ui

from ..config import BASE_DIR, CONFIG
from ..llm import call_llm, get_stage_models
from ..pipeline import PIPELINE, STAGE1_PRD_DELIVERABLES, STAGE1_INFRASTRUCTURE_SECTION, STAGE1_EXTERNAL_SECTION
from ..state import STATE
from ..utils import show_toast, get_sd
from .stages import _save_manual_input, _save_qa_answer, _save_review_note, _set_review


def render_stage1_prd():
    """Render Stage 1 PRD in wizard mode."""
    sd = STATE.stage_data.get("1", {})
    stage = PIPELINE[0]

    # Build question list
    STATE.s1_flat_questions = build_flat_question_list()
    if not STATE.s1_flat_questions:
        with ui.card().classes("w-full max-w-4xl mx-auto"):
            ui.label("No questions loaded for Stage 1.").classes("text-lg")
        return

    # Get current question
    if STATE.s1_current_question >= len(STATE.s1_flat_questions):
        STATE.s1_current_question = 0
    q = STATE.s1_flat_questions[STATE.s1_current_question]

    # View mode toggle
    with ui.row().classes("w-full max-w-4xl mx-auto justify-between items-center"):
        ui.label(f"Question {STATE.s1_current_question + 1} of {len(STATE.s1_flat_questions)}").classes("text-sm text-gray-500")
        ui.button("Full View" if STATE.s1_view_mode == "wizard" else "Wizard View", on_click=_toggle_s1_view) \
            .props("outline size=sm")

    # Question card
    with ui.card().classes("w-full max-w-4xl mx-auto min-h-[200px]"):
        val = sd.get("inputs", {}).get(q["id"], "")

        if q["type"] == "statement":
            ui.label(q["desc"]).classes("text-base font-medium text-amber-700 bg-amber-50 p-3 rounded-lg")
        elif q["type"] == "function_count":
            ui.label(f"[{q['id']}] {q['desc']}").classes("text-sm font-medium")
            if q.get("meta", {}).get("hint"):
                ui.label(q["meta"]["hint"]).classes("text-xs text-gray-400")
            inp = ui.input(value=str(val) if val else "1").props('type="number" min="1" max="10"').classes("w-full")
            inp.on_value_change(lambda v: _s1_set_func_count(v))
        elif q["type"] == "function_name":
            idx = q.get("meta", {}).get("idx", 0)
            ui.label(f"[{q['id']}] {q['desc']}").classes("text-sm font-medium")
            names = sd.get("functionNames", [])
            inp = ui.input(value=names[idx] if idx < len(names) else "").classes("w-full")
            inp.on_value_change(lambda v, i=idx: _s1_set_func_name(i, v))
        elif q["type"] == "function_summary":
            idx = q.get("meta", {}).get("idx", 0)
            ui.label(f"[{q['id']}] {q['desc']}").classes("text-sm font-medium")
            summaries = sd.get("functionSummaries", [])
            ta = ui.textarea(value=summaries[idx] if idx < len(summaries) else "").classes("w-full")
            ta.on_value_change(lambda v, i=idx: _s1_set_func_summary(i, v))
        elif q["type"] == "function_scoping":
            idx = q.get("meta", {}).get("idx", 0)
            ui.label(f"[{q['id']}] {q['desc']}").classes("text-sm font-medium")
            scoping = sd.get("functionScoping", [])
            selected = scoping[idx] if idx < len(scoping) else []
            active_opts = get_active_scoping_options()
            if not active_opts:
                ui.label("Complete Infrastructure section first").classes("text-xs text-gray-400")
            else:
                with ui.column():
                    for opt in active_opts:
                        chk = ui.checkbox(opt, value=opt in selected)
                        chk.on_value_change(lambda v, o=opt, i=idx: _s1_set_func_scoping(i, o, v))
        elif q["type"] == "yesno":
            ui.label(f"[{q['id']}] {q['desc']}").classes("text-sm font-medium")
            if q.get("meta", {}).get("hint"):
                ui.label(q["meta"]["hint"]).classes("text-xs text-gray-400")
            with ui.row():
                btn_yes = ui.button("Yes", on_click=lambda: _s1_set_yesno(q["id"], "yes", q.get("meta")))
                btn_no = ui.button("No", on_click=lambda: _s1_set_yesno(q["id"], "no", None))
                if val == "yes":
                    btn_yes.props("color=primary")
                elif val == "no":
                    btn_no.props("color=negative")
            # Follow-ups for Yes
            if val == "yes" and q.get("meta"):
                follow_ups = q["meta"].get("followUpYes") or q["meta"].get("infraFollowUps") or []
                if follow_ups:
                    with ui.column().classes("ml-4 mt-2"):
                        for fu in follow_ups:
                            ui.label(f"[{fu['id']}] {fu['desc']}").classes("text-xs font-medium")
                            fu_val = sd.get("inputs", {}).get(fu["id"], "")
                            ta = ui.textarea(value=fu_val).classes("w-full")
                            ta.on_value_change(lambda v, fid=fu["id"]: _s1_set_input(fid, v))
        elif q["type"] == "manual":
            ui.label(f"[{q['id']}] {q['desc']}").classes("text-sm font-medium")
            if q.get("meta", {}).get("hint"):
                ui.label(q["meta"]["hint"]).classes("text-xs text-gray-400")
            ta = ui.textarea(value=val).classes("w-full")
            ta.on_value_change(lambda v: _s1_set_input(q["id"], v))
        elif q["type"] == "checkboxes":
            ui.label(f"[{q['id']}] {q['desc']}").classes("text-sm font-medium")
            if q.get("meta", {}).get("hint"):
                ui.label(q["meta"]["hint"]).classes("text-xs text-gray-400")
            options = q.get("meta", {}).get("options", [])
            selected = sd.get("inputs", {}).get(q["id"], []) or []
            with ui.column():
                for opt in options:
                    chk = ui.checkbox(opt, value=opt in selected)
                    chk.on_value_change(lambda v, o=opt: _s1_set_checkbox(q["id"], o, v))

    # Navigation
    with ui.row().classes("w-full max-w-4xl mx-auto justify-between items-center pt-4"):
        if STATE.s1_current_question > 0:
            ui.button("Back", on_click=lambda: _s1_prev_question()).props("outline")
        else:
            ui.label("").classes("w-24")

        # Jump to
        with ui.row().classes("items-center gap-2"):
            jump_val = ui.input(value=str(STATE.s1_current_question + 1)).props('type="number" min="1" style="width:60px"')
            ui.button("Go", on_click=lambda: _s1_jump(jump_val.value)).props("size=sm")

        is_last = STATE.s1_current_question >= len(STATE.s1_flat_questions) - 1
        if is_last:
            ui.button("Finish → D5 Checks", on_click=_s1_finish_to_d5).props("color=primary")
        else:
            ui.button("Forward →", on_click=lambda: _s1_next_question()).props("color=primary")


def _s1_next_question():
    _s1_save_current()
    STATE.s1_current_question += 1
    _rebuild_content()


def _s1_prev_question():
    _s1_save_current()
    STATE.s1_current_question -= 1
    _rebuild_content()


def _s1_jump(target_str: str):
    try:
        target = int(target_str) - 1
        target = max(0, min(target, len(STATE.s1_flat_questions) - 1))
        STATE.s1_current_question = target
        _rebuild_content()
    except (ValueError, IndexError):
        pass


def _s1_save_current():
    pass  # Values are saved reactively via on_value_change


def _s1_finish_to_d5():
    STATE.s1_view_mode = "full"
    STATE.view_mode = "full"
    _rebuild_content()
    show_toast("Switched to Full View", "info")


def _s1_set_input(key: str, value: str):
    sd = STATE.stage_data.get("1", {})
    if "inputs" not in sd:
        sd["inputs"] = {}
    sd["inputs"][key] = value


def _s1_set_yesno(key: str, value: str, meta: dict = None):
    sd = STATE.stage_data.get("1", {})
    if "inputs" not in sd:
        sd["inputs"] = {}
    sd["inputs"][key] = value
    _rebuild_content()


def _s1_set_checkbox(key: str, opt: str, checked: bool):
    sd = STATE.stage_data.get("1", {})
    if "inputs" not in sd:
        sd["inputs"] = {}
    if key not in sd["inputs"] or not isinstance(sd["inputs"][key], list):
        sd["inputs"][key] = []
    if checked and opt not in sd["inputs"][key]:
        sd["inputs"][key].append(opt)
    elif not checked and opt in sd["inputs"][key]:
        sd["inputs"][key].remove(opt)


def _s1_set_func_count(value: str):
    sd = STATE.stage_data.get("1", {})
    try:
        count = min(max(int(value), 0), 10)
    except (ValueError, TypeError):
        count = 0
    sd["functionCount"] = count
    if "inputs" not in sd:
        sd["inputs"] = {}
    sd["inputs"]["D1.4.1"] = str(count)
    # Ensure arrays match
    while len(sd.get("functionNames", [])) < count:
        if "functionNames" not in sd:
            sd["functionNames"] = []
        sd["functionNames"].append("")
    while len(sd.get("functionSummaries", [])) < count:
        if "functionSummaries" not in sd:
            sd["functionSummaries"] = []
        sd["functionSummaries"].append("")
    while len(sd.get("functionScoping", [])) < count:
        if "functionScoping" not in sd:
            sd["functionScoping"] = []
        sd["functionScoping"].append([])
    _rebuild_content()


def _s1_set_func_name(idx: int, value: str):
    sd = STATE.stage_data.get("1", {})
    if "functionNames" not in sd:
        sd["functionNames"] = []
    while len(sd["functionNames"]) <= idx:
        sd["functionNames"].append("")
    sd["functionNames"][idx] = value


def _s1_set_func_summary(idx: int, value: str):
    sd = STATE.stage_data.get("1", {})
    if "functionSummaries" not in sd:
        sd["functionSummaries"] = []
    while len(sd["functionSummaries"]) <= idx:
        sd["functionSummaries"].append("")
    sd["functionSummaries"][idx] = value


def _s1_set_func_scoping(idx: int, opt: str, checked: bool):
    sd = STATE.stage_data.get("1", {})
    if "functionScoping" not in sd:
        sd["functionScoping"] = []
    while len(sd["functionScoping"]) <= idx:
        sd["functionScoping"].append([])
    if checked and opt not in sd["functionScoping"][idx]:
        sd["functionScoping"][idx].append(opt)
    elif not checked and opt in sd["functionScoping"][idx]:
        sd["functionScoping"][idx].remove(opt)


def _toggle_s1_view():
    if STATE.s1_view_mode == "wizard":
        STATE.s1_view_mode = "full"
        STATE.view_mode = "full"
    else:
        STATE.s1_view_mode = "wizard"
        STATE.view_mode = "wizard"
    _rebuild_content()


# ═══════════════════════════════════════════════════════════════
# STAGE 1 FULL VIEW (Accordion sections)
# ═══════════════════════════════════════════════════════════════

def render_stage1_full_view():
    sd = STATE.stage_data.get("1", {})
    if "inputs" not in sd:
        sd["inputs"] = {}

    with ui.column().classes("w-full max-w-4xl mx-auto"):
        ui.label("📝 Stage 1: PRD — Product Requirements Document").classes("text-lg font-bold")
        ui.label("✨ Complete all sections, then run D5 Auto-Checks and D4 Context Diagram.") \
            .classes("text-sm text-amber-700 bg-amber-50 p-3 rounded-lg")

    # Render all sections
    all_sections = list(STAGE1_PRD_DELIVERABLES) + [STAGE1_INFRASTRUCTURE_SECTION, STAGE1_EXTERNAL_SECTION]
    for section in all_sections:
        _render_s1_section(section, sd)

    # Functions detail (if any)
    count = sd.get("functionCount", 0)
    if count > 0:
        with ui.expansion(f"⚙️ Functions Detail ({count})", value=True).classes("w-full max-w-4xl mx-auto"):
            for i in range(count):
                names = sd.get("functionNames", [])
                summaries = sd.get("functionSummaries", [])
                scoping = sd.get("functionScoping", [])
                name = names[i] if i < len(names) else ""
                summary = summaries[i] if i < len(summaries) else ""
                scope = scoping[i] if i < len(scoping) else []
                with ui.card().classes("w-full border-l-4 border-l-indigo-400"):
                    ui.label(f"Function {i+1}: {name or '(unnamed)'}").classes("text-sm font-bold")
                    ui.input(label=f"Name of function {i+1}", value=name) \
                        .classes("w-full").on_value_change(lambda v, idx=i: _s1_set_func_name(idx, v))
                    ui.textarea(label=f"Summary of function {i+1}", value=summary) \
                        .classes("w-full").on_value_change(lambda v, idx=i: _s1_set_func_summary(idx, v))
                    active_opts = get_active_scoping_options()
                    if active_opts:
                        ui.label("Scope:").classes("text-xs font-semibold")
                        with ui.row().classes("flex-wrap gap-2"):
                            for opt in active_opts:
                                chk = ui.checkbox(opt, value=opt in scope)
                                chk.on_value_change(lambda v, o=opt, idx=i: _s1_set_func_scoping(idx, o, v))

    # External section with dynamic products
    _render_s1_external_section(sd)

    # D5 section
    _render_s1_d5_section(sd)

    # D4 section
    _render_s1_d4_section(sd)


def _render_s1_section(section: dict, sd: dict):
    sid = section["id"]
    if not section.get("items"):
        return
    # Count progress
    items = [it for it in section["items"] if it["type"] != "statement"]
    answered = 0
    total = len(items)
    for it in items:
        val = sd.get("inputs", {}).get(it["id"], "")
        if it["type"] == "yesno":
            if val in ("yes", "no"):
                answered += 1
        elif it["type"] == "checkboxes":
            if val and isinstance(val, list) and len(val) > 0:
                answered += 1
        else:
            if val and str(val).strip():
                answered += 1

    title = section.get("title", sid)
    with ui.expansion(f"{title} ({answered}/{total})", value=sid == "section_basics").classes("w-full max-w-4xl mx-auto"):
        for item in section["items"]:
            if item["type"] == "statement":
                ui.label(item["desc"]).classes("text-sm text-amber-700 bg-amber-50 p-2 rounded-lg w-full")
            elif item["type"] == "manual":
                val = sd.get("inputs", {}).get(item["id"], "")
                with ui.card().classes("w-full"):
                    ui.label(f"[{item['id']}] {item['desc']}").classes("text-sm font-medium")
                    if item.get("hint"):
                        ui.label(item["hint"]).classes("text-xs text-gray-400")
                    if item.get("isFunctionCount"):
                        inp = ui.input(value=str(val) if val else "1").props('type="number" min="1" max="10"').classes("w-full")
                        inp.on_value_change(_s1_set_func_count)
                    else:
                        ta = ui.textarea(value=val).classes("w-full")
                        ta.on_value_change(lambda v, key=item["id"]: _s1_set_input(key, v))
            elif item["type"] == "yesno":
                val = sd.get("inputs", {}).get(item["id"], "")
                with ui.card().classes("w-full"):
                    ui.label(f"[{item['id']}] {item['desc']}").classes("text-sm font-medium")
                    if item.get("hint"):
                        ui.label(item["hint"]).classes("text-xs text-gray-400")
                    with ui.row():
                        ui.button("Yes", on_click=lambda key=item["id"], fu=item.get("followUpYes") or item.get("infraFollowUps"): _s1_set_yesno(key, "yes", {"followUpYes": fu} if item.get("followUpYes") else {"infraFollowUps": fu})).props(f'color={"primary" if val == "yes" else "default"} size=sm')
                        ui.button("No", on_click=lambda key=item["id"]: _s1_set_yesno(key, "no", None)).props(f'color={"negative" if val == "no" else "default"} size=sm')
                    if val == "yes":
                        follow_ups = item.get("followUpYes") or item.get("infraFollowUps") or []
                        for fu in follow_ups:
                            fu_val = sd.get("inputs", {}).get(fu["id"], "")
                            ui.label(f"[{fu['id']}] {fu['desc']}").classes("text-xs ml-4 mt-1")
                            ta = ui.textarea(value=fu_val).classes("w-full ml-4")
                            ta.on_value_change(lambda v, fid=fu["id"]: _s1_set_input(fid, v))
            elif item["type"] == "checkboxes":
                val = sd.get("inputs", {}).get(item["id"], []) or []
                with ui.card().classes("w-full"):
                    ui.label(f"[{item['id']}] {item['desc']}").classes("text-sm font-medium")
                    options = item.get("options", [])
                    with ui.column():
                        for opt in options:
                            chk = ui.checkbox(opt, value=opt in val)
                            chk.on_value_change(lambda v, o=opt: _s1_set_checkbox(item["id"], o, v))


def _render_s1_external_section(sd: dict):
    ext_counts = sd.get("externalCounts", {})
    with ui.expansion("🔗 External Linkages", value=False).classes("w-full max-w-4xl mx-auto"):
        for item in STAGE1_EXTERNAL_SECTION["items"]:
            if item["type"] == "statement":
                ui.label(item["desc"]).classes("text-sm text-amber-700 bg-amber-50 p-2 rounded-lg w-full")
            elif item["type"] == "yesno":
                val = sd.get("inputs", {}).get(item["id"], "")
                with ui.card().classes("w-full"):
                    ui.label(f"[{item['id']}] {item['desc']}").classes("text-sm font-medium")
                    with ui.row():
                        ui.button("Yes", on_click=lambda key=item["id"]: _s1_set_yesno(key, "yes")).props(f'color={"primary" if val == "yes" else "default"} size=sm')
                        ui.button("No", on_click=lambda key=item["id"]: _s1_set_yesno(key, "no")).props(f'color={"negative" if val == "no" else "default"} size=sm')
            elif item["type"] == "checkboxes":
                val = sd.get("inputs", {}).get(item["id"], []) or []
                with ui.card().classes("w-full"):
                    ui.label(f"[{item['id']}] {item['desc']}").classes("text-sm font-medium")
                    for opt in item.get("options", []):
                        chk = ui.checkbox(opt, value=opt in val)
                        chk.on_value_change(lambda v, o=opt: _s1_set_checkbox(item["id"], o, v))

        # Dynamic external products
        for ext_type, label, count_key in [("bff", "BFF", "D3.3"), ("perm", "Database", "D3.4"), ("imm", "In-Memory", "D3.5")]:
            cnt = ext_counts.get(ext_type, 0)
            for i in range(1, cnt + 1):
                key = f"{count_key}.{ext_type}_{i}"
                val = sd.get("inputs", {}).get(key, "")
                with ui.card().classes("w-full"):
                    ui.label(f"[{key}] External product {i} ({label})").classes("text-sm font-medium")
                    inp = ui.input(value=val).classes("w-full")
                    inp.on_value_change(lambda v, k=key: _s1_set_input(k, v))
            with ui.row().classes("gap-2"):
                ui.button(f"+ Add {label} product", on_click=lambda t=ext_type: _s1_add_external(t)).props("outline size=sm")


def _s1_add_external(ext_type: str):
    sd = STATE.stage_data.get("1", {})
    if "externalCounts" not in sd:
        sd["externalCounts"] = {}
    sd["externalCounts"][ext_type] = sd["externalCounts"].get(ext_type, 0) + 1
    _rebuild_content()


def _render_s1_d5_section(sd: dict):
    has_results = bool(sd.get("d5Results"))
    with ui.expansion(f"🔍 Auto-Generated Checks (D5)" + (" ✓ Complete" if has_results else ""),
                       value=False).classes("w-full max-w-4xl mx-auto") as d5_exp:
        ui.label("The LLM will review all collected data and perform self-checks, cross-checks, and ambiguity analysis.").classes("text-sm text-gray-500")
        ui.button("Run D5 Auto-Checks" if not has_results else "Re-run D5 Checks",
                  on_click=_run_d5_checks).props("color=primary")
        if has_results:
            ui.markdown(f"```json\n{sd['d5Results']}\n```").classes("text-xs")


async def _run_d5_checks():
    sd = STATE.stage_data.get("1", {})
    stage = PIPELINE[0]
    json_data = build_stage1_json()
    context = json.dumps(json_data, indent=2)
    system = (
        "You are a senior requirements analyst performing auto-checks on a PRD.\n"
        "For each function defined, perform self-checks (compare summary vs scope) and cross-checks (find overlaps).\n"
        "Return ONLY valid JSON with 'selfChecks', 'crossChecks', and 'summary' fields."
    )
    user = f"PRD data:\n\n{context}"
    try:
        models = get_stage_models(stage)
        raw = await call_llm(system, user, models[0] if models else None)
        raw = raw.replace("```json", "").replace("```", "").strip()
        match = re.search(r"\{[\s\S]*\}", raw)
        parsed = json.loads(match.group(0)) if match else None
        if parsed:
            sd["d5Results"] = json.dumps(parsed, indent=2)
        else:
            sd["d5Results"] = raw
        show_toast("D5 checks completed ✓", "positive")
        # Auto-run D4
        await _run_d4_generation()
        _rebuild_content()
    except Exception as e:
        show_toast(f"D5 failed: {e}", "negative")


def _render_s1_d4_section(sd: dict):
    has_d4 = bool(sd.get("d4ContextDiagram"))
    with ui.expansion(f"🏗️ Context Diagram (D4)" + (" ✓ Generated" if has_d4 else ""),
                       value=False).classes("w-full max-w-4xl mx-auto"):
        ui.label("Based on reviewed inputs, the LLM generates a C4 Context Diagram.").classes("text-sm text-gray-500")
        ui.button("Generate D4 Context Diagram" if not has_d4 else "Re-generate D4",
                  on_click=_run_d4_generation).props("color=primary")
        if has_d4:
            with ui.card().classes("w-full"):
                ui.markdown(sd["d4ContextDiagram"]).classes("text-xs font-mono")


async def _run_d4_generation():
    sd = STATE.stage_data.get("1", {})
    stage = PIPELINE[0]
    json_data = build_stage1_json()
    context = json.dumps(json_data, indent=2)
    system = (
        "You are an expert software architect. Based on the PRD data provided, "
        "generate a C4 Context Diagram (textual representation) of the entire product. "
        "Describe the system, user types, external systems, infrastructure components, and their connections."
    )
    user = f"Generate C4 Context Diagram:\n\n{context}"
    try:
        models = get_stage_models(stage)
        raw = await call_llm(system, user, models[0] if models else None)
        sd["d4ContextDiagram"] = raw
        show_toast("D4 diagram generated ✓", "positive")
        _rebuild_content()
    except Exception as e:
        show_toast(f"D4 failed: {e}", "negative")


# ═══════════════════════════════════════════════════════════════
# STAGE 1 HELPERS — QUESTION FLATTENING & FLOATING
# ═══════════════════════════════════════════════════════════════

def get_active_scoping_options() -> list:
    sd = STATE.stage_data.get("1", {})
    inputs = sd.get("inputs", {})
    options = []
    if inputs.get("D1.6.1.1") == "yes": options.append("Public Webapp")
    if inputs.get("D1.6.2.1") == "yes": options.append("Private Webapp")
    if inputs.get("D1.6.3.1") == "yes": options.append("Public Android App")
    if inputs.get("D1.6.4.1") == "yes": options.append("Private Android App")
    if inputs.get("D1.6.5.1") == "yes": options.append("Public BFF")
    if inputs.get("D1.6.6.1") == "yes": options.append("Private BFF")
    if inputs.get("D1.6.7.1") == "yes": options.append("Permanent Database")
    if inputs.get("D1.6.9.1") == "yes": options.append("In-memory Database")
    if inputs.get("D3.1") == "yes": options.append("External Links")
    return options


def build_flat_question_list() -> list:
    sd = STATE.stage_data.get("1", {})
    qlist = []

    def add_item(ident, typ, desc, hint, section, src, meta=None):
        qlist.append({"id": ident, "type": typ, "desc": desc, "hint": hint, "section": section, "src": src, "meta": meta or {}})

    def add_statement(ident, desc, section, src):
        qlist.append({"id": ident, "type": "statement", "desc": desc, "section": section, "src": src})

    # Basics
    basics = None
    for s in STAGE1_PRD_DELIVERABLES:
        if s["id"] == "section_basics":
            basics = s
            break
    if basics:
        for item in basics["items"]:
            if item["type"] == "statement":
                add_statement(item["id"], item["desc"], basics["id"], "basics")
            elif item["type"] == "manual":
                add_item(item["id"], item["type"], item["desc"], item.get("hint", ""), basics["id"], "basics", item)
            elif item["type"] == "yesno":
                add_item(item["id"], item["type"], item["desc"], item.get("hint", ""), basics["id"], "basics", item)

    # Github
    gh = None
    for s in STAGE1_PRD_DELIVERABLES:
        if s["id"] == "section_github":
            gh = s
            break
    if gh:
        for item in gh["items"]:
            if item["type"] == "statement":
                add_statement(item["id"], item["desc"], gh["id"], "github")
            elif item["type"] == "yesno":
                add_item(item["id"], item["type"], item["desc"], item.get("hint", ""), gh["id"], "github", item)

    # Infrastructure
    infra = STAGE1_INFRASTRUCTURE_SECTION
    add_statement(infra["items"][0]["id"], infra["items"][0]["desc"], infra["id"], "infra")
    for item in infra["items"][1:]:
        add_item(item["id"], item["type"], item["desc"], item.get("hint", ""), infra["id"], "infra", item)

    # Function count
    funcs = None
    for s in STAGE1_PRD_DELIVERABLES:
        if s["id"] == "section_functions":
            funcs = s
            break
    if funcs:
        for item in funcs["items"]:
            if item["type"] == "statement":
                add_statement(item["id"], item["desc"], funcs["id"], "functions")
            elif item.get("isFunctionCount"):
                add_item(item["id"], "function_count", item["desc"], item.get("hint", ""), funcs["id"], "functions", item)

    # Dynamic function items
    count = sd.get("functionCount", 0)
    for i in range(count):
        add_item(f"D1.4.2.{i+1}", "function_name", f"Name of function {i+1}",
                 "Enter a short, descriptive name.", funcs["id"] if funcs else "functions", "functions", {"idx": i})
        add_item(f"D2.1.{i+1}", "function_summary", f"Function {i+1} summary",
                 "Describe what this function does.", funcs["id"] if funcs else "functions", "functions", {"idx": i})
        add_item(f"D2.2.{i+1}", "function_scoping", f"For function {i+1}, scope its impact",
                 "Tick all infrastructure components this function touches.", funcs["id"] if funcs else "functions", "functions", {"idx": i})

    # External linkages
    ext = STAGE1_EXTERNAL_SECTION
    add_statement(ext["items"][0]["id"], ext["items"][0]["desc"], ext["id"], "external")
    for item in ext["items"][1:]:
        add_item(item["id"], item["type"], item["desc"], item.get("hint", ""), ext["id"], "external", item)

    return qlist


# ═══════════════════════════════════════════════════════════════
# STAGE 1 JSON / D5 / D4 BUILDERS
# ═══════════════════════════════════════════════════════════════

def build_stage1_json() -> dict:
    sd = STATE.stage_data.get("1", {})
    inputs = sd.get("inputs", {})
    j = {
        "exportedAt": datetime.utcnow().isoformat(),
        "productName": inputs.get("D1.1", ""),
        "businessPurpose": inputs.get("D1.2.1", ""),
        "newUserWorkflow": inputs.get("D1.2.2", ""),
        "userTypes": {
            "readOnlyUser": inputs.get("D1.2.3.1") == "yes",
            "writeOnlyUser": inputs.get("D1.2.3.2") == "yes",
            "premiumUser": inputs.get("D1.2.3.3") == "yes",
            "premiumSubTypes": int(inputs.get("D1.2.3.4", "0")),
            "adminPage": inputs.get("D1.2.3.5") == "yes",
            "superAdminPage": inputs.get("D1.2.3.6") == "yes",
        },
        "github": inputs.get("D1.3") == "yes",
        "functionCount": sd.get("functionCount", 0),
        "functions": [],
        "infrastructure": {},
        "externalLinkages": {
            "hasExternal": inputs.get("D3.1") == "yes",
            "interfaces": inputs.get("D3.2") or [],
            "bffProducts": [],
            "databaseProducts": [],
            "inMemoryProducts": [],
        },
        "historyLog": sd.get("historyLog", []),
    }

    # Functions
    names = sd.get("functionNames", [])
    summaries = sd.get("functionSummaries", [])
    scoping = sd.get("functionScoping", [])
    for i, name in enumerate(names):
        j["functions"].append({
            "name": name,
            "summary": summaries[i] if i < len(summaries) else "",
            "scope": scoping[i] if i < len(scoping) else [],
        })

    # Infrastructure
    for item in STAGE1_INFRASTRUCTURE_SECTION["items"]:
        if item["type"] == "yesno":
            key = item["id"]
            j["infrastructure"][key] = {"required": inputs.get(key) == "yes", "details": {}}
            for fu in item.get("infraFollowUps", []):
                j["infrastructure"][key]["details"][fu["id"]] = inputs.get(fu["id"], "")

    # External products
    ext_counts = sd.get("externalCounts", {})
    for i in range(1, ext_counts.get("bff", 0) + 1):
        j["externalLinkages"]["bffProducts"].append(inputs.get(f"D3.3.bff_{i}", ""))
    for i in range(1, ext_counts.get("perm", 0) + 1):
        j["externalLinkages"]["databaseProducts"].append(inputs.get(f"D3.4.perm_{i}", ""))
    for i in range(1, ext_counts.get("imm", 0) + 1):
        j["externalLinkages"]["inMemoryProducts"].append(inputs.get(f"D3.5.imm_{i}", ""))

    if inputs.get("D1.2.3.1") == "yes":
        j["userTypes"]["readOnlyDescription"] = inputs.get("D1.2.3.1a", "")
    if inputs.get("D1.2.3.2") == "yes":
        j["userTypes"]["writeOnlyDescription"] = inputs.get("D1.2.3.2a", "")
    if inputs.get("D1.2.3.3") == "yes":
        j["userTypes"]["premiumFeatures"] = inputs.get("D1.2.3.3a", "")
    if sd.get("d5Results"):
        j["d5Results"] = sd["d5Results"]
    if sd.get("d4ContextDiagram"):
        j["d4ContextDiagram"] = sd["d4ContextDiagram"]

    return j


# ═══════════════════════════════════════════════════════════════
# CONTENT DISPATCHER
# ═══════════════════════════════════════════════════════════════

def _rebuild_content():
    """Clear and rebuild the main content area based on current stage."""
    from .shell import content_container
    content_container.clear()
    with content_container:
        stage = get_stage()

        # Update top bar markers
        badge = f"Stage {stage['id']}"
        badge_class = "gate" if stage.get("isGate") else ""
        title = stage.get("name", "")

        # Stage 1 PRD
        if stage.get("isStage1PRD"):
            if STATE.s1_view_mode == "full" or STATE.view_mode == "full":
                render_stage1_full_view()
            else:
                render_stage1_prd()
            return

        # Stage 2 FRS sub-pipeline
        if stage.get("hasFrsSubPipeline"):
            from .stage2 import render_frs_pipeline
            render_frs_pipeline()
            return

        # Generic stages 3-9
        render_generic_stage()