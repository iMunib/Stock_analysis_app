"""OpenRouter narration client. Free-models only (:free latch). Never logs the key."""
from __future__ import annotations

import json
import time
from typing import Any
from urllib import error, request

from app.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

SYSTEM_PROMPT = (
    "You are writing for a personal equity-research app. Explain the provided facts in "
    "grade-10 English, 120-180 words. Use only the numbers in the JSON. If a field is "
    "null or missing, say it is unknown - never guess or invent numbers. Never give buy "
    "or sell advice; the deterministic score is the rating, your text is narration only. "
    "End with one sentence: research notes, not investment advice."
)


def free_latch(model: str) -> bool:
    """Only model ids containing ':free' may be called."""
    return isinstance(model, str) and model.strip().lower().endswith(":free") and ":free" in model


def llm_status(model: str, fallback: str) -> dict:
    return {
        "configured": bool(OPENROUTER_API_KEY) and free_latch(model) and free_latch(fallback),
        "model": model,
        "fallback": fallback,
        "free_latch": True,
    }


def _chat(model: str, facts: dict[str, Any], timeout: float = 45.0) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not configured")
    if not free_latch(model):
        raise ValueError(f"refusing non-free model: {model}")
    req = request.Request(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        data=json.dumps(
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps({"facts": facts}, ensure_ascii=False)},
                ],
                "temperature": 0.3,
                "max_tokens": 500,
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "Personal Research Desk",
        },
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise RuntimeError(f"openrouter http {exc.code}") from exc
    content = (body.get("choices") or [{}])[0].get("message", {}).get("content")
    if not content or not str(content).strip():
        raise RuntimeError("openrouter returned empty content")
    return str(content).strip()


def narrate(facts: dict[str, Any], model: str, fallback: str, timeout: float = 45.0) -> dict:
    """Try primary, then fallback. Returns {narration, model}. Raises on total failure."""
    t0 = time.monotonic()
    try:
        text = _chat(model, facts, timeout=timeout)
        return {"narration": text, "model": model, "elapsed_ms": int((time.monotonic() - t0) * 1000)}
    except Exception as primary_error:  # noqa: BLE001
        if fallback and fallback != model:
            try:
                text = _chat(fallback, facts, timeout=timeout)
                return {
                    "narration": text,
                    "model": fallback,
                    "elapsed_ms": int((time.monotonic() - t0) * 1000),
                    "fallback_from": model,
                    "primary_error": str(primary_error),
                }
            except Exception as fallback_error:  # noqa: BLE001
                raise RuntimeError(
                    f"narration_unavailable: primary={primary_error}; fallback={fallback_error}"
                ) from fallback_error
        raise


SWOT_SYSTEM_PROMPT = (
    "You are writing a structured Moat and SWOT draft for a personal equity-research app. "
    "Use ONLY the numbers and facts provided in the JSON. If a field is null or missing, "
    "state that it is unknown - never guess or invent numbers. Never give buy or sell advice; "
    "the deterministic score is the rating, your text is qualitative analysis only. "
    "Structure your output using these exact headings: "
    "Strengths: "
    "Weaknesses: "
    "Opportunities: "
    "Threats: "
    "Competitive advantage: (exactly 1 line) "
    "End with one sentence: research notes, not investment advice."
)


def _chat_swot(model: str, facts: dict[str, Any], timeout: float = 45.0) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not configured")
    if not free_latch(model):
        raise ValueError(f"refusing non-free model: {model}")
    req = request.Request(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        data=json.dumps(
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": SWOT_SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps({"facts": facts}, ensure_ascii=False)},
                ],
                "temperature": 0.3,
                "max_tokens": 600,
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "Personal Research Desk",
        },
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise RuntimeError(f"openrouter http {exc.code}") from exc
    content = (body.get("choices") or [{}])[0].get("message", {}).get("content")
    if not content or not str(content).strip():
        raise RuntimeError("openrouter returned empty content")
    return str(content).strip()


def draft_swot(facts: dict[str, Any], model: str, fallback: str, timeout: float = 45.0) -> dict:
    t0 = time.monotonic()
    try:
        text = _chat_swot(model, facts, timeout=timeout)
        return {"swot": text, "model": model, "elapsed_ms": int((time.monotonic() - t0) * 1000)}
    except Exception as primary_error:  # noqa: BLE001
        if fallback and fallback != model:
            try:
                text = _chat_swot(fallback, facts, timeout=timeout)
                return {
                    "swot": text,
                    "model": fallback,
                    "elapsed_ms": int((time.monotonic() - t0) * 1000),
                    "fallback_from": model,
                    "primary_error": str(primary_error),
                }
            except Exception as fallback_error:  # noqa: BLE001
                raise RuntimeError(
                    f"swot_unavailable: primary={primary_error}; fallback={fallback_error}"
                ) from fallback_error
        raise


def call_openrouter(
    messages: list[dict],
    model: str = "minimax/minimax-m3:free",
    fallback: str = "mistralai/mistral-small-24b-instruct-2501:free",
    timeout: float = 45.0,
    max_tokens: int = 600,
    temperature: float = 0.3,
) -> dict:
    """Generic multi-turn conversation call for the chat endpoint.

    Accepts a full messages list (system + user + assistant turns).
    Returns {content, model}. Tries primary then fallback.
    Never logs the key; free_latch enforced on every model ID.
    """
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not configured")
    if not free_latch(model):
        raise ValueError(f"refusing non-free model: {model!r}")

    def _do_call(m: str) -> tuple[str, str]:
        if not free_latch(m):
            raise ValueError(f"refusing non-free model: {m!r}")
        req = request.Request(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            data=json.dumps(
                {
                    "model": m,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5173",
                "X-Title": "Personal Research Desk",
            },
        )
        with request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = (body.get("choices") or [{}])[0].get("message", {}).get("content")
        if not content or not str(content).strip():
            raise RuntimeError("openrouter returned empty content")
        actual_model = body.get("model") or m
        return str(content).strip(), str(actual_model)

    try:
        content, actual = _do_call(model)
        return {"content": content, "model": actual}
    except Exception as primary_err:  # noqa: BLE001
        if fallback and fallback != model and free_latch(fallback):
            try:
                content, actual = _do_call(fallback)
                return {"content": content, "model": actual, "fallback_from": model}
            except Exception:  # noqa: BLE001
                pass
        raise primary_err