# Auditoría de integración — frontend web

## Alcance

Repositorio revisado: `DoLean_Frontend` (Vite/React).

## Integrado correctamente

- Registro, login, refresh token y logout.
- Creación, listado, actualización y eliminación de proyectos.
- Carga, listado y descarga de audios.
- Persistencia de sesión en `sessionStorage`.
- Renovación de sesión programada mediante el refresh token.

## Hallazgo principal

La pantalla `src/pages/analysis/ui/AnalysisPage.jsx` utiliza `initialNotes`, `seedProjects` y datos locales. El propio código indica que el análisis real todavía será conectado al backend.

Por tanto, el gráfico, las métricas y la tabla de notas no representan actualmente el resultado de:

```text
POST /api/v1/audio-files/{audio_file_id}/analyses
GET  /api/v1/jobs/{job_id}
GET  /api/v1/analyses/{analysis_id}
GET  /api/v1/analyses/{analysis_id}/notes
```

## Pendientes críticos

### Análisis real

La página debe recibir el `analysis_id` real y consultar el backend hasta que el estado sea `completed` o `failed`. El piano roll debe utilizar los `note_id`, `start_time`, `end_time`, `detected_midi` y `deviation_cents` devueltos por la API.

### Corrección y exportación

No existen clientes para:

```text
POST /api/v1/audio-files/{audio_file_id}/corrections
GET  /api/v1/audio-files/{audio_file_id}/versions
GET  /api/v1/versions/{version_id}
GET  /api/v1/versions/{version_id}/download
```

La edición actual usa `noteRepository` y `localStorage`; modificar una nota en pantalla no genera un archivo corregido.

### Perfil

No se consumen:

```text
GET   /api/v1/users/me
PATCH /api/v1/users/me
PUT   /api/v1/users/me/password
```

## Corrección de configuración

Este frontend agrega `api/v1` dentro de sus rutas. Por ello debe configurarse:

```text
VITE_API_BASE_URL=http://localhost:8000
```

No debe incluir `/api/v1`, porque produciría rutas duplicadas.

## Orden de implementación recomendado

1. Reemplazar `initialNotes` por `GET /analyses/{analysis_id}`.
2. Implementar polling de `GET /jobs/{job_id}`.
3. Asociar cada bloque del piano roll con un `note_id` real.
4. Enviar `target_midi` desde la herramienta de edición.
5. Consultar y mostrar el historial de versiones.
6. Descargar y reproducir el WAV corregido.
7. Añadir comparación A/B y deshacer/rehacer respaldado por estado de edición.

## Estado

El frontend web integra autenticación, proyectos y archivos. El análisis y la corrección continúan siendo parcialmente demostrativos y deben conectarse a la API real.
