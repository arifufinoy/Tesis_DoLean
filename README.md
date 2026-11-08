# DoLean Backend — Fase 1 / Sprint 1

Backend inicial para el proyecto de titulación **Desarrollo de aplicación web y móvil para el análisis y corrección de afinación de audio monofónico mediante procesamiento digital de señales**.

Este repositorio contiene la base reproducible de la Fase 0, la Fase 1 completa y la gestión, análisis DSP y procesamiento asíncrono iniciales de la Fase 2.

El bloque inicial de Fase 1 (1.1) añade registro, login, JWT, refresh token con rotación, logout y recuperación de contraseña mediante Mailpit.

## Requisitos

- Windows 10/11.
- Docker Desktop con Docker Compose habilitado.
- Git.
- Opcional para pruebas locales sin Docker: Python 3.11.

## Inicio rápido con Docker Desktop

En PowerShell, desde esta carpeta:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose ps
```

Ejecuta la migración inicial:

```powershell
docker compose run --rm api alembic upgrade head
```

Comprueba la API:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
```

Abre Swagger UI en [http://localhost:8000/docs](http://localhost:8000/docs). La consola de MinIO está en [http://localhost:9001](http://localhost:9001) y Mailpit en [http://localhost:8025](http://localhost:8025), únicamente para desarrollo local.

Para detener los contenedores conservando los datos:

```powershell
docker compose down
```

Para eliminar también los volúmenes locales de este entorno de demostración:

```powershell
docker compose down -v
```

## Pruebas

Con Python local:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest
```

Las pruebas unitarias de contrato no requieren PostgreSQL; validan seguridad, rutas protegidas y disponibilidad de OpenAPI. La demo funcional completa de perfiles y proyectos se ejecuta dentro de Docker Compose y está descrita en `docs/demos/sprint_1.md`.

## Estructura

```text
app/
  api/v1/          Endpoints y router versionado
  core/            Configuración, logging y excepciones
  db/              Base declarativa, engine y sesiones
  models/          Modelo relacional inicial
  schemas/         Contratos Pydantic
  tasks/           Tareas Celery de procesamiento asíncrono
  dsp/             Detección de F0, notas, cents y segmentos
alembic/           Migraciones de PostgreSQL
tests/             Pruebas unitarias, funcionales e integración
docs/              Arquitectura, contratos y demo
```

## Fase 1: administrador, perfil y proyectos

Crear o promover una cuenta administrativa sin guardar credenciales en el código:

```powershell
docker compose run --rm -e DOLEAN_ADMIN_EMAIL=admin@dolean.dev -e DOLEAN_ADMIN_PASSWORD="Cambiar123!" api python scripts/create_admin.py
```

La contraseña se proporciona únicamente en tiempo de ejecución. El rol administrador queda preparado para futuras funciones de gestión; no se incluye todavía un panel administrativo.

Ejecutar la demo completa de la Fase 1 desde la red interna de Compose:

```powershell
docker compose run --rm -e DOLEAN_DEMO_EMAIL=demo1@dolean.dev -e DOLEAN_DEMO_PASSWORD="Seguro123!" -e DOLEAN_API_URL=http://api:8000 api python scripts/demo_sprint_1.py
```

Las rutas protegidas disponibles son `GET/PATCH /api/v1/users/me`, `PUT /api/v1/users/me/password` y el CRUD de `/api/v1/projects`. La propiedad se verifica por `owner_id`; un usuario no puede consultar ni modificar proyectos ajenos.

## Fase 2: análisis de afinación

Reconstruir API y worker después de actualizar el código y aplicar las migraciones:

```powershell
docker compose up --build -d api worker
docker compose run --rm api alembic upgrade head
```

Ejecutar la demo completa con un WAV sintético:

```powershell
python scripts/generate_test_audio.py
$env:DOLEAN_DEMO_EMAIL="demo2@dolean.dev"
$env:DOLEAN_DEMO_PASSWORD="Seguro123!"
$env:DOLEAN_AUDIO_FILE="artifacts/audio-fixtures/a4_440hz.wav"
python scripts/demo_sprint_2.py
```

Las rutas nuevas son `POST /api/v1/audio-files/{audio_file_id}/analyses`, `GET /api/v1/analyses/{analysis_id}`, `GET /api/v1/analyses/{analysis_id}/notes` y `GET /api/v1/jobs/{job_id}`. Swagger las documenta automáticamente en `/docs`.

## Seguridad y producción

`.env` no se versiona. Los puertos de PostgreSQL, Redis y MinIO están ligados a `127.0.0.1` solo para la demo local. En producción deben eliminarse esas publicaciones y las credenciales deben inyectarse mediante un gestor de secretos. Las contraseñas se almacenan con Argon2, los refresh tokens se almacenan como hash y los endpoints de recursos requieren un access token válido.

