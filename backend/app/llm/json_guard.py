"""
JSON Guard — schema-validated LLM calls with retry and fallback.

Pass a JSON schema to the model, ALWAYS validate with Pydantic,
and on failure retry up to 2 times with the validation error appended,
then fall back to the deterministic path.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.base import LLMClient
from app.pii import safe_log

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

MAX_RETRIES = 2


async def guarded_llm_call(
    client: LLMClient,
    messages: list[dict[str, str]],
    response_model: type[T] | None = None,
    response_list_model: type[T] | None = None,
    json_schema: dict[str, Any] | None = None,
    fallback_fn: Callable[[], Any] | None = None,
    temperature: float = 0.1,
) -> T | list[T] | Any:
    """
    Make an LLM call with JSON schema validation and retry logic.

    Args:
        client: The LLM client to use.
        messages: Chat messages.
        response_model: Pydantic model for single-object response.
        response_list_model: Pydantic model for list response (each item validated).
        json_schema: JSON schema to pass to the model.
        fallback_fn: Deterministic fallback if all retries fail.
        temperature: Sampling temperature.

    Returns:
        Validated Pydantic model(s) or fallback result.
    """
    attempt_messages = list(messages)

    for attempt in range(1 + MAX_RETRIES):
        try:
            raw_response = await client.chat(
                messages=attempt_messages,
                json_schema=json_schema,
                temperature=temperature,
            )

            # Try to parse JSON from the response
            parsed = _extract_json(raw_response)

            # Validate with Pydantic
            if response_list_model is not None:
                if not isinstance(parsed, list):
                    parsed = [parsed]
                validated = [response_list_model.model_validate(item) for item in parsed]
                logger.info(safe_log(
                    f"JSON guard: validated {len(validated)} items on attempt {attempt + 1}"
                ))
                return validated

            elif response_model is not None:
                validated = response_model.model_validate(parsed)
                logger.info(safe_log(
                    f"JSON guard: validated response on attempt {attempt + 1}"
                ))
                return validated

            else:
                return parsed

        except (json.JSONDecodeError, ValidationError, TypeError, KeyError) as e:
            error_msg = str(e)
            logger.warning(safe_log(
                f"JSON guard: attempt {attempt + 1} failed",
                error=error_msg[:200],
            ))

            if attempt < MAX_RETRIES:
                # Append error to messages for retry
                attempt_messages.append({
                    "role": "user",
                    "content": (
                        f"Your previous response was invalid. Error: {error_msg}\n"
                        "Please fix the JSON and try again. Return ONLY valid JSON."
                    ),
                })
            else:
                logger.warning(safe_log(
                    "JSON guard: all retries exhausted, falling back to deterministic path"
                ))

    # All retries failed — use fallback
    if fallback_fn is not None:
        logger.info(safe_log("JSON guard: using fallback function"))
        return fallback_fn()

    raise ValueError("LLM JSON guard: all retries failed and no fallback provided")


def _extract_json(text: str) -> Any:
    """
    Extract JSON from LLM response text.
    Handles cases where JSON is wrapped in markdown code blocks.
    """
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    if "```" in text:
        # Find content between ``` markers
        parts = text.split("```")
        for part in parts[1::2]:  # odd indices are inside code blocks
            # Remove language hint (e.g., "json\n")
            content = part.strip()
            if content.startswith("json"):
                content = content[4:].strip()
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                continue

    # Try finding JSON array or object
    for start_char, end_char in [("[", "]"), ("{", "}")]:
        start_idx = text.find(start_char)
        end_idx = text.rfind(end_char)
        if start_idx != -1 and end_idx > start_idx:
            try:
                return json.loads(text[start_idx : end_idx + 1])
            except json.JSONDecodeError:
                continue

    raise json.JSONDecodeError("No valid JSON found in response", text, 0)
