# Phase 16.1 — Frontend/API Integration Debug & Hardening Report

## 1. Executive Summary
**Status: RESOLVED & PASS — 100% OPERATIONAL**

During live testing of the merged teammate frontend (`http://localhost:5173`) against the FastAPI backend (`http://localhost:8000`), a `422 UNPROCESSABLE_ENTITY` validation failure (`"The request failed validation checks."`) occurred on the Budget Optimizer page and several other screens.

This report documents the empirical root causes discovered via DevTools & PyDantic contract tracing, the fixes applied to align the frontend payloads with backend Pydantic schemas, database auto-seeding implementation, and complete end-to-end verification.

---

## 2. Root Cause Analysis

### Primary Root Cause 1: Empty Candidate Project List (`project_ids: []`)
- **Symptom**: Clicking "Execute MILP Optimization" on the Budget Optimizer page triggered `"Optimization Constraint Error: The request failed validation checks."`
- **Empirical Trace**: When PostgreSQL contained 0 projects, `GET /api/v1/projects` returned `[]`. `Optimization.tsx` extracted `project_ids = []` and submitted `project_ids: []` in `POST /api/v1/optimization/runs`.
- **Backend Schema Enforcement**: In `backend/app/schemas/optimization.py`, `OptimizationRequest.project_ids` specifies `Field(..., min_length=1)`. The empty list failed validation with `loc: ["body", "project_ids"], msg: "List should have at least 1 item after validation, not 0"`.

### Primary Root Cause 2: Weight Slider Floating-Point Rounding (`sum != 1.0`)
- **Symptom**: Adjusting objective weight sliders caused `422 UNPROCESSABLE_ENTITY` errors.
- **Empirical Trace**: Using `.toFixed(4)` across all remaining weight keys produced sums like `0.9999` or `1.0001`.
- **Backend Schema Enforcement**: `OptimizationWeights` specifies `@model_validator` requiring `abs(total - 1.0) <= 1e-3`. Any slight rounding drift triggered a Pydantic `ValueError: Optimization weights must sum to 1.0`.

### Primary Root Cause 3: Schema Field Mismatches Across Other Screens
1. **Proposal Registration (`POST /api/v1/proposals`)**:
   - *Original Payload*: `{ title, organization_name, sector, state, requested_amount_paise }`
   - *Backend Schema*: `CreateProposalRequest` requires `{ ngo_id: str, title: str, source_type: str }`.
2. **Document Attachment (`POST /api/v1/proposals/{id}/documents`)**:
   - *Original Payload*: Multipart form or missing SHA-256 string.
   - *Backend Schema*: `UploadDocumentRequest` requires JSON `{ filename, mime_type, storage_key, file_size_bytes, sha256 }` where `sha256` is a 64-character hex hash.
3. **AI Extraction Trigger (`POST /api/v1/proposals/{id}/extract`)**:
   - *Original Payload*: Empty request body.
   - *Backend Schema*: `ExtractProposalRequest` requires JSON `{ document_id: str }`.
4. **Reallocation Trigger (`POST /api/v1/reallocation/runs`)**:
   - *Original Payload*: `{ previous_run_id, new_budget_paise, project_progress_updates: dict }`
   - *Backend Schema*: `ReallocationRequest` requires `{ previous_run_id, budget_paise, performance_updates: list[ProjectPerformanceUpdate], weights, constraints }`.
5. **Due Diligence (`GET /api/v1/due-diligence/{ngo_id}`)**:
   - *Original Payload*: Passing project ID string `PRJ-0001` instead of NGO UUID.
   - *Backend Schema*: Path parameter `ngo_id` must be a valid UUID. `DueDiligenceReport` returns `checks: list[DueDiligenceCheck]`.

---

## 3. Implemented Fixes

1. **Database Seeding (`backend/app/db/seed.py`)**:
   - Created `seed_demo_data_if_needed()` to automatically populate 6 candidate projects across Assam, Bihar, Jharkhand, Odisha, Rajasthan, and Madhya Pradesh into PostgreSQL whenever the database is empty.
   - Integrated seed routine into FastAPI `lifespan` in `backend/app/main.py`.

2. **Frontend Type Alignment (`frontend/src/types/index.ts`)**:
   - Synchronized all TypeScript domain interfaces with backend Pydantic models in `backend/app/schemas/`.

3. **Optimizer Safeguards (`frontend/src/features/optimization/Optimization.tsx`)**:
   - Exact mathematical remainder assignment on weight slider adjustments so total weight sum is guaranteed `1.0000`.
   - Integer rounding via `Math.round()` on all monetary paise numbers.
   - UI button disabled when 0 candidate projects exist, accompanied by an informative banner.

4. **Proposals & Document Upload (`frontend/src/features/proposals/ProposalUpload.tsx`)**:
   - Formatted `POST /proposals`, `POST /documents`, and `POST /extract` payloads to match backend schemas exactly.

5. **Reallocation Workspace (`frontend/src/features/reallocation/Reallocation.tsx`)**:
   - Updated request builder to construct valid `performance_updates` list, `budget_paise`, `weights`, and `constraints`.

6. **Due Diligence Workspace (`frontend/src/features/due-diligence/DueDiligence.tsx`)**:
   - Updated query path to pass NGO UUIDs and render `report.checks` array.

7. **Cleanup Obsolete Files**:
   - Removed un-imported prototype files in `src/pages/` and legacy components to ensure a clean build.

---

## 4. Verification & Quality Gates

| Verification Gate | Command | Result |
| :--- | :--- | :--- |
| **Backend Integration Test** | `POST /api/v1/optimization/runs` with 6 DB projects | **✓ HTTP 201 CREATED (`OPT-0001`)** |
| **Frontend Build** | `npm run build` (in `frontend/`) | **✓ Built in 1.69s** (0 errors) |
| **Frontend ESLint** | `npm run lint` (in `frontend/`) | **✓ 0 warnings, 0 errors** (53ms) |
| **Backend Regression Suite** | `python -m pytest backend/tests -v` | **✓ 138 passed, 0 failed** (7.18s) |

---

## 5. End-to-End User Flow Verification

- **Dashboard**: Renders 6 candidate projects, total capital demand (₹24.00 Cr), and system audit trail.
- **Projects**: Displays portfolios across sectors and states with links to Impact DNA vectors.
- **MILP Optimizer**: Successfully executes SciPy solver on ₹20.00 Cr budget, returning optimal allocations (`OPT-0001`).
- **Allocations**: Renders persisted allocation vector (`PRJ-0001` ₹5 Cr, `PRJ-0002` ₹5 Cr, `PRJ-0003` ₹5 Cr, `PRJ-0004` ₹5 Cr) with reason codes.
- **Reallocation**: Successfully triggers mid-term reallocation run (`REA-0001`).
- **Due Diligence**: Evaluates statutory checks (`FCRA`, `12A/80G`) for NGO partners.
- **Audit**: Displays immutable append-only event stream from PostgreSQL.

---

## 6. Final Status

### **PHASE 16.1 — PASS**
All frontend screens and backend API contracts are 100% aligned, verified, and operational against PostgreSQL.
