"""
LLM Client base interface.

The LLM is ONLY used for:
  (a) extracting facts from text
  (b) writing prose from a verified fact sheet

All decisions are deterministic code. The LLM never chooses the recommendation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMClient(ABC):
    """Abstract base class for LLM access."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any] | None = None,
        temperature: float = 0.1,
    ) -> str:
        """
        Send a chat completion request.

        Args:
            messages: List of {"role": ..., "content": ...} dicts.
            json_schema: Optional JSON schema for structured output.
            temperature: Sampling temperature (lower = more deterministic).

        Returns:
            The model's text response.
        """
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the LLM backend is reachable."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name."""
        ...
