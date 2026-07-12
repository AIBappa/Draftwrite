"""Shared UI components and connection test functions."""
from __future__ import annotations

import httpx

from nicegui import ui

from ..config import CONFIG, CONNECTION_STATUS
from ..utils import show_toast


# ─── Connection Test Functions ───

async def _test_ollama():
    try:
        url = f"{CONFIG.ollama_url.rstrip('/')}/api/tags"
        async with httpx.AsyncClient(timeout=4) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            models = data.get("models", [])
            names = [m.get("name", "") for m in models[:3]]
            show_toast(f"Connected — models: {', '.join(names) or 'none'}", "positive")
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
            show_toast(f"API key valid — {CONFIG.cloud_model}", "positive")
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
            show_toast(f"API key valid — {CONFIG.openai_model}", "positive")
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
            show_toast(f"API key valid — {CONFIG.gemini_model}", "positive")
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
            show_toast(f"Connected — {CONFIG.azure_deployment}", "positive")
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
            show_toast(f"Connected — {CONFIG.groq_model}", "positive")
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
            show_toast(f"Connected — {CONFIG.cerebras_model}", "positive")
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
            show_toast(f"Connected — {CONFIG.openrouter_model}", "positive")
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
            show_toast(f"Connected — {CONFIG.nvidia_model}", "positive")
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
            show_toast(f"Connected — {CONFIG.siliconflow_model}", "positive")
    except Exception as e:
        show_toast(f"SiliconFlow test failed: {e}", "negative")