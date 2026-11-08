# Demo reproducible — Fase 1 / Sprint 1

Esta demostración valida el criterio de finalización de la Fase 1: registro, autenticación, perfil, proyectos, autorización por propiedad y persistencia.

## Preparación

```powershell
docker compose up --build -d
docker compose run --rm api alembic upgrade head
docker compose ps
```

## Demo automática

La contraseña se entrega mediante una variable temporal; no se encuentra escrita en el repositorio.

```powershell
docker compose run --rm `
  -e DOLEAN_DEMO_EMAIL=demo1@dolean.dev `
  -e DOLEAN_DEMO_PASSWORD="Seguro123!" `
  -e DOLEAN_API_URL=http://api:8000 `
  api python scripts/demo_sprint_1.py
```

El script comprueba:

1. Salud de la API y login.
2. Consulta y actualización del perfil autenticado.
3. Creación, listado y actualización de un proyecto.
4. Rechazo `404` al intentar consultar el proyecto con otro usuario.
5. Rotación del refresh token y cierre de sesión.

## Demo manual en Swagger

1. Abrir `http://localhost:8000/docs`.
2. Ejecutar `POST /api/v1/auth/login`.
3. Pulsar `Authorize`, pegar el `access_token` y confirmar.
4. Ejecutar `GET /api/v1/users/me`.
5. Ejecutar `PATCH /api/v1/users/me` con:

```json
{
  "display_name": "Demo DoLean",
  "bio": "Perfil de demostración"
}
```

6. Crear un proyecto con `POST /api/v1/projects`:

```json
{
  "name": "Mi primer proyecto musical",
  "description": "Proyecto de prueba para la tesis"
}
```

7. Consultarlo con `GET /api/v1/projects/{project_id}` y modificarlo con `PATCH`.
8. Usar otro usuario para solicitar el mismo identificador. La respuesta esperada es `404 Proyecto no encontrado`.

## Cuenta administrativa

```powershell
docker compose run --rm `
  -e DOLEAN_ADMIN_EMAIL=admin@dolean.dev `
  -e DOLEAN_ADMIN_PASSWORD="Cambiar123!" `
  api python scripts/create_admin.py
```

El comando crea o promueve el usuario a `admin`. No existe panel administrativo en esta fase.

## Recuperación de contraseña

Ejecutar `POST /api/v1/auth/forgot-password` y abrir `http://localhost:8025`. El correo de desarrollo se visualiza en Mailpit; el token es temporal y de un solo uso.

## Resultado esperado

- `GET /api/v1/users/me`: `200 OK`.
- `PATCH /api/v1/users/me`: `200 OK`.
- `POST /api/v1/projects`: `201 Created`.
- `GET/PATCH /api/v1/projects/{project_id}` del propietario: `200 OK`.
- Acceso con otro usuario: `404 Not Found`.
- `DELETE /api/v1/projects/{project_id}`: `204 No Content`.
