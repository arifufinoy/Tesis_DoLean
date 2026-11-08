# DoLean Backend — API de análisis y corrección de afinación

Backend del proyecto de titulación **Desarrollo de aplicación web y móvil para el análisis y corrección de afinación de audio monofónico mediante procesamiento digital de señales**.

Este repositorio contiene la base reproducible de la Fase 0, la Fase 1 completa y la gestión, análisis DSP y procesamiento asíncrono iniciales de la Fase 2.

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

Las pruebas unitarias de contrato no requieren PostgreSQL; validan seguridad, rutas protegidas y disponibilidad de OpenAPI. La demo funcional completa de perfiles y proyectos se ejecuta dentro de Docker Compose y está descrita en `docs/demos/sprint_1.md`.

## Estructura

```text
app/
  api/v1/          Endpoints y router versionado
  core/            Configuración, logging y excepciones
  db/              Base declarativa, engine y sesiones
  models/          Modelo relacional inicial
  schemas/         Contratos Pydantic
  tasks/           Tareas Celery de procesamiento asíncrono
  dsp/             Detección de F0, notas, cents y segmentos
alembic/           Migraciones de PostgreSQL
tests/             Pruebas unitarias, funcionales e integración
docs/              Arquitectura, contratos y demo
```

## Fase 1: administrador, perfil y proyectos

Crear o promover una cuenta administrativa sin guardar credenciales en el código:

```powershell
docker compose run --rm -e DOLEAN_ADMIN_EMAIL=admin@dolean.dev -e DOLEAN_ADMIN_PASSWORD="Cambiar123!" api python scripts/create_admin.py
```

La contraseña se proporciona únicamente en tiempo de ejecución. El rol administrador queda preparado para futuras funciones de gestión; no se incluye todavía un panel administrativo.

Ejecutar la demo completa de la Fase 1 desde la red interna de Compose:

```powershell
docker compose run --rm -e DOLEAN_DEMO_EMAIL=demo1@dolean.dev -e DOLEAN_DEMO_PASSWORD="Seguro123!" -e DOLEAN_API_URL=http://api:8000 api python scripts/demo_sprint_1.py
```

Las rutas protegidas disponibles son `GET/PATCH /api/v1/users/me`, `PUT /api/v1/users/me/password` y el CRUD de `/api/v1/projects`. La propiedad se verifica por `owner_id`; un usuario no puede consultar ni modificar proyectos ajenos.

## Fase 2: análisis de afinación

Reconstruir API y worker después de actualizar el código y aplicar las migraciones:

```powershell
docker compose up --build -d api worker
docker compose run --rm api alembic upgrade head
```

Ejecutar la demo completa con un WAV sintético:

```powershell
python scripts/generate_test_audio.py
$env:DOLEAN_DEMO_EMAIL="demo2@dolean.dev"
$env:DOLEAN_DEMO_PASSWORD="Seguro123!"
$env:DOLEAN_AUDIO_FILE="artifacts/audio-fixtures/a4_440hz.wav"
python scripts/demo_sprint_2.py
```

Las rutas nuevas son `POST /api/v1/audio-files/{audio_file_id}/analyses`, `GET /api/v1/analyses/{analysis_id}`, `GET /api/v1/analyses/{analysis_id}/notes` y `GET /api/v1/jobs/{job_id}`. Swagger las documenta automáticamente en `/docs`.

## Integración de clientes: frontend web y aplicación móvil

Esta sección describe cómo consumir la API desde el frontend web y desde la aplicación móvil. La fuente de verdad del contrato es la interfaz Swagger en `/docs` y la especificación viva en `/openapi.json`; `docs/openapi.yaml` es una copia resumida de referencia. Para las rutas de análisis y trabajos, consulta siempre la especificación viva.

### 1. URL base y entornos

Todas las rutas funcionales llevan el prefijo `/api/v1`. Los identificadores son UUID, las propiedades JSON usan `snake_case` y las fechas son ISO 8601 en UTC.

