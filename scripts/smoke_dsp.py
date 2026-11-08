"""Ejecuta una comprobación real del detector DSP con una fixture sintética."""

import json
import os
from pathlib import Path

from app.dsp.pitch import analyze_pitch


def main() -> None:
    fixtures_dir = Path(os.getenv("DOLEAN_AUDIO_FIXTURES", "artifacts/audio-fixtures"))
    audio_path = fixtures_dir / "a4_440hz.wav"
    if not audio_path.exists():
        raise SystemExit(f"No existe la fixture: {audio_path}")

    result = analyze_pitch(audio_path)
    print(
        json.dumps(
            {
                "audio": str(audio_path),
                "sample_rate": result.sample_rate,
                "duration_seconds": result.duration_seconds,
                "notes": [note.__dict__ for note in result.notes],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
