#!/usr/bin/env python3
"""
Pipeline Author — LLM-Assisted Software Development
===================================================
Unified production-grade application built with NiceGUI.
Replaces the legacy loose JavaScript frontend + Python server.

All-in-one: UI, API proxies, session persistence, export (PDF/DOCX/CSV).

Containerized deployment via Coolify:
    python main.py   # binds 0.0.0.0:8080
"""

# ═══════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════

import asyncio
import json
import os
import re
import time
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from io import BytesIO
from typing import Optional

from nicegui import ui, app, events, Client

# ─── Export generators (PDF / DOCX) ───
try:
    from Code.python.exporter import generate_pdf_bytes, generate_docx_bytes
except ImportError:
    generate_pdf_bytes = None
    generate_docx_bytes = None

# ═══════════════════════════════════════════════════════════════
# FILESYSTEM LAYOUT
# ═══════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent.resolve()
SESSIONS_DIR = BASE_DIR / "sessions"
EXPORTS_DIR = BASE_DIR / "exports"
CONFIG_FILE = SESSIONS_DIR / "config.json"

SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# PIPELINE DEFINITION (ported from pipeline-config.js)
# ═══════════════════════════════════════════════════════════════

TAG_CODES = {
    "MGFP": "Manually_Generated_firstpass",
    "AGFP": "AI_Generated_firstpass",
    "AGRM": "AI_Generated_Review_Manualentry",
    "MAAP": "Manually_Accepted_AI_Proposal",
    "MEAP": "Manually_Edited_AI_Proposal",
    "MRAP": "Manually_Rejected_AI_Proposal",
}

TAG_LABELS = {
    "MGFP": "Manually entered",
    "AGFP": "AI generated",
    "AGRM": "AI reviewed",
    "MAAP": "Accepted AI proposal",
    "MEAP": "Edited AI proposal",
    "MRAP": "Rejected AI proposal",
}

TAG_COLORS = {
    "MGFP": "#6366f1",
    "AGFP": "#10b981",
    "AGRM": "#f59e0b",
    "MAAP": "#3b82f6",
    "MEAP": "#8b5cf6",
    "MRAP": "#ef4444",
}

