# Services

The data-access layer lives here: API clients, request/response mapping, and integration with external systems. Services are consumed by features and hooks — UI components should never call a service directly.

`httpClient.ts` is the shared base client (typed `apiGet`, throws `ApiError` on non-2xx). Resource-specific services live inside their feature folder (e.g. `features/plant/services/plantService.ts`) and are responsible for mapping the backend's snake_case JSON into the feature's camelCase domain types — components never see wire format.
