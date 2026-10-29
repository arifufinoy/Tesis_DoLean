# Diagrama entidad-relación — Sprint 0

```mermaid
erDiagram
    USERS ||--o| PROFILES : "tiene"
    USERS ||--o{ PROJECTS : "administra"
    USERS ||--o{ RECOVERY_TOKENS : "solicita"
    USERS ||--o{ REFRESH_SESSIONS : "mantiene"
    PROJECTS ||--o{ AUDIO_FILES : "contiene"
    AUDIO_FILES ||--o{ ANALYSES : "recibe"
    AUDIO_FILES ||--o{ PROCESSED_VERSIONS : "origina"
    ANALYSES ||--o{ NOTE_SEGMENTS : "genera"
    ANALYSES ||--o{ CORRECTION_REQUESTS : "recibe"
    CORRECTION_REQUESTS ||--o{ PROCESSED_VERSIONS : "produce"

    USERS {
        uuid id PK
        string email UK
        string password_hash
        enum role
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    PROFILES {
        uuid id PK
        uuid user_id FK
        string display_name
        text bio
        datetime created_at
        datetime updated_at
    }
    PROJECTS {
        uuid id PK
        uuid owner_id FK
        string name
        text description
        datetime created_at
        datetime updated_at
    }
    AUDIO_FILES {
        uuid id PK
        uuid project_id FK
        string original_filename
        string content_type
        string storage_key UK
        bigint size_bytes
        float duration_seconds
        int sample_rate
        int channels
    }
    ANALYSES {
        uuid id PK
        uuid audio_file_id FK
        enum status
        int sample_rate
        float duration_seconds
        text error_message
        datetime created_at
        datetime updated_at
    }
    NOTE_SEGMENTS {
        uuid id PK
        uuid analysis_id FK
        int segment_index
        float start_time
        float end_time
        float detected_midi
        string note_name
        float frequency_hz
        float deviation_cents
        float confidence
    }
    PROCESSING_JOBS {
        uuid id PK
        string job_type
        enum status
        string celery_task_id
        text error_message
        datetime created_at
        datetime updated_at
    }
    CORRECTION_REQUESTS {
        uuid id PK
        uuid analysis_id FK
        json parameters
        enum status
        datetime created_at
        datetime updated_at
    }
    PROCESSED_VERSIONS {
        uuid id PK
        uuid source_audio_file_id FK
        uuid correction_request_id FK
        string storage_key UK
        string content_type
        bigint size_bytes
        datetime created_at
    }
    RECOVERY_TOKENS {
        uuid id PK
        uuid user_id FK
        string token_hash UK
        datetime expires_at
        datetime used_at
        datetime created_at
    }
    REFRESH_SESSIONS {
        uuid id PK
        uuid user_id FK
        string token_hash UK
        datetime expires_at
        datetime revoked_at
        datetime created_at
    }
```

`PROCESSING_JOBS` es una entidad técnica preparada para enlazar tareas Celery con los servicios de análisis y corrección. En los siguientes sprints se completará la relación lógica con el recurso procesado.