# ─── Stage 1 PRD Deliverables ───
STAGE1_PRD_DELIVERABLES = [
    {
        "id": "section_basics",
        "title": "\U0001f4e6 Product Basics",
        "items": [
            {"id": "D1.1", "type": "manual", "desc": "Product name",
             "hint": "A new folder with this name will be created at the default location.",
             "reason_llm": "Check if name is appropriate.", "manual": True, "llm": True, "skipD5": False},
            {"id": "D1.2", "type": "statement", "desc": "Lets proceed with product description.",
             "hint": "", "reason_llm": "", "manual": False, "llm": False, "skipD5": False},
            {"id": "D1.2.1", "type": "manual", "desc": "Business Purpose of Product",
             "hint": "What is the core business reason for building this product?",
             "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
            {"id": "D1.2.2", "type": "manual", "desc": "Explain for a new user what will happen on first click?",
             "hint": "Describe the onboarding workflow.", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
            {"id": "D1.2.3", "type": "statement", "desc": "Describe the types of users.",
             "hint": "", "reason_llm": "", "manual": False, "llm": False, "skipD5": False},
            {"id": "D1.2.3.1", "type": "yesno", "desc": "Will you have a normal user who only looks at reading data?",
             "hint": "Check if read-only users are needed.", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True,
             "followUpYes": [{"id": "D1.2.3.1a", "type": "manual", "desc": "Describe what read-only users will see and do.",
                              "hint": "What pages/screens will they access?", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True}]},
            {"id": "D1.2.3.2", "type": "yesno", "desc": "Will you have a normal user who only looks at writing data?",
             "hint": "Check if write-only users are needed.", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True,
             "followUpYes": [{"id": "D1.2.3.2a", "type": "manual", "desc": "Describe what write-only users will be able to create/edit.",
                              "hint": "What data can they submit/modify?", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True}]},
            {"id": "D1.2.3.3", "type": "yesno", "desc": "Will you have a paid/premium user who accesses premium features?",
             "hint": "Check if premium tier is needed.", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True,
             "followUpYes": [{"id": "D1.2.3.3a", "type": "manual", "desc": "List the premium features they will access.",
                              "hint": "What features justify the premium tier?", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True}]},
            {"id": "D1.2.3.4", "type": "manual", "desc": "How many different sub-types of paid/premium users?",
             "hint": "Will you have paid-lite, premium-heavy? Enter a number (0 if none).",
             "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
            {"id": "D1.2.3.5", "type": "yesno", "desc": "Do you need an admin page for colleagues?",
             "hint": "Check if admin login is needed for internal team.", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
            {"id": "D1.2.3.6", "type": "yesno", "desc": "Do you need a super-admin page?",
             "hint": "Check if super-admin login is needed.", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
        ]
    },
    {
        "id": "section_github",
        "title": "\U0001f4c1 Repository Setup",
        "items": [
            {"id": "D1.3", "type": "yesno", "desc": "Do you need files stored on Github or only locally?",
             "hint": "Check if Github is needed.", "reason_llm": "Setting up Github folder only",
             "manual": True, "llm": False, "skipD5": False}
        ]
    },
    {
        "id": "section_functions",
        "title": "\u2699\ufe0f Functions",
        "items": [
            {"id": "D1.4", "type": "statement", "desc": "Lets proceed with a list of functions for your product.",
             "hint": "", "reason_llm": "", "manual": False, "llm": False, "skipD5": False},
            {"id": "D1.4.1", "type": "manual", "desc": "How many functions? Enter Integer.",
             "hint": "Enter a number between 1 and 10.", "reason_llm": "D5",
             "manual": True, "llm": True, "skipD5": True, "isFunctionCount": True, "maxCount": 10}
        ]
    }
]

STAGE1_INFRASTRUCTURE_SECTION = {
    "id": "section_infrastructure",
    "title": "\U0001f5a5\ufe0f Infrastructure",
    "items": [
        {"id": "D1.6", "type": "statement", "desc": "What type of infrastructure will your product need?",
         "hint": "", "reason_llm": "", "manual": False, "llm": False, "skipD5": False},
        {"id": "D1.6.1.1", "type": "yesno", "desc": "Webapp for normal read-only and paid/premium users?",
         "hint": "Public-facing webapp?", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True,
         "infraFollowUps": [
             {"id": "D1.6.1.2", "type": "manual", "desc": "Where will it be hosted?", "hint": "e.g. CF Pages", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
             {"id": "D1.6.1.3", "type": "manual", "desc": "What language?", "hint": "e.g. Hono TS", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
         ]},
        {"id": "D1.6.2.1", "type": "yesno", "desc": "Webapp for admin users and super-admins?",
         "hint": "Private/admin webapp?", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True,
         "infraFollowUps": [
             {"id": "D1.6.2.2", "type": "manual", "desc": "Where will it be hosted?", "hint": "e.g. CF Pages", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
             {"id": "D1.6.2.3", "type": "manual", "desc": "What language?", "hint": "e.g. Hono TS", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
         ]},
        {"id": "D1.6.3.1", "type": "yesno", "desc": "Android app for normal and paid/premium users?",
         "hint": "Public Android app?", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True,
         "infraFollowUps": [
             {"id": "D1.6.3.2", "type": "manual", "desc": "Where will it be built?", "hint": "e.g. GitHub Actions", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
             {"id": "D1.6.3.3", "type": "manual", "desc": "What language?", "hint": "e.g. Kotlin/KMM", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
         ]},
        {"id": "D1.6.4.1", "type": "yesno", "desc": "Android app for admin users and super-admins?",
         "hint": "Private/admin Android app?", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True,
         "infraFollowUps": [
             {"id": "D1.6.4.2", "type": "manual", "desc": "Where will it be built?", "hint": "e.g. GitHub Actions", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
             {"id": "D1.6.4.3", "type": "manual", "desc": "What language?", "hint": "e.g. Kotlin/KMM", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
         ]},
        {"id": "D1.6.5.1", "type": "yesno", "desc": "BFF with public URL for normal and paid/premium users?",
         "hint": "Public BFF?", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True,
         "infraFollowUps": [
             {"id": "D1.6.5.2", "type": "manual", "desc": "Where will it be hosted?", "hint": "e.g. CF Worker", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
             {"id": "D1.6.5.3", "type": "manual", "desc": "What language?", "hint": "e.g. Hono TS", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
         ]},
        {"id": "D1.6.6.1", "type": "yesno", "desc": "BFF with private URL? For login, external endpoints and admins.",
         "hint": "Private BFF?", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True,
         "infraFollowUps": [
             {"id": "D1.6.6.2", "type": "manual", "desc": "Where will it be hosted?", "hint": "e.g. CF Worker", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
             {"id": "D1.6.6.3", "type": "manual", "desc": "What language?", "hint": "e.g. Hono TS", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
         ]},
        {"id": "D1.6.7.1", "type": "yesno", "desc": "Permanent database?",
         "hint": "Persistent database required?", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True,
         "infraFollowUps": [
             {"id": "D1.6.7.2", "type": "manual", "desc": "Where will it be hosted?", "hint": "e.g. Supabase Cloud", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
             {"id": "D1.6.7.3", "type": "manual", "desc": "What database?", "hint": "e.g. Postgres", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
         ]},
        {"id": "D1.6.8.1", "type": "yesno", "desc": "Permanent Database functions?",
         "hint": "Backend functions tied to permanent DB?", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True,
         "infraFollowUps": [
             {"id": "D1.6.8.2", "type": "manual", "desc": "Where will it be hosted?", "hint": "e.g. Supabase Edge Functions", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
             {"id": "D1.6.8.3", "type": "manual", "desc": "What language?", "hint": "e.g. Hono TS", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
         ]},
        {"id": "D1.6.9.1", "type": "yesno", "desc": "In-memory / cache database?",
         "hint": "Redis/Dragonfly required?", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True,
         "infraFollowUps": [
             {"id": "D1.6.9.2", "type": "manual", "desc": "Where will it be hosted?", "hint": "e.g. Hetzner Coolify", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
             {"id": "D1.6.9.3", "type": "manual", "desc": "What database?", "hint": "e.g. Dragonfly / Redis", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
         ]},
        {"id": "D1.6.10.1", "type": "yesno", "desc": "In-memory database functions?",
         "hint": "Backend functions for in-memory DB?", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True,
         "infraFollowUps": [
             {"id": "D1.6.10.2", "type": "manual", "desc": "Where will it be hosted?", "hint": "e.g. Hetzner Coolify", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
             {"id": "D1.6.10.3", "type": "manual", "desc": "What language?", "hint": "e.g. Python/Cpp/Rust/Go", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
         ]},
    ]
}

STAGE1_EXTERNAL_SECTION = {
    "id": "section_external",
    "title": "\U0001f517 External Linkages",
    "items": [
        {"id": "D3", "type": "statement", "desc": "Lets start with External linkages for external products.",
         "hint": "", "reason_llm": "", "manual": False, "llm": False, "skipD5": False},
        {"id": "D3.1", "type": "yesno", "desc": "Will the external products interface with the product?",
         "hint": "e.g. SMS receiver, payment gateway like Razorpay.", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True},
        {"id": "D3.2", "type": "checkboxes", "desc": "Will it interface with BFF or Permanent Database Backend or In-memory database backend?",
         "hint": "Check all that apply.", "reason_llm": "D5", "manual": True, "llm": True, "skipD5": True,
         "options": ["BFF", "Permanent Database Backend", "In-memory Database Backend"]}
    ]
}

SCOPING_OPTIONS = [
    "Public Webapp", "Private Webapp", "Public Android App", "Private Android App",
    "Public BFF", "Private BFF", "Permanent Database", "In-memory Database", "External Links"
]

# ─── Pipeline Stages ───
PIPELINE = [
    {"id": 1, "name": "Product Requirements Document (PRD)", "type": "Manual+LLM",
     "models": ["deepseek-r1:7b", "gemma3:4b"], "isGate": False,
     "note": "Gemma3:4b is excellent for structuring. DeepSeek-R1 excels at reasoning over ambiguity.",
     "isStage1PRD": True, "manualDeliverables": [], "aiDeliverables": [], "reviewType": "questions"},
    {"id": 2, "name": "System Requirements Specification (SRS / FRS)", "type": "Manual+LLM",
     "models": ["qwen2.5-coder:7b", "gemma3:4b"], "isGate": False,
     "note": "State machines and flowcharts are well within Qwen2.5-Coder capability.",
     "manualDeliverables": [
         {"id": "d1", "label": "D1 \u2014 Detailed requirements: Frontend, Android, BFF, Backend", "badge": "manual",
          "placeholder": "Write structured requirements for each layer:\nFrontend: ...\nAndroid: ...\nBFF: ...\nBackend: ..."}
     ],
     "aiDeliverables": [
         {"id": "ai1", "label": "D2 \u2014 High-level state machines"},
         {"id": "ai2", "label": "D3 \u2014 Flowcharts of functions"},
         {"id": "ai3", "label": "D4 \u2014 C4 Container Diagram"},
         {"id": "ai4", "label": "D5 \u2014 System invariants document"}
     ], "reviewType": "questions", "hasFrsSubPipeline": True},
    {"id": 3, "name": "Requirements Validation Gate", "type": "Gate", "isGate": True,
     "models": ["deepseek-r1:7b", "qwen2.5-coder:7b"],
     "note": "DeepSeek-R1:7b is the right model here \u2014 strongest reasoning.",
     "manualDeliverables": [
         {"id": "d1", "label": "D1 \u2014 Contradiction review findings", "badge": "manual",
          "placeholder": "Document contradictions found between requirements..."},
         {"id": "d2", "label": "D2 \u2014 Ambiguity review findings", "badge": "manual", "placeholder": "List ambiguous requirements."},
         {"id": "d3", "label": "D3 \u2014 Missing requirements review", "badge": "manual", "placeholder": "What's missing?"},
         {"id": "d4", "label": "D4 \u2014 Concurrency & offline-risk review", "badge": "manual", "placeholder": "Race conditions, offline sync risks."}
     ],
     "aiDeliverables": [{"id": "ai1", "label": "D5 \u2014 Approved finalized requirements document"}],
     "reviewType": "gate-review",
     "gateReviews": [
         {"id": "r1", "question": "Are all functional requirements complete and unambiguous?"},
         {"id": "r2", "question": "Have all contradictions been resolved between PRD and SRS?"},
         {"id": "r3", "question": "Are concurrency and offline risks documented?"},
         {"id": "r4", "question": "Are all external system linkages accounted for?"},
         {"id": "r5", "question": "Is the requirements document ready to drive architecture decisions?"}
     ]},
    {"id": 4, "name": "Software Requirements Document (Architecture + Contracts)", "type": "LLM+Manual",
     "models": ["qwen2.5-coder:7b"], "isGate": False,
     "note": "OpenAPI YAML generation is reliable with Qwen2.5-Coder.",
     "manualDeliverables": [],
     "aiDeliverables": [
         {"id": "ai1", "label": "D1 \u2014 Data schema of functions"},
         {"id": "ai2", "label": "D2 \u2014 UML diagrams of functions"},
         {"id": "ai3", "label": "D3 \u2014 OpenAPI YAML files"},
         {"id": "ai4", "label": "D4 \u2014 PlantUML screen stencils"},
         {"id": "ai5", "label": "D5 \u2014 C4 Component Diagram"}
     ], "reviewType": "questions"},
    {"id": 5, "name": "Security & Architecture Validation Gate", "type": "Gate", "isGate": True,
     "models": ["deepseek-r1:7b"],
     "note": "R1:7b handles multi-step security reasoning well.",
     "manualDeliverables": [],
     "aiDeliverables": [
         {"id": "ai1", "label": "D1 \u2014 Security review"},
         {"id": "ai2", "label": "D2 \u2014 Offline sync / race-condition review"},
         {"id": "ai3", "label": "D3 \u2014 Architecture consistency review"},
         {"id": "ai4", "label": "D4 \u2014 Dependency validation review"}
     ],
     "reviewType": "gate-review",
     "gateReviews": [
         {"id": "r1", "question": "Are all security risks identified?"},
         {"id": "r2", "question": "Are offline sync and race conditions handled?"},
         {"id": "r3", "question": "Is the architecture internally consistent?"},
         {"id": "r4", "question": "Are all dependencies validated?"},
         {"id": "r5", "question": "Is the architecture ready to freeze?"}
     ]},
    {"id": 6, "name": "SDD + Atomic Task Generation", "type": "LLM+Manual",
     "models": ["qwen2.5-coder:7b", "qwen3:4b"], "isGate": False,
     "note": "HARDEST STAGE. Context packet schema must be defined before LLM runs.",
     "manualDeliverables": [
         {"id": "d1", "label": "D3 \u2014 Folder structure & repository layout", "badge": "manual",
          "placeholder": "Define the repository structure."}
     ],
     "aiDeliverables": [
         {"id": "ai1", "label": "D1 \u2014 Atomic task list (1:1 to implementation)"},
         {"id": "ai2", "label": "D2 \u2014 Deployment / configuration manual"},
         {"id": "ai3", "label": "D4 \u2014 Dev & curl-based verification document"},
         {"id": "ai4", "label": "D5 \u2014 Dependency graph JSON + context packets"}
     ], "reviewType": "questions"},
    {"id": 7, "name": "Task Validation Gate", "type": "Gate", "isGate": True,
     "models": ["qwen3:4b"],
     "note": "Max task size = 1 file + 1 function.",
     "manualDeliverables": [],
     "aiDeliverables": [
         {"id": "ai1", "label": "D1 \u2014 Oversized task detection"},
         {"id": "ai2", "label": "D2 \u2014 Hidden dependency review"},
         {"id": "ai3", "label": "D3 \u2014 Task ambiguity review"},
         {"id": "ai4", "label": "D4 \u2014 Context-window suitability review"}
     ],
     "reviewType": "gate-review",
     "gateReviews": [
         {"id": "r1", "question": "Are all tasks atomic (max 1 file + 1 function each)?"},
         {"id": "r2", "question": "Are hidden dependencies between tasks identified?"},
         {"id": "r3", "question": "Are all tasks unambiguous and implementation-ready?"},
         {"id": "r4", "question": "Do all context packets fit within the 6k token budget?"},
         {"id": "r5", "question": "Is the approved task graph ready for code generation?"}
     ]},
    {"id": 8, "name": "Local Task-by-Task Code Generation", "type": "LLM+Manual",
     "models": ["qwen2.5-coder:7b", "llama3:8b", "deepseek-r1:7b"], "isGate": False,
     "note": "Run one task at a time.",
     "manualDeliverables": [
         {"id": "d1", "label": "D4 \u2014 Implementation notes", "badge": "manual",
          "placeholder": "Implementation notes for this task batch..."}
     ],
     "aiDeliverables": [
         {"id": "ai1", "label": "D1 \u2014 Generated code"},
         {"id": "ai2", "label": "D2 \u2014 Unit tests"},
         {"id": "ai3", "label": "D3 \u2014 Updated DTOs / interfaces"},
         {"id": "ai4", "label": "D5 \u2014 Code review findings"}
     ], "reviewType": "questions"},
    {"id": 9, "name": "Integration & Deployment Validation", "type": "Mixed",
     "models": ["phi3:mini", "qwen3:4b"], "isGate": False,
     "note": "Phi3:mini is sufficient for diff-based contract validation.",
     "manualDeliverables": [
         {"id": "d2", "label": "D2 \u2014 Contract mismatch review", "badge": "manual", "placeholder": "Contract mismatches..."},
         {"id": "d3", "label": "D3 \u2014 Regression verification checklist", "badge": "manual", "placeholder": "Regression checks..."},
         {"id": "d4", "label": "D4 \u2014 Deployment readiness review", "badge": "manual", "placeholder": "Production readiness..."}
     ],
     "aiDeliverables": [
         {"id": "ai1", "label": "D1 \u2014 Integration validation report"},
         {"id": "ai5", "label": "D5 \u2014 Release approval document"}
     ],
     "reviewType": "gate-review",
     "gateReviews": [
         {"id": "r1", "question": "Do all endpoints match OpenAPI contracts?"},
         {"id": "r2", "question": "Have all regression tests passed?"},
         {"id": "r3", "question": "Is the deployment environment correctly configured?"},
         {"id": "r4", "question": "Are all contract mismatches resolved?"},
         {"id": "r5", "question": "Is the system ready for production release?"}
     ]}
]

# ═══════════════════════════════════════════════════════════════
# GLOBAL STATE
# ═══════════════════════════════════════════════════════════════

class PipelineState:
    """Central mutable state for the entire application."""

    def __init__(self):
        self.current_stage: int = 1
        self.current_session_id: Optional[str] = None
        self.stage_data: dict = {}
        self.view_mode: str = "wizard"  # "wizard" | "full"
        self.theme: str = "light"
        self.assist_open: bool = False
        self.history_open: bool = False
        self.export_dropdown_open: bool = False
        # Stage 1 wizard state
        self.s1_flat_questions: list = []
        self.s1_current_question: int = 0
        self.s1_view_mode: str = "wizard"
        # FRS state
        self.frs_active_doc_id: Optional[str] = None
        # Init stage data
        self._init_stage_data()

    def _init_stage_data(self):
        for s in PIPELINE:
            sid = str(s["id"])
            self.stage_data[sid] = {
                "manualInputs": {},
                "prdIntro": {"productName": "", "tagline": "", "targetUsers": "", "problem": "", "goals": ""},
                "aiOutputs": {}, "qaAnswers": {}, "reviewAnswers": {}, "reviewNotes": {},
                "aiQuestions": [], "completed": False, "aiGenerated": False,
                "modelOverride": None,
                "inputs": {},
                "functionCount": 0,
                "functionNames": [],
                "functionSummaries": [],
                "functionScoping": [],
                "infrastructure": {},
                "externalLinkages": {},
                "externalCounts": {},
                "historyLog": [],
                "d5Results": None,
                "d4ContextDiagram": "",
                "savedJsonAt": None,
                "frsData": None,
            }


# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

class AppConfig:
    """Provider configuration, persisted to disk."""

    def __init__(self):
        self.mode: str = "local"
        # Ollama
        self.ollama_url: str = "http://localhost:11434"
        self.ollama_model: str = ""
        # Anthropic
        self.api_key: str = ""
        self.cloud_model: str = "claude-sonnet-4-6"
        # OpenAI
        self.openai_key: str = ""
        self.openai_model: str = "gpt-4o"
        # Gemini
        self.gemini_key: str = ""
        self.gemini_model: str = "gemini-2.0-flash"
        # Azure
        self.azure_key: str = ""
        self.azure_endpoint: str = ""
        self.azure_deployment: str = "gpt-4o"
        self.azure_model: str = "gpt-4o"
        # Groq
        self.groq_key: str = ""
        self.groq_model: str = "llama3-70b-8192"
        # Cerebras
        self.cerebras_key: str = ""
        self.cerebras_model: str = "llama-3.1-8b"
        # OpenRouter
        self.openrouter_key: str = ""
        self.openrouter_model: str = "deepseek/deepseek-chat"
        # NVIDIA
        self.nvidia_key: str = ""
        self.nvidia_model: str = "minimaxai/minimax-m3"
        # SiliconFlow
        self.siliconflow_key: str = ""
        self.siliconflow_model: str = "Qwen/Qwen3-32B"
        # Advanced params
        self.advanced: dict = {}
        self.exports_dir: str = "exports"
        self._init_advanced()

    def _init_advanced(self):
        providers = ["local", "cloud", "openai", "gemini", "azure", "groq",
                     "cerebras", "openrouter", "nvidia", "siliconflow"]
        defaults = {"maxTokens": 2000, "temperature": 0.70, "topP": 1.00, "stream": False}
        for p in providers:
            self.advanced[p] = dict(defaults)
        self.advanced["cloud"]["topK"] = 0
        self.advanced["gemini"]["topK"] = 0
        for p in ["openai", "azure", "groq", "cerebras", "openrouter", "nvidia", "siliconflow"]:
            self.advanced[p]["reasoningEffort"] = ""

    def get_active_model(self) -> str:
        mapping = {
            "local": self.ollama_model or "default (per-stage)",
            "cloud": self.cloud_model,
            "openai": self.openai_model,
            "gemini": self.gemini_model,
            "azure": self.azure_model,
            "groq": self.groq_model,
            "cerebras": self.cerebras_model,
            "openrouter": self.openrouter_model,
            "nvidia": self.nvidia_model,
            "siliconflow": self.siliconflow_model,
        }
        return mapping.get(self.mode, "\u2014")

    def get_provider_label(self) -> str:
        labels = {
            "local": "\U0001f5a5 Ollama", "cloud": "\u2601\ufe0f Claude",
            "openai": "\U0001f916 OpenAI", "gemini": "\u2726 Gemini",
            "azure": "\U0001f537 Azure", "groq": "\U0001f7e3 Groq",
            "cerebras": "\U0001f7e1 Cerebras", "openrouter": "\U0001f9e1 OpenRouter",
            "nvidia": "\U0001f7e2 NVIDIA NIM", "siliconflow": "\U0001f537 SiliconFlow",
        }
        return labels.get(self.mode, "Not set")

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    @classmethod
    def from_dict(cls, d: dict):
        cfg = cls()
        for k, v in d.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
        return cfg


# ═══════════════════════════════════════════════════════════════
# INSTANTIATE GLOBALS
# ═══════════════════════════════════════════════════════════════

STATE = PipelineState()
CONFIG = AppConfig()
CONNECTION_STATUS = {p: {"status": "untested", "message": "Not tested yet"}
                     for p in ["local", "cloud", "openai", "gemini", "azure", "groq",
                               "cerebras", "openrouter", "nvidia", "siliconflow"]}


# ═══════════════════════════════════════════════════════════════
# SESSION PERSISTENCE
# ═══════════════════════════════════════════════════════════════

def list_sessions() -> list:
    sessions = []
    for f in sorted(SESSIONS_DIR.glob("*.json"), key=os.path.getmtime, reverse=True):
        if f.name == "config.json":
            continue
        try:
            data = json.loads(f.read_text("utf-8"))
            sessions.append({
                "id": data.get("id", f.stem),
                "name": data.get("name", "Untitled Session"),
                "description": data.get("description", ""),
                "createdAt": data.get("createdAt", ""),
                "updatedAt": data.get("updatedAt", ""),
                "currentStage": data.get("currentStage", 1),
                "completed": data.get("completed", 0),
                "totalStages": data.get("totalStages", 9),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return sessions


def load_session(session_id: str) -> Optional[dict]:
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_session(session_id: str, data: dict):
    path = SESSIONS_DIR / f"{session_id}.json"
    data["id"] = session_id
    data["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    path.write_text(json.dumps(data, indent=2), "utf-8")


def delete_session(session_id: str) -> bool:
    path = SESSIONS_DIR / f"{session_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def save_state_to_session():
    if not STATE.current_session_id:
        return
    data = {
        "currentStage": STATE.current_stage,
        "stageData": STATE.stage_data,
        "name": "Pipeline Session",
        "description": "",
        "config": CONFIG.to_dict(),
    }
    completed = sum(1 for s in PIPELINE if STATE.stage_data.get(str(s["id"]), {}).get("completed"))
    data["completed"] = completed
    save_session(STATE.current_session_id, data)


def load_state_from_session(session_id: str) -> bool:
    data = load_session(session_id)
    if not data:
        return False
    if data.get("stageData"):
        for sid, sd in data["stageData"].items():
            if sid in STATE.stage_data:
                for k, v in sd.items():
                    if isinstance(v, dict) and not isinstance(v, list) and v is not None:
                        STATE.stage_data[sid][k] = {**STATE.stage_data[sid].get(k, {}), **v}
                    else:
                        STATE.stage_data[sid][k] = v
    if data.get("currentStage"):
        STATE.current_stage = data["currentStage"]
    if data.get("config"):
        cfg_dict = data["config"]
        for k, v in cfg_dict.items():
            if hasattr(CONFIG, k):
                setattr(CONFIG, k, v)
    return True


def load_server_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"exportsDir": "exports"}


def save_server_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), "utf-8")


# ═══════════════════════════════════════════════════════════════
# LLM API CALLERS (10 providers)
# ═══════════════════════════════════════════════════════════════

import httpx


def _get_advanced_body(provider: str) -> dict:
    adv = CONFIG.advanced.get(provider, {})
    body = {}
    if adv.get("maxTokens"):
        body["max_tokens"] = adv["maxTokens"]
    if adv.get("temperature"):
        body["temperature"] = adv["temperature"]
    if adv.get("topP"):
        body["top_p"] = adv["topP"]
    if adv.get("stream"):
        body["stream"] = adv["stream"]
    if adv.get("reasoningEffort"):
        body["reasoning_effort"] = adv["reasoningEffort"]
    if adv.get("topK"):
        body["top_k"] = adv["topK"]
    return body


async def call_ollama(system: str, user: str, model: str = None) -> str:
    effective_model = (CONFIG.ollama_model or "").strip() or model or "gemma3:4b"
    adv = _get_advanced_body("local")
    body = {
        "model": effective_model,
        "stream": adv.get("stream", False),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    options = {}
    if adv.get("temperature"):
        options["temperature"] = adv["temperature"]
    if adv.get("top_p"):
        options["top_p"] = adv["top_p"]
    if adv.get("max_tokens"):
        options["num_predict"] = adv["max_tokens"]
    if options:
        body["options"] = options

    url = f"{CONFIG.ollama_url.rstrip('/')}/api/chat"
    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(url, json=body)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")


async def call_anthropic(system: str, user: str) -> str:
    adv = _get_advanced_body("cloud")
    body = {
        "model": CONFIG.cloud_model,
        "max_tokens": adv.get("max_tokens", 2000),
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    if adv.get("temperature"):
        body["temperature"] = adv["temperature"]
    if adv.get("top_p"):
        body["top_p"] = adv["top_p"]
    if adv.get("top_k"):
        body["top_k"] = adv["top_k"]

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            json=body,
            headers={
                "Content-Type": "application/json",
                "x-api-key": CONFIG.api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        for block in data.get("content", []):
            if block.get("type") == "text":
                return block.get("text", "")
        return ""


async def call_openai(system: str, user: str) -> str:
    adv = _get_advanced_body("openai")
    body = {
        "model": CONFIG.openai_model,
        "max_tokens": adv.get("max_tokens", 2000),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if adv.get("temperature"):
        body["temperature"] = adv["temperature"]
    if adv.get("top_p"):
        body["top_p"] = adv["top_p"]
    if adv.get("reasoning_effort"):
        body["reasoning_effort"] = adv["reasoning_effort"]

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CONFIG.openai_key}",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")


async def call_gemini(system: str, user: str) -> str:
    adv = _get_advanced_body("gemini")
    body = {"contents": [{"parts": [{"text": system + "\n\n" + user}]}]}
    gen_config = {}
    if adv.get("max_tokens"):
        gen_config["maxOutputTokens"] = adv["max_tokens"]
    if adv.get("temperature"):
        gen_config["temperature"] = adv["temperature"]
    if adv.get("top_p"):
        gen_config["topP"] = adv["top_p"]
    if adv.get("top_k"):
        gen_config["topK"] = adv["top_k"]
    if gen_config:
        body["generationConfig"] = gen_config

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{CONFIG.gemini_model}:generateContent?key={CONFIG.gemini_key}"
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, json=body)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "")
        return ""


async def call_azure(system: str, user: str) -> str:
    adv = _get_advanced_body("azure")
    body = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": adv.get("max_tokens", 2000),
    }
    if adv.get("temperature"):
        body["temperature"] = adv["temperature"]
    if adv.get("top_p"):
        body["top_p"] = adv["top_p"]
    if adv.get("reasoning_effort"):
        body["reasoning_effort"] = adv["reasoning_effort"]

    url = f"{CONFIG.azure_endpoint.rstrip('/')}/openai/deployments/{CONFIG.azure_deployment}/chat/completions?api-version=2024-02-01"
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            url,
            json=body,
            headers={"Content-Type": "application/json", "api-key": CONFIG.azure_key},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")


async def call_groq(system: str, user: str) -> str:
    adv = _get_advanced_body("groq")
    body = {
        "model": CONFIG.groq_model,
        "max_tokens": adv.get("max_tokens", 2000),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if adv.get("temperature"):
        body["temperature"] = adv["temperature"]
    if adv.get("top_p"):
        body["top_p"] = adv["top_p"]
    if adv.get("reasoning_effort"):
        body["reasoning_effort"] = adv["reasoning_effort"]

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CONFIG.groq_key}",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")


async def call_cerebras(system: str, user: str) -> str:
    adv = _get_advanced_body("cerebras")
    body = {
        "model": CONFIG.cerebras_model,
        "max_tokens": adv.get("max_tokens", 2000),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if adv.get("temperature"):
        body["temperature"] = adv["temperature"]
    if adv.get("top_p"):
        body["top_p"] = adv["top_p"]
    if adv.get("reasoning_effort"):
        body["reasoning_effort"] = adv["reasoning_effort"]

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.cerebras.ai/v1/chat/completions",
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CONFIG.cerebras_key}",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")


async def call_openrouter(system: str, user: str) -> str:
    adv = _get_advanced_body("openrouter")
    body = {
        "model": CONFIG.openrouter_model,
        "max_tokens": adv.get("max_tokens", 2000),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if adv.get("temperature"):
        body["temperature"] = adv["temperature"]
    if adv.get("top_p"):
        body["top_p"] = adv["top_p"]
    if adv.get("reasoning_effort"):
        body["reasoning_effort"] = adv["reasoning_effort"]

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CONFIG.openrouter_key}",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")


async def call_nvidia(system: str, user: str) -> str:
    adv = _get_advanced_body("nvidia")
    body = {
        "model": CONFIG.nvidia_model,
        "max_tokens": adv.get("max_tokens", 2000),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if adv.get("temperature"):
        body["temperature"] = adv["temperature"]
    if adv.get("top_p"):
        body["top_p"] = adv["top_p"]
    if adv.get("reasoning_effort"):
        body["reasoning_effort"] = adv["reasoning_effort"]

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CONFIG.nvidia_key}",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")


async def call_siliconflow(system: str, user: str) -> str:
    adv = _get_advanced_body("siliconflow")
    body = {
        "model": CONFIG.siliconflow_model,
        "max_tokens": adv.get("max_tokens", 2000),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if adv.get("temperature"):
        body["temperature"] = adv["temperature"]
    if adv.get("top_p"):
        body["top_p"] = adv["top_p"]
    if adv.get("reasoning_effort"):
        body["reasoning_effort"] = adv["reasoning_effort"]

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.siliconflow.com/v1/chat/completions",
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CONFIG.siliconflow_key}",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")


async def call_llm(system: str, user: str, model: str = None) -> str:
    """Route to the correct provider based on CONFIG.mode."""
    router = {
        "local": lambda: call_ollama(system, user, model),
        "cloud": lambda: call_anthropic(system, user),
        "openai": lambda: call_openai(system, user),
        "gemini": lambda: call_gemini(system, user),
        "azure": lambda: call_azure(system, user),
        "groq": lambda: call_groq(system, user),
        "cerebras": lambda: call_cerebras(system, user),
        "openrouter": lambda: call_openrouter(system, user),
        "nvidia": lambda: call_nvidia(system, user),
        "siliconflow": lambda: call_siliconflow(system, user),
    }
    fn = router.get(CONFIG.mode)
    if fn is None:
        return await call_ollama(system, user, model)
    return await fn()


def get_stage_models(stage: dict) -> list:
    sid = str(stage["id"])
    sd = STATE.stage_data.get(sid, {})
    override = sd.get("modelOverride")
    return override or stage.get("models", [])


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def esc_html(s) -> str:
    if not s:
        return ""
    return (str(s)
            .replace("&", "&")
            .replace("<", "<")
            .replace(">", ">")
            .replace('"', "&#34;"))


def show_toast(msg: str, color: str = "info"):
    ui.notify(msg, type=color, position="bottom-right", timeout=3000)


def get_sd() -> dict:
    return STATE.stage_data.get(str(STATE.current_stage), {})


def get_stage() -> dict:
    return PIPELINE[STATE.current_stage - 1]


def update_progress():
    done = sum(1 for s in PIPELINE if STATE.stage_data.get(str(s["id"]), {}).get("completed"))
    total = len(PIPELINE)
    return done, total


# ═══════════════════════════════════════════════════════════════
# STAGE 1 PRD HELPERS — QUESTION FLATTENING & FLOATING
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
# BUILD STAGE 1 JSON / D5 / D4
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
# EXPORT SYSTEM
# ═══════════════════════════════════════════════════════════════

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
        show_toast(f"Saved to server \u2713", "positive")
    except OSError as e:
        show_toast(f"Save failed: {e}", "negative")


def export_csv():
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


# ═══════════════════════════════════════════════════════════════
# GENERIC STAGES 2-9 RENDERER
# ═══════════════════════════════════════════════════════════════

def render_generic_stage():
    stage = get_stage()
    sd = get_sd()

    # Stage note
    if stage.get("note"):
        with ui.card().classes("w-full max-w-4xl mx-auto"):
            ui.label(f"\u2139\ufe0f Stage note: {stage['note']}").classes("text-sm text-indigo-600")

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
                ui.label(f"\u26a0\ufe0f No {mode} API key configured. Click Connection Setup in sidebar.").classes("text-amber-800 text-sm")

    # Manual deliverables
    if stage.get("manualDeliverables"):
        with ui.card().classes("w-full max-w-4xl mx-auto border-l-4 border-l-amber-400"):
            with ui.card_section():
                ui.label("\u270d\ufe0f Your inputs \u2014 manual authoring required").classes(
                    "text-xs font-semibold uppercase tracking-wider text-amber-700")
            for d in stage["manualDeliverables"]:
                did = d["id"]
                label = d["label"]
                placeholder = d.get("placeholder", "")
                with ui.card().classes("w-full"):
                    ui.label(label).classes("text-sm font-medium")
                    val = sd.get("manualInputs", {}).get(did, "")
                    ta = ui.textarea(value=val).props("outlined").classes("w-full").props(f'placeholder="{placeholder}"')
                    ta.on_value_change(lambda v, d_id=did: _save_manual_input(d_id, v))

    # AI deliverables
    if stage.get("aiDeliverables"):
        with ui.card().classes("w-full max-w-4xl mx-auto border-l-4 border-l-emerald-400"):
            with ui.card_section():
                ai_gen = sd.get("aiGenerated", False)
                label_text = "AI-generated outputs"
                if not ai_gen:
                    label_text += " \u2014 Click Generate AI Output to populate"
                ui.label("\U0001f916 " + label_text).classes("text-xs font-semibold uppercase tracking-wider text-emerald-700")
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
            label = "Gate approved \u2014 proceed to next stage" if approved else "Gate review \u2014 all items must pass"
            ui.label("\u26a1 " + label).classes("text-xs font-semibold uppercase tracking-wider")
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
        show_toast("Gate review complete \u2014 stage approved \u2713", "positive")
        update_progress()


# ═══════════════════════════════════════════════════════════════
# STAGE 1 PRD RENDERER (Wizard Mode)
# ═══════════════════════════════════════════════════════════════

def render_stage1_prd():
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
            ui.button("Finish \u2192 D5 Checks", on_click=_s1_finish_to_d5).props("color=primary")
        else:
            ui.button("Forward \u2192", on_click=lambda: _s1_next_question()).props("color=primary")


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
# STAGE 1 PRD FULL VIEW (Accordion sections)
# ═══════════════════════════════════════════════════════════════

def render_stage1_full_view():
    sd = STATE.stage_data.get("1", {})
    if "inputs" not in sd:
        sd["inputs"] = {}

    with ui.column().classes("w-full max-w-4xl mx-auto"):
        ui.label("\U0001f4dd Stage 1: PRD \u2014 Product Requirements Document").classes("text-lg font-bold")
        ui.label("\u2728 Complete all sections, then run D5 Auto-Checks and D4 Context Diagram.") \
            .classes("text-sm text-amber-700 bg-amber-50 p-3 rounded-lg")

    # Render all sections
    all_sections = list(STAGE1_PRD_DELIVERABLES) + [STAGE1_INFRASTRUCTURE_SECTION, STAGE1_EXTERNAL_SECTION]
    for section in all_sections:
        _render_s1_section(section, sd)

    # Functions detail (if any)
    count = sd.get("functionCount", 0)
    if count > 0:
        with ui.expansion(f"\u2699\ufe0f Functions Detail ({count})", value=True).classes("w-full max-w-4xl mx-auto"):
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
    with ui.expansion("\U0001f517 External Linkages", value=False).classes("w-full max-w-4xl mx-auto"):
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
    with ui.expansion(f"\U0001f50d Auto-Generated Checks (D5)" + (" \u2713 Complete" if has_results else ""),
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
        show_toast("D5 checks completed \u2713", "positive")
        # Auto-run D4
        await _run_d4_generation()
        _rebuild_content()
    except Exception as e:
        show_toast(f"D5 failed: {e}", "negative")


def _render_s1_d4_section(sd: dict):
    has_d4 = bool(sd.get("d4ContextDiagram"))
    with ui.expansion(f"\U0001f3d7\ufe0f Context Diagram (D4)" + (" \u2713 Generated" if has_d4 else ""),
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
        show_toast("D4 diagram generated \u2713", "positive")
        _rebuild_content()
    except Exception as e:
        show_toast(f"D4 failed: {e}", "negative")


# ═══════════════════════════════════════════════════════════════
# AI GENERATION (Stages 2-9)
# ═══════════════════════════════════════════════════════════════

async def generate_ai_output():
    stage = get_stage()
    sd = get_sd()
    if "aiOutputs" not in sd:
        sd["aiOutputs"] = {}
    if "aiQuestions" not in sd:
        sd["aiQuestions"] = []

    # Build context from manual inputs
    manual_ctx = ""
    for d in stage.get("manualDeliverables", []):
        val = sd.get("manualInputs", {}).get(d["id"], "")
        manual_ctx += f"{d['label']}:\n{val or '(not filled)'}\n\n"

    # QA context
    qa_ctx = ""
    if sd.get("aiQuestions") and sd.get("qaAnswers"):
        qa_parts = []
        for i, q in enumerate(sd["aiQuestions"]):
            answer = sd.get("qaAnswers", {}).get(i, "")
            if answer:
                qa_parts.append(f"Q: {q.get('question', '')}\nA: {answer}")
        if qa_parts:
            qa_ctx = "\n\nClarifications:\n" + "\n\n".join(qa_parts)

    models = get_stage_models(stage)
    ai_deliverables = stage.get("aiDeliverables", [])
    deliverable_keys = [d["id"] for d in ai_deliverables]

    system = (
        f"You are an expert software architect working on Stage {stage['id']}: '{stage['name']}'.\n\n"
        "Return ONLY valid JSON with 'deliverables' and 'questions' fields.\n"
        f"Deliverables keys: {', '.join(deliverable_keys)}\n"
        "Questions: array of {'question': ..., 'linkedSection': ...} objects."
    )
    user = f"Stage {stage['id']}: {stage['name']}\n\n{manual_ctx}{qa_ctx}\n\nGenerate all deliverables and open questions."

    try:
        raw = await call_llm(system, user, models[0] if models else None)
        raw = raw.replace("```json", "").replace("```", "").strip()
        match = re.search(r"\{[\s\S]*\}", raw)
        parsed = json.loads(match.group(0)) if match else None

        if parsed and parsed.get("deliverables"):
            for d in ai_deliverables:
                sd["aiOutputs"][d["id"]] = parsed["deliverables"].get(d["id"], "(No content)")
            sd["aiQuestions"] = parsed.get("questions", [])
        else:
            for d in ai_deliverables:
                sd["aiOutputs"][d["id"]] = raw[:500] + "\n\u2026[truncated]"
            sd["aiQuestions"] = []

        sd["aiGenerated"] = True
        show_toast("AI output generated \u2713", "positive")
        _rebuild_content()
    except Exception as e:
        show_toast(f"AI generation failed: {e}", "negative")


# ═══════════════════════════════════════════════════════════════
# STAGE 2 FRS SUB-PIPELINE
# ═══════════════════════════════════════════════════════════════

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
                ui.label("\u2192").classes("text-gray-300")
            is_current = pn == fd.get("activePhase", 1)
            is_completed = pn < fd.get("activePhase", 1)
            color = "green" if is_completed else "primary" if is_current else "default"
            icon = "\u2713" if is_completed else str(pn)
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
    _rebuild_content()


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
        ui.button("Run AI cleanup \u2192", on_click=_frs_run_phase2).props("color=primary")


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
        show_toast(f"{len(points)} points identified \u2713", "positive")
        _rebuild_content()
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
            ui.button("Run AI review \u2192", on_click=_frs_run_phase3).props("color=primary")


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
        show_toast("AI review complete \u2713", "positive")
        _rebuild_content()
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
            ui.button("Go to acceptance \u2192", on_click=lambda: _frs_go_to_phase(4)).props("color=primary")


def _frs_render_phase4(doc: dict):
    points = _frs_active_points(doc)
    incongruent = [p for p in points if p.get("proposalStatus") == "incongruent"]

    with ui.column().classes("w-full max-w-4xl mx-auto"):
        if incongruent:
            with ui.card().classes("w-full bg-red-50 border-red-200"):
                ui.label(f"\u26a0 {len(incongruent)} point(s) have incongruent proposals").classes("text-sm text-red-700")

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
        show_toast("FRS accepted! \u2713", "positive")
        _rebuild_content()
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
        _rebuild_content()
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
            ui.label(f"\u2713 FRS accepted \u2014 version {doc.get('version', {}).get('a', '\u2014')}").classes("text-lg font-bold text-green-700")
            ui.label(f"All points accepted after {len(doc.get('history', []))} review round(s).").classes("text-sm text-green-600")

        if doc.get("history"):
            with ui.card().classes("w-full"):
                ui.label("Round History").classes("text-sm font-semibold")
                for r in doc["history"]:
                    with ui.row().classes("gap-2 text-xs"):
                        ui.label(f"Round {r.get('round', '?')}").classes("font-mono")
                        ui.label(r.get("r_version", "")).classes("font-mono text-gray-500")
                        ui.label(f"({r.get('changes', [])[:1]})").classes("text-gray-400")


# ═══════════════════════════════════════════════════════════════
# CONTENT DISPATCHER
# ═══════════════════════════════════════════════════════════════

def _rebuild_content():
    """Clear and rebuild the main content area based on current stage."""
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
            render_frs_pipeline()
            return

        # Generic stages 3-9
        render_generic_stage()


# ═══════════════════════════════════════════════════════════════
# UI SHELL
# ═══════════════════════════════════════════════════════════════

content_container = ui.column().classes("w-full")


def build_ui():
    """Build the complete UI shell."""
    # ── Dark mode support ──
    app.add_static_files("/static", BASE_DIR / "static" if (BASE_DIR / "static").exists() else BASE_DIR)

    # ── Sidebar ──
    with ui.left_drawer(bordered=True).classes("w-[280px] bg-indigo-950 text-white") as drawer:
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
                        num = "\u26e8" if is_gate else str(s["id"])
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
                ui.button("\U0001f4c2 Sessions", on_click=_show_sessions).props("flat dense size=sm").classes("text-indigo-300 w-full")
                ui.button("\u2699\ufe0f Connection Setup", on_click=_show_setup).props("flat dense size=sm").classes("text-indigo-300 w-full")
                ui.button("\U0001f4be Save to Server", on_click=export_pipeline_json).props("flat dense size=sm").classes("text-indigo-300 w-full")

    # ── Main content area ──
    with ui.column().classes("w-full h-full p-0"):
        # Top bar
        with ui.row().classes("w-full items-center gap-4 p-3 bg-white border-b border-gray-200"):
            stage = get_stage()
            badge = f"Stage {stage['id']}"
            with ui.row().classes("items-center gap-1"):
                ui.label(badge).classes("text-xs font-semibold px-3 py-1 rounded-full bg-indigo-100 text-indigo-700") \
                    if not stage.get("isGate") else \
                    ui.label("\u26e8 Gate").classes("text-xs font-semibold px-3 py-1 rounded-full bg-red-100 text-red-700")
            ui.label(stage.get("name", "")).classes("text-sm font-semibold flex-1")
            ui.label(CONFIG.get_active_model()).classes("text-xs font-mono bg-indigo-50 text-indigo-600 px-2 py-1 rounded-full")
            ui.button("\U0001f4cb History", on_click=lambda: setattr(STATE, 'history_open', not STATE.history_open)).props("flat dense size=sm")

        # Progress bar
        done, total = update_progress()
        ui.linear_progress(value=done / total if total > 0 else 0, color="indigo").classes("w-full h-1")

        # Scrollable content area
        with ui.scroll_area().classes("flex-1 w-full p-6"):
            _rebuild_content()

    # ── Setup dialog ───
    with ui.dialog().props("maximized") as setup_dialog:
        STATE._setup_dialog = setup_dialog
        with ui.card().classes("w-full max-w-3xl mx-auto"):
            with ui.column().classes("p-4 gap-4"):
                ui.label("Connection Setup").classes("text-lg font-bold")
                # Provider tabs
                providers = [
                    ("local", "\U0001f5a5 Local (Ollama)"), ("cloud", "\u2601\ufe0f Anthropic"),
                    ("openai", "\U0001f916 OpenAI"), ("gemini", "\u2726 Gemini"),
                    ("azure", "\U0001f537 Azure"), ("groq", "\U0001f7e3 Groq"),
                    ("cerebras", "\U0001f7e1 Cerebras"), ("openrouter", "\U0001f9e1 OpenRouter"),
                    ("nvidia", "\U0001f7e2 NVIDIA NIM"), ("siliconflow", "\U0001f537 SiliconFlow"),
                ]
                tabs = ui.tabs().classes("w-full")
                tab_panels = ui.tab_panels(tabs, value="local").classes("w-full")
                for pkey, plabel in providers:
                    tab = ui.tab(pkey, label=plabel)
                    with tab_panels.add(tab_panel := ui.tab_panel(pkey)):
                        _render_setup_tab(pkey, tab_panel)
                with ui.row().classes("w-full justify-end gap-2 pt-4"):
                    ui.button("Cancel", on_click=lambda: setup_dialog.close()).props("flat")
                    ui.button("Save & Close", on_click=lambda: _save_setup(setup_dialog)).props("color=primary")

    # ── Sessions dialog ───
    with ui.dialog().props("maximized") as session_dialog:
        STATE._session_dialog = session_dialog
        with ui.card().classes("w-full max-w-3xl mx-auto"):
            with ui.column().classes("p-4 gap-4"):
                ui.label("Pipeline Sessions").classes("text-lg font-bold")
                _render_sessions_list(session_dialog)

    # ── History panel (slide-in) ───
    STATE.history_panel = ui.slide_panel().props("right width=380")


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
            ui.input(label="NVIDIA NIM API Key", value=CONFIG.nvidia_key, password=True, placeholder="nvapi-...") \
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
    # This dialog shows when opening sessions from sidebar
    pass


def _go_to_stage(stage_id: int):
    """Navigate to a specific stage."""
    if stage_id < 1 or stage_id > len(PIPELINE):
        return
    STATE.current_stage = stage_id
    # Reset FRS phase if needed
    _rebuild_content()
    show_toast(f"Stage {stage_id}", "info")


# ═══════════════════════════════════════════════════════════════
# CONNECTION TEST FUNCTIONS
# ═══════════════════════════════════════════════════════════════

async def _test_ollama():
    try:
        url = f"{CONFIG.ollama_url.rstrip('/')}/api/tags"
        async with httpx.AsyncClient(timeout=4) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            models = data.get("models", [])
            names = [m.get("name", "") for m in models[:3]]
            show_toast(f"Connected \u2014 models: {', '.join(names) or 'none'}", "positive")
            CONNECTION_STATUS["local"] = {"status": "passed", "message": "Connected"}
    except Exception as e:
        show_toast(f"Ollama connection failed: {e}", "negative")
        CONNECTION_STATUS["local"] = {"status": "failed", "message": str(e)}


async def _test_anthropic():
    if not CONFIG.api_key:
        show_toast("Enter an API key first", "warning")
        return
    try:
        body = {"model": CONFIG.cloud_model, "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}]}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                json=body,
                headers={"Content-Type": "application/json", "x-api-key": CONFIG.api_key,
                         "anthropic-version": "2023-06-01"},
            )
            resp.raise_for_status()
            show_toast(f"API key valid \u2014 {CONFIG.cloud_model}", "positive")
    except Exception as e:
        show_toast(f"Anthropic test failed: {e}", "negative")


async def _test_openai():
    if not CONFIG.openai_key:
        show_toast("Enter an API key first", "warning")
        return
    try:
        body = {"model": CONFIG.openai_model, "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}]}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json=body,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {CONFIG.openai_key}"},
            )
            resp.raise_for_status()
            show_toast(f"API key valid \u2014 {CONFIG.openai_model}", "positive")
    except Exception as e:
        show_toast(f"OpenAI test failed: {e}", "negative")


async def _test_gemini():
    if not CONFIG.gemini_key:
        show_toast("Enter an API key first", "warning")
        return
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{CONFIG.gemini_model}:generateContent?key={CONFIG.gemini_key}"
        body = {"contents": [{"parts": [{"text": "Hi"}]}]}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=body)
            resp.raise_for_status()
            show_toast(f"API key valid \u2014 {CONFIG.gemini_model}", "positive")
    except Exception as e:
        show_toast(f"Gemini test failed: {e}", "negative")


async def _test_azure():
    if not CONFIG.azure_key or not CONFIG.azure_endpoint:
        show_toast("Fill in all fields first", "warning")
        return
    try:
        url = f"{CONFIG.azure_endpoint.rstrip('/')}/openai/deployments/{CONFIG.azure_deployment}/chat/completions?api-version=2024-02-01"
        body = {"messages": [{"role": "user", "content": "Hi"}], "max_tokens": 10}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=body,
                                     headers={"Content-Type": "application/json", "api-key": CONFIG.azure_key})
            resp.raise_for_status()
            show_toast(f"Connected \u2014 {CONFIG.azure_deployment}", "positive")
    except Exception as e:
        show_toast(f"Azure test failed: {e}", "negative")


async def _test_groq():
    if not CONFIG.groq_key:
        show_toast("Enter an API key first", "warning")
        return
    try:
        body = {"model": CONFIG.groq_model, "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}]}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=body,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {CONFIG.groq_key}"},
            )
            resp.raise_for_status()
            show_toast(f"Connected \u2014 {CONFIG.groq_model}", "positive")
    except Exception as e:
        show_toast(f"Groq test failed: {e}", "negative")


async def _test_cerebras():
    if not CONFIG.cerebras_key:
        show_toast("Enter an API key first", "warning")
        return
    try:
        body = {"model": CONFIG.cerebras_model, "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}]}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.cerebras.ai/v1/chat/completions",
                json=body,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {CONFIG.cerebras_key}"},
            )
            resp.raise_for_status()
            show_toast(f"Connected \u2014 {CONFIG.cerebras_model}", "positive")
    except Exception as e:
        show_toast(f"Cerebras test failed: {e}", "negative")


async def _test_openrouter():
    if not CONFIG.openrouter_key:
        show_toast("Enter an API key first", "warning")
        return
    try:
        body = {"model": CONFIG.openrouter_model, "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}]}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=body,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {CONFIG.openrouter_key}"},
            )
            resp.raise_for_status()
            show_toast(f"Connected \u2014 {CONFIG.openrouter_model}", "positive")
    except Exception as e:
        show_toast(f"OpenRouter test failed: {e}", "negative")


async def _test_nvidia():
    if not CONFIG.nvidia_key:
        show_toast("Enter an API key first", "warning")
        return
    try:
        body = {"model": CONFIG.nvidia_model, "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}]}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                json=body,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {CONFIG.nvidia_key}"},
            )
            resp.raise_for_status()
            show_toast(f"Connected \u2014 {CONFIG.nvidia_model}", "positive")
    except Exception as e:
        show_toast(f"NVIDIA test failed: {e}", "negative")


async def _test_siliconflow():
    if not CONFIG.siliconflow_key:
        show_toast("Enter an API key first", "warning")
        return
    try:
        body = {"model": CONFIG.siliconflow_model, "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}]}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.siliconflow.com/v1/chat/completions",
                json=body,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {CONFIG.siliconflow_key}"},
            )
            resp.raise_for_status()
            show_toast(f"Connected \u2014 {CONFIG.siliconflow_model}", "positive")
    except Exception as e:
        show_toast(f"SiliconFlow test failed: {e}", "negative")


# ═══════════════════════════════════════════════════════════════
# BOTTOM TOOLBAR (Stage navigation, AI generation, Export)
# ═══════════════════════════════════════════════════════════════

def create_bottom_toolbar():
    with ui.row().classes("w-full items-center gap-3 p-3 bg-white border-t border-gray-200"):
        # Status message
        stage = get_stage()
        sd = get_sd()
        status = "Fill in your inputs."
        if stage.get("isStage1PRD"):
            status = "Complete all sections to enable D5 Auto-Checks \u2192"
        elif sd.get("aiGenerated"):
            status = "AI output generated. Proceed or regenerate."
        elif sd.get("completed"):
            status = "Stage completed."
        ui.label(status).classes("text-xs text-gray-400 flex-1 italic")

        # AI Assistant toggle
        ui.button("\U0001f4ac AI Assistant", on_click=lambda: setattr(STATE, "assist_open", not STATE.assist_open)) \
            .props("flat dense size=sm")

        # Previous
        ui.button("\u2190 Previous", on_click=lambda: _go_to_stage(STATE.current_stage - 1)) \
            .props(f'outline dense size=sm {"disabled" if STATE.current_stage <= 1 else ""}')

        # Generate / Main action
        if not stage.get("isStage1PRD") and not stage.get("hasFrsSubPipeline"):
            if not sd.get("aiGenerated"):
                ui.button("Generate AI Output \u2192", on_click=generate_ai_output).props("color=primary dense size=sm")
            else:
                ui.button("\u21bb Regenerate", on_click=generate_ai_output).props("outline dense size=sm")

        # Export dropdown
        with ui.row().classes("items-center gap-1"):
            ui.button("Export \u25bc").props("flat dense size=sm")
            # Export sub-buttons (always visible for simplicity)
            ui.button("JSON", on_click=export_pipeline_json).props("flat dense size=sm")
            ui.button("CSV", on_click=lambda: _download_csv()).props("flat dense size=sm")

        # Next
        disabled_next = STATE.current_stage >= len(PIPELINE)
        ui.button("Next Stage \u2192", on_click=lambda: _go_to_stage(STATE.current_stage + 1)) \
            .props(f'color=primary dense size=sm {"disabled" if disabled_next else ""}')


def _download_csv():
    csv_content = export_csv()
    # Use NiceGUI's download
    ui.download(csv_content.encode("utf-8-sig"), filename=f"pipeline-export.csv")


# ═══════════════════════════════════════════════════════════════
# APPLICATION ENTRY POINT
# ═══════════════════════════════════════════════════════════════

@ui.page("/")
def index():
    # Apply dark theme if set
    if STATE.theme == "dark":
        ui.add_head_html('<style>body { background: #0d0b1e; color: #e0e0f0; }</style>')

    build_ui()
    create_bottom_toolbar()

    # Toolbar action for generating AI output (from bottom bar)
    # This hooks into the generate button defined in create_bottom_toolbar


def main():
    print("\U0001f680 Pipeline Author server starting...")
    print(f"\U0001f4c1 Sessions: {SESSIONS_DIR}")
    print(f"\U0001f4e6 Exports: {EXPORTS_DIR}")
    print(f"\U0001f50c Ollama proxy: {CONFIG.ollama_url}")
    print(f"\U0001f4bb Binds: 0.0.0.0:8080")
    print(f"\u2757 NICEGUI_RELOAD=false (production mode)")
    print()

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
