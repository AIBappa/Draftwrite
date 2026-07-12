"""Export functions (JSON/CSV)."""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Dict

from .config import BASE_DIR, CONFIG
from .pipeline import PIPELINE, STAGE1_PRD_DELIVERABLES, STAGE1_INFRASTRUCTURE_SECTION, STAGE1_EXTERNAL_SECTION, SCOPING_OPTIONS
from .state import STATE
from .llm import get_stage_models

EXPORTS_DIR = BASE_DIR / "exports"


def build_export_payload() -> dict:
    export_sd = {}
    for stage in PIPELINE:
        sid = str(stage["id"])
        export_sd[sid] = STATE.stage_data.get(sid, {})
    clean_pipeline = []
    for stage in PIPELINE:
        clean = {k: v for k, v in stage.items() if not callable(v)}
        clean_pipeline.append(clean)
    return {
        "stageData": export_sd,
        "pipelineDef": clean_pipeline,
        "stage1Questions": {
            "deliverables": STAGE1_PRD_DELIVERABLES,
            "infrastructure": STAGE1_INFRASTRUCTURE_SECTION,
            "external": STAGE1_EXTERNAL_SECTION,
            "scopingOptions": SCOPING_OPTIONS,
        }
    }


async def export_pipeline_json():
    data = build_export_payload()
    data["version"] = 3
    data["sessionId"] = STATE.current_session_id or ""
    data["currentStage"] = STATE.current_stage
    data["stagesCompleted"] = sum(1 for s in PIPELINE if STATE.stage_data.get(str(s["id"]), {}).get("completed"))
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"pipeline-{timestamp}.json"
    filepath = EXPORTS_DIR / filename
    try:
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        filepath.write_text(json.dumps(data, indent=2), "utf-8")
        return str(filepath)
    except OSError as e:
        raise e


def export_csv() -> str:
    sd_all = STATE.stage_data
    lines = ["Stage ID,Stage Name,Section,Field ID,Field Label,Type,Value"]
    for stage in PIPELINE:
        sid = str(stage["id"])
        sd = sd_all.get(sid, {})
        sname = stage["name"]
        is_s1 = stage.get("isStage1PRD", False)
        if is_s1:
            inputs = sd.get("inputs", {})
            for key, val in inputs.items():
                if not val:
                    continue
                section = "Other"
                if key.startswith("D1.1") or key.startswith("D1.2"):
                    section = "Product Basics"
                elif key.startswith("D1.3"):
                    section = "Repository"
                elif key.startswith("D1.4") or key.startswith("D2"):
                    section = "Functions"
                elif key.startswith("D1.6"):
                    section = "Infrastructure"
                elif key.startswith("D3"):
                    section = "External Linkages"
                elif key.startswith("D5"):
                    section = "Auto-Checks"
                val_str = str(val).replace('"', '""')
                if isinstance(val, list):
                    val_str = "; ".join(val)
                lines.append(f'{sid},"{sname}","{section}","{key}","{key}",text,"{val_str}"')
            # Function names/summaries/scoping
            for i, name in enumerate(sd.get("functionNames", [])):
                if name:
                    lines.append(f'{sid},"{sname}",Functions,D1.4.2.{i+1},"Function {i+1} Name",text,"{name}"')
            for i, summary in enumerate(sd.get("functionSummaries", [])):
                if summary:
                    lines.append(f'{sid},"{sname}",Functions,D2.1.{i+1},"Function {i+1} Summary",text,"{summary}"')
        # Manual deliverables (stages 2-9)
        for d in stage.get("manualDeliverables", []):
            val = sd.get("manualInputs", {}).get(d["id"], "")
            if val:
                lines.append(f'{sid},"{sname}",Manual,"{d["id"]}","{d["label"]}",text,"{val}"')
        # AI deliverables
        for d in stage.get("aiDeliverables", []):
            val = sd.get("aiOutputs", {}).get(d["id"], "")
            if val:
                lines.append(f'{sid},"{sname}",AI,"{d["id"]}","{d["label"]}",text,"{val}"')
    csv_content = "\n".join(lines)
    return csv_content