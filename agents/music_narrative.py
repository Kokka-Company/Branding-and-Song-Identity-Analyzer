"""Agent 3 — Music Narrative. Music JSON → long-form prose."""
from __future__ import annotations

import json
from typing import Any

from .base import DEFAULT_MODEL, call_claude, load_prompt

SYSTEM = load_prompt("03_music_narrative.md")


async def run_music_narrative(
    *,
    artist: str,
    music_analysis: dict[str, Any],
    model: str = DEFAULT_MODEL,
) -> str:
    user = (
        f"# Artist\n{artist}\n\n"
        "# Music Analysis (structured)\n"
        "```json\n" + json.dumps(music_analysis, indent=2) + "\n```\n\n"
        "Write the music narrative essay using the section headers in the system prompt."
    )
    return await call_claude(
        system=SYSTEM,
        user_content=user,
        model=model,
        max_tokens=6000,
        temperature=0.85,
    )
