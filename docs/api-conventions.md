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

