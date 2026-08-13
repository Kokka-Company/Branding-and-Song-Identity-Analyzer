"""Streaming pipeline runner for the FastAPI backend.

Mirrors the six-stage analysis pipeline in `main.py`, but yields a plain,
JSON-serializable state dict after every stage transition instead of driving
a Gradio UI. The API layer (`server/main.py`) turns each yielded dict into an
SSE `data:` frame.
"""
from __future__ import annotations

import asyncio
import traceback
from pathlib import Path
from typing import Any, AsyncIterator

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

STAGES: list[tuple[str, str]] = [
    ("audio", "Audio Features"),
    ("music_analysis", "Music Analysis"),
    ("persona_analysis", "Persona Analysis"),
    ("music_narrative", "Music Narrative"),
    ("persona_narrative", "Persona Narrative"),
    ("brand_alignment", "Brand Alignment"),
    ("final_report", "Final Report"),
]


class StageError(RuntimeError):
    """Stage-tagged error so the UI can surface which stage failed."""

    def __init__(self, stage: str, original: BaseException) -> None:
        self.stage = stage
        self.original = original
        super().__init__(f"{stage}: {type(original).__name__}: {original}")


async def _guarded(stage: str, coro):
    try:
        return await coro
    except BaseException as e:  # noqa: BLE001 - re-tagged and re-raised below
        raise StageError(stage, e) from e


async def _noop_persona() -> dict[str, Any]:
    return {
        "visual_features": {}, "persona_features": {}, "cultural_positioning": {},
        "brand_archetypes": [], "audience_perception": {}, "confidence_scores": {},
        "data_gaps": ["No images were supplied; persona analysis was skipped."],
    }


def _download_files(out_dir: Path) -> list[str]:
    wanted = [
        "00_audio_features.json", "01_music_analysis.json", "02_persona_analysis.json",
        "03_music_narrative.md", "04_persona_narrative.md",
        "05_brand_alignment.md", "06_final_report.md",
    ]
    return [f for f in wanted if (out_dir / f).exists()]


def _fresh_state(artist_slug: str) -> dict[str, Any]:
    return {
        "artist_slug": artist_slug,
        "stages": [
            {"key": key, "label": label, "status": "pending"}
            for key, label in STAGES
        ],
        "message": "Idle.",
        "error": None,
        "audio": None,
        "music_json": None,
        "persona_json": None,
        "music_narr": "",
        "persona_narr": "",
        "alignment": "",
        "report": "",
        "downloads": [],
        "done": False,
    }


def _set_stage(state: dict[str, Any], key: str, status: str) -> None:
    for stage in state["stages"]:
        if stage["key"] == key:
            stage["status"] = status
            return


