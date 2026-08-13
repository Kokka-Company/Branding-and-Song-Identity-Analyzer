"""FastAPI backend for the Artist Brand & Sonic Identity Analyzer.

Run with:
    uvicorn server.main:app --reload --port 8000

Exposes:
    POST /api/analyze     -- multipart form, streams stage-by-stage state as
                              Server-Sent Events while the pipeline runs.
    GET  /api/download/{artist_slug}/{filename}
                           -- fetch a written artifact from outputs/<slug>/.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from server.pipeline import run_pipeline_stream

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = ROOT / "outputs"
UPLOADS_DIR = OUTPUTS_DIR / "_uploads"
FRONTEND_DIST = ROOT / "frontend" / "dist"

app = FastAPI(title="Artist Brand & Sonic Identity Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "artist"


LYRICS_HEADER_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def parse_lyrics(blob: str) -> dict[str, str] | None:
    blob = (blob or "").strip()
    if not blob:
        return None
    headers = list(LYRICS_HEADER_RE.finditer(blob))
    if not headers:
        return {"Untitled": blob}
    out: dict[str, str] = {}
    for i, m in enumerate(headers):
        title = m.group(1).strip()
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(blob)
        out[title] = blob[start:end].strip()
    return out


def parse_metadata(blob: str) -> dict[str, Any] | None:
    blob = (blob or "").strip()
    if not blob:
        return None
    try:
        parsed = json.loads(blob)
    except json.JSONDecodeError as e:
        raise HTTPException(400, f"Metadata is not valid JSON: {e.msg} (line {e.lineno}, col {e.colno})")
    if not isinstance(parsed, dict):
        raise HTTPException(400, "Metadata must be a JSON object.")
    return parsed


async def _save_uploads(files: list[UploadFile], dest: Path) -> list[str]:
    dest.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for f in files:
        if not f.filename:
            continue
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", f.filename)
        target = dest / safe_name
        with target.open("wb") as out:
            shutil.copyfileobj(f.file, out)
        paths.append(str(target))
    return paths


@app.post("/api/analyze")
async def analyze(
    artist: str = Form(...),
    lyrics: str = Form(""),
    metadata: str = Form(""),
    music_notes: str = Form(""),
    persona_notes: str = Form(""),
    captions: str = Form(""),
    audio: list[UploadFile] = File(default=[]),
    images: list[UploadFile] = File(default=[]),
):
    artist = artist.strip()
    if not artist:
        raise HTTPException(400, "Artist name is required.")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(
            500,
            "ANTHROPIC_API_KEY is not set on the server. Put it in a .env file "
            "next to server/main.py, or export it before launching uvicorn.",
        )

    parsed_lyrics = parse_lyrics(lyrics)
    parsed_metadata = parse_metadata(metadata)

    artist_slug = slugify(artist)
    run_id = uuid.uuid4().hex[:8]
    upload_dir = UPLOADS_DIR / f"{artist_slug}-{run_id}"

    audio_paths = await _save_uploads(audio, upload_dir / "audio")
    image_paths = await _save_uploads(images, upload_dir / "images")

    caption_lines = [c.strip() for c in (captions or "").splitlines() if c.strip()]
    image_inputs = [
        {"path": path, "caption": caption_lines[i] if i < len(caption_lines) else f"Image {i + 1}"}
        for i, path in enumerate(image_paths)
    ]

    out_dir = OUTPUTS_DIR / artist_slug

    async def event_stream():
        try:
            async for state in run_pipeline_stream(
                artist=artist,
                artist_slug=artist_slug,
                out_dir=out_dir,
                audio_paths=audio_paths,
                lyrics=parsed_lyrics,
                metadata=parsed_metadata,
                music_notes=music_notes,
                images=image_inputs,
                persona_notes=persona_notes,
            ):
                yield f"data: {json.dumps(state)}\n\n"
        finally:
            shutil.rmtree(upload_dir, ignore_errors=True)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/download/{artist_slug}/{filename}")
async def download(artist_slug: str, filename: str):
    if "/" in filename or ".." in filename or "/" in artist_slug or ".." in artist_slug:
        raise HTTPException(400, "Invalid path.")
    path = OUTPUTS_DIR / artist_slug / filename
    if not path.exists():
        raise HTTPException(404, "Artifact not found.")
    return FileResponse(path, filename=filename)


@app.get("/api/health")
async def health():
    return {"status": "ok", "anthropic_key_present": bool(os.environ.get("ANTHROPIC_API_KEY"))}


# Serve the built Vue app (after `npm run build` in frontend/) so a single
# `uvicorn server.main:app` command can run the whole thing in production.
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
