"""Agent 2 — Persona Analysis. Images + captions → structured JSON via Claude vision."""
from __future__ import annotations

from typing import Any

from .base import DEFAULT_MODEL, call_claude, encode_image, load_prompt, parse_json_strict

SYSTEM = load_prompt("02_persona_analysis.md")


async def run_persona_analysis(
    *,
    artist: str,
    images: list[dict[str, str]],
    notes: str | None = None,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """`images` is a list of {"path": "...", "caption": "..."} dicts."""
    if not images:
        raise ValueError("Persona analysis requires at least one image.")

    content: list[dict[str, Any]] = [
        {"type": "text", "text": f"# Artist\n{artist}\n\n# Images for analysis\n"
                                  "Each image is followed by its caption."}
    ]
    for img in images:
        content.append(encode_image(img["path"]))
        caption = img.get("caption", "(no caption)")
        content.append({"type": "text", "text": f"Caption: {caption}\n"})

    if notes:
        content.append({"type": "text", "text": f"\n# Additional notes\n{notes}\n"})
    content.append({
        "type": "text",
        "text": "Return only the JSON object specified in the system prompt."
    })

    raw = await call_claude(
        system=SYSTEM,
        user_content=content,
        model=model,
        max_tokens=4096,
        temperature=0.4,
    )
    return parse_json_strict(raw)
