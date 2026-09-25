# Error Categories

## Critical

None found after running diagnostics from the correct package directories.

## High

None found. Backend imports, migrations, database connection, 127 tests, frontend build, and TypeScript checks pass.

## Medium

- Mypy unavailable because it is not declared/installed.
- Ruff unavailable because it is not declared/installed.
- ESLint unavailable because it is not declared/installed.
- One Starlette deprecation warning remains from an external dependency.

## Low

- Historical documentation was cluttering the root and was moved to `legacy/docs`.
- Generated caches and duplicate local artifacts were removed.

## Launcher-specific

The launcher used the correct backend `/healthz` readiness route after repair, starts each service with an explicit working directory, waits for readiness, delays two seconds, and opens `http://localhost:5173`.
