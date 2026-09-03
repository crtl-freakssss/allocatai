# AllocateAI — Backend Platform

AllocateAI is an AI-driven resource allocation and portfolio optimization platform.

This repository houses the backend service built with **FastAPI**, **SQLAlchemy 2.0**, **Alembic**, and **PostgreSQL**.

---

## Project Status

- **Phase 0 (Project Foundation)**: **COMPLETE & VERIFIED**
- **Phase 1 (Database Architecture)**: **COMPLETE & VERIFIED**
- **Phase 2 (Schemas & Validation Boundary)**: **COMPLETE & VERIFIED**
- **Phase 3 (Repository / Data Access Layer)**: **COMPLETE & VERIFIED**
- **Phase 4 (Services & Workflow Orchestration)**: **COMPLETE & VERIFIED**
- **Phase 5 (API Endpoints & Integration)**: **COMPLETE & VERIFIED**
- **Phase 6 (Intelligence Engine Integration)**: **COMPLETE & VERIFIED**
- **Phase 7 (End-to-End Integration & Demo Hardening)**: **COMPLETE & VERIFIED**

---

## Phase 6 Intelligence Engine Architecture

Phase 6 implements the concrete mathematical, AI, and algorithmic engines under `backend/app/engine/`:
- **AI / Document Extraction (`RealExtractionEngine`)**: Structured fact and unverified evidence item extraction (`gemini-1.5-pro-structured` / `extraction-v1.0`) with deterministic offline zero-secret fallback.
- **Impact DNA (`RealImpactDNAEngine`)**: Multidimensional impact dimension generation across need, expected impact, cost efficiency, evidence strength, scalability, and implementation risk (`impact-dna-v1`).
- **Deterministic Scoring (`ScoringEngine`)**: Normalized multi-attribute utility calculation weighted by contract-defined `OptimizationWeights` (`scoring-v1`).
- **CSR Saturation Index (`RealSaturationEngine`)**: Regional saturation ratio combining existing CSR disbursements against benchmark capacity and demographic need (`sat-v1`).
- **Marginal Impact (`MarginalImpactCalculator`)**: Diminishing utility modeling over incremental capital tranches ($\Delta \text{Impact} / \Delta \text{Budget}$, `marginal-v1`).
- **MILP Portfolio Optimizer (`RealOptimizationEngine`)**: Mixed Integer Linear Programming solver (`scipy.optimize.milp` / `scipy-milp-v1`) guaranteeing strict integer paise conservation ($allocated + unallocated = budget$), project caps, regional caps, regional equity distribution, and explainability reason codes.
- **Dynamic Reallocation (`RealReallocationEngine`)**: Milestone velocity evaluation redirecting capital from lagging to high-performing projects while keeping historical runs immutable (`realloc-v1`).
- **Due Diligence (`RealDueDiligenceEngine`)**: Statutory compliance auditing (12A/80G, Darpan, FCRA) preserving mandatory legal non-certification disclaimers (`due-diligence-v1`).

---

## Phase 5 API Endpoint Layer

Phase 5 exposes all backend workflows under `/api/v1` using FastAPI:
- `POST /api/v1/proposals`: Ingest new proposal, validate NGO existence, return sequential `PRO-xxxx`.
- `GET  /api/v1/proposals`: Paginated list of proposals with NGO and status filters.
- `GET  /api/v1/proposals/{id}`: Detailed proposal state lookup by public ID.
- `POST /api/v1/proposals/{id}/documents`: Attach proposal document metadata and SHA-256 fingerprint (`DOC-xxxx`), rejecting duplicates.
- `GET  /api/v1/proposals/{id}/documents`: List attached documents for a proposal.
- `POST /api/v1/proposals/{id}/extract`: Trigger AI extraction on attached document, assign official `PRJ-xxxx`, and advance proposal status.
- `POST /api/v1/projects`: Create CSR project with geographic scope and integer paise financials.
- `GET  /api/v1/projects`: Paginated list of projects with sector and NGO filters.
- `GET  /api/v1/projects/{id}`: Fetch project details by public ID.
- `POST /api/v1/optimization/runs`: Trigger MILP portfolio optimization run with conservation invariant checks.
- `GET  /api/v1/optimization/runs/{id}`: Retrieve optimization results, input snapshots, and allocation items.
- `GET  /api/v1/optimization/runs`: List historical optimization solver runs.
- `POST /api/v1/reallocation/runs`: Execute mid-cycle reallocation adjustments based on project performance updates.
- `GET  /api/v1/reallocation/runs/{id}`: Retrieve reallocation run snapshot details.
- `POST /api/v1/due-diligence/{ngo_id}/evaluate`: Evaluate NGO regulatory compliance markers (`DD-xxxx`).
- `GET  /api/v1/due-diligence/{ngo_id}`: Retrieve latest compliance report with legal non-certification disclaimer.
- `GET  /api/v1/audit/events`: Paginated query of immutable audit events with actor and request ID filters.
- `GET  /api/v1/audit/events/{id}`: Fetch individual audit record by public identifier.

