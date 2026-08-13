"""Agent 4 — Persona Narrative. Persona JSON → long-form prose."""
from __future__ import annotations

import json
from typing import Any

from .base import DEFAULT_MODEL, call_claude, load_prompt

SYSTEM = load_prompt("04_persona_narrative.md")


async def run_persona_narrative(
    *,
    artist: str,
    persona_analysis: dict[str, Any],
    model: str = DEFAULT_MODEL,
) -> str:
    user = (
        f"# Artist\n{artist}\n\n"
        "# Persona Analysis (structured)\n"
        "```json\n" + json.dumps(persona_analysis, indent=2) + "\n```\n\n"
        "Write the persona narrative essay using the section headers in the system prompt."
    )
    return await call_claude(
        system=SYSTEM,
        user_content=user,
        model=model,
        max_tokens=6000,
        temperature=0.85,
    )
