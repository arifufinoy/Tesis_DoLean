from pathlib import Path

import pytest

from app.services.audio import AudioValidationError, safe_filename


def test_safe_filename_removes_client_path_components() -> None:
    assert safe_filename(r"C:\fake\recording.wav") == "recording.wav"


def test_safe_filename_rejects_empty_name() -> None:
    with pytest.raises(AudioValidationError):
        safe_filename("..")


def test_audio_validation_rejects_unsupported_extension(tmp_path: Path) -> None:
    from app.services.audio import inspect_audio

    path = tmp_path / "recording.txt"
    path.write_text("not audio", encoding="utf-8")
    with pytest.raises(AudioValidationError) as error:
        inspect_audio(path, path.name, "text/plain")
    assert error.value.status_code == 415
