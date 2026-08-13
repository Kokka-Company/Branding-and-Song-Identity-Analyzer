"""Agent 1 — Music Analysis. Audio features + lyrics + metadata → structured JSON."""
from __future__ import annotations

import json
from typing import Any

from .base import DEFAULT_MODEL, call_claude, load_prompt, parse_json_strict

SYSTEM = load_prompt("01_music_analysis.md")


def _build_user_message(
    *,
    artist: str,
    audio_features: dict[str, Any],
    lyrics: dict[str, str] | None,
    metadata: dict[str, Any] | None,
    notes: str | None,
) -> str:
    parts = [f"# Artist\n{artist}\n"]
    if metadata:
        parts.append("# Metadata\n```json\n" + json.dumps(metadata, indent=2) + "\n```\n")
    parts.append("# Extracted audio features (librosa)\n```json\n"
                 + json.dumps(audio_features, indent=2) + "\n```\n")
    if lyrics:
        parts.append("# Lyrics")
        for title, text in lyrics.items():
            parts.append(f"\n## {title}\n{text}")
        parts.append("")
    if notes:
        parts.append(f"# Additional notes\n{notes}\n")
    parts.append("Return only the JSON object specified in the system prompt.")
    return "\n".join(parts)


async def run_music_analysis(
    *,
    artist: str,
    audio_features: dict[str, Any],
    lyrics: dict[str, str] | None = None,
    metadata: dict[str, Any] | None = None,
    notes: str | None = None,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    user = _build_user_message(
        artist=artist, audio_features=audio_features,
        lyrics=lyrics, metadata=metadata, notes=notes,
    )
    raw = await call_claude(
        system=SYSTEM,
        user_content=user,
        model=model,
        max_tokens=4096,
        temperature=0.4,  # extraction wants steadier output
    )
    return parse_json_strict(raw)
