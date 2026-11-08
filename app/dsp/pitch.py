"""Detección de tono monofónico y agrupación de segmentos musicales.

Librosa aporta la lectura de audio, detección de actividad y el estimador pYIN.
La conversión a notas, cálculo de cents, filtrado y agrupación temporal son
lógica propia de DoLean para mantener explícito el contrato del análisis.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    import librosa
except ModuleNotFoundError:  # Permite probar las conversiones puras fuera del contenedor.
    librosa = None  # type: ignore[assignment]


NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def _require_librosa():
    if librosa is None:
        raise RuntimeError("librosa es necesaria para ejecutar el análisis DSP")
    return librosa


@dataclass(frozen=True)
class PitchSegment:
    """Resultado estable de una región con una nota musical dominante."""

    segment_index: int
    start_time: float
    end_time: float
    detected_midi: float
    note_name: str
    frequency_hz: float
    deviation_cents: float
    confidence: float


@dataclass(frozen=True)
class PitchAnalysisResult:
    """Resultado completo del análisis de un archivo de audio."""

    sample_rate: int
    duration_seconds: float
    notes: tuple[PitchSegment, ...]


def midi_to_note_name(midi: int) -> str:
    """Convierte un MIDI entero a nombre científico de nota."""

    if midi < 0 or midi > 127:
        raise ValueError("El valor MIDI debe estar entre 0 y 127")
    octave = (midi // 12) - 1
    return f"{NOTE_NAMES[midi % 12]}{octave}"


def frequency_to_pitch(frequency_hz: float) -> tuple[float, int, str, float]:
    """Calcula MIDI, nota y desviación respecto al temperamento igual."""

    if not np.isfinite(frequency_hz) or frequency_hz <= 0:
        raise ValueError("La frecuencia debe ser positiva y finita")
    midi = float(69.0 + 12.0 * np.log2(frequency_hz / 440.0))
    nearest_midi = int(np.clip(np.rint(midi), 0, 127))
    reference_frequency = 440.0 * (2.0 ** ((nearest_midi - 69) / 12.0))
    deviation_cents = float(1200.0 * np.log2(frequency_hz / reference_frequency))
    return midi, nearest_midi, midi_to_note_name(nearest_midi), deviation_cents


def _activity_mask(
    signal: np.ndarray,
    frame_count: int,
    frame_length: int,
    hop_length: int,
    top_db: float,
) -> np.ndarray:
    librosa_module = _require_librosa()
    intervals = librosa_module.effects.split(
        signal,
        top_db=top_db,
        frame_length=frame_length,
        hop_length=hop_length,
    )
    frame_centers = np.arange(frame_count) * hop_length + frame_length / 2
    active = np.zeros(frame_count, dtype=bool)
    for start, end in intervals:
        active |= (frame_centers >= start) & (frame_centers < end)
    return active


def _build_segments(
    f0: np.ndarray,
    voiced_flag: np.ndarray,
    voiced_probability: np.ndarray,
    active: np.ndarray,
    frame_times: np.ndarray,
    hop_seconds: float,
    duration_seconds: float,
    *,
    min_confidence: float,
    min_segment_seconds: float,
    max_gap_frames: int,
) -> tuple[PitchSegment, ...]:
    valid = (
        active
        & voiced_flag.astype(bool)
        & np.isfinite(f0)
        & (f0 > 0)
        & np.isfinite(voiced_probability)
        & (voiced_probability >= min_confidence)
    )
    if not np.any(valid):
        return ()

    rounded_midi = np.full(f0.shape, -1, dtype=int)
    rounded_midi[valid] = np.rint(69.0 + 12.0 * np.log2(f0[valid] / 440.0)).astype(int)
    groups: list[tuple[list[int], list[int]]] = []
    current_indices: list[int] = []
    current_values: list[int] = []
    last_valid = -1

    def close_group() -> None:
        nonlocal current_indices, current_values
        if current_indices:
            groups.append((current_indices, current_values))
        current_indices = []
        current_values = []

    for frame_index, is_valid in enumerate(valid):
        if not is_valid:
            continue
        midi_value = int(rounded_midi[frame_index])
        gap = frame_index - last_valid - 1
        if not current_indices:
            current_indices = [frame_index]
            current_values = [midi_value]
        elif midi_value == current_values[-1] and gap <= max_gap_frames:
            current_indices.append(frame_index)
            current_values.append(midi_value)
        else:
            close_group()
            current_indices = [frame_index]
            current_values = [midi_value]
        last_valid = frame_index
    close_group()

    segments: list[PitchSegment] = []
    for indices, _ in groups:
        start_time = float(frame_times[indices[0]])
        end_time = float(min(duration_seconds, frame_times[indices[-1]] + hop_seconds))
        if end_time - start_time < min_segment_seconds:
            continue
        frequencies = f0[indices]
        probabilities = voiced_probability[indices]
        median_frequency = float(np.median(frequencies))
        detected_midi, _, note_name, deviation_cents = frequency_to_pitch(median_frequency)
        segments.append(
            PitchSegment(
                segment_index=len(segments),
                start_time=max(0.0, start_time),
                end_time=end_time,
                detected_midi=detected_midi,
                note_name=note_name,
                frequency_hz=median_frequency,
                deviation_cents=deviation_cents,
                confidence=float(np.median(probabilities)),
            )
        )
    return tuple(segments)


def analyze_pitch(
    audio_path: str | Path,
    *,
    frame_length: int = 2048,
    hop_length: int = 256,
    activity_top_db: float = 35.0,
    min_confidence: float = 0.55,
    min_segment_seconds: float = 0.08,
    max_gap_frames: int = 2,
    fmin_hz: float = 65.4064,
    fmax_hz: float = 2093.0,
) -> PitchAnalysisResult:
    """Analiza un audio monofónico usando pYIN y devuelve segmentos musicales.

    `confidence` es la mediana de la probabilidad de voz devuelta por pYIN en
    los frames del segmento. `deviation_cents` es la distancia logarítmica de
    la frecuencia mediana frente a la nota temperada más cercana.
    """

    if frame_length <= 0 or hop_length <= 0:
        raise ValueError("frame_length y hop_length deben ser positivos")
    if not 0 < min_confidence <= 1:
        raise ValueError("min_confidence debe estar entre 0 y 1")
    if min_segment_seconds <= 0 or max_gap_frames < 0:
        raise ValueError("Los umbrales temporales no son válidos")

    librosa_module = _require_librosa()
    signal, sample_rate = librosa_module.load(str(audio_path), sr=None, mono=True)
    if signal.size == 0 or sample_rate <= 0:
        raise ValueError("El archivo no contiene una señal de audio válida")
    duration_seconds = float(signal.size / sample_rate)
    f0, voiced_flag, voiced_probability = librosa_module.pyin(
        signal,
        fmin=fmin_hz,
        fmax=min(fmax_hz, sample_rate / 2 - 1),
        sr=sample_rate,
        frame_length=frame_length,
        hop_length=hop_length,
        fill_na=np.nan,
    )
    frame_count = len(f0)
    frame_times = librosa_module.frames_to_time(
        np.arange(frame_count), sr=sample_rate, hop_length=hop_length
    )
    active = _activity_mask(
        signal,
        frame_count,
        frame_length,
        hop_length,
        activity_top_db,
    )
    segments = _build_segments(
        f0,
        voiced_flag,
        voiced_probability,
        active,
        frame_times,
        hop_length / sample_rate,
        duration_seconds,
        min_confidence=min_confidence,
        min_segment_seconds=min_segment_seconds,
        max_gap_frames=max_gap_frames,
    )
    return PitchAnalysisResult(
        sample_rate=sample_rate,
        duration_seconds=duration_seconds,
        notes=segments,
    )
