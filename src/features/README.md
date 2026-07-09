# Features

Domain modules live here, one folder per business capability (e.g. `incidents/`, `plant/`, `reports/`). Each feature folder is self-contained and may include its own:

- `components/` — UI specific to the feature
- `hooks/` — feature-specific hooks
- `services/` — feature-specific API/data access
- `types/` — feature-specific types

Cross-cutting building blocks (design system, layouts, generic hooks) stay in the top-level `components/`, `layouts/`, and `hooks/` folders instead of being duplicated per feature.

No features have been implemented yet — this is Phase 1 (shell only).
