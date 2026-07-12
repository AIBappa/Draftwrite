"""LLM API callers for all providers."""
from __future__ import annotations

import httpx
import re

from .config import CONFIG


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
    from .state import STATE
    sid = str(stage["id"])
    sd = STATE.stage_data.get(sid, {})
    override = sd.get("modelOverride")
    return override or stage.get("models", [])