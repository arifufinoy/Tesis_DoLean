# Arquitectura inicial

DoLean usa una arquitectura por capas y una API versionada:

```text
Cliente web/móvil
      |
      v
FastAPI /api/v1  --->  Servicios de negocio (Sprints 1-3)
      |                         |
      v                         v
SQLAlchemy/Alembic         MinIO / Celery / Redis
      |
      v
PostgreSQL
```

En Sprint 0 solo están activos los endpoints de sistema y la configuración de Celery. Las capas futuras ya tienen un lugar definido para evitar mezclar HTTP, persistencia, almacenamiento y DSP.

- `app/api`: transporte HTTP, validación y contratos.
- `app/core`: configuración y preocupaciones transversales.
- `app/db`: engine, sesiones y metadata.
- `app/models`: entidades persistentes.
- `app/schemas`: modelos Pydantic de entrada y salida.
- `app/tasks`: aplicación Celery y configuración del broker.
- `alembic`: historial reproducible de cambios de PostgreSQL.

