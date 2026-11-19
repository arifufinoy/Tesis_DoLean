# Endpoints actuales del backend DoLean

Base funcional:

```text
http://localhost:8000/api/v1
```

Salvo salud y autenticación, las rutas requieren:

```http
Authorization: Bearer <access_token>
```

## Sistema

| Método | Ruta | Descripción breve |
|---|---|---|
| GET | `/health` | Confirma que la API está viva. |
| GET | `/ready` | Comprueba PostgreSQL, Redis, MinIO y Mailpit. |
| GET | `/api/v1/health` | Comprobación de salud versionada. |
| GET | `/api/v1/ready` | Comprobación de dependencias versionada. |

## Autenticación

| Método | Ruta | Descripción breve |
|---|---|---|
| POST | `/auth/register` | Registra un usuario y su perfil inicial. |
| POST | `/auth/login` | Valida credenciales y devuelve access/refresh token. |
| POST | `/auth/refresh` | Rota el refresh token y entrega una nueva sesión. |
| POST | `/auth/logout` | Revoca la sesión asociada al refresh token. |
| POST | `/auth/forgot-password` | Genera un token temporal y envía recuperación a Mailpit/SMTP. |
| POST | `/auth/reset-password` | Consume el token de recuperación y cambia la contraseña. |

## Perfil

| Método | Ruta | Descripción breve |
|---|---|---|
| GET | `/users/me` | Consulta el perfil del usuario autenticado. |
| PATCH | `/users/me` | Actualiza nombre visible y biografía. |
| PUT | `/users/me/password` | Cambia la contraseña verificando la actual. |

## Proyectos

| Método | Ruta | Descripción breve |
|---|---|---|
| POST | `/projects` | Crea un proyecto propio. |
| GET | `/projects` | Lista los proyectos del usuario. |
| GET | `/projects/{project_id}` | Consulta un proyecto propio. |
| PATCH | `/projects/{project_id}` | Actualiza nombre y descripción. |
| DELETE | `/projects/{project_id}` | Elimina un proyecto propio y sus recursos dependientes. |

## Archivos de audio

| Método | Ruta | Descripción breve |
|---|---|---|
| POST | `/projects/{project_id}/audio-files` | Carga y normaliza un WAV/MP3 autorizado. |
| GET | `/projects/{project_id}/audio-files` | Lista los audios del proyecto. |
| GET | `/audio-files/{audio_file_id}` | Consulta metadatos de un audio. |
| GET | `/audio-files/{audio_file_id}/download` | Descarga el audio original autorizado. |
| DELETE | `/audio-files/{audio_file_id}` | Elimina el audio y sus objetos de MinIO. |

## Análisis

| Método | Ruta | Descripción breve |
|---|---|---|
| POST | `/audio-files/{audio_file_id}/analyses` | Encola un análisis DSP asíncrono. |
| GET | `/analyses/{analysis_id}` | Consulta estado, metadatos y notas detectadas. |
| GET | `/analyses/{analysis_id}/notes` | Lista las notas con paginación. |
| GET | `/jobs/{job_id}` | Consulta el estado de un trabajo Celery. |

## Corrección y versiones

| Método | Ruta | Descripción breve |
|---|---|---|
| POST | `/audio-files/{audio_file_id}/corrections` | Encola una corrección de notas seleccionadas. |
| GET | `/audio-files/{audio_file_id}/versions` | Lista versiones corregidas del audio. |
| GET | `/versions/{version_id}` | Consulta metadatos de una versión. |
| GET | `/versions/{version_id}/download` | Descarga el WAV corregido. |

## Flujo principal

```text
login
  → crear proyecto
  → cargar audio
  → iniciar análisis
  → consultar job
  → consultar notas
  → solicitar corrección
  → consultar job de corrección
  → listar versión
  → descargar WAV corregido
```

La documentación viva se encuentra en `http://localhost:8000/docs` y `http://localhost:8000/openapi.json`.