| Cliente | URL base en desarrollo |
| --- | --- |
| Web en el mismo equipo | `http://localhost:8000/api/v1` |
| Emulador Android (AVD) | `http://10.0.2.2:8000/api/v1` |
| Emulador Genymotion | `http://10.0.3.2:8000/api/v1` |
| Simulador iOS | `http://127.0.0.1:8000/api/v1` |
| Dispositivo físico en la misma red | `http://<IP_LAN_DEL_EQUIPO>:8000/api/v1` |
| Producción | `https://<dominio-de-la-api>/api/v1` |

Los endpoints de infraestructura también existen fuera del prefijo: `GET /health` y `GET /ready`, además de sus equivalentes `GET /api/v1/health` y `GET /api/v1/ready`. Se recomienda usar la API versionada para las comprobaciones del cliente.

En el frontend web, configura la URL por entorno (`VITE_API_BASE_URL`, `NEXT_PUBLIC_API_BASE_URL` o equivalente) y no la escribas directamente en los componentes. En móvil usa una constante de configuración por sabor/entorno (`dev`, `staging`, `prod`).

### 2. CORS y red

El backend permite CORS únicamente sobre los orígenes declarados en `CORS_ORIGINS` (separados por coma). El valor por defecto es:

```text
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

Añade el origen exacto del frontend (incluido esquema y puerto) y reinicia el servicio `api`. No uses `*` si se habilitan credenciales. Las apps móviles nativas no están sujetas a CORS (una WebView sí lo está), pero necesitan permiso de red y, en desarrollo, permiso para usar HTTP sin TLS.

Para un dispositivo físico, el teléfono debe estar en la misma red que el equipo, el puerto `8000` debe estar accesible y el firewall de Windows debe permitir la conexión. No uses `localhost` desde un dispositivo físico: ese nombre apunta al propio teléfono.

### 3. Autenticación y sesión

El flujo es:

1. `POST /auth/register` crea la cuenta y devuelve el usuario. No emite tokens.
2. `POST /auth/login` devuelve `access_token`, `refresh_token`, `token_type: "bearer"` y `expires_in` (900 segundos por defecto).
3. Envía el access token en cada petición protegida:

```http
Authorization: Bearer <access_token>
```

4. Cuando una petición protegida responda `401`, renueva una sola vez con `POST /auth/refresh` enviando el refresh token y repite la petición original.
5. Al cerrar sesión, llama a `POST /auth/logout` con el refresh token y elimina ambos tokens del cliente.

```http
POST /api/v1/auth/login
Content-Type: application/json
```

```json
{
  "email": "estudiante@dolean.dev",
  "password": "Seguro123!"
}
```

```http
200 OK
Content-Type: application/json
```

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 900
}
```

Consideraciones importantes:

- El access token dura 15 minutos y el refresh token 30 días por defecto.
- El refresh token rota en cada renovación: el anterior queda revocado. Si dos peticiones intentan refrescar a la vez con el mismo token, una fallará. Implementa una promesa o mutex compartido para que solo haya una renovación en curso.
- El logout revoca el refresh token enviado, no el access token, que sigue siendo válido hasta expirar. Descartar el access token en el cliente es obligatorio.
- `PUT /users/me/password` y `POST /auth/reset-password` revocan todas las sesiones del usuario. Tras cambiar o restablecer la contraseña hay que iniciar sesión de nuevo.
- `POST /auth/forgot-password` siempre responde `202` para no revelar si el correo existe. En desarrollo, el enlace se puede leer en Mailpit (`http://localhost:8025`) y contiene `?token=...`; el token es de un solo uso y expira en 30 minutos.
- `PASSWORD_RESET_URL` define la URL del enlace del correo. En web debe apuntar a la pantalla que lee `token` de la query string. Para móvil, apunta a una página web que redirija a la app mediante deep link/universal link, o usa HTTPS con App Links/Universal Links.
- No registres tokens ni contraseñas en logs, analítica o reportes de errores.

Almacenamiento recomendado:

- **Web:** access token en memoria y refresh token en `sessionStorage` o almacenamiento seguro equivalente, con CSP estricta y protección contra XSS. `localStorage` es aceptable solo como decisión consciente; la opción ideal a futuro es una cookie `HttpOnly` emitida por un BFF.
- **Móvil:** Keychain en iOS y Keystore en Android mediante `flutter_secure_storage`, `react-native-keychain` o `expo-secure-store`. No uses `AsyncStorage` ni preferencias planas para el refresh token.

