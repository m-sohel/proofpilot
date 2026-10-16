"""
PII masking utility — applied to all log output.

Regex-based masker for synthetic data. NOT production-grade.
Masks: emails, phone numbers, credit card numbers, SSNs, IP addresses.
"""

from __future__ import annotations

import re
from typing import Any

# Patterns and their replacement labels
_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Credit card numbers (13-19 digits with optional separators)
    (re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "[CARD_MASKED]"),
    # SSN
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN_MASKED]"),
    # Email
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL_MASKED]"),
    # Phone numbers (various formats)
    (re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b"), "[PHONE_MASKED]"),
    # IPv4
    (re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "[IP_MASKED]"),
]


def mask_pii(text: str) -> str:
    """Replace PII patterns in text with masked placeholders."""
    result = text
    for pattern, replacement in _PII_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def mask_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively mask PII in dictionary values."""
    masked: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str):
            masked[key] = mask_pii(value)
        elif isinstance(value, dict):
            masked[key] = mask_dict(value)
        elif isinstance(value, list):
            masked[key] = [
                mask_pii(v) if isinstance(v, str)
                else mask_dict(v) if isinstance(v, dict)
                else v
                for v in value
            ]
        else:
            masked[key] = value
    return masked


def safe_log(message: str, **kwargs: Any) -> str:
    """Create a PII-masked log message."""
    masked_msg = mask_pii(message)
    if kwargs:
        masked_kwargs = mask_dict(kwargs)
        parts = [masked_msg] + [f"{k}={v}" for k, v in masked_kwargs.items()]
        return " | ".join(parts)
    return masked_msg
