"""Agent 6 — Final Report. Synthesize everything into a polished dossier."""
from __future__ import annotations

import json
from typing import Any

from .base import HEAVY_MODEL, call_claude, load_prompt

SYSTEM = load_prompt("06_final_report.md")


async def run_final_report(
    *,
    artist: str,
    music_analysis: dict[str, Any],
    persona_analysis: dict[str, Any],
    music_narrative: str,
    persona_narrative: str,
    brand_alignment: str,
    model: str = HEAVY_MODEL,
) -> str:
    user = (
        f"# Artist\n{artist}\n\n"
        "# Music Analysis (JSON)\n"
        "```json\n" + json.dumps(music_analysis, indent=2) + "\n```\n\n"
        "# Persona Analysis (JSON)\n"
        "```json\n" + json.dumps(persona_analysis, indent=2) + "\n```\n\n"
        "# Music Narrative\n"
        f"{music_narrative}\n\n"
        "# Persona Narrative\n"
        f"{persona_narrative}\n\n"
        "# Brand Alignment Memo\n"
        f"{brand_alignment}\n\n"
        "Compose the final dossier following the structure and voice in the system prompt."
    )
    return await call_claude(
        system=SYSTEM,
        user_content=user,
        model=model,
        max_tokens=10000,
        temperature=0.75,
    )
