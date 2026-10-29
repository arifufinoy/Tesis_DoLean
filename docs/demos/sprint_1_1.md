# Demo reproducible — Fase 1, bloque 1.1

Esta demo valida registro, autenticación, rotación de refresh token, cierre de sesión y recuperación de contraseña mediante Mailpit.

## 1. Levantar la actualización

```powershell
docker compose up --build -d
docker compose run --rm api alembic upgrade head
docker compose ps
```

La API debe estar disponible en `http://localhost:8000` y Mailpit en `http://localhost:8025`.

## 2. Registrar usuario

En Swagger (`http://localhost:8000/docs`), ejecutar `POST /api/v1/auth/register`:

```json
{
  "email": "demo@dolean.local",
  "password": "Seguro123!"
}
```

Resultado esperado: `201 Created`, rol `user` y un UUID.

En Postman, seleccionar `Body > raw > JSON` y confirmar que el encabezado sea `Content-Type: application/json`. No utilizar el modo `Text`.

## 3. Iniciar sesión

Ejecutar `POST /api/v1/auth/login`:

```json
{
  "email": "demo@dolean.local",
  "password": "Seguro123!"
}
```

Resultado esperado: `200 OK` con `access_token`, `refresh_token`, `token_type` y `expires_in`. El access token se utiliza como `Bearer` en los endpoints protegidos de los siguientes bloques.

## 4. Renovar y cerrar sesión

Enviar el refresh token a `POST /api/v1/auth/refresh`. El servidor rota el refresh token anterior y entrega un par nuevo.

Después, enviar el refresh token vigente a `POST /api/v1/auth/logout`. Resultado esperado: `204 No Content`. Reutilizar ese refresh token debe ser rechazado.

## 5. Recuperar contraseña

Ejecutar `POST /api/v1/auth/forgot-password`:

```json
{
  "email": "demo@dolean.local"
}
```

Abrir `http://localhost:8025` y verificar el mensaje recibido. El enlace incluye un token temporal de un solo uso.

## 6. Comprobaciones de seguridad

- Registrar el mismo correo devuelve `409 Conflict`.
- Credenciales incorrectas devuelven `401 Unauthorized`.
- Contraseñas menores de 8 caracteres devuelven `422 Unprocessable Entity`.
- El token de recuperación usado o expirado devuelve `400 Bad Request`.
- El sistema nunca devuelve la contraseña ni el token de recuperación en la respuesta HTTP.

