"""Demo reproducible de carga y análisis asíncrono de un audio."""

import os
import sys
import time
import uuid
from pathlib import Path

import httpx


BASE_URL = os.getenv("DOLEAN_API_URL", "http://localhost:8000").rstrip("/")
EMAIL = os.getenv("DOLEAN_DEMO_EMAIL")
PASSWORD = os.getenv("DOLEAN_DEMO_PASSWORD")
AUDIO_PATH = Path(os.getenv("DOLEAN_AUDIO_FILE", "artifacts/audio-fixtures/a4_440hz.wav"))


def ensure(response: httpx.Response, expected: int | tuple[int, ...], label: str) -> dict:
    expected_codes = (expected,) if isinstance(expected, int) else expected
    if response.status_code not in expected_codes:
        raise RuntimeError(f"{label}: HTTP {response.status_code}: {response.text}")
    return response.json() if response.content else {}


def register_or_login(client: httpx.Client, email: str, password: str) -> dict:
    registration = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    if registration.status_code not in (201, 409):
        ensure(registration, 201, "registro")
    return ensure(client.post("/api/v1/auth/login", json={"email": email, "password": password}), 200, "login")


def main() -> None:
    if not EMAIL or not PASSWORD:
        raise SystemExit("Define DOLEAN_DEMO_EMAIL y DOLEAN_DEMO_PASSWORD antes de ejecutar la demo.")
    if not AUDIO_PATH.exists():
        raise SystemExit(f"No existe el audio de prueba: {AUDIO_PATH}")

    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        ensure(client.get("/health"), 200, "health")
        tokens = register_or_login(client, EMAIL, PASSWORD)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        project = ensure(
            client.post(
                "/api/v1/projects",
                headers=headers,
                json={"name": f"Demo DSP {uuid.uuid4().hex[:8]}", "description": "Demo de análisis de afinación"},
            ),
            201,
            "crear proyecto",
        )
        print(f"1. Proyecto creado: {project['id']}")

        with AUDIO_PATH.open("rb") as audio:
            upload = ensure(
                client.post(
                    f"/api/v1/projects/{project['id']}/audio-files",
                    headers=headers,
                    files={"upload": (AUDIO_PATH.name, audio, "audio/wav")},
                ),
                201,
                "cargar audio",
            )
        print(f"2. Audio cargado: {upload['original_filename']} ({upload['duration_seconds']} s)")

        start = ensure(
            client.post(f"/api/v1/audio-files/{upload['id']}/analyses", headers=headers),
            202,
            "solicitar análisis",
        )
        print(f"3. Análisis solicitado: {start['analysis_id']} (job {start['job_id']})")

        job = {}
        for _ in range(60):
            job = ensure(client.get(f"{start['status_url']}", headers=headers), 200, "consultar trabajo")
            if job["status"] in {"completed", "failed"}:
                break
            time.sleep(1)
        if job.get("status") != "completed":
            raise RuntimeError(f"El análisis no terminó correctamente: {job}")
        analysis = ensure(client.get(start["analysis_url"], headers=headers), 200, "consultar análisis")
        notes = ensure(client.get(f"/api/v1/analyses/{start['analysis_id']}/notes", headers=headers), 200, "consultar notas")
        print(f"4. Trabajo completado: {job['status']}")
        print(f"5. Resultado persistido: {analysis['status']}, notas detectadas: {notes['total']}")
        if notes["items"]:
            note = notes["items"][0]
            print(
                f"6. Primera nota: {note['note_name']} | "
                f"{note['frequency_hz']:.2f} Hz | {note['deviation_cents']:.2f} cents | "
                f"confianza {note['confidence']:.2f}"
            )


if __name__ == "__main__":
    try:
        main()
    except (httpx.HTTPError, OSError) as exc:
        raise SystemExit(f"No se pudo completar la demo: {exc}") from exc
