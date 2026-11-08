# Demo reproducible — Fase 2

Esta demo valida carga, normalización, detección de afinación, persistencia y
procesamiento asíncrono mediante Celery y Redis.

## Preparar el entorno

```powershell
docker compose up --build -d api worker
docker compose run --rm api alembic upgrade head
python scripts/generate_test_audio.py
```

El cambio de `redis-py` a `6.1.0` es necesario para la compatibilidad con el
transporte Redis de Celery 5.4.

## Ejecutar la demo

```powershell
$env:DOLEAN_DEMO_EMAIL="demo2@dolean.dev"
$env:DOLEAN_DEMO_PASSWORD="Seguro123!"
$env:DOLEAN_AUDIO_FILE="artifacts/audio-fixtures/a4_440hz.wav"
python scripts/demo_sprint_2.py
```

La salida debe mostrar el proyecto, el audio cargado, el `analysis_id`, el
trabajo completado y las notas detectadas. Para una señal A4 sintética se espera
una frecuencia cercana a 440 Hz y una desviación cercana a 0 cents; los valores
son los medidos por el detector, no datos simulados.

## Flujo equivalente en Swagger

1. Iniciar sesión en `/api/v1/auth/login` y autorizar el `access_token`.
2. Cargar un WAV mediante `POST /api/v1/projects/{project_id}/audio-files`.
3. Solicitar el procesamiento en `POST /api/v1/audio-files/{audio_file_id}/analyses`.
4. Consultar `GET /api/v1/jobs/{job_id}` hasta obtener `completed`.
5. Consultar `GET /api/v1/analyses/{analysis_id}`.
6. Consultar `GET /api/v1/analyses/{analysis_id}/notes`.

## Limitaciones conocidas

- El detector está diseñado para audio monofónico con una voz o línea melódica
  dominante.
- La confianza es la mediana de la probabilidad de voz de pYIN por segmento.
- Las regiones sin tono estable pueden producir una respuesta sin notas.
- La corrección de afinación y las versiones procesadas pertenecen a la Fase 3.
