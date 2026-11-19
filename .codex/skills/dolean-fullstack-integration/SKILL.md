---
name: dolean-fullstack-integration
description: Implement and audit the DoLean backend contract across the web and mobile clients, covering auth, projects, audio, DSP analysis, corrections, versions, polling, downloads, and export flows.
metadata:
  short-description: Integrate DoLean API with web and mobile
---

# DoLean full-stack integration

Use this skill when implementing or reviewing DoLean backend consumption in the Expo mobile client or the Vite web client.

## Source of truth

- Backend contract: `docs/endpoints-backend.md` and live `/openapi.json`.
- Mobile audit: `docs/auditoria-movil.md`.
- Web audit: `docs/auditoria-frontend.md`.
- API base URL must be configured per client; do not duplicate `/api/v1`.

## Required workflow

1. Inspect the target client’s API/config, session manager, DTOs, repositories, hooks and screen flow before editing.
2. Match every request to the backend path, method, authentication, JSON field names and response envelope.
3. Preserve `snake_case` at the HTTP boundary and map to client naming only inside the client layer.
4. Send `Authorization: Bearer <access_token>` for protected routes.
5. On a protected `401`, perform one coordinated refresh using the refresh token, rotate and persist both tokens, retry once, then clear the session.
6. For uploads, send `multipart/form-data` with field `upload`; in React Native let the networking library generate the multipart boundary.
7. For analysis and correction, persist resource IDs and poll `/jobs/{job_id}` while status is `pending` or `processing`.
8. Never display local demo notes as backend results. Mark fixtures explicitly and replace them with `analysis.notes` before enabling real editing.
9. For correction, submit only real `note_id` values belonging to the selected analysis and a validated `target_midi` between 0 and 127.
10. After correction completes, list versions, fetch metadata, download the protected WAV with the bearer token, and provide original/corrected A/B playback.
11. Keep the original audio immutable; versions are separate server resources.
12. Add tests for successful requests, auth refresh, invalid ownership, failed jobs, empty notes, upload errors, correction validation and version download.

## Client-specific configuration

### Web

Set:

```text
VITE_API_BASE_URL=http://localhost:8000
```

The web client already prefixes routes with `api/v1`.

### Mobile

Set the complete versioned URL:

```text
EXPO_PUBLIC_API_URL=http://localhost:8000/api/v1
```

For Android Emulator use `http://10.0.2.2:8000/api/v1`; for a physical device use the host LAN IP.

## Correction contract

```json
{
  "analysis_id": "analysis-uuid",
  "edits": [
    {
      "note_id": "note-uuid",
      "target_midi": 67
    }
  ],
  "output_format": "wav"
}
```

The response provides `correction_request_id`, `job_id` and `status_url`. Poll the job, then request versions and download the generated WAV.

## Quality gates

Before declaring integration complete:

- Verify the live OpenAPI paths.
- Run backend tests and client tests/builds.
- Test a real WAV upload, not only a fixture object in local storage.
- Confirm the analysis screen renders server `note_id` values.
- Confirm a correction creates a new version and leaves the original downloadable.
- Test token expiry and refresh without duplicate concurrent refresh calls.
- Test ownership failures with a second user.
- Document any DSP artifacts; do not claim Melodyne-level quality. The current backend correction is a prototype and needs transition/crossfade and stronger pitch-shifting quality before production claims.
