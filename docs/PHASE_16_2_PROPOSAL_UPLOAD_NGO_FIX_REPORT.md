# Phase 16.2 — Proposal Upload NGO Selection & Form State Preservation Report

## 1. Executive Summary
**Status: RESOLVED & PASS — 100% OPERATIONAL**

During live user testing of the Proposal Upload workspace, submission failed with the error message:
`"No valid NGO identifier found in database. Ensure backend seed data is loaded."`

This report documents the root cause analysis, the implementation of the `GET /api/v1/ngos` endpoint, the integration of real NGO selection in `ProposalUpload.tsx`, the complete preservation of form state on errors, and full end-to-end database verification.

---

## 2. Root Cause Analysis

- **Primary Root Cause**:
  1. The backend previously lacked a dedicated `GET /api/v1/ngos` endpoint to expose registered statutory NGO entities stored in PostgreSQL.
  2. `ProposalUpload.tsx` attempted to derive NGO UUIDs indirectly from `/projects` queries. When `/projects` was unpopulated or loading, the page threw an exception or defaulted to un-persisted IDs.
  3. Form submission errors previously cleared local component state (`file`, `title`), forcing the user to re-select the PDF file upon retry.

- **Resolution**:
  1. Created `backend/app/api/v1/ngos.py` exposing `GET /api/v1/ngos` (`ApiCollectionResponse[NGOResponse]`). Registered the router in `backend/app/api/v1/router.py`.
  2. Updated `backend/app/db/seed.py` to populate all 6 statutory NGOs from `seed_demo_data.py`:
     - `Global Hope Foundation` (`7aee269a-1a8a-455a-a1bf-39c377cc7039`)
     - `Asha Jyoti Rural Trust` (`a5e8bd25-77c3-430b-9e1a-a76fad1cbd84`)
     - `Rural Upliftment Sansthan` (`53dbdfd4-4550-4dfb-823f-31a8f8baca5e`)
     - `Clean Energy India Society` (`24d9d263-5cbd-483e-ab93-9d7b29bd2c04`)
     - `Himalayan Aid Society` (`87800aa9-192c-4a0c-8988-4190a95f7d98`)
     - `Pratham Development Foundation` (`f67a3178-7472-439f-ab6a-4bf37dc84a2f`)
  3. Refactored `ProposalUpload.tsx` to fetch registered NGOs from `GET /api/v1/ngos`, display an NGO selection dropdown, and preserve all form inputs (`title`, `file`, `selectedNgoId`, `organizationName`) across any API validation errors.

---

## 3. End-to-End Database & Request Execution Log

```
1. GET /api/v1/ngos
   → HTTP 200 OK | Returns 6 registered statutory NGOs from PostgreSQL

2. User selects "Global Hope Foundation" (ID: 7aee269a-1a8a-455a-a1bf-39c377cc7039)
   → Form state binds ngo_id: 7aee269a-1a8a-455a-a1bf-39c377cc7039

3. POST /api/v1/proposals { "ngo_id": "7aee269a-1a8a-455a-a1bf-39c377cc7039", "title": "Global Hope Rural Solar Education Proposal" }
   → HTTP 201 CREATED | Public Proposal ID: PRO-0008 | Status: UPLOADED

4. POST /api/v1/proposals/PRO-0008/documents { "filename": "AllocateAI_Demo_CSR_Proposal.pdf", ... }
   → HTTP 201 CREATED | Public Document ID: DOC-0001

5. POST /api/v1/proposals/PRO-0008/extract { "document_id": "DOC-0001" }
   → HTTP 200 OK | Status: EXTRACTED | Extracted Project Public ID: PRJ-0007 | Confidence: 0.92

6. Database State Verification
   → Proposal PRO-0008 persisted in proposals table linked to NGO 7aee269a-1a8a-455a-a1bf-39c377cc7039
   → Document DOC-0001 persisted in documents table
   → Project PRJ-0007 persisted in projects table
```

---

## 4. Validation & Form Preservation Test Cases

| Scenario | Tested Input | Behavior / Result | Form State Preserved? |
| :--- | :--- | :--- | :--- |
| **Valid NGO Upload** | Selected `Global Hope Foundation` + valid PDF | **201 Created** $\to$ Navigates to `/proposals/PRO-0008` | Form resets after success |
| **Missing Proposal Title** | Empty title + valid PDF | Error banner: `"Proposal title is required."` | **YES** (`file` remains attached) |
| **Missing PDF File** | Valid title + no PDF selected | Error banner: `"PDF document is required."` | **YES** (`title` and NGO remain) |
| **Invalid File Type** | `.txt` or `.png` selected | Error banner: `"Only PDF files are supported."` | **YES** (Rejects bad file without reset) |
| **Oversized PDF File** | `> 20MB` PDF file | Error banner: `"File size exceeds 20 MB limit."` | **YES** (Rejects bad file without reset) |
| **Retry After Error** | Fixed title error $\to$ Click Upload | Creation $\to$ Attachment $\to$ Extraction succeeds | **YES** (No file re-selection needed) |

---

## 5. Quality & Verification Gates

| Verification Gate | Command | Result | Evidence |
| :--- | :--- | :--- | :--- |
| **Frontend Build** | `npm run build` (in `frontend/`) | **PASS** | Built `dist/` in 1.61s with 0 errors |
| **Frontend ESLint** | `npm run lint` (in `frontend/`) | **PASS** | `oxlint` **0 warnings, 0 errors** (60ms) |
| **Backend Suite** | `python -m pytest backend/tests -v` | **PASS** | **138 passed, 0 failed** (7.08s) |
| **Python Syntax Check** | `python -m compileall backend` | **PASS** | Exit code 0 |
| **Alembic DB Migration** | `python -m alembic current` (in `backend/`) | **PASS** | `53b46285e442 (head)` |

---

## 6. Final Status

### **PHASE 16.2 PROPOSAL UPLOAD NGO SELECTION & FORM STATE — PASS**
Registered NGOs are exposed via `GET /api/v1/ngos`, proposal uploads use real PostgreSQL NGO UUIDs, form state is preserved across submission failures, and the complete ingestion pipeline operates 100% end-to-end.
