# Fase 2, subfase 2.2 — Motor DSP de detección de afinación

Esta subfase incorpora un detector monofónico basado en pYIN. Librosa se utiliza
para leer la señal, separar actividad y estimar F0; la conversión a MIDI,
desviación en cents, filtrado y agrupación de ventanas consecutivas pertenecen
a la lógica de DoLean.

## Contrato interno

`analyze_pitch(path)` devuelve:

- `sample_rate`: frecuencia real de muestreo leída del archivo.
- `duration_seconds`: duración de la señal cargada.
- `notes`: segmentos estables, no una fila por ventana DSP.
- `confidence`: mediana de la probabilidad de voz de pYIN en el segmento.
- `deviation_cents`: diferencia logarítmica entre la frecuencia mediana y la
  nota temperada más cercana; `0` representa afinación exacta.

## Parámetros iniciales

El detector utiliza frame de 2048 muestras, salto de 256 muestras, actividad con
`top_db=35`, confianza mínima `0.55` y duración mínima de segmento `0.08 s`.
Los parámetros quedan configurables mediante variables `DSP_*`.

## Verificación

```powershell
python -m compileall -q app alembic scripts tests
pytest tests/unit/test_dsp_pitch.py
```

Para verificar el detector dentro de la imagen de runtime, donde están
instaladas las dependencias DSP:

```powershell
docker compose run --rm api sh -c "python scripts/generate_test_audio.py && python scripts/smoke_dsp.py"
```

Con un audio ya cargado, se puede validar además la persistencia del análisis
y sus notas contra PostgreSQL y MinIO:

```powershell
$env:DOLEAN_AUDIO_FILE_ID = "<audio-file-id>"
docker compose run --rm -v "${PWD}:/app" -e PYTHONPATH=/app api alembic upgrade head
docker compose run --rm -v "${PWD}:/app" -e PYTHONPATH=/app api python scripts/smoke_analysis.py
```

La ejecución asíncrona reutiliza este módulo sin enviar matrices NumPy por Redis.
La solicitud HTTP se crea mediante `POST /api/v1/audio-files/{audio_file_id}/analyses`;
el cliente consulta el trabajo y el resultado mediante las rutas documentadas en
Swagger.
