"""Stage 2 - SRS/FRS with sub-pipeline."""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Optional

from nicegui import ui

from ..config import CONFIG
from ..llm import call_llm, get_stage_models
from ..pipeline import PIPELINE
from ..state import STATE
from ..utils import show_toast, get_sd, get_stage


def render_frs_pipeline():
    sd = get_sd()
    if "frsData" not in sd or not sd["frsData"]:
        sd["frsData"] = {
            "documents": [],
            "activeDocId": None,
            "activePhase": 1,
        }
    fd = sd["frsData"]
    if not fd.get("documents"):
        doc_id = str(uuid.uuid4())
        fd["documents"] = [{
            "id": doc_id, "name": "Untitled FRS", "rawInput": "",
            "version": {"p": "P_1.0", "r": "R_0", "a": None},
            "points": [], "status": "draft", "history": [],
        }]
        fd["activeDocId"] = doc_id
        fd["activePhase"] = 1

    doc = fd.get("activeDocId") and next((d for d in fd["documents"] if d["id"] == fd["activeDocId"]), None)
    if not doc:
        return

    # Phase stepper
    phases = [
        (1, "Input"), (2, "Cleanup"), (3, "Review"), (4, "Accept"),
    ]
    with ui.row().classes("w-full max-w-4xl mx-auto items-center gap-2 bg-gray-50 p-2 rounded-lg"):
        for i, (pn, plabel) in enumerate(phases):
            if i > 0:
                ui.label("→").classes("text-gray-300")
            is_current = pn == fd.get("activePhase", 1)
            is_completed = pn < fd.get("activePhase", 1)
            color = "green" if is_completed else "primary" if is_current else "default"
            icon = "✓" if is_completed else str(pn)
            ui.button(f"{icon} {plabel}",
                      on_click=lambda p=pn: _frs_go_to_phase(p)).props(f"size=sm {'outline' if not is_current and not is_completed else ''} color={color} flat={is_completed}")
        # Version badge
        ver_parts = [doc["version"]["p"]]
        if doc["version"]["r"] != "R_0":
            ver_parts.append(doc["version"]["r"])
        if doc["version"]["a"]:
            ver_parts.append(doc["version"]["a"])
        ui.label(" | ".join(ver_parts)).classes("text-xs font-mono text-gray-400 ml-auto")

    # Phase content
    active_phase = fd.get("activePhase", 1)
    if active_phase == 5:
        _frs_render_accepted(doc)
    elif active_phase == 1:
        _frs_render_phase1(doc)
    elif active_phase == 2:
        _frs_render_phase2(doc)
    elif active_phase == 3:
        _frs_render_phase3(doc)
    elif active_phase == 4:
        _frs_render_phase4(doc)


def _frs_go_to_phase(phase: int):
    from .shell import content_container

    sd = get_sd()
    fd = sd.get("frsData", {})
    doc = fd.get("activeDocId") and next((d for d in fd["documents"] if d["id"] == fd["activeDocId"]), None)
    if not doc:
        return
    if phase == 2 and not doc.get("rawInput", "").strip():
        show_toast("Paste raw FRS text first", "warning")
        return
    if phase == 3 and len(doc.get("points", [])) == 0:
        show_toast("Run AI cleanup first", "warning")
        return
    fd["activePhase"] = phase
    content_container.clear()
    with content_container:
        render_frs_pipeline()


def _frs_render_phase1(doc: dict):
    with ui.column().classes("w-full max-w-4xl mx-auto"):
        ui.input(label="FRS Document Name", value=doc.get("name", "Untitled FRS")).classes("w-full text-lg font-bold") \
            .on_value_change(lambda v: _frs_set_name(v))
        ui.textarea(label="Paste your raw FRS document here...",
                     value=doc.get("rawInput", ""),
                     placeholder="Paste raw FRS text with paragraphs and bullet points...") \
            .classes("w-full min-h-[300px] font-mono") \
            .props('outlined') \
            .on_value_change(lambda v: _frs_set_raw(v))
        ui.button("Run AI cleanup →", on_click=_frs_run_phase2).props("color=primary")


