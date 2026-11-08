import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.projects import ProjectCreateRequest


client = TestClient(app)


@pytest.mark.parametrize("path", ["/api/v1/users/me", "/api/v1/projects"])
def test_protected_phase1_resources_require_authentication(path: str) -> None:
    response = client.get(path)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "http_401"


def test_project_schema_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ProjectCreateRequest(name="Proyecto", unexpected="no permitido")


def test_phase1_routes_are_published_in_openapi() -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/users/me" in paths
    assert "/api/v1/users/me/password" in paths
    assert "/api/v1/projects" in paths
    assert "/api/v1/projects/{project_id}" in paths