### 4. Referencia de endpoints

Todas las rutas de la tabla se anteponen a la URL base. Salvo los endpoints de autenticación y salud, requieren `Authorization: Bearer <access_token>`. Los recursos están aislados por propietario: consultar o modificar un proyecto o audio ajeno responde `404`, igual que un identificador inexistente.

| Método | Ruta | Éxito | Descripción |
| --- | --- | --- | --- |
| POST | `/auth/register` | `201` | Registrar usuario con `email` y `password`. |
| POST | `/auth/login` | `200` | Iniciar sesión y obtener tokens. |
| POST | `/auth/refresh` | `200` | Rotar tokens con `refresh_token`. |
| POST | `/auth/logout` | `204` | Revocar el refresh token enviado. |
| POST | `/auth/forgot-password` | `202` | Solicitar enlace de recuperación. |
| POST | `/auth/reset-password` | `200` | Restablecer con `token` y `new_password`. |
| GET | `/users/me` | `200` | Perfil del usuario autenticado. |
| PATCH | `/users/me` | `200` | Actualizar `display_name` y/o `bio`. |
| PUT | `/users/me/password` | `204` | Cambiar contraseña con `current_password` y `new_password`. |
| POST | `/projects` | `201` | Crear proyecto con `name` y `description`. |
| GET | `/projects` | `200` | Listar proyectos propios con paginación. |
| GET | `/projects/{project_id}` | `200` | Consultar un proyecto propio. |
| PATCH | `/projects/{project_id}` | `200` | Actualizar nombre y/o descripción. |
| DELETE | `/projects/{project_id}` | `204` | Eliminar un proyecto propio. |
| POST | `/projects/{project_id}/audio-files` | `201` | Subir WAV o MP3 como `multipart/form-data`. |
| GET | `/projects/{project_id}/audio-files` | `200` | Listar audios del proyecto. |
| GET | `/audio-files/{audio_file_id}` | `200` | Consultar metadatos del audio. |
| DELETE | `/audio-files/{audio_file_id}` | `204` | Eliminar audio y sus objetos almacenados. |
| GET | `/audio-files/{audio_file_id}/download` | `200` | Descargar el archivo original (binario). |
| POST | `/audio-files/{audio_file_id}/analyses` | `202` | Encolar análisis de afinación. |
| GET | `/analyses/{analysis_id}` | `200` | Consultar análisis y sus notas. |
| GET | `/analyses/{analysis_id}/notes` | `200` | Listar notas detectadas con paginación. |
| GET | `/jobs/{job_id}` | `200` | Consultar estado del trabajo asíncrono. |

Paginación:

- Proyectos y audios: `limit` entre 1 y 100 (por defecto 20) y `offset` mayor o igual que 0. Se ordenan del más reciente al más antiguo.
- Notas: `limit` entre 1 y 500 (por defecto 100) y `offset` mayor o igual que 0. Se ordenan por `segment_index` ascendente.
- Las respuestas de lista tienen la forma `{ "items": [...], "total": n, "limit": n, "offset": n }`. La lista de notas añade `analysis_id`.

Los `PATCH` exigen al menos un campo y rechazan campos desconocidos con `422`. El perfil devuelve `id`, `user_id`, `email`, `role`, `is_active`, `display_name`, `bio`, `created_at` y `updated_at`.

### 5. Carga de audio

La carga usa `multipart/form-data` con el campo obligatorio `upload`:

```http
POST /api/v1/projects/{project_id}/audio-files
Authorization: Bearer <access_token>
Content-Type: multipart/form-data; boundary=...
```

Restricciones del servidor:

- Formatos: `.wav` y `.mp3`, con contenido `audio/wav`, `audio/x-wav`, `audio/mpeg`, `audio/mp3` o `application/octet-stream`.
- Tamaño máximo: 50 MB.
- Duración máxima: 3 minutos.
- El servidor valida con FFprobe, normaliza a WAV mono 44.1 kHz para el DSP y guarda el original por separado.
- La respuesta `201` devuelve los metadatos (`id`, `project_id`, `original_filename`, `size_bytes`, `duration_seconds`, `sample_rate`, `channels`, `normalized_sample_rate`, `normalized_channels`, etc.). No devuelve una URL pública; la descarga pasa por el endpoint autenticado.
- La descarga devuelve el archivo **original**, no la versión normalizada.