def _frs_set_name(value: str):
    sd = get_sd()
    fd = sd.get("frsData", {})
    doc = fd.get("activeDocId") and next((d for d in fd["documents"] if d["id"] == fd["activeDocId"]), None)
    if doc:
        doc["name"] = value or "Untitled FRS"


def _frs_set_raw(value: str):
    sd = get_sd()
    fd = sd.get("frsData", {})
    doc = fd.get("activeDocId") and next((d for d in fd["documents"] if d["id"] == fd["activeDocId"]), None)
    if doc:
        doc["rawInput"] = value


async def _frs_run_phase2():
    sd = get_sd()
    fd = sd.get("frsData", {})
    doc = fd.get("activeDocId") and next((d for d in fd["documents"] if d["id"] == fd["activeDocId"]), None)
    if not doc or not doc.get("rawInput", "").strip():
        show_toast("Paste raw FRS text first", "warning")
        return

    system = (
        "You are an FRS analyst. Parse the raw input and split it into atomic sub-requirements. "
        "Each point must represent exactly one testable behavior. Return JSON only:\n"
        '{"points": [{"id": "1.0", "text": "...", "paragraph": "..."}]}'
    )
    try:
        raw = await call_llm(system, doc["rawInput"])
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        points = parsed.get("points", [])
        if not points:
            raise ValueError("No points identified")
        doc["points"] = [
            {"id": p["id"], "text": p["text"], "paragraph": p.get("paragraph", ""),
             "prev_text": None, "change_origin": "initial", "source_impact": None,
             "review": None, "decision": None, "rejectionNote": "",
             "proposalStatus": None, "proposalNote": None, "accepted": False}
            for p in points
        ]
        doc["status"] = "cleanup"
        doc["version"]["p"] = "P_1.0"
        doc["version"]["r"] = "R_0"
        fd["activePhase"] = 2
        show_toast(f"{len(points)} points identified ✓", "positive")
        from .shell import content_container
        content_container.clear()
        with content_container:
            render_frs_pipeline()
    except Exception as e:
        show_toast(f"Cleanup failed: {e}", "negative")


def _frs_render_phase2(doc: dict):
    points = doc.get("points", [])
    with ui.column().classes("w-full max-w-4xl mx-auto"):
        ui.label(f"{len(points)} points identified").classes("text-sm font-semibold text-gray-600")
        ui.separator()
        for i, p in enumerate(points):
            with ui.card().classes("w-full"):
                with ui.row().classes("items-start gap-2"):
                    ui.label(p.get("id", "")).classes("text-xs font-mono bg-indigo-100 text-indigo-700 px-2 py-1 rounded")
                    ta = ui.textarea(value=p.get("text", "")).classes("flex-1").props("outlined dense")
                    ta.on_value_change(lambda v, idx=i: _frs_update_point_text(idx, v))
                if p.get("paragraph"):
                    with ui.expansion("Context paragraph", value=False).classes("w-full"):
                        ui.label(p["paragraph"]).classes("text-xs text-gray-500")
        with ui.row().classes("justify-between w-full pt-4"):
            ui.button("Back to input", on_click=lambda: _frs_go_to_phase(1)).props("outline")
            ui.button("Run AI review →", on_click=_frs_run_phase3).props("color=primary")


def _frs_update_point_text(idx: int, value: str):
    sd = get_sd()
    fd = sd.get("frsData", {})
    doc = fd.get("activeDocId") and next((d for d in fd["documents"] if d["id"] == fd["activeDocId"]), None)
    if doc and idx < len(doc.get("points", [])):
        doc["points"][idx]["text"] = value


