from pathlib import Path

import numpy as np
import pytest

from app.dsp.pitch import analyze_pitch, frequency_to_pitch, midi_to_note_name


def test_frequency_to_pitch_reports_a4_without_deviation() -> None:
    midi, nearest_midi, note_name, deviation = frequency_to_pitch(440.0)

    assert midi == pytest.approx(69.0)
    assert nearest_midi == 69
    assert note_name == "A4"
    assert deviation == pytest.approx(0.0)


def test_frequency_to_pitch_reports_detuning_in_cents() -> None:
    _, nearest_midi, note_name, deviation = frequency_to_pitch(432.0)

    assert nearest_midi == 69
    assert note_name == "A4"
    assert deviation == pytest.approx(-31.7666, abs=0.01)


def test_midi_note_name_uses_scientific_pitch_notation() -> None:
    assert midi_to_note_name(60) == "C4"
    assert midi_to_note_name(69) == "A4"


def test_analyze_pitch_detects_generated_a4(tmp_path: Path) -> None:
    librosa = pytest.importorskip("librosa")
    soundfile = pytest.importorskip("soundfile")
    sample_rate = 44_100
    duration = 1.5
    time = np.arange(int(sample_rate * duration)) / sample_rate
    signal = 0.5 * np.sin(2 * np.pi * 440.0 * time).astype(np.float32)
    audio_path = tmp_path / "a4.wav"
    soundfile.write(audio_path, signal, sample_rate)

    result = analyze_pitch(
        audio_path,
        min_confidence=0.5,
        min_segment_seconds=0.2,
        fmin_hz=librosa.note_to_hz("C3"),
        fmax_hz=librosa.note_to_hz("C6"),
    )

    assert result.sample_rate == sample_rate
    assert result.duration_seconds == pytest.approx(duration, abs=1 / sample_rate)
    assert result.notes
    assert result.notes[0].note_name == "A4"
    assert result.notes[0].frequency_hz == pytest.approx(440.0, abs=2.0)
    assert result.notes[0].deviation_cents == pytest.approx(0.0, abs=8.0)