Errores esperados: `404` si el proyecto no pertenece al usuario, `413` por tamaño o duración, `415` por formato no admitido, `422` si el archivo no es decodificable y `503` si FFmpeg, MinIO o la base de datos no están disponibles.

### 6. Flujo de análisis asíncrono

1. Sube el audio y guarda `audio_file_id`.
2. Solicita el análisis:

```http
POST /api/v1/audio-files/{audio_file_id}/analyses
```

```http
202 Accepted
Content-Type: application/json
```

```json
{
  "analysis_id": "<uuid>",
  "job_id": "<uuid>",
  "status": "pending",
  "analysis_url": "/api/v1/analyses/<uuid>",
  "status_url": "/api/v1/jobs/<uuid>"
}
```

3. Consulta `GET /jobs/{job_id}` hasta que `status` sea `completed` o `failed`. Los estados posibles son `pending`, `processing`, `completed` y `failed`. Si falla, muestra `error_message`.
4. Con el trabajo completado, obtén `GET /analyses/{analysis_id}` o pagina con `GET /analyses/{analysis_id}/notes`.

La respuesta del análisis incluye las notas embebidas y estos metadatos:

```json
{
  "id": "<uuid>",
  "audio_file_id": "<uuid>",
  "status": "completed",
  "sample_rate": 44100,
  "duration_seconds": 12.4,
  "error_message": null,
  "notes": [
    {
      "id": "<uuid>",
      "analysis_id": "<uuid>",
      "segment_index": 0,
      "start_time": 0.0,
      "end_time": 0.45,
      "detected_midi": 69.02,
      "note_name": "A4",
      "frequency_hz": 440.8,
      "deviation_cents": 3.2,
      "confidence": 0.98
    }
  ],
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:05Z"
}
```

Recomendaciones de polling:

- Empieza con intervalos de 1 a 2 segundos y aplica un retroceso gradual hasta 4 o 5 segundos.
- Detén el polling al recibir `completed` o `failed`, al desmontar la pantalla o tras un tiempo máximo razonable (por ejemplo, 5 minutos).
- El trabajo continúa en el servidor si la app pasa a segundo plano; al volver, retoma el polling con el `job_id` guardado.
- No reintentes automáticamente `POST /analyses` ante un `409`: significa que ya existe un análisis en ejecución para ese audio. Consulta el job activo o espera.
- Un audio en silencio o con ruido no musical puede producir `completed` con `notes` vacío.
- No hay WebSocket ni Server-Sent Events; el estado se consulta por HTTP.

### 7. Formato de errores y manejo en el cliente

Los errores usan un sobre uniforme:

```json
{
  "error": {
    "code": "http_404",
    "message": "Archivo de audio no encontrado"
  }
}
```

Los errores de validación (`422`) añaden `details`:

```json
{
  "error": {
    "code": "validation_error",
    "message": "La solicitud no es válida.",
    "details": []
  }
}
```

Códigos que el cliente debe tratar:

| Estado | Acción recomendada |
| --- | --- |
| `400` | Mostrar el mensaje; corregir token de recuperación o contraseña actual. |
| `401` | Renovar una vez. Si la renovación falla, limpiar tokens y volver al login. |
| `403` | Cuenta desactivada; no reintentar. |
| `404` | Recurso inexistente o ajeno; no revelar detalles internos. |
| `409` | Correo ya registrado o análisis ya en ejecución. |
| `413` | Rechazar el archivo antes de subir o pedir uno más corto/ligero. |
| `415` | Solicitar WAV o MP3. |
| `422` | Resaltar campos inválidos usando `details`. |
| `500` | Error interno; reintento limitado y reporte con hora y contexto de la operación. |
| `503` | Infraestructura no disponible; permitir reintento manual con retroceso. |

Las respuestas `204` no tienen cuerpo: no intentes parsearlas como JSON.

### 8. Cliente web: ejemplo base en TypeScript