async def _frs_run_phase3():
    sd = get_sd()
    fd = sd.get("frsData", {})
    doc = fd.get("activeDocId") and next((d for d in fd["documents"] if d["id"] == fd["activeDocId"]), None)
    if not doc or not doc.get("points"):
        return

    system = (
        "You are a systems engineer reviewing FRS points. Return a structured review for every point.\n"
        'Return JSON only: {"reviews": {"<id>": {"clarity_score": N, "ambiguity_flags": [], '
        '"suggested_reword": "", "testability": "high|medium|low", "cross_impact": []}}}'
    )
    payload = json.dumps({"points": [{"id": p["id"], "text": p["text"]} for p in doc["points"]]})
    try:
        raw = await call_llm(system, payload)
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        reviews = parsed.get("reviews", {})
        for p in doc["points"]:
            r = reviews.get(p["id"])
            if r:
                p["review"] = {
                    "clarity_score": r.get("clarity_score", 3),
                    "ambiguity_flags": r.get("ambiguity_flags", []),
                    "suggested_reword": r.get("suggested_reword", ""),
                    "testability": r.get("testability", "medium"),
                    "cross_impact": r.get("cross_impact", []),
                }
        doc["status"] = "reviewed"
        doc["version"]["r"] = "R_1.0"
        fd["activePhase"] = 3
        show_toast("AI review complete ✓", "positive")
        from .shell import content_container
        content_container.clear()
        with content_container:
            render_frs_pipeline()
    except Exception as e:
        show_toast(f"Review failed: {e}", "negative")


def _frs_render_phase3(doc: dict):
    points = doc.get("points", [])
    total = len(points)
    reviewed = [p for p in points if p.get("review")]
    avg_clarity = sum(p["review"]["clarity_score"] for p in reviewed) / len(reviewed) if reviewed else 0

    with ui.column().classes("w-full max-w-4xl mx-auto"):
        with ui.row().classes("gap-4 bg-gray-50 p-3 rounded-lg"):
            ui.label(f"{total} points").classes("text-sm font-semibold")
            ui.label(f"Avg clarity: {avg_clarity:.1f}/5").classes("text-sm text-gray-600")
        ui.separator()

        for p in points:
            with ui.expansion(f"[{p.get('id', '')}] {p.get('text', '')[:60]}...", value=False).classes("w-full"):
                if p.get("review"):
                    r = p["review"]
                    pct = (r.get("clarity_score", 3) / 5) * 100
                    color = "green" if pct >= 80 else "orange" if pct >= 50 else "red"
                    ui.label(f"Clarity: {r.get('clarity_score', 3)}/5").classes("text-sm")
                    ui.linear_progress(value=pct / 100, color=color).classes("w-full")
                    if r.get("ambiguity_flags"):
                        ui.label(f"Ambiguity flags: {', '.join(r['ambiguity_flags'])}").classes("text-sm text-amber-600")
                    if r.get("suggested_reword"):
                        ui.label(f"Suggested: {r['suggested_reword']}").classes("text-sm text-indigo-600")
                    ui.label(f"Testability: {r.get('testability', 'medium')}").classes("text-sm")
                else:
                    ui.label("Pending review...").classes("text-sm text-gray-400")

        with ui.row().classes("justify-between w-full pt-4"):
            ui.button("Back to cleanup", on_click=lambda: _frs_go_to_phase(2)).props("outline")
            ui.button("Go to acceptance →", on_click=lambda: _frs_go_to_phase(4)).props("color=primary")


