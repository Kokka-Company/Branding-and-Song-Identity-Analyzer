"""Agent 5 — Brand Alignment. Music + Persona narratives → strategic memo + scores.

Uses the heavy reasoning model (Opus 4.7) — this is the analytical pivot of
the pipeline and benefits most from depth.
"""
from __future__ import annotations

from .base import HEAVY_MODEL, call_claude, load_prompt

SYSTEM = load_prompt("05_brand_alignment.md")


async def run_brand_alignment(
    *,
    artist: str,
    music_narrative: str,
    persona_narrative: str,
    model: str = HEAVY_MODEL,
) -> str:
    user = (
        f"# Artist\n{artist}\n\n"
        "# Music Narrative\n"
        f"{music_narrative}\n\n"
        "# Persona Narrative\n"
        f"{persona_narrative}\n\n"
        "Produce the alignment memo with the section headers and scores defined "
        "in the system prompt."
    )
    return await call_claude(
        system=SYSTEM,
        user_content=user,
        model=model,
        max_tokens=8000,
        temperature=0.7,
    )
