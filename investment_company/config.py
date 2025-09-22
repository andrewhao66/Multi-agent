"""Configuration helpers for environment and LLM settings."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"


def _load_dotenv(env_file: Path | None) -> None:
    """Load variables from a ``.env`` file when ``python-dotenv`` is available."""

    if env_file is None or not env_file.exists():
        return

    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover - optional dependency
        return

    load_dotenv(dotenv_path=env_file, override=False)


@dataclass
class LLMConfig:
    """Container for Large Language Model connection settings."""

    provider: str
    api_key: Optional[str]
    base_url: Optional[str]
    model: str
    temperature: float
    max_tokens: int

    def headers(self) -> Dict[str, str]:
        """Return default HTTP headers for REST-based providers."""

        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.provider.lower() == "openrouter":
            headers.setdefault("HTTP-Referer", "https://github.com/")
        return headers

    def to_dict(self) -> Dict[str, object]:
        """Serialize the configuration for debugging or logging purposes."""

        return {
            "provider": self.provider,
            "base_url": self.base_url,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "has_api_key": bool(self.api_key),
        }


def load_llm_config(
    env_file: Path | None = None,
    *,
    require_api_key: bool = False,
) -> LLMConfig:
    """Load :class:`LLMConfig` from environment variables.

    Parameters
    ----------
    env_file:
        Optional explicit path to a ``.env`` file. Defaults to the project root.
    require_api_key:
        When ``True`` a missing ``LLM_API_KEY`` results in :class:`RuntimeError`.
    """

    env_path = env_file if env_file is not None else DEFAULT_ENV_FILE
    _load_dotenv(env_path)

    provider = os.getenv("LLM_PROVIDER", "openrouter")

    api_key: Optional[str] = None
    for env_var in ("LLM_API_KEY", "OPENROUTER_API_KEY", "OPENAI_API_KEY"):
        api_key = os.getenv(env_var)
        if api_key:
            break

    base_url = os.getenv("LLM_BASE_URL")
    if not base_url and provider.lower() == "openrouter":
        base_url = "https://openrouter.ai/api/v1"
    model = os.getenv("LLM_MODEL", "gpt-4.1-mini")

    temperature_str = os.getenv("LLM_TEMPERATURE", "0.2")
    max_tokens_str = os.getenv("LLM_MAX_TOKENS", "1024")

    try:
        temperature = float(temperature_str)
    except ValueError as exc:  # pragma: no cover - guard rails
        raise RuntimeError("LLM_TEMPERATURE must be a float") from exc

    try:
        max_tokens = int(max_tokens_str)
    except ValueError as exc:  # pragma: no cover - guard rails
        raise RuntimeError("LLM_MAX_TOKENS must be an integer") from exc

    if require_api_key and not api_key:
        raise RuntimeError(
            "Missing LLM_API_KEY environment variable. Set it in the .env file before "
            "attempting to use LLM-powered agents."
        )

    return LLMConfig(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )


__all__ = ["LLMConfig", "load_llm_config"]
