from pathlib import Path

import librosa
import numpy as np
import soundfile as sf


def correct_segments(source: Path, output: Path, edits: list[dict]) -> None:
    """Apply validated note shifts while preserving unselected audio."""
    signal, sample_rate = librosa.load(str(source), sr=None, mono=True)
    for edit in sorted(edits, key=lambda item: item["start_time"]):
        start = max(0, int(edit["start_time"] * sample_rate))
        end = min(len(signal), int(edit["end_time"] * sample_rate))
        if end <= start:
            raise ValueError("El segmento de corrección no tiene duración válida")
        segment = signal[start:end]
        shifted = librosa.effects.pitch_shift(segment, sr=sample_rate, n_steps=edit["n_steps"])
        size = min(len(segment), len(shifted))
        signal[start : start + size] = shifted[:size]
    sf.write(str(output), signal, sample_rate, subtype="PCM_16")
