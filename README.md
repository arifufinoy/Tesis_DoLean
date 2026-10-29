# DoLean Backend — Sprint 0

Backend inicial para el proyecto de titulación **Desarrollo de aplicación web y móvil para el análisis y corrección de afinación de audio monofónico mediante procesamiento digital de señales**.

Este repositorio contiene únicamente la Fase 0 / Sprint 0: ambiente reproducible, infraestructura local, modelo relacional inicial, migración, endpoints de salud y documentación base. Las funcionalidades de usuarios, proyectos, archivos y DSP se implementarán en los sprints siguientes.

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

Las pruebas del Sprint 0 no requieren PostgreSQL: validan que la aplicación cargue, que los endpoints de salud respondan y que OpenAPI esté disponible. La comprobación completa de infraestructura se realiza mediante Docker Compose y está descrita en `docs/demos/sprint_0.md`.

## Estructura

```text
app/
  api/v1/          Endpoints y router versionado
  core/            Configuración, logging y excepciones
  db/              Base declarativa, engine y sesiones
  models/          Modelo relacional inicial
  schemas/         Contratos Pydantic
  tasks/           Configuración base de Celery
alembic/           Migraciones de PostgreSQL
tests/             Pruebas del Sprint 0
docs/              Arquitectura, contratos y demo
```

## Seguridad y producción

`.env` no se versiona. Los puertos de PostgreSQL, Redis y MinIO están ligados a `127.0.0.1` solo para la demo local. En producción deben eliminarse esas publicaciones y las credenciales deben inyectarse mediante un gestor de secretos. El Sprint 0 no habilita todavía autenticación ni operaciones sobre recursos.

