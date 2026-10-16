"""
Application configuration — loads from environment and config.yaml.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

_ROOT = Path(__file__).resolve().parent.parent.parent  # proofpilot/
_CONFIG_PATH = _ROOT / "config.yaml"


class EconomicsConfig(BaseModel):
    handling_cost: float = 15.0
    dispute_fee: float = 25.0
    challenge_threshold: float = 10.0
    min_evidence_strength: float = 0.4
    min_preparation_hours: float = 4.0
    currency: str = "USD"


class TriageConfig(BaseModel):
    urgency_high: float = 2.0
    urgency_medium: float = 1.5
    urgency_low: float = 1.0
    effort_hours: float = 1.0


class ContradictionPenalties(BaseModel):
    high: float = 0.25
    medium: float = 0.10
    low: float = 0.05


class AppConfig(BaseModel):
    # LLM
    llm_provider: str = "mock"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.1:8b"

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = "sqlite:///proofpilot.db"
    demo_mode: bool = False
    log_level: str = "INFO"

    # Sub-configs
    economics: EconomicsConfig = EconomicsConfig()
    triage: TriageConfig = TriageConfig()
    contradiction_penalties: ContradictionPenalties = ContradictionPenalties()


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Load configuration from environment variables and config.yaml."""
    # Load yaml defaults
    yaml_data: dict = {}
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH) as f:
            yaml_data = yaml.safe_load(f) or {}

    economics = EconomicsConfig(**(yaml_data.get("economics", {})))
    triage = TriageConfig(**(yaml_data.get("triage", {})))
    penalties = ContradictionPenalties(**(yaml_data.get("contradiction_penalties", {})))

    return AppConfig(
        llm_provider=os.getenv("LLM_PROVIDER", "mock").lower(),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        database_url=os.getenv("DATABASE_URL", "sqlite:///proofpilot.db"),
        demo_mode=os.getenv("DEMO_MODE", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        economics=economics,
        triage=triage,
        contradiction_penalties=penalties,
    )
