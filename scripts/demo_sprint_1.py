"""Run the reproducible Phase 1 demo against a running local API."""

import os
import sys
import time
import uuid

import httpx


BASE_URL = os.getenv("DOLEAN_API_URL", "http://localhost:8000").rstrip("/")
EMAIL = os.getenv("DOLEAN_DEMO_EMAIL")
PASSWORD = os.getenv("DOLEAN_DEMO_PASSWORD")


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
    if len(PASSWORD) < 8:
        raise SystemExit("DOLEAN_DEMO_PASSWORD debe tener al menos 8 caracteres.")

    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        ensure(client.get("/health"), 200, "health")
        tokens = register_or_login(client, EMAIL, PASSWORD)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        profile = ensure(client.get("/api/v1/users/me", headers=headers), 200, "consultar perfil")
        print(f"1. Perfil consultado: {profile['email']}")

        updated = ensure(
            client.patch(
                "/api/v1/users/me",
                headers=headers,
                json={"display_name": "Demo DoLean", "bio": "Perfil de demostración de la Fase 1"},
            ),
            200,
            "actualizar perfil",
        )
        print(f"2. Perfil actualizado: {updated['display_name']}")

        project = ensure(
            client.post(
                "/api/v1/projects",
                headers=headers,
                json={"name": f"Proyecto demo {uuid.uuid4().hex[:8]}", "description": "Proyecto musical de prueba"},
            ),
            201,
            "crear proyecto",
        )
        project_id = project["id"]
        print(f"3. Proyecto creado: {project_id}")
        ensure(client.get("/api/v1/projects", headers=headers), 200, "listar proyectos")
        ensure(
            client.patch(f"/api/v1/projects/{project_id}", headers=headers, json={"name": "Proyecto demo actualizado"}),
            200,
            "actualizar proyecto",
        )
        print("4. Proyecto consultado y actualizado")

        other_email = f"{EMAIL.split('@')[0]}+owner-{int(time.time())}@{EMAIL.split('@', 1)[1]}"
        other_tokens = register_or_login(client, other_email, PASSWORD)
        foreign = client.get(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {other_tokens['access_token']}"},
        )
        ensure(foreign, 404, "acceso a proyecto ajeno")
        print("5. Acceso a proyecto ajeno rechazado: 404")

        rotated = ensure(
            client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}),
            200,
            "renovar sesión",
        )
        ensure(client.post("/api/v1/auth/logout", json={"refresh_token": rotated["refresh_token"]}), 204, "logout")
        print("6. Renovación y cierre de sesión comprobados")


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPError as exc:
        raise SystemExit(f"No se pudo conectar con {BASE_URL}: {exc}") from exc
