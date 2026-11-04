# Artist Brand & Sonic Identity Analyzer

A multi-agent pipeline that analyzes an artist's **music** and **public persona** in parallel, then compares them to produce a publication-quality brand intelligence dossier — the kind of document a label A&R, manager, or creative agency could act on.

The system is built as six specialized Claude agents, each with its own engineered system prompt under [`prompts/`](prompts/). The runtime in [`agents/`](agents/) and [`main.py`](main.py) wires them together, runs parallelizable stages concurrently, and writes every intermediate artifact to disk.

## The pipeline

```
                ┌─ Music Analysis  ─→ Music Narrative  ─┐
audio + lyrics ─┤                                       ├─→ Brand Alignment ─→ Final Report
images        ──┴─ Persona Analysis → Persona Narrative ┘            (Opus)        (Opus)
   ↑
librosa features
```

| # | Agent              | Input                                | Output                    | Model        |
|---|--------------------|--------------------------------------|---------------------------|--------------|
| 1 | Music Analysis     | librosa features + lyrics + metadata | structured JSON           | Sonnet 4.6   |
| 2 | Persona Analysis   | images (vision) + captions           | structured JSON           | Sonnet 4.6   |
| 3 | Music Narrative    | Agent 1 JSON                         | long-form prose           | Sonnet 4.6   |
| 4 | Persona Narrative  | Agent 2 JSON                         | long-form prose           | Sonnet 4.6   |
| 5 | Brand Alignment    | Agents 3 + 4 prose                   | strategic memo + 4 scores | **Opus 4.7** |
| 6 | Final Report       | everything above                     | polished dossier          | **Opus 4.7** |

Stages 1+2 and 3+4 run in parallel via `asyncio.gather`. System prompts are sent with `cache_control: ephemeral` so repeated runs reuse them.

## Setup

**Requires Python 3.10 or newer.** macOS ships with 3.9 by default, which is too old for both this codebase (PEP 604 union types) and modern Gradio. If you don't already have a newer Python, `brew install python@3.13`.

```bash
# Create venv on a modern Python — adjust the binary path as needed.
/opt/homebrew/bin/python3.13 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
# add your ANTHROPIC_API_KEY to .env
```

`librosa` pulls in audio dependencies. On macOS you may need `brew install ffmpeg` if your input files aren't WAV.

> **Don't run scripts with the system `python3`.** It's 3.9 on macOS by default, which is too old for this codebase's `dict[str, str] | None` syntax. Always activate `.venv` first.

The web UI also needs the frontend's own dependencies:

```bash
cd frontend
npm install
cd ..
```

## Running

### Option A — Web UI (Vue + FastAPI)

Two processes: the FastAPI backend (wraps the pipeline, streams progress over SSE) and the Vite dev server for the Vue frontend.

```bash
# Terminal 1 — backend, from the repo root
source .venv/bin/activate
uvicorn server.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

Open `http://localhost:5173`. The form accepts audio + image uploads, lyrics, metadata JSON, and notes; an animated stepper tracks all seven pipeline stages live, and results stream into tabs as each stage completes — audio features → music/persona JSON → narratives → alignment memo → final dossier. Every artifact is also written to `outputs/<artist-slug>/` and offered as a download when the run finishes.

For a single-process deployment, build the frontend once and let FastAPI serve it directly:

```bash
cd frontend && npm run build && cd ..
uvicorn server.main:app --port 8000
```

`server/main.py` mounts `frontend/dist/` automatically when it exists, so `http://localhost:8000` serves the built app and the API from the same origin.

### Option B — CLI

1. Copy [`examples/sample_input.json`](examples/sample_input.json) to a new file and fill in real paths and content.
2. Run:

   ```bash
   python main.py path/to/your_input.json
   ```

