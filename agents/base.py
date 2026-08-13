"""Shared Claude client + helpers for every agent.

Design notes:
- Every agent loads its system prompt from `prompts/`. System prompts are
  cached with `cache_control` so repeated runs reuse them (the system prompt is
  the largest static block we send, so caching pays off immediately).
- Sonnet 4.6 is the default; the two heavy reasoning agents (brand alignment,
  final report) override to Opus 4.7 in their own modules.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
from pathlib import Path
from typing import Any

from anthropic import AsyncAnthropic

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

DEFAULT_MODEL = "claude-sonnet-4-6"
HEAVY_MODEL = "claude-opus-4-7"

_client: AsyncAnthropic | None = None


def get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic()
    return _client


def load_prompt(filename: str) -> str:
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8")


def system_block(text: str) -> list[dict[str, Any]]:
    """Build a cacheable system block."""
    return [
        {
            "type": "text",
            "text": text,
            "cache_control": {"type": "ephemeral"},
        }
    ]


def encode_image(path: str) -> dict[str, Any]:
    """Encode an image file as a multimodal content block."""
    mime, _ = mimetypes.guess_type(path)
    if mime is None or not mime.startswith("image/"):
        # default to jpeg if unknown — Claude will reject genuinely bad payloads
        mime = "image/jpeg"
    data = base64.standard_b64encode(Path(path).read_bytes()).decode("ascii")
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": mime, "data": data},
    }


# Models that no longer accept the `temperature` parameter on the Messages API.
# Opus 4.7 returns 400 invalid_request_error: "`temperature` is deprecated for this model."
_NO_TEMPERATURE_MODELS = {"claude-opus-4-7", "claude-opus-4-7[1m]"}


async def call_claude(
    *,
    system: str,
    user_content: str | list[dict[str, Any]],
    model: str = DEFAULT_MODEL,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> str:
    client = get_client()
    if isinstance(user_content, str):
        content: list[dict[str, Any]] = [{"type": "text", "text": user_content}]
    else:
        content = user_content

    kwargs: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system_block(system),
        "messages": [{"role": "user", "content": content}],
    }
    if model not in _NO_TEMPERATURE_MODELS:
        kwargs["temperature"] = temperature

    msg = await client.messages.create(**kwargs)
    parts: list[str] = []
    for block in msg.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts).strip()


_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.DOTALL)


def parse_json_strict(text: str) -> dict[str, Any]:
    """Parse a JSON object from a model response, tolerating accidental fences."""
    candidate = text.strip()
    candidate = _JSON_FENCE_RE.sub("", candidate).strip()
    # If extra prose was emitted, slice from first '{' to last '}'
    if not candidate.startswith("{"):
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1:
            candidate = candidate[start : end + 1]
    return json.loads(candidate)


def write_output(out_dir: str | os.PathLike[str], filename: str, content: str | dict[str, Any]) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / filename
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
