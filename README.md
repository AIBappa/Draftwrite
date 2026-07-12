# Pipeline Author — LLM-Assisted Software Development

A local desktop tool for authoring software requirements using LLMs. Supports local models via Ollama and cloud APIs (Anthropic, OpenAI, Gemini, Azure, Groq, Cerebras, OpenRouter, NVIDIA, SiliconFlow).

## Getting Started

### Option 1: Local Use (Laptop)

1. **Install dependencies** (local development only):
    ```
    pip install -r requirements.txt
    ```
    **Note:** If deploying via Docker/Coolify (Option 3), dependencies are installed automatically during the image build.

2. **Start the server**:
    ```
    python launcher.py
    ```
    Or run `python Code/python/main.py` directly. The app serves the web UI, manages sessions on disk, and proxies LLM API calls.

3. **Open the app** in your browser:
    ```
    http://localhost:8080/
    ```

4. **Configure your AI provider**:  
    Click **"Connection Setup"** in the sidebar and choose one of:
    - **Local (Ollama)** — for running LLMs on your machine
    - **Anthropic** — Claude models via API key
    - **OpenAI** — GPT models via API key
    - **Gemini** — Google Gemini models via API key
    - **Azure** — Azure OpenAI via API key and endpoint
    - **Groq** — Groq API for fast inference
    - **Cerebras** — Cerebras wafer-scale engine
    - **OpenRouter** — Unified API for multiple providers
    - **NVIDIA NIM** — NVIDIA inference models
    - **SiliconFlow** — SiliconFlow API

    Also note: https://freellm.net/providers/ - this contains list of free LLM providers.

### Option 2: Run Locally with Docker

Build and run the Docker image on your local machine:

1. **Build the image**:
    ```
    docker build -t pipeline-author .
    ```

2. **Run the container**:
    ```
    docker run -p 8080:8080 \
      -v $(pwd)/sessions:/app/sessions \
      -v $(pwd)/saved_exports:/app/exports \
      -v $(pwd)/keys:/app/keys \
      pipeline-author
    ```
    On Windows PowerShell:
    ```
    docker run -p 8080:8080 `
      -v "${PWD}/sessions:/app/sessions" `
      -v "${PWD}/saved_exports:/app/exports" `
      -v "${PWD}/keys:/app/keys" `
      pipeline-author
    ```

3. **Open the app**:
    ```
    http://localhost:8080/
    ```

The `-v` flags mount persistent directories so your data survives container restarts:
- `sessions/` — pipeline session JSON files and `config.json`
- `saved_exports/` — JSON/CSV exports from the pipeline
- `keys/` — API key files and optional `model_names.json` for auto-loading provider settings on startup

### Option 3: Access from Phone via Cloudflare Tunnel

1. Run `python launcher.py` on your laptop (leave it running)
2. In a separate terminal, start Cloudflare Tunnel:
    ```
    cloudflared tunnel --url http://localhost:8080
    ```
    Download `cloudflared` from [developers.cloudflare.com](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) if you don't have it.
3. Cloudflare will give you a URL like `https://something.trycloudflare.com`
4. Open that URL on your phone — everything works because the server proxies Ollama calls

**No CORS issues, no separate browser, no extra config.** The phone just becomes another input device.

### Option 4: Deploy on Coolify / Hetzner

A `Dockerfile` is included in the root for easy deployment.

1. Push this repository to GitHub
2. In Coolify, create a new project and point it to your GitHub repo
3. Select "Dockerfile" as the build type (build path: repository root)
4. Coolify will build and serve the app with HTTPS on port 8080

**Note:** The application is a self-contained NiceGUI app. All Python code lives under `Code/python/` and is launched via `launcher.py`.

## Project Structure

```
├── main.py                 # Root entry point (delegates to Code/python/main.py)
├── launcher.py             # Alternative launcher
├── Code/python/
│   ├── main.py             # Application entry point (ui.run)
│   ├── config.py           # Provider configuration
│   ├── state.py            # Global PipelineState
│   ├── pipeline.py         # Pipeline stage definitions
│   ├── llm.py              # LLM API callers (10 providers)
│   ├── session.py          # Session persistence
│   ├── exporters.py        # JSON/CSV export
│   ├── utils.py            # Helper functions
│   └── ui/
│       ├── shell.py        # Sidebar, dialogs, setup tabs
│       ├── stage1.py       # PRD wizard + full view + D4/D5
│       ├── stage2.py       # SRS/FRS sub-pipeline
│       ├── stages.py       # Generic renderer for stages 3-9
│       ├── stage3.py       # Requirements Validation Gate
│       ├── stage4.py       # Architecture + Contracts
│       ├── stage5.py       # Security Validation Gate
│       ├── stage6.py       # SDD + Atomic Tasks
│       ├── stage7.py       # Task Validation Gate
│       ├── stage8.py       # Code Generation
│       ├── stage9.py       # Integration & Deployment
│       └── components.py   # Connection test functions
├── Dockerfile              # Multi-stage Dockerfile for Coolify
└── README.md
```

## Sessions

The app supports **multiple pipeline sessions** stored on the server:

- **Create sessions** — each session tracks its own pipeline progress
- **Resume anywhere** — work on your laptop, then open the same session from your phone
- **Auto-save** — every change is saved to the server automatically
- **Session list** — when you open the app, you'll see all your sessions

## Requirements

- **Python 3.11+** — for the application
- **NiceGUI** — web UI framework (`pip install nicegui`)
- **Ollama** — required only for local mode ([ollama.com](https://ollama.com))
- **API keys** — required only for cloud providers
- **cloudflared** — optional, for remote access via Cloudflare Tunnel

## Pipeline Stages

The tool guides you through 9 stages of software requirements authoring:

1. Product Requirements Document (PRD)
2. System Requirements Specification (SRS / FRS)
3. Requirements Validation Gate
4. Software Requirements Document (Architecture + Contracts)
5. Security & Architecture Validation Gate
6. SDD + Atomic Task Generation
7. Task Validation Gate
8. Local Task-by-Task Code Generation
9. Integration & Deployment Validation