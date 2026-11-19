import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings


class AudioValidationError(ValueError):
    def __init__(self, message: str, status_code: int = 422, code: str = "audio_invalid") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code


class AudioToolError(RuntimeError):
    pass


@dataclass(frozen=True)
class AudioMetadata:
    duration_seconds: float
    sample_rate: int
    channels: int
    codec_name: str
    format_name: str


ALLOWED_EXTENSIONS = {".wav", ".mp3"}
ALLOWED_CONTENT_TYPES = {"audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3", "application/octet-stream"}


def safe_filename(filename: str | None) -> str:
    # Upload clients may send Windows paths even when the API runs on Linux.
    # Normalize separators before taking the basename to avoid persisting
    # client-side directory components.
    raw_name = (filename or "audio").replace("\\", "/")
    name = Path(raw_name).name.strip()
    if not name or name in {".", ".."}:
        raise AudioValidationError("El archivo debe tener un nombre válido")
    if len(name) > 255:
        raise AudioValidationError("El nombre del archivo es demasiado largo")
    return name


def inspect_audio(path: Path, filename: str | None, content_type: str | None) -> AudioMetadata:
    safe_name = safe_filename(filename)
    extension = Path(safe_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise AudioValidationError("Solo se admiten archivos WAV o MP3", status_code=415, code="unsupported_audio_format")
    if content_type and content_type.lower() not in ALLOWED_CONTENT_TYPES:
        raise AudioValidationError("El tipo de contenido no corresponde a un audio admitido", status_code=415, code="unsupported_audio_format")
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise AudioValidationError("No se pudo leer el archivo recibido") from exc
    if size == 0:
        raise AudioValidationError("El archivo de audio está vacío")
    if size > settings.audio_max_size_bytes:
        raise AudioValidationError("El archivo supera el tamaño máximo permitido", status_code=413, code="audio_too_large")

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=format_name,duration:stream=codec_name,codec_type,sample_rate,channels,duration",
                "-of",
                "json",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise AudioToolError("FFprobe no está instalado en el contenedor") from exc
    except subprocess.TimeoutExpired as exc:
        raise AudioValidationError("La inspección del audio superó el tiempo permitido") from exc
    if result.returncode != 0:
        raise AudioValidationError("El archivo no contiene un audio decodificable")
    try:
        probe = json.loads(result.stdout)
        audio_stream = next(stream for stream in probe.get("streams", []) if stream.get("codec_type") == "audio")
        duration = float(probe.get("format", {}).get("duration") or audio_stream.get("duration") or 0)
        sample_rate = int(audio_stream.get("sample_rate") or 0)
        channels = int(audio_stream.get("channels") or 0)
        codec_name = str(audio_stream.get("codec_name") or "unknown")
        format_name = str(probe.get("format", {}).get("format_name") or "")
    except (KeyError, StopIteration, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise AudioValidationError("No se pudieron obtener los metadatos del audio") from exc

    formats = {item.strip().lower() for item in format_name.split(",")}
    if not formats.intersection({"wav", "mp3"}):
        raise AudioValidationError("El contenedor de audio no está admitido", status_code=415, code="unsupported_audio_format")
    if duration <= 0:
        raise AudioValidationError("La duración del audio no es válida")
    if duration > settings.audio_max_duration_seconds:
        raise AudioValidationError("La duración supera el máximo permitido", status_code=413, code="audio_too_long")
    if sample_rate <= 0 or channels <= 0:
        raise AudioValidationError("Los metadatos técnicos del audio no son válidos")
    return AudioMetadata(duration, sample_rate, channels, codec_name, format_name)


def normalize_audio(source: Path, output: Path) -> None:
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(source),
                "-map",
                "0:a:0",
                "-ac",
                "1",
                "-ar",
                str(settings.audio_normalized_sample_rate),
                "-sample_fmt",
                "s16",
                str(output),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError as exc:
        raise AudioToolError("FFmpeg no está instalado en el contenedor") from exc
    except subprocess.TimeoutExpired as exc:
        raise AudioToolError("La normalización del audio superó el tiempo permitido") from exc
    if result.returncode != 0 or not output.exists() or output.stat().st_size == 0:
        raise AudioValidationError("No se pudo convertir el audio a la representación interna")
