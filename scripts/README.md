# Scripts

- `create_admin.py`: crea o promueve una cuenta administrativa usando `DOLEAN_ADMIN_EMAIL` y `DOLEAN_ADMIN_PASSWORD` proporcionados en tiempo de ejecución.
- `demo_sprint_1.py`: ejecuta el recorrido reproducible de perfiles, proyectos, autorización y rotación de sesión.
- `generate_test_audio.py`: genera localmente los WAV sintéticos utilizados en la Fase 2.
- `demo_sprint_2.py`: carga un WAV y solicita el análisis asíncrono hasta recuperar las notas detectadas.
- `smoke_dsp.py`: ejecuta el detector DSP sobre la fixture A4 dentro del contenedor.
- `smoke_analysis.py`: valida la persistencia de un análisis y sus notas contra PostgreSQL y MinIO.

La demo del Sprint 0 está documentada en `docs/demos/sprint_0.md` y usa comandos estándar de Docker Compose para que sea reproducible en Windows.