async def run_pipeline_stream(
    *,
    artist: str,
    artist_slug: str,
    out_dir: Path,
    audio_paths: list[str],
    lyrics: dict[str, str] | None,
    metadata: dict[str, Any] | None,
    music_notes: str | None,
    images: list[dict[str, str]],
    persona_notes: str | None,
) -> AsyncIterator[dict[str, Any]]:
    state = _fresh_state(artist_slug)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        # ---- Stage 0: librosa extraction ----
        if audio_paths:
            _set_stage(state, "audio", "running")
            state["message"] = f"Extracting audio features from {len(audio_paths)} track(s)..."
            yield state
            try:
                audio_features = await asyncio.to_thread(extract_corpus_features, audio_paths)
            except BaseException as e:
                raise StageError("Audio Features", e) from e
            write_output(out_dir, "00_audio_features.json", audio_features)
            state["audio"] = audio_features
            _set_stage(state, "audio", "done")
        else:
            audio_features = {"tracks": [], "aggregate": {}}
            state["audio"] = audio_features
            _set_stage(state, "audio", "skipped")
            state["message"] = "No audio supplied — skipping audio feature extraction."
            yield state

        # ---- Stages 1+2: analysis agents in parallel ----
        _set_stage(state, "music_analysis", "running")
        _set_stage(state, "persona_analysis", "running")
        state["message"] = "Running Music Analysis + Persona Analysis in parallel..."
        yield state

        music_coro = _guarded(
            "Music Analysis",
            run_music_analysis(
                artist=artist,
                audio_features=audio_features,
                lyrics=lyrics,
                metadata=metadata,
                notes=music_notes or None,
            ),
        )
        persona_coro = (
            _guarded(
                "Persona Analysis",
                run_persona_analysis(artist=artist, images=images, notes=persona_notes or None),
            )
            if images
            else _noop_persona()
        )

        music_analysis, persona_analysis = await asyncio.gather(music_coro, persona_coro)

        state["music_json"] = music_analysis
        state["persona_json"] = persona_analysis
        write_output(out_dir, "01_music_analysis.json", music_analysis)
        write_output(out_dir, "02_persona_analysis.json", persona_analysis)
        _set_stage(state, "music_analysis", "done")
        _set_stage(state, "persona_analysis", "done" if images else "skipped")
        state["message"] = "Music + Persona analysis complete."
        yield state

        # ---- Stages 3+4: narratives in parallel ----
        _set_stage(state, "music_narrative", "running")
        _set_stage(state, "persona_narrative", "running")
        state["message"] = "Generating Music Narrative + Persona Narrative in parallel..."
        yield state

        music_narrative, persona_narrative = await asyncio.gather(
            _guarded(
                "Music Narrative",
                run_music_narrative(artist=artist, music_analysis=music_analysis),
            ),
            _guarded(
                "Persona Narrative",
                run_persona_narrative(artist=artist, persona_analysis=persona_analysis),
            ),
        )
        state["music_narr"] = music_narrative
        state["persona_narr"] = persona_narrative
        write_output(out_dir, "03_music_narrative.md", music_narrative)
        write_output(out_dir, "04_persona_narrative.md", persona_narrative)
        _set_stage(state, "music_narrative", "done")
        _set_stage(state, "persona_narrative", "done")
        state["message"] = "Both narratives ready."
        yield state

        # ---- Stage 5: brand alignment (Opus) ----
        _set_stage(state, "brand_alignment", "running")
        state["message"] = "Brand Alignment Agent thinking on Opus..."
        yield state
        alignment = await _guarded(
            "Brand Alignment",
            run_brand_alignment(
                artist=artist,
                music_narrative=state["music_narr"],
                persona_narrative=state["persona_narr"],
            ),
        )
        state["alignment"] = alignment
        write_output(out_dir, "05_brand_alignment.md", alignment)
        _set_stage(state, "brand_alignment", "done")
        state["message"] = "Alignment memo ready."
        yield state

        # ---- Stage 6: final report (Opus) ----
        _set_stage(state, "final_report", "running")
        state["message"] = "Composing final dossier on Opus..."
        yield state
        report = await _guarded(
            "Final Report",
            run_final_report(
                artist=artist,
                music_analysis=music_analysis,
                persona_analysis=persona_analysis,
                music_narrative=state["music_narr"],
                persona_narrative=state["persona_narr"],
                brand_alignment=alignment,
            ),
        )
        state["report"] = report
        write_output(out_dir, "06_final_report.md", report)
        _set_stage(state, "final_report", "done")
        state["message"] = "Analysis complete."
        state["downloads"] = _download_files(out_dir)
        state["done"] = True
        yield state

    except StageError as se:
        _set_stage(state, _stage_key_for_label(se.stage), "error")
        state["error"] = f"{se.stage} failed — {type(se.original).__name__}: {se.original}"
        state["message"] = state["error"]
        state["done"] = True
        yield state
    except BaseException as be:  # noqa: BLE001 - surfaced to the client, not swallowed
        state["error"] = f"Unexpected error: {type(be).__name__}: {be}"
        state["message"] = state["error"]
        state["done"] = True
        yield state
        raise


def _stage_key_for_label(label: str) -> str:
    for key, stage_label in STAGES:
        if stage_label == label:
            return key
    return STAGES[-1][0]
