"""Local audio feature extraction via librosa.

These features are *approximations* of the Spotify-style descriptors the Music
Analysis Agent expects. They are computed deterministically from the waveform
so the LLM has grounded technical numbers to interpret rather than guess.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from typing import Any

import librosa
import numpy as np


SR = 22050  # librosa default; sufficient for the descriptors we compute
KEY_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


@dataclass
class TrackFeatures:
    path: str
    duration_sec: float
    bpm: float
    beat_regularity: float          # 0–1, higher = steadier
    rms_loudness_db: float          # negative; closer to 0 = louder
    dynamic_range_db: float
    spectral_centroid_hz: float     # brightness proxy
    spectral_rolloff_hz: float
    zero_crossing_rate: float       # noisiness/percussiveness proxy
    spectral_contrast: float
    harmonic_to_percussive_ratio: float
    onset_density_per_sec: float    # rhythmic activity
    chroma_entropy: float           # 0=tonal/diatonic, ~1=harmonically diffuse
    estimated_key: str
    estimated_mode: str             # "major" / "minor"
    energy: float                   # 0–1 proxy
    danceability: float             # 0–1 proxy
    acousticness: float             # 0–1 proxy
    instrumentalness: float         # 0–1 proxy (very rough — vocal detection is hard)
    valence: float                  # 0–1 proxy from mode + brightness + tempo
    note: str = (
        "Spotify-style fields are heuristic approximations from librosa. "
        "Use them as relative signal, not absolute truth."
    )


def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    return float(a / b) if b else default


def _estimate_key(y: np.ndarray, sr: int) -> tuple[str, str]:
    """Krumhansl-Schmuckler key estimation."""
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    major_profile = np.array(
        [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    )
    minor_profile = np.array(
        [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
    )
    major_corr = [np.corrcoef(np.roll(major_profile, i), chroma)[0, 1] for i in range(12)]
    minor_corr = [np.corrcoef(np.roll(minor_profile, i), chroma)[0, 1] for i in range(12)]
    if max(major_corr) >= max(minor_corr):
        return KEY_NAMES[int(np.argmax(major_corr))], "major"
    return KEY_NAMES[int(np.argmax(minor_corr))], "minor"


def _normalize(value: float, lo: float, hi: float) -> float:
    if hi == lo:
        return 0.5
    return float(np.clip((value - lo) / (hi - lo), 0.0, 1.0))


def extract_track_features(path: str) -> dict[str, Any]:
    """Extract a feature dict for a single audio file."""
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    y, sr = librosa.load(path, sr=SR, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    # Tempo + beat regularity
    # librosa >= 0.10 returns tempo as a 1-element array; numpy 2 refuses to
    # float() that, so collapse it to a scalar before anything downstream.
    tempo_raw, beats = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(np.atleast_1d(tempo_raw).ravel()[0])
    if len(beats) > 2:
        beat_times = librosa.frames_to_time(beats, sr=sr)
        intervals = np.diff(beat_times)
        cv = np.std(intervals) / np.mean(intervals) if np.mean(intervals) else 1.0
        beat_regularity = float(np.clip(1.0 - cv, 0.0, 1.0))
    else:
        beat_regularity = 0.0

    # Loudness + dynamics
    rms = librosa.feature.rms(y=y)[0]
    rms_db = 20 * np.log10(np.maximum(rms, 1e-6))
    rms_loudness_db = float(rms_db.mean())
    dynamic_range_db = float(np.percentile(rms_db, 95) - np.percentile(rms_db, 5))

    # Spectral
    centroid = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
    rolloff = float(librosa.feature.spectral_rolloff(y=y, sr=sr).mean())
    zcr = float(librosa.feature.zero_crossing_rate(y).mean())
    contrast = float(librosa.feature.spectral_contrast(y=y, sr=sr).mean())

    # Harmonic / percussive split
    y_harm, y_perc = librosa.effects.hpss(y)
    h_energy = float(np.mean(y_harm ** 2))
    p_energy = float(np.mean(y_perc ** 2))
    h2p = _safe_div(h_energy, p_energy, default=1.0)

    # Onset density
    onsets = librosa.onset.onset_detect(y=y, sr=sr, units="time")
    onset_density = _safe_div(len(onsets), duration, default=0.0)

    # Chroma entropy (harmonic diffuseness)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    chroma = chroma / (chroma.sum() + 1e-9)
    chroma_entropy = float(-np.sum(chroma * np.log(chroma + 1e-9)) / np.log(12))

    key, mode = _estimate_key(y, sr)

    # Heuristic Spotify-style proxies
    energy = _normalize(rms_loudness_db, -40, -5) * 0.6 + _normalize(p_energy, 0, 0.05) * 0.4
    energy = float(np.clip(energy, 0, 1))

    # Danceability: steady tempo in dance range + percussive energy
    tempo_fit = float(np.exp(-((tempo - 118) ** 2) / (2 * 22 ** 2)))  # peak ~118 bpm
    danceability = float(np.clip(0.55 * beat_regularity + 0.30 * tempo_fit + 0.15 * _normalize(p_energy, 0, 0.04), 0, 1))

    # Acousticness: low percussive energy, mid-low brightness, low ZCR
    acousticness = float(np.clip(
        0.5 * (1 - _normalize(p_energy, 0, 0.04))
        + 0.3 * (1 - _normalize(centroid, 1500, 4500))
        + 0.2 * (1 - _normalize(zcr, 0.03, 0.18)),
        0, 1
    ))

    # Instrumentalness: very rough — high spectral contrast + low ZCR variance
    zcr_series = librosa.feature.zero_crossing_rate(y)[0]
    zcr_var = float(np.var(zcr_series))
    instrumentalness = float(np.clip(_normalize(contrast, 15, 30) * 0.6 + (1 - _normalize(zcr_var, 0, 0.005)) * 0.4, 0, 1))

    # Valence: mode + brightness + tempo
    mode_bonus = 0.6 if mode == "major" else 0.3
    valence = float(np.clip(
        0.45 * mode_bonus
        + 0.30 * _normalize(centroid, 1200, 4500)
        + 0.25 * _normalize(tempo, 70, 140),
        0, 1
    ))

    feats = TrackFeatures(
        path=path,
        duration_sec=round(float(duration), 2),
        bpm=round(tempo, 1),
        beat_regularity=round(beat_regularity, 3),
        rms_loudness_db=round(rms_loudness_db, 2),
        dynamic_range_db=round(dynamic_range_db, 2),
        spectral_centroid_hz=round(centroid, 1),
        spectral_rolloff_hz=round(rolloff, 1),
        zero_crossing_rate=round(zcr, 4),
        spectral_contrast=round(contrast, 3),
        harmonic_to_percussive_ratio=round(h2p, 3),
        onset_density_per_sec=round(onset_density, 3),
        chroma_entropy=round(chroma_entropy, 3),
        estimated_key=key,
        estimated_mode=mode,
        energy=round(energy, 3),
        danceability=round(danceability, 3),
        acousticness=round(acousticness, 3),
        instrumentalness=round(instrumentalness, 3),
        valence=round(valence, 3),
    )
    return asdict(feats)


def extract_corpus_features(paths: list[str]) -> dict[str, Any]:
    """Run extraction over a list of tracks and produce per-track + aggregate stats."""
    tracks: list[dict[str, Any]] = []
    for p in paths:
        try:
            tracks.append(extract_track_features(p))
        except Exception as exc:  # one bad file shouldn't kill the corpus
            tracks.append({"path": p, "error": f"{type(exc).__name__}: {exc}"})

    valid = [t for t in tracks if "error" not in t]
    aggregate: dict[str, Any] = {}
    if valid:
        numeric_keys = [
            "bpm", "beat_regularity", "rms_loudness_db", "dynamic_range_db",
            "spectral_centroid_hz", "zero_crossing_rate", "harmonic_to_percussive_ratio",
            "onset_density_per_sec", "chroma_entropy", "energy", "danceability",
            "acousticness", "instrumentalness", "valence",
        ]
        for k in numeric_keys:
            vals = [t[k] for t in valid]
            aggregate[k] = {
                "mean": round(float(np.mean(vals)), 3),
                "std": round(float(np.std(vals)), 3),
                "min": round(float(np.min(vals)), 3),
                "max": round(float(np.max(vals)), 3),
            }
        modes = [t["estimated_mode"] for t in valid]
        aggregate["mode_distribution"] = {
            "major": modes.count("major"),
            "minor": modes.count("minor"),
        }
        aggregate["track_count"] = len(valid)

    return {"tracks": tracks, "aggregate": aggregate}
