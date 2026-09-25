# Legacy Cleanup Archive

This directory contains files intentionally moved out of the active project during the audit cleanup.

Moved items:
- hello.txt — empty placeholder file; no runtime or project references.
- collect.txt — empty placeholder file; no runtime or project references.
- backend/leadpilot.db — stale SQLite database duplicate; the active runtime uses backend/leadpilot_local.db via the app config.
- frontend/dist — generated production build output; not imported by the source tree.
- frontend/node_modules — generated dependency tree; not source-controlled and not referenced at runtime.
- backend/.pytest_cache — generated pytest cache.
- backend/__pycache__ and nested __pycache__ directories — generated Python bytecode caches.

These files were moved instead of deleted to preserve a safe rollback path during the audit.
