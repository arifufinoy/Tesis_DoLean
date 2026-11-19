# Auditoría de integración — aplicación móvil

## Alcance

Repositorio revisado: `DoLean` (Expo/React Native).

## Integrado correctamente

- Registro, login, refresh token, logout y recuperación de contraseña.
- CRUD de proyectos.
- Carga, listado, consulta, descarga y eliminación de audios.
- Inicio de análisis y consulta de resultados.
- Consulta de notas detectadas.
- Consulta de trabajos de procesamiento.
- Renovación automática del access token mediante interceptores de Axios.
- Grabación desde micrófono y carga como `multipart/form-data`.

## Pendientes críticos

### Corrección de afinación

No existen clientes para:

```text
POST /api/v1/audio-files/{audio_file_id}/corrections
GET  /api/v1/audio-files/{audio_file_id}/versions
GET  /api/v1/versions/{version_id}
GET  /api/v1/versions/{version_id}/download
```

La aplicación todavía no puede seleccionar una nota real, enviarla a una nota objetivo, esperar la corrección ni descargar la versión generada.

### Perfil

No se consumen:

```text
GET   /api/v1/users/me
PATCH /api/v1/users/me
PUT   /api/v1/users/me/password
```

### Flujo pendiente

1. Cargar audio.
2. Crear análisis.
3. Esperar `pending`/`processing` hasta `completed`.
4. Mostrar notas reales.
5. Seleccionar `note_id`.
6. Solicitar corrección con `target_midi`.
7. Consultar el nuevo `job_id`.
8. Listar versiones.
9. Descargar y reproducir la versión corregida.

## Mejoras técnicas

- Agregar clientes tipados para correcciones y versiones en `src/entities/audio/api/audio.api.ts`.
- Agregar rutas en `src/shared/config/endpoints.ts`.
- Mostrar el estado del trabajo de corrección con polling de 2 segundos.
- Mantener el `analysis_id`, `audio_file_id`, `note_id`, `job_id` y `version_id` en el estado de la pantalla, no solo en almacenamiento local.
- No establecer manualmente el header `Content-Type: multipart/form-data` en React Native; dejar que Axios genere el `boundary`.
- Añadir pruebas para corrección, versiones, errores de autorización y descarga.
- Configurar `EXPO_PUBLIC_API_URL` con `http://10.0.2.2:8000/api/v1` para Android Emulator y con la IP LAN para un dispositivo físico.

## Estado

La integración móvil cubre autenticación, proyectos, audio y análisis. Corrección, versiones y perfil todavía requieren implementación.
