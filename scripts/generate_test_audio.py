"""Generate copyright-free WAV fixtures for the Phase 2 demonstrations."""

import math
import os
import random
import wave
from pathlib import Path


SAMPLE_RATE = 44_100


def write_wav(path: Path, samples: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for sample in samples:
            clipped = max(-1.0, min(1.0, sample))
            frames.extend(int(clipped * 32767).to_bytes(2, byteorder="little", signed=True))
        wav_file.writeframes(frames)


def tone(frequency: float, seconds: float, amplitude: float = 0.5) -> list[float]:
    count = int(seconds * SAMPLE_RATE)
    fade = min(int(0.02 * SAMPLE_RATE), count // 2)
    samples: list[float] = []
    for index in range(count):
        envelope = 1.0
        if index < fade:
            envelope = index / max(fade, 1)
        elif index >= count - fade:
            envelope = (count - index - 1) / max(fade, 1)
        samples.append(amplitude * envelope * math.sin(2 * math.pi * frequency * index / SAMPLE_RATE))
    return samples


def silence(seconds: float) -> list[float]:
    return [0.0] * int(seconds * SAMPLE_RATE)


def noise(seconds: float) -> list[float]:
    generator = random.Random(20261103)
    return [0.25 * (generator.random() * 2 - 1) for _ in range(int(seconds * SAMPLE_RATE))]


def main() -> None:
    output = Path(os.getenv("DOLEAN_AUDIO_FIXTURES", "artifacts/audio-fixtures"))
    write_wav(output / "a4_440hz.wav", tone(440.0, 2.0))
    write_wav(output / "a4_detuned_432hz.wav", tone(432.0, 2.0))
    write_wav(output / "melody_three_notes.wav", tone(440.0, 1.0) + tone(523.25, 1.0) + tone(659.25, 1.0))
    write_wav(output / "a4_with_silences.wav", silence(0.5) + tone(440.0, 1.0) + silence(0.5))
    write_wav(output / "non_musical_noise.wav", noise(2.0))
    print(f"Archivos WAV generados en {output.resolve()}")


if __name__ == "__main__":
    main()
