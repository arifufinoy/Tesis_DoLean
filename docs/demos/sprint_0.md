# Demo reproducible — Fase 0 / Sprint 0

## Objetivo

Levantar FastAPI, PostgreSQL, Redis, MinIO y Celery; ejecutar la migración inicial; comprobar los endpoints de salud y verificar las tablas previstas.

## 1. Preparación

Desde PowerShell, abrir la carpeta del proyecto y ejecutar:

```powershell
Copy-Item .env.example .env
docker version
docker compose version
```

Resultado esperado: Docker Desktop responde con sus versiones. Si Docker no responde, abrir Docker Desktop y esperar a que indique que el motor está en ejecución.

## 2. Arranque

```powershell
docker compose up --build -d
docker compose ps
```

Resultado esperado: `db`, `redis`, `minio`, `api` y `worker` aparecen creados. Los servicios de infraestructura deben alcanzar el estado `healthy`; API y worker pueden tardar unos segundos adicionales durante la primera construcción.

## 3. Migración desde cero

```powershell
docker compose run --rm api alembic upgrade head
docker compose run --rm api alembic current
```

Resultado esperado: la revisión activa es `0001_initial_schema`.

## 4. Comprobación de API y Swagger

```powershell
Invoke-RestMethod http://localhost:8000/health | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/ready | ConvertTo-Json
Start-Process http://localhost:8000/docs
```

Resultado esperado para `/health`: `status` igual a `ok`. Resultado esperado para `/ready`: `status` igual a `ready` y los checks `postgresql`, `redis` y `minio` iguales a `ok`. Swagger UI debe mostrar los cuatro endpoints de sistema.

## 5. Verificación de tablas

```powershell
docker compose exec db psql -U dolean -d dolean -c "\dt"
```

Resultado esperado: aparecen `users`, `profiles`, `projects`, `audio_files`, `analyses`, `note_segments`, `processing_jobs`, `correction_requests`, `processed_versions`, `recovery_tokens` y `alembic_version`.

## 6. Persistencia

```powershell
docker compose restart api worker
Invoke-RestMethod http://localhost:8000/ready | ConvertTo-Json
```

Resultado esperado: la API vuelve a estar lista y PostgreSQL/Redis/MinIO mantienen sus volúmenes. La persistencia de registros de negocio se demostrará con datos reales en Sprint 1.

## 7. Detención

```powershell
docker compose down
```

No usar `-v` si se desea conservar los datos. `docker compose down -v` elimina únicamente los volúmenes de este entorno de demostración.

