"""Central mutable state for the entire application."""
from __future__ import annotations

from typing import Optional


class PipelineState:
    """Central mutable state for the entire application."""

    def __init__(self):
        self.current_stage: int = 1
        self.current_session_id: Optional[str] = None
        self.stage_data: dict = {}
        self.view_mode: str = "full"  # "wizard" | "full"
        self.theme: str = "light"
        self.assist_open: bool = False
        self.history_open: bool = False
        self.export_dropdown_open: bool = False
        # Stage 1 wizard state
        self.s1_flat_questions: list = []
        self.s1_current_question: int = 0
        self.s1_view_mode: str = "full"
        # FRS state
        self.frs_active_doc_id: Optional[str] = None
        # Init stage data
        self._init_stage_data()

    def _init_stage_data(self):
        from .pipeline import PIPELINE
        for s in PIPELINE:
            sid = str(s["id"])
            self.stage_data[sid] = {
                "manualInputs": {}, "prdIntro": {
                    "productName": "", "tagline": "", "targetUsers": "", "problem": "", "goals": ""
                },
                "aiOutputs": {}, "qaAnswers": {}, "reviewAnswers": {}, "reviewNotes": {},
                "aiQuestions": [], "completed": False, "aiGenerated": False,
                "modelOverride": None, "inputs": {}, "functionCount": 0, "functionNames": [],
                "functionSummaries": [], "functionScoping": [], "infrastructure": {},
                "externalLinkages": {}, "externalCounts": {}, "historyLog": [],
                "d5Results": None, "d4ContextDiagram": "", "savedJsonAt": None, "frsData": None,
            }


STATE = PipelineState()