El siguiente ejemplo concentra login, renovación con una sola petición en curso, peticiones autenticadas y subida de archivos. Adáptalo al framework que uses.

```ts
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
};

let accessToken: string | null = null;
// El guard evita fallos durante renderizado en servidor (SSR).
let refreshToken: string | null =
  typeof window === "undefined" ? null : sessionStorage.getItem("dolean.refresh_token");
let refreshInFlight: Promise<void> | null = null;

function saveTokens(tokens: TokenResponse) {
  accessToken = tokens.access_token;
  refreshToken = tokens.refresh_token;
  sessionStorage.setItem("dolean.refresh_token", tokens.refresh_token);
}

async function apiError(response: Response) {
  const payload = await response.json().catch(() => null);
  return new Error(payload?.error?.message ?? `HTTP ${response.status}`);
}

export async function login(email: string, password: string) {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) throw await apiError(response);
  saveTokens(await response.json());
}

async function refreshSession() {
  if (!refreshToken) throw new Error("Sesión expirada");
  refreshInFlight ??= (async () => {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!response.ok) {
      accessToken = null;
      refreshToken = null;
      sessionStorage.removeItem("dolean.refresh_token");
      throw new Error("Sesión expirada");
    }
    saveTokens(await response.json());
  })().finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
}

export async function api<T>(path: string, init: RequestInit = {}, canRetry = true): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });

  if (response.status === 401 && canRetry && refreshToken) {
    await refreshSession();
    return api<T>(path, init, false);
  }
  if (!response.ok) throw await apiError(response);
  return (response.status === 204 ? undefined : await response.json()) as T;
}

export async function uploadAudio(projectId: string, file: File) {
  const form = new FormData();
  form.append("upload", file, file.name);
  return api<{ id: string; duration_seconds: number | null }>(
    `/projects/${projectId}/audio-files`,
    { method: "POST", body: form },
  );
}

export async function logout() {
  const token = refreshToken;
  accessToken = null;
  refreshToken = null;
  sessionStorage.removeItem("dolean.refresh_token");
  if (token) {
    await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: token }),
    }).catch(() => undefined);
  }
}
```

Notas para web:

- No establezcas manualmente `Content-Type` al enviar `FormData`; el navegador debe generar el `boundary`.
- `fetch` no informa progreso de subida. Si necesitas barra de progreso, usa `XMLHttpRequest` o `axios` con `onUploadProgress`.
- Para reproducir un audio protegido, descarga el binario con el header `Authorization`, crea un `Blob` y usa `URL.createObjectURL(blob)`. Libera la URL con `URL.revokeObjectURL` al terminar.
- Para el restablecimiento de contraseña, lee `token` de la query string de la ruta configurada en `PASSWORD_RESET_URL` y envíalo a `POST /auth/reset-password`.
- Si usas un Service Worker, no cachees respuestas con `Authorization` ni endpoints de autenticación.

### 9. Aplicación móvil: Android, iOS, Flutter y React Native

Reglas generales:

- Usa HTTPS en producción. En desarrollo se puede usar HTTP, pero solo mediante excepciones locales explícitas.
- Guarda los tokens en almacenamiento seguro y no los incluyas en logs, capturas ni backups.
- Serializa la renovación del refresh token para evitar perder la sesión por rotaciones concurrentes.
- Reintenta `GET` con retroceso exponencial; no reintentes ciegamente `POST /analyses` ni `POST /auth/refresh`.
- Comprueba el espacio disponible antes de grabar o descargar audio.
- Al eliminar un audio, el servidor borra el original y la versión normalizada. No guardes rutas internas de MinIO en la app.

#### Android

El emulador accede al equipo anfitrión mediante `10.0.2.2`. En desarrollo, habilita tráfico HTTP solo para los hosts locales; no dejes `usesCleartextTraffic` activo en producción.

```xml
<application
    android:networkSecurityConfig="@xml/network_security_config"
    ...>
```

```xml
<!-- app/src/main/res/xml/network_security_config.xml -->
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">10.0.2.2</domain>
        <domain includeSubdomains="true">192.168.1.50</domain>
    </domain-config>
</network-security-config>
```

Sustituye `192.168.1.50` por la IP de tu equipo. En producción elimina estas excepciones y usa HTTPS.

