"""
DeployGTM LLM provider layer.

Supports Anthropic (Claude) and OpenAI (GPT-4o). Each platform task has an
opinionated default provider chosen for that task's characteristics:

  ICP strategy    → Claude   (deep market segmentation, long-context reasoning)
  Signal strategy → Claude   (domain-specific signal creativity)
  Account scoring → GPT-4o   (structured JSON, parallel per-account calls, speed)
                    falls back to Claude if OPENAI_API_KEY is not set

Override defaults:
  LLM_PROVIDER=openai         switches global default to OpenAI
  LLM_PROVIDER=claude         (default) uses Claude globally
  Pass provider= kwarg to any call_json() call to override per-call.

Offline / test mode:
  Set LLM_SKIP=true to bypass all API calls and return the canned fallback.
  This keeps existing unit tests working without API keys.
"""

from __future__ import annotations

import json
import os
import re
from enum import Enum
from typing import Any


class Provider(str, Enum):
    CLAUDE = "claude"
    OPENAI = "openai"


# Per-task default providers. Scoring defaults to OPENAI because GPT-4o is
# faster and more reliable for structured JSON at scale; falls back to Claude
# automatically if OPENAI_API_KEY is absent.
TASK_DEFAULTS: dict[str, Provider] = {
    "icp_strategy": Provider.CLAUDE,
    "signal_strategy": Provider.CLAUDE,
    "account_scoring": Provider.OPENAI,
}

# Model pinning — update here when rotating models
CLAUDE_MODEL = "claude-sonnet-4-6"
OPENAI_MODEL = "gpt-4o"


def _global_default() -> Provider:
    raw = os.environ.get("LLM_PROVIDER", "claude").lower().strip()
    try:
        return Provider(raw)
    except ValueError:
        return Provider.CLAUDE


def _skip() -> bool:
    return os.environ.get("LLM_SKIP", "").lower() in ("1", "true", "yes")


def provider_for_task(task: str) -> Provider:
    """Return the appropriate provider for a named task, respecting env overrides."""
    if "LLM_PROVIDER" in os.environ:
        return _global_default()
    preferred = TASK_DEFAULTS.get(task, Provider.CLAUDE)
    # If preferred is OpenAI but no key is configured, fall back to Claude
    if preferred == Provider.OPENAI and not os.environ.get("OPENAI_API_KEY"):
        return Provider.CLAUDE
    return preferred


def _extract_json(text: str) -> dict | list:
    """Strip markdown fences and parse JSON from an LLM response."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ``` fences
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    text = text.strip()
    return json.loads(text)


def _call_claude(
    messages: list[dict],
    system: str,
    model: str,
    max_tokens: int,
    temperature: float,
) -> str:
    import anthropic  # local import keeps startup fast when OpenAI-only
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=messages,
    )
    return response.content[0].text


def _call_openai(
    messages: list[dict],
    system: str,
    model: str,
    max_tokens: int,
    temperature: float,
) -> str:
    import openai  # local import
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    full_messages = [{"role": "system", "content": system}] + messages
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=full_messages,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def call_json(
    prompt: str,
    system: str,
    task: str = "",
    provider: Provider | str | None = None,
    model: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.3,
    fallback: dict | None = None,
) -> dict[str, Any]:
    """
    Call an LLM and return parsed JSON.

    Args:
        prompt:      User-facing prompt (the actual request).
        system:      System/persona instruction.
        task:        Named task key for default provider lookup (e.g. "icp_strategy").
        provider:    Override provider. None = use task default.
        model:       Override model. None = use provider default.
        max_tokens:  Max response tokens.
        temperature: Sampling temperature (lower = more deterministic).
        fallback:    Dict to return if LLM_SKIP=true or on error (logged clearly).

    Returns:
        Parsed dict from the LLM response.
    """
    if _skip():
        return fallback or {}

    resolved_provider = Provider(provider) if provider else provider_for_task(task)
    messages = [{"role": "user", "content": prompt}]

    try:
        if resolved_provider == Provider.CLAUDE:
            resolved_model = model or CLAUDE_MODEL
            raw = _call_claude(messages, system, resolved_model, max_tokens, temperature)
        else:
            resolved_model = model or OPENAI_MODEL
            raw = _call_openai(messages, system, resolved_model, max_tokens, temperature)

        return _extract_json(raw)

    except Exception as exc:  # noqa: BLE001
        print(f"[llm] {resolved_provider.value} call failed for task={task!r}: {exc}")
        if fallback is not None:
            print(f"[llm] using fallback for task={task!r}")
            return fallback
        raise
