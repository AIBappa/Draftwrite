"""Pipeline definition and Stage 1 data structures."""
from __future__ import annotations

# ─── Stage 1 PRD Deliverables ───
STAGE1_PRD_DELIVERABLES = [
    {
        "id": "section_basics",
        "title": "📦 Product Basics",
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
        "title": "📁 Repository Setup",
        "items": [
            {"id": "D1.3", "type": "yesno", "desc": "Do you need files stored on Github or only locally?",
             "hint": "Check if Github is needed.", "reason_llm": "Setting up Github folder only",
             "manual": True, "llm": False, "skipD5": False}
        ]
    },
    {
        "id": "section_functions",
        "title": "⚙️ Functions",
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
    "title": "🖥️ Infrastructure",
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
    "title": "🔗 External Linkages",
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
         {"id": "d1", "label": "D1 — Detailed requirements: Frontend, Android, BFF, Backend", "badge": "manual",
          "placeholder": "Write structured requirements for each layer:\nFrontend: ...\nAndroid: ...\nBFF: ...\nBackend: ..."}
     ],
     "aiDeliverables": [
         {"id": "ai1", "label": "D2 — High-level state machines"},
         {"id": "ai2", "label": "D3 — Flowcharts of functions"},
         {"id": "ai3", "label": "D4 — C4 Container Diagram"},
         {"id": "ai4", "label": "D5 — System invariants document"}
     ], "reviewType": "questions", "hasFrsSubPipeline": True},
    {"id": 3, "name": "Requirements Validation Gate", "type": "Gate", "isGate": True,
     "models": ["deepseek-r1:7b", "qwen2.5-coder:7b"],
     "note": "DeepSeek-R1:7b is the right model here — strongest reasoning.",
     "manualDeliverables": [
         {"id": "d1", "label": "D1 — Contradiction review findings", "badge": "manual",
          "placeholder": "Document contradictions found between requirements..."},
         {"id": "d2", "label": "D2 — Ambiguity review findings", "badge": "manual", "placeholder": "List ambiguous requirements."},
         {"id": "d3", "label": "D3 — Missing requirements review", "badge": "manual", "placeholder": "What's missing?"},
         {"id": "d4", "label": "D4 — Concurrency & offline-risk review", "badge": "manual", "placeholder": "Race conditions, offline sync risks."}
     ],
     "aiDeliverables": [{"id": "ai1", "label": "D5 — Approved finalized requirements document"}],
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
         {"id": "ai1", "label": "D1 — Data schema of functions"},
         {"id": "ai2", "label": "D2 — UML diagrams of functions"},
         {"id": "ai3", "label": "D3 — OpenAPI YAML files"},
         {"id": "ai4", "label": "D4 — PlantUML screen stencils"},
         {"id": "ai5", "label": "D5 — C4 Component Diagram"}
     ], "reviewType": "questions"},
    {"id": 5, "name": "Security & Architecture Validation Gate", "type": "Gate", "isGate": True,
     "models": ["deepseek-r1:7b"],
     "note": "R1:7b handles multi-step security reasoning well.",
     "manualDeliverables": [],
     "aiDeliverables": [
         {"id": "ai1", "label": "D1 — Security review"},
         {"id": "ai2", "label": "D2 — Offline sync / race-condition review"},
         {"id": "ai3", "label": "D3 — Architecture consistency review"},
         {"id": "ai4", "label": "D4 — Dependency validation review"}
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
         {"id": "d1", "label": "D3 — Folder structure & repository layout", "badge": "manual",
          "placeholder": "Define the repository structure."}
     ],
     "aiDeliverables": [
         {"id": "ai1", "label": "D1 — Atomic task list (1:1 to implementation)"},
         {"id": "ai2", "label": "D2 — Deployment / configuration manual"},
         {"id": "ai3", "label": "D4 — Dev & curl-based verification document"},
         {"id": "ai4", "label": "D5 — Dependency graph JSON + context packets"}
     ], "reviewType": "questions"},
    {"id": 7, "name": "Task Validation Gate", "type": "Gate", "isGate": True,
     "models": ["qwen3:4b"],
     "note": "Max task size = 1 file + 1 function.",
     "manualDeliverables": [],
     "aiDeliverables": [
         {"id": "ai1", "label": "D1 — Oversized task detection"},
         {"id": "ai2", "label": "D2 — Hidden dependency review"},
         {"id": "ai3", "label": "D3 — Task ambiguity review"},
         {"id": "ai4", "label": "D4 — Context-window suitability review"}
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
         {"id": "d1", "label": "D4 — Implementation notes", "badge": "manual",
          "placeholder": "Implementation notes for this task batch..."}
     ],
     "aiDeliverables": [
         {"id": "ai1", "label": "D1 — Generated code"},
         {"id": "ai2", "label": "D2 — Unit tests"},
         {"id": "ai3", "label": "D3 — Updated DTOs / interfaces"},
         {"id": "ai4", "label": "D5 — Code review findings"}
     ], "reviewType": "questions"},
    {"id": 9, "name": "Integration & Deployment Validation", "type": "Mixed",
     "models": ["phi3:mini", "qwen3:4b"], "isGate": False,
     "note": "Phi3:mini is sufficient for diff-based contract validation.",
     "manualDeliverables": [
         {"id": "d2", "label": "D2 — Contract mismatch review", "badge": "manual", "placeholder": "Contract mismatches..."},
         {"id": "d3", "label": "D3 — Regression verification checklist", "badge": "manual", "placeholder": "Regression checks..."},
         {"id": "d4", "label": "D4 — Deployment readiness review", "badge": "manual", "placeholder": "Production readiness..."}
     ],
     "aiDeliverables": [
         {"id": "ai1", "label": "D1 — Integration validation report"},
         {"id": "ai5", "label": "D5 — Release approval document"}
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