---

## Phase 4 Service / Orchestration Architecture

Phase 4 implements business workflow orchestration under `backend/app/services/`:
- **Transaction Ownership**: Services own transaction boundaries (`session.commit()`, `session.rollback()`). Repositories flush, but never commit.
- **Engine Protocol Abstraction**: Mathematical solvers and AI components (`ExtractionEngine`, `ImpactDNAEngine`, `SaturationEngine`, `OptimizationEngine`, `ReallocationEngine`, `DueDiligenceEngine`) are defined as pure Python Protocols. Services orchestrate and validate results without coupling to specific LLMs or optimization solvers.
- **Authoritative Identity**: Official persistent IDs (`PRO-xxxx`, `DOC-xxxx`, `PRJ-xxxx`, `DNA-xxxx`, `OPT-xxxx`, `REA-xxxx`, `DD-xxxx`, `AUD-xxxx`) are strictly generated and governed by backend services. Any client or engine-suggested identifiers are overridden.
- **Conservation & Invariants**: Full enforcement of the budget conservation invariant ($allocated + unallocated = budget$).
- **Audit Trails**: Every state mutation triggers an append-only audit event in the transactional write.
- **Exception Normalization**: Domain-specific service exceptions (`ResourceNotFoundError`, `ResourceAlreadyExistsError`, `ServiceValidationError`, `ConflictError`, `InvalidStateTransitionError`, `ProcessingError`) shield callers from raw database exceptions.

---

## Phase 3 Repository Architecture

Phase 3 implements the data access layer across all 14 entities under `backend/app/repositories/`.

### Repository Principles:
- **Transaction Ownership**: Repositories accept an active SQLAlchemy `Session`, invoking `flush()` and `refresh()` as needed, but never call `commit()` or `close()`. Transactions are owned and committed by callers (services).
- **Immutability Protection**: `OptimizationRepository` prevents any modification of `input_snapshot`, `result_snapshot`, weights, or calculation metadata once a run transitions to `COMPLETED`.
- **Append-Only Auditing**: `AuditRepository` provides `create()` and `bulk_create()` but strictly prohibits updates and deletes.
- **Deterministic Pagination**: All paginated queries sort by `created_at DESC, id ASC` to guarantee stable ordering.
- **Public ID Lookups**: Repositories support fast lookups by indexed `public_id` strings (e.g. `PRO-0001`, `PRJ-0001`, `OPT-0001`) separate from internal UUIDs.
- **Relational Integrity**: Projects referenced by allocations cannot be hard-deleted, strictly respecting PostgreSQL `RESTRICT` constraints.

## Phase 1 Database Architecture

Phase 1 establishes the complete PostgreSQL database foundation strictly adhering to the AllocateAI Technical Contract.

### Key Database Rules Enforced:
1. **Migrations**: Managed via Alembic; all schema evolutions are version-controlled and reversible.
2. **Primary Keys**: Internal database IDs use standard `UUID` (`uuid4`).
3. **Public Identifiers**: API-facing entities have unique string `public_id` values generated backend-side with standard entity prefixes (e.g. `PRO-0001`, `PRJ-0001`, `NGO-0001`, `OPT-0001`, `DOC-0001`, `DNA-0001`, `DDR-0001`, `REA-0001`, `AUD-0001`).
4. **Monetary Precision**: All monetary values (`requested_amount`, `current_funding`, `budget_paise`, `allocated_amount`, `existing_csr_amount`) are stored as `BIGINT` in **paise** (1 Rupee = 100 paise). Float and Numeric are forbidden for monetary columns.
5. **Score Precision**: All statistical and AI scores use `NUMERIC` with exact scale and precision (e.g. `NUMERIC(6,5)` for normalized [0, 1] indices; `NUMERIC(14,4)` and `NUMERIC(18,4)` for predicted impact metrics).
6. **Snapshots & Evidence**: Structured evidence and calculation configurations are stored in PostgreSQL `JSONB` columns (`input_snapshot`, `result_snapshot`, `weights`, `constraints`, `calculation_versions`, `checks`, `flags`, `reason_codes`, `payload`).
7. **Snapshot Immutability**: `OptimizationRun` snapshots are immutable upon completion.
8. **Append-Only Audit**: `AuditEvent` records are immutable and append-only.
9. **Deletion Safeguards**: Projects referenced by `allocations` cannot be hard-deleted (`ondelete="RESTRICT"`).
10. **Timestamps**: Consistent timezone-aware timestamps (`created_at` with server default `now()`, `updated_at` with auto-update trigger/hook).

