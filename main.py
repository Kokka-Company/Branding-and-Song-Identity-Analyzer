"""Artist Brand & Sonic Identity Analyzer — pipeline orchestrator.

Usage:
    python main.py examples/sample_input.json

Input JSON schema (see examples/sample_input.json for a filled-in example):

{
  "artist": "Artist Name",
  "audio_files": ["path/to/track1.mp3", ...],
  "lyrics": {"Track Title": "lyrics text..."},
  "metadata": {... arbitrary release/streaming context ...},
  "music_notes": "optional free-form notes for the music agent",
  "images": [{"path": "path/to/img.jpg", "caption": "press 2024"}],
  "persona_notes": "optional free-form notes for the persona agent",
  "output_dir": "outputs/<slug>"   // optional, defaults to outputs/<artist-slug>
}
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from agents import (
    run_brand_alignment,
    run_final_report,
    run_music_analysis,
    run_music_narrative,
    run_persona_analysis,
    run_persona_narrative,
)
from agents.base import write_output
from extractors import extract_corpus_features


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "artist"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


async def run_pipeline(spec: dict[str, Any]) -> dict[str, Path]:
    artist = spec["artist"]
    out_dir = Path(spec.get("output_dir") or f"outputs/{slugify(artist)}")
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- Audio feature extraction (local, blocking) ----
    audio_paths = spec.get("audio_files", [])
    if audio_paths:
        log(f"Extracting librosa features from {len(audio_paths)} track(s)...")
        audio_features = extract_corpus_features(audio_paths)
        write_output(out_dir, "00_audio_features.json", audio_features)
    else:
        log("No audio files provided — skipping librosa extraction.")
        audio_features = {"tracks": [], "aggregate": {}}

    # ---- Stage A: music + persona analysis in parallel ----
    log("Running Music Analysis + Persona Analysis in parallel...")
    music_task = run_music_analysis(
        artist=artist,
        audio_features=audio_features,
        lyrics=spec.get("lyrics"),
        metadata=spec.get("metadata"),
        notes=spec.get("music_notes"),
    )
    persona_task = (
        run_persona_analysis(
            artist=artist,
            images=spec["images"],
            notes=spec.get("persona_notes"),
        )
        if spec.get("images")
        else _noop_persona()
    )
    music_analysis, persona_analysis = await asyncio.gather(music_task, persona_task)
    write_output(out_dir, "01_music_analysis.json", music_analysis)
    write_output(out_dir, "02_persona_analysis.json", persona_analysis)

    # ---- Stage B: narratives in parallel ----
    log("Generating Music Narrative + Persona Narrative in parallel...")
    music_narr_task = run_music_narrative(artist=artist, music_analysis=music_analysis)
    persona_narr_task = run_persona_narrative(artist=artist, persona_analysis=persona_analysis)
    music_narrative, persona_narrative = await asyncio.gather(music_narr_task, persona_narr_task)
    write_output(out_dir, "03_music_narrative.md", music_narrative)
    write_output(out_dir, "04_persona_narrative.md", persona_narrative)

    # ---- Stage C: alignment ----
    log("Running Brand Alignment Agent (Opus)...")
    alignment = await run_brand_alignment(
        artist=artist,
        music_narrative=music_narrative,
        persona_narrative=persona_narrative,
    )
    write_output(out_dir, "05_brand_alignment.md", alignment)

    # ---- Stage D: final report ----
    log("Composing Final Report (Opus)...")
    report = await run_final_report(
        artist=artist,
        music_analysis=music_analysis,
        persona_analysis=persona_analysis,
        music_narrative=music_narrative,
        persona_narrative=persona_narrative,
        brand_alignment=alignment,
    )
    report_path = write_output(out_dir, "06_final_report.md", report)

    log(f"Done. Final dossier → {report_path}")
    return {
        "audio_features": out_dir / "00_audio_features.json",
        "music_analysis": out_dir / "01_music_analysis.json",
        "persona_analysis": out_dir / "02_persona_analysis.json",
        "music_narrative": out_dir / "03_music_narrative.md",
        "persona_narrative": out_dir / "04_persona_narrative.md",
        "brand_alignment": out_dir / "05_brand_alignment.md",
        "final_report": report_path,
    }


async def _noop_persona() -> dict[str, Any]:
    """Stand-in when no images are supplied — downstream agents still need *some* JSON."""
    return {
        "visual_features": {},
        "persona_features": {},
        "cultural_positioning": {},
        "brand_archetypes": [],
        "audience_perception": {},
        "confidence_scores": {},
        "data_gaps": ["No images were supplied; persona analysis was skipped."],
    }


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Artist Brand & Sonic Identity Analyzer")
    parser.add_argument("input_json", help="Path to the input spec JSON")
    args = parser.parse_args()

    spec = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    if not spec.get("artist"):
        print("error: input JSON must include an 'artist' field", file=sys.stderr)
        sys.exit(2)

    asyncio.run(run_pipeline(spec))


if __name__ == "__main__":
    main()
