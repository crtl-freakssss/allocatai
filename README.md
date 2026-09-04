\# AllocatAI

### AI-Powered CSR Fund Allocation & Project Prioritization

> **Find where the next rupee of CSR budget creates the most additional impact — not just which project scores highest.**

AllocateAI is an intelligent CSR fund allocation platform designed to help CSR committees move from spreadsheet-based project evaluation to **data-driven, constraint-aware and explainable capital allocation**.

Instead of simply ranking NGO proposals, AllocateAI evaluates projects using **Impact DNA, project scoring, regional CSR saturation and marginal impact**, then uses a deterministic **Mixed-Integer Linear Programming (MILP)** optimizer to determine how a limited CSR budget should be distributed.

---

## Table of Contents

- [Overview](#overview)
- [Problem](#problem)
- [Solution](#solution)
- [Key Differentiators](#key-differentiators)
- [How AllocateAI Works](#how-allocateai-works)
- [System Architecture](#system-architecture)
- [Repository Structure](#repository-structure)
- [Technology Stack](#technology-stack)
- [Core Modules](#core-modules)
- [AI Pipeline](#ai-pipeline)
- [Scoring Engine](#scoring-engine)
- [CSR Saturation Engine](#csr-saturation-engine)
- [Marginal Impact Engine](#marginal-impact-engine)
- [MILP Optimization](#milp-optimization)
- [Reallocation Engine](#reallocation-engine)
- [Due Diligence](#due-diligence)
- [Auditability](#auditability)
- [Data & Financial Integrity](#data--financial-integrity)
- [API Overview](#api-overview)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [End-to-End Workflow](#end-to-end-workflow)
- [Testing](#testing)
- [Security](#security)
- [Design Principles](#design-principles)
- [Current Validation](#current-validation)
- [Limitations](#limitations)
- [Future Roadmap](#future-roadmap)
- [Team Architecture](#team-architecture)
- [Project Status](#project-status)
- [License](#license)

---

# Overview

CSR committees frequently evaluate multiple projects competing for a limited annual CSR budget.

Traditional workflow:

```text
NGO Proposals
     ↓
Spreadsheet
     ↓
Manual Scoring
     ↓
Committee Discussion
     ↓
Funding Decision
```

The highest-scoring project is not necessarily the project where the **next rupee of funding creates the greatest additional impact**.

AllocateAI turns the process into:

```text
Proposal
   ↓
AI Extraction
   ↓
Impact DNA
   ↓
Project Scoring
   ↓
Regional Saturation
   ↓
Marginal Impact
   ↓
MILP Optimization
   ↓
Allocation
   ↓
Performance Monitoring
   ↓
Reallocation
   ↓
Audit Trail
```

---

# Problem

CSR committees face several challenges:

### 1. Manual evaluation
Large numbers of proposals are often compared using spreadsheets and subjective scoring.

### 2. Ranking is not allocation
Knowing which project is best does not answer:

> How should ₹X crore actually be split across the portfolio?

### 3. Regional concentration
Funding can become concentrated in regions that already receive significant CSR support.

### 4. Diminishing returns
Additional funding to an already well-funded project may produce less additional impact than funding an underserved project.

### 5. Limited explainability
A final allocation needs to be defensible to internal stakeholders, auditors and decision-makers.

---

# Solution

AllocateAI combines AI-assisted document understanding with deterministic optimization.

The system:

1. Accepts CSR project proposals.
2. Extracts structured information from proposal documents.
3. Generates project-level Impact DNA.
4. Calculates normalized project scores.
5. Measures regional CSR saturation.
6. Estimates marginal impact.
7. Optimizes allocation under budget and equity constraints.
8. Stores optimization runs and allocation results.
9. Supports performance-based reallocation.
10. Maintains an append-only audit trail.

---

# Key Differentiators

## 1. Marginal Impact Engine

Most systems ask:

> Which project is best?

AllocateAI asks:

> **Where does the next rupee create the most additional impact?**

This enables funding decisions based on incremental impact rather than only absolute project scores.

## 2. CSR Saturation Index

AllocateAI considers how much CSR funding is already concentrated within a region.

```text
Regional CSR Funding
        +
Regional Benchmark
        ↓
Saturation Index
        ↓
Additional-impact adjustment
```

## 3. AI Impact DNA

Proposal documents are transformed into structured project characteristics.

```text
PDF
 ↓
Extraction
 ↓
Structured Project Data
 ↓
Impact DNA
```

## 4. Deterministic Allocation

The LLM is **not the final decision-maker**.

```text
AI
 ↓
Understand proposals
```

is separated from:

```text
Mathematical Engine
 ↓
Make allocation decisions
```

This makes allocation more reproducible and auditable.

## 5. Closed-Loop Allocation

```text
Initial Allocation
       ↓
Project Performance
       ↓
Performance Velocity
       ↓
Reallocation
       ↓
Updated Portfolio
```

---

# How AllocateAI Works

```text
                  ┌─────────────────┐
                  │  CSR Committee  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ React Frontend  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   FastAPI API   │
                  └────────┬────────┘
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
      ┌──────────────┐          ┌────────────────┐
      │  AI Pipeline │          │ Decision Engine│
      └──────┬───────┘          └───────┬────────┘
             │                          │
             ▼                          ▼
      Impact DNA                   Scoring
      Extraction                   Saturation
      Evidence                     Marginal Impact
      Due Diligence                MILP Optimization
             │                          │
             └────────────┬─────────────┘
                          ▼
                  ┌───────────────┐
                  │  PostgreSQL   │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Audit / Trace │
                  └───────────────┘
```

---

# System Architecture

```text
Frontend
   ↓
REST API
   ↓
Services
   ↓
AI / Decision Engines
   ↓
Repositories
   ↓
PostgreSQL
```

### Frontend
Responsible for user interaction, dashboards, forms, visualizations, optimization controls, API state and loading/error states.

### Backend
Responsible for business logic, validation, orchestration, persistence, AI integration, optimization and auditability.

### AI Layer
Responsible for document extraction, structured interpretation, Impact DNA and evidence extraction.

### Decision Engine
Responsible for scoring, saturation, marginal impact, MILP optimization and reallocation.

### Database
Responsible for persistent state, relationships, financial values, optimization snapshots and audit records.

---

# Repository Structure

```text
AllocateAI/
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       ├── api/
│       │   └── client.ts
│       ├── types/
│       │   └── index.ts
│       ├── utils/
│       │   └── money.ts
│       ├── router/
│       │   └── index.tsx
│       ├── components/
│       │   ├── Navbar.tsx
│       │   ├── Sidebar.tsx
│       │   ├── StatCard.tsx
│       │   ├── ImpactDnaRadar.tsx
│       │   ├── AllocationTable.tsx
│       │   └── AuditTimeline.tsx
│       └── pages/
│           ├── DashboardPage.tsx
│           ├── ProposalsPage.tsx
│           ├── ProjectsPage.tsx
│           ├── OptimizationPage.tsx
│           ├── ReallocationPage.tsx
│           ├── SaturationPage.tsx
│           ├── DueDiligencePage.tsx
│           └── AuditPage.tsx
│
├── backend/
│   ├── ...
│   ├── API routers
│   ├── services
│   ├── repositories
│   ├── schemas
│   ├── database models
│   ├── AI pipeline
│   ├── optimization engines
│   └── tests
│
├── alembic/
│   ├── env.py
│   └── versions/
│
├── docs/
├── uploads/
├── docker-compose.yml
├── .gitignore
└── README.md
```

> The repository filesystem is the authoritative source for the exact current file tree.

---

# Technology Stack

## Frontend

| Technology | Purpose |
|---|---|
| React 19 | UI framework |
| TypeScript | Type safety |
| Vite | Build tooling |
| React Router 7 | Routing |
| React Query 5 | Server state |
| Tailwind CSS 4 | Styling |
| Recharts | Visualization |

## Backend

| Technology | Purpose |
|---|---|
| Python | Backend language |
| FastAPI | REST API |
| Pydantic | Validation/contracts |
| SQLAlchemy | Database access |
| Alembic | Database migrations |
| PostgreSQL | Persistent storage |

## AI

- PDF processing
- structured extraction
- LLM integration
- Impact DNA generation
- evidence extraction
- deterministic offline fallback

## Optimization

- SciPy
- Mixed-Integer Linear Programming
- piecewise-linear marginal utility
- saturation-based decay

---

# Core Modules

## Proposal Management

Handles:

- proposal creation
- proposal retrieval
- proposal validation
- proposal-to-project lifecycle

## Document Management

Handles:

- PDF upload
- file validation
- file storage
- SHA-256 fingerprinting
- extraction

---

# AI Pipeline

```text
Document
   ↓
Text Extraction
   ↓
AI Extraction
   ↓
Canonical Schema
```

The canonical backend schemas remain authoritative.

The system supports an offline deterministic fallback when live LLM access is unavailable.

---

# Scoring Engine

Project attributes are transformed into normalized scores.

Scores are represented internally on:

```text
0.0 → 1.0
```

For example:

```text
0.84
```

can be displayed as:

```text
84%
```

The frontend does not independently recalculate authoritative scores.

---

# CSR Saturation Engine

The saturation layer evaluates regional funding concentration.

```text
Regional Funding
       +
Benchmark
       ↓
Saturation
       ↓
Marginal-impact adjustment
```

The current implementation uses the `sat-v1` calculation version.

---

# Marginal Impact Engine

The implementation uses:

- saturation-based decay
- diminishing marginal utility
- discrete funding tranches
- piecewise-linear concave utility

Conceptually:

```text
Funding
   │
   ▼
Marginal Impact
   │
   ├── Tranche 1 → high impact
   ├── Tranche 2 → lower impact
   └── Tranche 3 → lower impact
```

---

# MILP Optimization

Canonical path:

```text
OptimizationService
        ↓
RealOptimizationEngine
        ↓
MILPOptimizerFormulation
        ↓
SciPy MILP
        ↓
Optimization Result
```

The optimizer considers:

- total CSR budget
- project-level allocation caps
- regional constraints
- underserved-region allocation floor
- optimization weights
- marginal impact
- saturation

### Financial constraint

```text
Allocated + Unallocated = Total Budget
```

Allocations must be non-negative and satisfy configured project and regional constraints.

---

# Reallocation Engine

```text
Original Allocation
       ↓
Performance Information
       ↓
Performance Velocity
       ↓
Reallocation Optimization
       ↓
Updated Allocation
```

---

# Due Diligence

AllocateAI provides structured due-diligence information for projects and organizations.

> AllocateAI's due-diligence functionality is **not legal certification or government verification**.

---

# Auditability

Important system events are recorded in an append-only audit trail.

```text
Proposal Created
      ↓
Document Uploaded
      ↓
Extraction Completed
      ↓
Project Created
      ↓
Optimization Run
      ↓
Allocation Generated
      ↓
Reallocation
```

Optimization runs retain relevant calculation/configuration information so decisions can be traced.

---

# Data & Financial Integrity

AllocateAI uses integer paise for monetary persistence and API values.

```text
₹1 = 100 paise
```

Example:

```text
₹10,000
=
1,000,000 paise
```

Money is represented internally using integers rather than floating-point arithmetic.

---

# Public IDs

Official identifiers are generated by the backend.

```text
PRO-xxxx   Proposal
DOC-xxxx   Document
PRJ-xxxx   Project
OPT-xxxx   Optimization Run
REA-xxxx   Reallocation Run
```

The frontend does not generate authoritative IDs.

---

# API Overview

API version:

```text
/api/v1
```

Representative endpoints:

```http
POST /api/v1/proposals
POST /api/v1/proposals/{proposal_id}/documents
POST /api/v1/proposals/{proposal_id}/extract
POST /api/v1/optimization/runs
GET  /api/v1/optimization/runs/{run_id}
POST /api/v1/reallocation/runs
```

The backend API contracts and Pydantic schemas are authoritative.

## Response envelope

```json
{
  "data": {},
  "meta": {
    "request_id": "...",
    "schema_version": "...",
    "timestamp": "..."
  }
}
```

## Error envelope

```json
{
  "error": {
    "code": "...",
    "message": "...",
    "details": {},
    "request_id": "..."
  }
}
```

---

# Installation

## Requirements

```text
Python 3.10+
Node.js
npm
PostgreSQL 18
Git
```

## Clone

```bash
git clone https://github.com/crtl-freakssss/csr-.git
cd csr-
```

## Backend

### Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies from the repository's backend dependency configuration.

Development validation used:

```text
Host: localhost
Port: 5433
Database: allocateai
```

Run migrations:

```bash
python -m alembic upgrade head
```

Check migration:

```bash
python -m alembic current
```

## Frontend

```bash
cd frontend
npm install
```

Configure:

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

# Running the Application

Start the FastAPI backend on:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

Start the frontend:

```bash
cd frontend
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# End-to-End Workflow

```text
1. Dashboard
        ↓
2. Create Proposal
        ↓
3. Upload PDF
        ↓
4. Extract Proposal
        ↓
5. Generate Project / Impact DNA
        ↓
6. Inspect Project
        ↓
7. Inspect Regional Saturation
        ↓
8. Configure Optimization
        ↓
9. Execute MILP Optimization
        ↓
10. Review Allocations
        ↓
11. Explain Decision
        ↓
12. Run Reallocation
        ↓
13. Review Due Diligence
        ↓
14. Review Audit Trail
```

---

# Testing

## Frontend build

```bash
cd frontend
npm run build
```

## Frontend lint

```bash
npm run lint
```

## Backend tests

```bash
python -m pytest backend/tests -v
```

## Backend compilation

```bash
python -m compileall backend
```

## Alembic

```bash
python -m alembic current
```

---

# Current Validation

Backend regression validation:

```text
138 passed
0 failed
0 skipped
0 errors
```

Frontend:

```text
Build: PASS
Lint: PASS
```

Backend compilation:

```text
PASS
```

Alembic validation during final verification:

```text
53b46285e442
```

---

# Security

The application includes:

- environment-based configuration
- no committed API secrets
- file type validation
- file size validation
- SHA-256 file fingerprinting
- path traversal protection
- structured error responses
- Pydantic validation
- database foreign-key enforcement
- controlled CORS configuration

---

# Design Principles

### Backend is the source of truth

The frontend does not independently reproduce business logic.

### AI does not directly control allocation

AI extracts and interprets information. Mathematical engines make allocation decisions.

### Financial values are integers

Money is represented in paise.

### IDs are backend-owned

Official IDs are generated by the backend.

### Optimization is reproducible

Given equivalent inputs, constraints and calculation versions, the deterministic optimization pipeline produces reproducible results.

### Auditability by design

Important actions and optimization decisions are traceable.

---

# Current Scope

Included:

- CSR proposal ingestion
- PDF upload
- AI-assisted extraction
- Impact DNA
- Project scoring
- Regional saturation
- Marginal impact
- Budget optimization
- MILP allocation
- Regional equity constraints
- Reallocation
- Due diligence information
- Audit trail
- React dashboard
- PostgreSQL persistence

---

# Out of Scope

The current implementation does not attempt to provide:

- government-certified NGO verification
- actual CSR fund disbursement
- payment processing
- live government need-index integration
- automatic legal certification
- BRSR/CSR-2 report generation
- fully autonomous CSR decision-making

---

# Limitations

The current system is a hackathon/prototype decision-support platform.

Production deployment would require:

- validated real-world CSR datasets
- live government datasets
- comprehensive NGO verification
- larger-scale optimization benchmarking
- formal model validation
- security penetration testing
- enterprise authentication and authorization
- production infrastructure
- monitoring and observability
- real CSR committee feedback

---

# Future Roadmap

## Phase 1 — Data Expansion

- Census data
- NFHS datasets
- district-level development indicators
- additional CSR funding datasets

## Phase 2 — NGO Due Diligence

- NGO verification
- historical project performance
- statutory information
- financial indicators
- evidence quality

## Phase 3 — Enterprise Deployment

- authentication
- role-based access control
- organization workspaces
- approval workflows
- multi-user collaboration
- enterprise audit controls

## Phase 4 — Continuous Impact Monitoring

```text
Funded Project
      ↓
Actual Outcomes
      ↓
Impact Measurement
      ↓
Model Feedback
      ↓
Future Allocation
```

---

# Team Architecture

### Member A — Frontend / Product UX

- React interface
- dashboards
- user workflows
- visualizations
- frontend UX

### Member B — AI / Data Pipeline

- PDF extraction
- AI integration
- Impact DNA
- evidence processing

### Member C — Quant / Optimization

- scoring
- saturation
- marginal impact
- MILP formulation
- reallocation logic

### Member D — Backend / Platform

- FastAPI
- PostgreSQL
- repositories
- services
- API integration
- persistence
- audit
- frontend/backend integration

---

# Development Phases

```text
Phase 0
Backend foundation

Phase 1
Database architecture

Phase 2
Schemas / contracts

Phase 3
Repositories

Phase 4
Services

Phase 5
REST API

Phase 6
AI + scoring + optimization

Phase 7
E2E backend hardening

Phase 8–13
Backend verification / production hardening

Phase 14
Frontend ↔ Backend integration

Phase 15
Production-readiness audit
```

---

# Project Status

```text
┌─────────────────────────────────────┐
│         ALLOCATEAI STATUS           │
├─────────────────────────────────────┤
│ Frontend Build          PASS        │
│ Frontend Lint           PASS        │
│ Backend Tests           138 PASS    │
│ Backend Compilation     PASS        │
│ Database Migrations     PASS        │
│ API Integration         COMPLETE*   │
│ E2E Validation          COMPLETE*   │
└─────────────────────────────────────┘
```

`*` Final production-readiness status should be interpreted together with the latest Phase 15/15.1 verification report and actual browser verification.

---

# Demo

Frontend:

```text
http://localhost:5173
```

Backend:

```text
http://localhost:8000
```

API Documentation:

```text
http://localhost:8000/docs
```

Recommended demo:

```text
Dashboard
   ↓
Create Proposal
   ↓
Upload CSR PDF
   ↓
AI Extraction
   ↓
Impact DNA
   ↓
Saturation
   ↓
MILP Optimization
   ↓
Allocation
   ↓
Reallocation
   ↓
Audit
```

---

# Core Pitch

> **AllocateAI doesn't just tell CSR committees which project is best. It determines how to distribute a limited CSR budget so that the next rupee produces the greatest additional impact, while accounting for project constraints, regional saturation and marginal returns.**

---

# Final Architecture

```text
                         ALLOCATEAI
                             │
                             ▼
                    ┌─────────────────┐
                    │ REACT FRONTEND  │
                    └────────┬────────┘
                             │
                         REST API
                             │
                             ▼
                    ┌─────────────────┐
                    │     FASTAPI     │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
       ┌──────────────┐             ┌─────────────────┐
       │ AI PIPELINE  │             │ DECISION ENGINE │
       │              │             │                 │
       │ Extraction   │             │ Scoring         │
       │ Impact DNA   │             │ Saturation      │
       │ Evidence     │             │ Marginal Impact │
       │ Due Diligence│             │ MILP            │
       └──────┬───────┘             │ Reallocation    │
              │                     └────────┬────────┘
              │                              │
              └──────────────┬───────────────┘
                             ▼
                    ┌─────────────────┐
                    │  REPOSITORIES   │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │  POSTGRESQL 18  │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ AUDIT / TRACE   │
                    └─────────────────┘
```

**Upload → Extract → Understand → Score → Measure Saturation → Calculate Marginal Impact → Optimize → Allocate → Monitor → Reallocate → Audit.**

---

# Repository

GitHub:

https://github.com/crtl-freakssss/allocatai
