# Demo reproducible — Fase 2, subfase 2.1

Esta subfase valida la carga, validación, normalización, almacenamiento y control de acceso de archivos WAV y MP3.

## Preparar infraestructura y migración

```powershell
docker compose up --build -d api worker
docker compose run --rm api alembic upgrade head
```

La migración `0003_audio_normalized_storage` agrega la referencia a la representación interna normalizada sin modificar el archivo original.

## Generar archivos de prueba

```powershell
python scripts/generate_test_audio.py
```

Si se ejecuta dentro del contenedor, usar:

```powershell
docker compose run --rm api python scripts/generate_test_audio.py
```

## Flujo manual

1. Iniciar sesión y autorizar Swagger con el `access_token`.
2. Crear o seleccionar un proyecto mediante `/api/v1/projects`.
3. Ejecutar `POST /api/v1/projects/{project_id}/audio-files` usando `multipart/form-data` y el campo `upload`.
4. Verificar que la respuesta incluya tamaño, duración, frecuencia de muestreo y canales.
5. Consultar el archivo con `GET /api/v1/audio-files/{audio_file_id}`.
6. Descargar el original con `GET /api/v1/audio-files/{audio_file_id}/download`.
7. Listar archivos con `GET /api/v1/projects/{project_id}/audio-files`.
8. Eliminarlo con `DELETE /api/v1/audio-files/{audio_file_id}`.

## Validaciones esperadas

- Extensiones admitidas: `.wav` y `.mp3`.
- El contenido real se comprueba con FFprobe; cambiar únicamente la extensión no permite cargar un archivo inválido.
- Tamaño máximo: 50 MB.
- Duración máxima: 3 minutos.
- La copia original se conserva en MinIO.
- La copia interna se convierte a WAV mono, PCM de 16 bits y 44.1 kHz.
- Un usuario distinto recibe `404` y no puede consultar, descargar ni eliminar el archivo.
