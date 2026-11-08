# Convenciones de API

- Prefijo funcional: `/api/v1`.
- Identificadores: UUID.
- JSON: propiedades en `snake_case`.
- Fechas: ISO 8601 con zona horaria UTC.
- Documentación interactiva: `/docs`.
- Especificación: `/openapi.json` y copia inicial en `docs/openapi.yaml`.
- Error estándar:

```json
{
  "error": {
    "code": "validation_error",
    "message": "La solicitud no es válida.",
    "details": []
  }
}
```

Los endpoints de infraestructura `/health` y `/ready` también se publican en `/api/v1/health` y `/api/v1/ready` para facilitar el versionado del contrato.

Los endpoints de autenticación están disponibles bajo `/api/v1/auth`. Los access tokens se envían mediante `Authorization: Bearer <token>`. Los refresh tokens se almacenan únicamente como hash y se rotan al renovar la sesión.

Los endpoints de perfil utilizan `/api/v1/users/me` y solo operan sobre el usuario asociado al access token. Los proyectos se exponen bajo `/api/v1/projects`; todas las consultas, modificaciones y eliminaciones filtran por `owner_id`. Las listas usan `limit` y `offset` y responden con `items`, `total`, `limit` y `offset`.

La subfase 2.1 expone la carga como `multipart/form-data` usando el campo `upload`. El archivo original se conserva en MinIO y la representación normalizada se mantiene separada para el procesamiento DSP. Las rutas de audio vuelven a comprobar la propiedad del proyecto o archivo en cada operación.

Las subfases 2.2–2.4 exponen el análisis asíncrono. `POST /api/v1/audio-files/{audio_file_id}/analyses` devuelve `202` con `analysis_id` y `job_id`; el cliente consulta `GET /api/v1/jobs/{job_id}` hasta obtener `completed` o `failed`, y luego recupera el resultado mediante `GET /api/v1/analyses/{analysis_id}` o sus notas paginadas. El detector no envía matrices NumPy por Redis: el worker recupera la representación normalizada desde MinIO usando el identificador del audio.