3. Outputs land in `outputs/<artist-slug>/`:

   ```
   outputs/example-artist/
   ├── 00_audio_features.json     # raw librosa output
   ├── 01_music_analysis.json
   ├── 02_persona_analysis.json
   ├── 03_music_narrative.md
   ├── 04_persona_narrative.md
   ├── 05_brand_alignment.md
   └── 06_final_report.md         # ← the deliverable
   ```

## Input spec

```jsonc
{
  "artist": "Required — the artist's name",
  "audio_files": ["abs/path/track1.mp3", "..."],   // optional but strongly recommended
  "lyrics":    { "Track Title": "lyrics text..." }, // optional
  "metadata":  { "label": "...", "monthly_listeners": 0, ... }, // any free-form context
  "music_notes":   "free-form notes for the music agent",
  "images":   [{ "path": "abs/path/img.jpg", "caption": "..." }], // optional
  "persona_notes": "free-form notes for the persona agent",
  "output_dir": "outputs/custom-name"   // optional
}
```

If you provide no audio files, the music agent still runs but with low-confidence technical fields. If you provide no images, the persona agent is skipped and downstream agents work from music alone.

## Editing prompts

Every agent's behavior is defined entirely by the Markdown file in [`prompts/`](prompts/) plus the small wrapper module in [`agents/`](agents/). To change tone, sectioning, or scoring discipline, edit the prompt file — no Python changes needed. Re-run the pipeline; outputs reflect the new prompt immediately.

## Audio features — caveat

The librosa extractor approximates Spotify-style descriptors (`danceability`, `energy`, `valence`, etc.) from the waveform. They are **heuristic proxies**, not Spotify's real numbers. The Music Analysis Agent is told this in its system prompt and is instructed to treat them as relative signal. If you want true Spotify features, swap [`extractors/audio_features.py`](extractors/audio_features.py) for a Spotify Web API client; the rest of the pipeline does not change.

## Cost & latency

A typical run with ~3 tracks and ~8 images:
- Stage A (parallel Sonnet calls): ~15–25 s
- Stage B (parallel Sonnet calls): ~25–40 s
- Stage C (Opus alignment): ~30–60 s
- Stage D (Opus final report): ~45–90 s

Total wall time: ~2–3 minutes. Token cost is dominated by the two Opus stages and the vision payload in stage A.

## Layout

```
.
├── server/                          # FastAPI web backend
│   ├── main.py                      # HTTP layer: /api/analyze (SSE), /api/download
│   └── pipeline.py                  # streaming pipeline runner shared by the API
├── frontend/                        # Vue 3 + Vite + anime.js UI
│   └── src/
│       ├── App.vue                  # layout, run state, hero animation
│       ├── api.js                   # SSE client for /api/analyze
│       └── components/
│           ├── AnalyzerForm.vue     # identity/music/persona inputs
│           ├── FileDropzone.vue     # drag-and-drop uploads
│           ├── ProgressStepper.vue  # animated 7-stage progress indicator
│           ├── ResultsPanel.vue     # tabbed results (markdown + JSON)
│           ├── MarkdownView.vue
│           ├── JsonView.vue / JsonNode.vue
├── main.py                          # pipeline orchestrator (CLI)
├── prompts/                         # agent system prompts (the real contract)
│   ├── 01_music_analysis.md
│   ├── 02_persona_analysis.md
│   ├── 03_music_narrative.md
│   ├── 04_persona_narrative.md
│   ├── 05_brand_alignment.md
│   └── 06_final_report.md
├── agents/                          # thin Python wrappers around each prompt
│   ├── base.py                      # shared client + helpers
│   ├── music_analysis.py
│   ├── persona_analysis.py
│   ├── music_narrative.py
│   ├── persona_narrative.py
│   ├── brand_alignment.py
│   └── final_report.py
├── extractors/
│   └── audio_features.py            # librosa feature extraction
├── examples/
│   └── sample_input.json
└── outputs/                         # generated reports land here
```

## License

Copyright (C) 2026 Kokka & Company

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the [GNU General Public License](LICENSE) for more details.