def _frs_render_phase4(doc: dict):
    points = _frs_active_points(doc)
    incongruent = [p for p in points if p.get("proposalStatus") == "incongruent"]

    with ui.column().classes("w-full max-w-4xl mx-auto"):
        if incongruent:
            with ui.card().classes("w-full bg-red-50 border-red-200"):
                ui.label(f"⚠️ {len(incongruent)} point(s) have incongruent proposals").classes("text-sm text-red-700")

        for p in points:
            with ui.card().classes("w-full").props(f'flat bordered'):
                with ui.row().classes("items-center gap-2"):
                    ui.label(p.get("id", "")).classes("text-xs font-mono bg-indigo-100 text-indigo-700 px-2 py-1 rounded")
                    ui.label(p.get("text", "")).classes("text-sm flex-1")
                    if p.get("accepted"):
                        ui.label("Accepted").classes("text-xs bg-green-100 text-green-700 px-2 py-1 rounded")
                    elif p.get("decision") == "N":
                        ui.label("Rejected").classes("text-xs bg-red-100 text-red-700 px-2 py-1 rounded")

                if p.get("prev_text"):
                    with ui.card().classes("w-full bg-gray-50"):
                        ui.label(f"Changed from: {p.get('prev_text', '')}").classes("text-xs text-gray-400 line-through")

                # Decision buttons
                if not p.get("accepted"):
                    with ui.row().classes("gap-2"):
                        ui.button("Accept", on_click=lambda pid=p["id"]: _frs_set_decision(pid, "Y")).props(
                            f'size=sm color={"green" if p.get("decision") == "Y" else "default"}')
                        ui.button("Reject", on_click=lambda pid=p["id"]: _frs_set_decision(pid, "N")).props(
                            f'size=sm color={"red" if p.get("decision") == "N" else "default"}')

                if p.get("decision") == "N" or p.get("proposalStatus") == "incongruent":
                    ta = ui.textarea(value=p.get("rejectionNote", ""), placeholder="Reason + new proposal...").classes("w-full")
                    ta.on_value_change(lambda v, pid=p["id"]: _frs_set_rejection(pid, v))

        with ui.row().classes("justify-between w-full pt-4"):
            decided = len([p for p in points if p.get("decision")])
            blocked_reasons = []
            undecided = [p for p in points if not p.get("decision") and not p.get("accepted")]
            if undecided:
                blocked_reasons.append(f"{len(undecided)} undecided")
            rejected_no_note = [p for p in points if p.get("decision") == "N" and not p.get("rejectionNote", "").strip()]
            if rejected_no_note:
                blocked_reasons.append(f"{len(rejected_no_note)} rejections need reason")
            if incongruent:
                blocked_reasons.append(f"{len(incongruent)} incongruent")

            ui.label(f"{decided}/{len(points)} decided").classes("text-sm")
            blocked = ", ".join(blocked_reasons)
            if blocked:
                ui.label(blocked).classes("text-xs text-red-500")
            else:
                ui.button("Submit all decisions", on_click=_frs_handle_submit).props("color=primary").bind_enabled_from(
                    ui.checkbox("All reviewed", value=False), 'value')


def _frs_active_points(doc: dict) -> list:
    points = doc.get("points", [])
    seen = {}
    for p in points:
        base = int(float(p.get("id", "0")))
        if base not in seen or _frs_cmp_versions(p["id"], seen[base]["id"]) > 0:
            seen[base] = p
    return sorted(seen.values(), key=lambda x: float(x.get("id", "0")))


def _frs_cmp_versions(a: str, b: str) -> int:
    pa = a.split(".")
    pb = b.split(".")
    ma, sa = int(pa[0]), int(pa[1]) if len(pa) > 1 else 0
    mb, sb = int(pb[0]), int(pb[1]) if len(pb) > 1 else 0
    if ma != mb:
        return ma - mb
    return sa - sb


def _frs_set_decision(point_id: str, decision: str):
    from .shell import content_container

    sd = get_sd()
    fd = sd.get("frsData", {})
    doc = fd.get("activeDocId") and next((d for d in fd["documents"] if d["id"] == fd["activeDocId"]), None)
    if doc:
        for p in doc.get("points", []):
            if p["id"] == point_id:
                p["decision"] = decision
                if decision == "Y":
                    p["rejectionNote"] = ""
                    p["proposalStatus"] = None
                break
    content_container.clear()
    with content_container:
        render_frs_pipeline()


def _frs_set_rejection(point_id: str, value: str):
    sd = get_sd()
    fd = sd.get("frsData", {})
    doc = fd.get("activeDocId") and next((d for d in fd["documents"] if d["id"] == fd["activeDocId"]), None)
    if doc:
        for p in doc.get("points", []):
            if p["id"] == point_id:
                p["rejectionNote"] = value
                break


