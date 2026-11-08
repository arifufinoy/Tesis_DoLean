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

En la Fase 1 están activos los endpoints de autenticación, perfil y proyectos. La subfase 2.1 añade la carga autorizada de audio y el adaptador de MinIO. Las subfases 2.2–2.4 incorporan el motor DSP monofónico basado en pYIN, la persistencia de resultados y la ejecución asíncrona mediante Celery y Redis.

- `app/api`: transporte HTTP, validación y contratos.
- `app/core`: configuración y preocupaciones transversales.
- `app/db`: engine, sesiones y metadata.
- `app/models`: entidades persistentes.
- `app/schemas`: modelos Pydantic de entrada y salida.
- `app/tasks`: aplicación Celery y configuración del broker.
- `app/dsp`: lectura de señal, estimación F0, conversión de notas, cents y agrupación de segmentos.
- `alembic`: historial reproducible de cambios de PostgreSQL.

Las operaciones de proyectos filtran siempre por el usuario autenticado. La API responde `404` cuando el identificador no pertenece al usuario actual, evitando revelar la existencia de recursos ajenos.