### Database Tables Implemented (14 Tables)

| # | Table Name | Description | Key Constraints & Types |
| :--- | :--- | :--- | :--- |
| 1 | `organizations` | Corporate donors and foundations | UUID PK, `name` |
| 2 | `users` | User accounts associated with organizations | UUID PK, `organization_id` FK, `email` (unique) |
| 3 | `ngos` | Non-governmental implementing partners | UUID PK, `external_id` (unique), `name`, `registration_number` |
| 4 | `proposals` | Project proposals submitted by NGOs | UUID PK, `public_id` (unique), `ngo_id` FK, `status`, `source_type` |
| 5 | `documents` | Proposal verification files and attachments | UUID PK, `public_id` (unique), `proposal_id` FK, `file_size_bytes` (BIGINT), `sha256` |
| 6 | `projects` | Distinct CSR interventions | UUID PK, `public_id` (unique), `ngo_id` FK, `proposal_id` FK, `requested_amount` (BIGINT paise), `current_funding` (BIGINT paise) |
| 7 | `project_geographies` | Target states, districts, and blocks | UUID PK, `project_id` FK, `state`, `district`, `block` |
| 8 | `impact_dna` | Extracted & computed impact dimensions | UUID PK, `public_id` (unique), `project_id` FK (unique), `need_score` / `impact_score` / etc. (NUMERIC(6,5)), `missing_fields` (JSONB) |
| 9 | `saturation_results` | Regional CSR funding saturation analytics | UUID PK, `project_id` FK, `saturation_index` (NUMERIC(6,5)), `existing_csr_amount` (BIGINT paise) |
| 10 | `due_diligence_reports` | NGO risk evaluation & compliance checks | UUID PK, `public_id` (unique), `ngo_id` FK, `checks` (JSONB), `flags` (JSONB) |
| 11 | `optimization_runs` | Portfolio optimization executions | UUID PK, `public_id` (unique), `budget_paise` (BIGINT paise), `input_snapshot` (JSONB), `result_snapshot` (JSONB), `total_predicted_impact` (NUMERIC(18,4)) |
| 12 | `allocations` | Recommended project funding allocations | UUID PK, `optimization_run_id` FK, `project_id` FK (`RESTRICT`), `allocated_amount` (BIGINT paise), `marginal_score` (NUMERIC(6,5)), `reason_codes` (JSONB) |
| 13 | `reallocation_runs` | Mid-cycle reallocation runs | UUID PK, `public_id` (unique), `previous_optimization_id` FK (`RESTRICT`), `budget_paise` (BIGINT paise), `performance_snapshot` (JSONB) |
| 14 | `audit_events` | Append-only event trail | UUID PK, `public_id` (unique), `event_type`, `request_id`, `run_id`, `payload` (JSONB) |

> **Note on `model_versions`**: As per Technical Contract instructions, `model_versions` is only referenced conceptually and has no defined schema in the contract; its implementation is deferred.

---

## Architecture Overview

```
React Frontend (Web Client)
           ↓
    FastAPI Router (/api/v1)
           ↓
     Service Layer [Phase 2+]
           ↓
    Repository Layer [Phase 2+]
           ↓
  SQLAlchemy 2.0 ORM Models
           ↓
  PostgreSQL (Relational Store)
```

---

## Requirements

- **Python**: 3.10 or higher
- **PostgreSQL**: 15+ (or Docker / Docker Compose)

---

## Configuration & Environment Setup

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Ensure `DATABASE_URL` points to your active PostgreSQL instance:
```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/allocateai
```

---

## Running Database Migrations (Alembic)

To apply all schema migrations up to head:

```bash
# From backend directory
python -m alembic upgrade head
```

To rollback migrations:

```bash
# Rollback one revision
python -m alembic downgrade -1

# Rollback to base
python -m alembic downgrade base
```

---

## Running the Backend

From the `backend/` directory:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **Health Probe**: `GET http://localhost:8000/api/v1/health`
- **Readiness Probe**: `GET http://localhost:8000/api/v1/health/ready`
- **Swagger Documentation**: `GET http://localhost:8000/docs`

---

## Running Tests

Run the complete test suite (Phase 0 + Phase 1):

```bash
# From project root
python -m pytest backend/tests -v

# Or from backend directory
python -m pytest tests -v
```