async def _frs_handle_submit():
    from .shell import content_container

    sd = get_sd()
    fd = sd.get("frsData", {})
    doc = fd.get("activeDocId") and next((d for d in fd["documents"] if d["id"] == fd["activeDocId"]), None)
    if not doc:
        return

    active = _frs_active_points(doc)
    rejected = [p for p in active if p.get("decision") == "N"]

    if not rejected and all(p.get("accepted") for p in active):
        doc["status"] = "accepted"
        fd["activePhase"] = 5
        show_toast("FRS accepted! ✓", "positive")
        content_container.clear()
        with content_container:
            render_frs_pipeline()
        return

    if not rejected:
        show_toast("No rejections to process", "warning")
        return

    # Create new sub-versions for rejected points
    new_points = []
    for old in rejected:
        nid = _frs_next_sub_v(old["id"], doc.get("points", []))
        new_points.append({
            "id": nid, "text": old.get("rejectionNote", old["text"]),
            "paragraph": old.get("paragraph", ""),
            "prev_text": old["text"], "change_origin": "manual",
            "source_impact": None, "review": None, "decision": None,
            "rejectionNote": "", "proposalStatus": None, "proposalNote": None,
            "accepted": False,
        })

    # AI re-review
    all_points = doc.get("points", []) + new_points
    system = (
        "You are a systems engineer reviewing an FRS update round. "
        "For each updated point, check legibility (legible or incongruent). "
        "Return JSON only:\n"
        '{"updated": {"<id>": {"review": {...}, "legibility": {"status": "legible|incongruent", "note": "..."}}}}'
    )
    payload = json.dumps({
        "updated_ids": [p["id"] for p in new_points],
        "all_points": [{"id": p["id"], "text": p["text"], "prev_text": p.get("prev_text"),
                        "change_origin": p.get("change_origin"), "accepted": p.get("accepted")}
                       for p in all_points]
    })

    try:
        raw = await call_llm(system, payload)
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)

        for np in new_points:
            upd = parsed.get("updated", {}).get(np["id"])
            if upd:
                np["review"] = upd.get("review")
                if upd.get("legibility", {}).get("status") == "incongruent":
                    np["proposalStatus"] = "incongruent"
                    np["proposalNote"] = upd["legibility"].get("note", "")
                    np["decision"] = "N"

        for np in new_points:
            doc["points"].append(np)

        cur_r = int(doc["version"]["r"].split("_")[1].split(".")[0]) if "r" in doc["version"] and "_" in doc["version"]["r"] else 0
        doc["version"]["r"] = f"R_{cur_r + 1}.0"
        if "history" not in doc:
            doc["history"] = []
        doc["history"].append({
            "round": len(doc["history"]) + 1,
            "timestamp": datetime.utcnow().isoformat(),
            "r_version": doc["version"]["r"],
            "changes": [f"Point {p['id']} rejected and revised" for p in rejected],
        })
        doc["status"] = "in-acceptance"

        new_active = _frs_active_points(doc)
        if all(p.get("accepted") for p in new_active):
            doc["status"] = "accepted"
            doc["version"]["a"] = f"A_{len(doc['history']) + 1}.0"
            fd["activePhase"] = 5
        show_toast(f"Round {len(doc['history'])} complete", "positive")
        content_container.clear()
        with content_container:
            render_frs_pipeline()
    except Exception as e:
        show_toast(f"Submit failed: {e}", "negative")


def _frs_next_sub_v(base_id: str, points: list) -> str:
    base = int(float(base_id))
    existing = [p for p in points if int(float(p.get("id", "0"))) == base]
    max_sub = 0
    for p in existing:
        parts = p.get("id", "").split(".")
        if len(parts) > 1:
            try:
                max_sub = max(max_sub, int(parts[1]))
            except ValueError:
                pass
    return f"{base}.{max_sub + 1}"


def _frs_render_accepted(doc: dict):
    with ui.column().classes("w-full max-w-4xl mx-auto"):
        with ui.card().classes("w-full bg-green-50 border-green-200"):
            ui.label(f"✓ FRS accepted — version {doc.get('version', {}).get('a', '—')}").classes("text-lg font-bold text-green-700")
            ui.label(f"All points accepted after {len(doc.get('history', []))} review round(s).").classes("text-sm text-green-600")

        if doc.get("history"):
            with ui.card().classes("w-full"):
                ui.label("Round History").classes("text-sm font-semibold")
                for r in doc["history"]:
                    with ui.row().classes("gap-2 text-xs"):
                        ui.label(f"Round {r.get('round', '?')}").classes("font-mono")
                        ui.label(r.get("r_version", "")).classes("font-mono text-gray-500")
                        ui.label(f"({r.get('changes', [])[:1]})").classes("text-gray-400")