# 📝 Deployment Post-Mortem: Pledge-Rover (Revision #00031)

## 📯 Executive Summary
The deployment of the Pledge-Rover module failed across 16 consecutive runs due to a combination of blocking linting errors, container pathing issues, and database driver incompatibilities. This document outlines the failures and the permanent corrective actions implemented.

---

## 🔍 The Challenges

### 1. The Build Layer (Linting)
- **Failure**: GitHub Actions blocked the build due to `no-unused-vars` and missing dependencies in `useEffect`.
- **Root Cause**: Manual edits without local lint verification.
- **Correction**: Prefix unused variables with `_` and wrap complex status pollers in `useCallback`.

### 2. The Container Layer (Filesystem)
- **Failure**: `ModuleNotFoundError: No module named 'src'`.
- **Root Cause**: The Dockerfile `WORKDIR` was set to `/app`, but the application code was nested inside `/app/backend/src`. When uvicorn tried to import `backend.src.server:app`, sub-imports like `from src.routes...` failed.
- **Correction**: Standardized `WORKDIR` to `/app/backend` and updated the entry point to `src.server:app`.

### 3. The Startup Layer (Resource Guarding)
- **Failure**: `RuntimeError: Directory '.../assets' does not exist`.
- **Root Cause**: The FastAPI app used `app.mount()` on a directory that might not be present if the React build was skipped or altered. This caused a crash during module import.
- **Correction**: Implemented **Guarded Mounting**. The app now checks for directory existence before mounting and logs a warning instead of crashing.

### 4. The Runtime Layer (Database)
- **Failure**: `InvalidRequestError: pg8000 is not async`.
- **Root Cause**: Attempting to use a synchronous driver (`pg8000`) with an `AsyncSession` engine.
- **Correction**: Switched the production stack to `asyncpg` using the `async_creator` pattern with the Google Cloud SQL Connector.

---

## 🚀 Action Items for Future-Proofing

### ✅ Mandatory Local Validation
Before any push to `main` that affects `pledge_rover/`:
1. **Frontend**: Run `npm run lint` in `pledge_rover/frontend`.
2. **Backend**: Run `python -m py_compile` on all files in `src/`.
3. **Docker**: Verify the container starts locally if changes were made to `Dockerfile`.

### ✅ Guarded Resources
Never allow a missing static file or a failed DB connection to stop the port from binding. 
- *Rule*: Always wrap `app.mount` and `init_db` in safety checks/try-blocks.

### ✅ Async/Sync Awareness
When building new Python services, strictly adhere to the **Async Driver Stack**:
- **Engine**: `create_async_engine`
- **Driver**: `asyncpg`
- **Connector**: `connector.connect_async`

---

**Status**: Resolved | **Version**: 1.1.0 | **Author**: Antigravity AI