#### iOS

El simulador puede usar `http://127.0.0.1:8000`. Si necesitas HTTP local, añade una excepción de ATS únicamente para desarrollo:

```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsLocalNetworking</key>
    <true/>
</dict>
```

Para un dispositivo físico con IP de LAN puede ser necesario configurar una excepción de dominio o, preferiblemente, usar HTTPS. En iOS 14 o superior, el acceso a la red local puede requerir además `NSLocalNetworkUsageDescription`. No publiques la app con excepciones ATS generales.

#### Flutter

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

const apiBase = 'http://10.0.2.2:8000/api/v1';
const secureStorage = FlutterSecureStorage();

Future<void> login(String email, String password) async {
  final response = await http.post(
    Uri.parse('$apiBase/auth/login'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'email': email, 'password': password}),
  );
  if (response.statusCode != 200) {
    throw Exception(response.body);
  }
  final tokens = jsonDecode(response.body) as Map<String, dynamic>;
  await secureStorage.write(key: 'access_token', value: tokens['access_token']);
  await secureStorage.write(key: 'refresh_token', value: tokens['refresh_token']);
}

Future<http.Response> uploadAudio(
  String projectId,
  String accessToken,
  String filePath,
) async {
  final request = http.MultipartRequest(
    'POST',
    Uri.parse('$apiBase/projects/$projectId/audio-files'),
  )
    ..headers['Authorization'] = 'Bearer $accessToken'
    ..files.add(await http.MultipartFile.fromPath('upload', filePath));

  return http.Response.fromStream(await request.send());
}
```

Para descargar un audio protegido usa una petición con `Authorization`, guarda los bytes en el directorio temporal o de documentos y reproduce el archivo local. No abras directamente la URL del endpoint en el reproductor del sistema, porque no adjuntará el token.

#### React Native

```ts
const API_BASE = "http://10.0.2.2:8000/api/v1"; // iOS: http://127.0.0.1:8000/api/v1

async function uploadAudio(projectId: string, fileUri: string, accessToken: string) {
  const form = new FormData();
  form.append("upload", {
    uri: fileUri,
    name: "grabacion.wav",
    type: "audio/wav",
  } as any);

  const response = await fetch(`${API_BASE}/projects/${projectId}/audio-files`, {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
    body: form,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.error?.message ?? `HTTP ${response.status}`);
  }
  return response.json();
}
```

No añadas `Content-Type` manualmente en React Native al usar `FormData`. Usa `react-native-keychain` o `expo-secure-store` para los tokens.

### 10. Lista de verificación para ambos clientes

- [ ] URL base configurable por entorno y sin `localhost` en builds de producción.
- [ ] Login, refresh con una sola renovación concurrente, logout y limpieza de tokens.
- [ ] Interceptor o wrapper que añada `Authorization: Bearer`.
- [ ] Manejo de `401` con un único reintento y redirección al login si falla.
- [ ] Tokens en memoria/almacenamiento seguro; nunca en logs.
- [ ] Carga `multipart/form-data` con el campo `upload` y sin `Content-Type` manual.
- [ ] Validación local de formato, tamaño máximo de 50 MB y duración máxima de 3 minutos.
- [ ] Polling de `GET /jobs/{job_id}` con retroceso, cancelación y timeout.
- [ ] Manejo de `409` al solicitar un análisis y de `503` en servicios no disponibles.
- [ ] Descarga autenticada del audio y liberación de recursos temporales.
- [ ] Pantalla de restablecimiento que lea el `token` del enlace de correo.
- [ ] CORS del frontend web declarado en `CORS_ORIGINS`.
- [ ] Excepciones HTTP locales en Android/iOS solo para desarrollo.
- [ ] HTTPS, certificados válidos y sin puertos de infraestructura expuestos en producción.

## Seguridad y producción

`.env` no se versiona. Los puertos de PostgreSQL, Redis y MinIO están ligados a `127.0.0.1` solo para la demo local. En producción deben eliminarse esas publicaciones y las credenciales deben inyectarse mediante un gestor de secretos. Las contraseñas se almacenan con Argon2, los refresh tokens se almacenan como hash y los endpoints de recursos requieren un access token válido.

