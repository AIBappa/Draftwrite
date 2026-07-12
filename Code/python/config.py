"""Application configuration (provider settings, persisted to disk)."""
from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent.resolve()
CONFIG_FILE = BASE_DIR / "sessions" / "config.json"
KEYS_DIR = BASE_DIR / "keys"


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

    def save_keys_to_disk(self):
        """Persist keys and model names into individual files under keys/."""
        try:
            KEYS_DIR.mkdir(parents=True, exist_ok=True)
            mapping = {
                "anthropic": ("api_key", "cloud_model"),
                "openai": ("openai_key", "openai_model"),
                "gemini": ("gemini_key", "gemini_model"),
                "azure": ("azure_key", "azure_model"),
                "groq": ("groq_key", "groq_model"),
                "cerebras": ("cerebras_key", "cerebras_model"),
                "openrouter": ("openrouter_key", "openrouter_model"),
                "nvidia": ("nvidia_key", "nvidia_model"),
                "siliconflow": ("siliconflow_key", "siliconflow_model"),
            }
            for name, (key_attr, model_attr) in mapping.items():
                data = {
                    "key": getattr(self, key_attr, ""),
                    "model": getattr(self, model_attr, ""),
                }
                (KEYS_DIR / f"{name}.json").write_text(json.dumps(data, indent=2), "utf-8")
        except OSError:
            pass

    @classmethod
    def load_keys_from_disk(cls):
        """Load keys and model names from individual files under keys/, if present."""
        if not KEYS_DIR.exists():
            return
        mapping = {
            "anthropic": ("api_key", "cloud_model"),
            "openai": ("openai_key", "openai_model"),
            "gemini": ("gemini_key", "gemini_model"),
            "azure": ("azure_key", "azure_model"),
            "groq": ("groq_key", "groq_model"),
            "cerebras": ("cerebras_key", "cerebras_model"),
            "openrouter": ("openrouter_key", "openrouter_model"),
            "nvidia": ("nvidia_key", "nvidia_model"),
            "siliconflow": ("siliconflow_key", "siliconflow_model"),
        }
        cfg = CONFIG
        for name, (key_attr, model_attr) in mapping.items():
            try:
                data = json.loads((KEYS_DIR / f"{name}.json").read_text("utf-8"))
                if data.get("key"):
                    setattr(cfg, key_attr, data["key"])
                if data.get("model"):
                    setattr(cfg, model_attr, data["model"])
            except (OSError, json.JSONDecodeError):
                continue

    @classmethod
    def from_dict(cls, d: dict):
        cfg = cls()
        for k, v in d.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
        return cfg


CONFIG = AppConfig()
CONNECTION_STATUS = {p: {"status": "untested", "message": "Not tested yet"}
                     for p in ["local", "cloud", "openai", "gemini", "azure", "groq",
                               "cerebras", "openrouter", "nvidia", "siliconflow"]}

# Auto-load provider keys/models from keys/ if available
AppConfig.load_keys_from_disk()


def load_server_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"exportsDir": "exports"}


def save_server_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), "utf-8")
    try:
        CONFIG.save_keys_to_disk()
    except Exception:
        pass
