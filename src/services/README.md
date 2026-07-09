# Services

The data-access layer lives here: API clients, request/response mapping, and integration with external systems. Services are consumed by features and hooks — UI components should never call a service directly.

No API integration exists yet — this is Phase 1 (shell only). When a backend is introduced, add a base HTTP client here (e.g. `httpClient.ts`) and one module per resource (e.g. `incidentsService.ts`).
