"""
Ollama LLM Client — HTTP wrapper for local Ollama API.

Endpoint: http://127.0.0.1:11434/api/chat
Model from env OLLAMA_MODEL (default: llama3.1:8b).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.llm.base import LLMClient
from app.pii import safe_log

logger = logging.getLogger(__name__)


class OllamaClient(LLMClient):
    """LLM client that talks to a local Ollama instance."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "llama3.1:8b"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.AsyncClient(timeout=120.0)

    async def chat(
        self,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any] | None = None,
        temperature: float = 0.1,
    ) -> str:
        url = f"{self.base_url}/api/chat"

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }

        # Pass JSON schema if supported (Ollama format field)
        if json_schema is not None:
            payload["format"] = "json"

        logger.debug(safe_log(f"Ollama request to {self.model}", message_count=str(len(messages))))

        response = await self._client.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        content = data.get("message", {}).get("content", "")

        logger.debug(safe_log("Ollama response received", length=str(len(content))))
        return content

    async def is_available(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            response = await self._client.get(f"{self.base_url}/api/tags", timeout=5.0)
            if response.status_code != 200:
                return False
            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            # Check if our model (or a variant) is available
            return any(self.model in m for m in models)
        except Exception:
            return False

    @property
    def provider_name(self) -> str:
        return f"ollama ({self.model})"

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._client.aclose()
