"""
LLM client initialization and provider factory.
"""

from __future__ import annotations

from app.config import get_config
from app.llm.base import LLMClient
from app.llm.mock_client import MockLLMClient
from app.llm.ollama_client import OllamaClient


def get_llm_client() -> LLMClient:
    cfg = get_config()
    if cfg.demo_mode or cfg.llm_provider == "mock":
        return MockLLMClient()
    elif cfg.llm_provider == "ollama":
        return OllamaClient(
            base_url=cfg.ollama_base_url,
            model=cfg.ollama_model,
        )
    return MockLLMClient()
