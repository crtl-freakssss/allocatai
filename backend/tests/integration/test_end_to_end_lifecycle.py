import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.repositories import NGORepository
from app.schemas.enums import ProposalStatus, OptimizationStatus


@pytest.fixture(scope="module", autouse=True)
def cleanup_database():
    yield
    with SessionLocal() as session:
        from sqlalchemy import text
        session.execute(
            text(
                "TRUNCATE audit_events, allocations, reallocation_runs, "
                "optimization_runs, saturation_results, impact_dna, "
                "project_geographies, projects, documents, proposals, "
                "users, ngos, organizations CASCADE;"
            )
        )
        session.commit()


@pytest.fixture(scope="module")
def seeded_ngo_id():
    with SessionLocal() as session:
        ngo_repo = NGORepository(session)
        ngo = ngo_repo.create(
            name="Himalayan Upliftment Trust",
            external_id=f"NGO-LIFECYCLE-{uuid.uuid4().hex[:6]}",
            registration_number="REG-HUT-2026",
        )
        session.commit()
        return str(ngo.id)


def test_complete_proposal_to_reallocation_lifecycle(seeded_ngo_id):
    """End-to-end integration test executing the complete lifecycle:
    Proposal -> Document Attachment -> AI Extraction -> Project Creation -> Portfolio Optimization -> Reallocation -> Audit Trail.
    """
    client = TestClient(app)

    # 1. Health check
    h_res = client.get("/api/v1/health")
    assert h_res.status_code == status.HTTP_200_OK

    # 2. Ingest Proposal (POST /api/v1/proposals)
    prop_res = client.post(
        "/api/v1/proposals",
        json={
            "ngo_id": seeded_ngo_id,
            "title": "Assam Rural Clean Drinking Water Station",
            "source_type": "PDF_UPLOAD",
        },
    )
    assert prop_res.status_code == status.HTTP_201_CREATED
    prop_data = prop_res.json()["data"]
    proposal_id = prop_data["proposal_id"]
    assert proposal_id.startswith("PRO-")

    # 3. Attach Document Metadata (POST /api/v1/proposals/{id}/documents)
    doc_res = client.post(
        f"/api/v1/proposals/{proposal_id}/documents",
        json={
            "filename": "assam_water_proposal_plan.pdf",
            "mime_type": "application/pdf",
            "storage_key": f"uploads/{proposal_id}/water.pdf",
            "file_size_bytes": 1024 * 400,
            "sha256": "a" * 64,
        },
    )
    assert doc_res.status_code == status.HTTP_201_CREATED
    doc_data = doc_res.json()["data"]
    document_id = doc_data["document_id"]
    assert document_id.startswith("DOC-")

    # 4. Trigger AI Extraction (POST /api/v1/proposals/{id}/extract)
    ext_res = client.post(
        f"/api/v1/proposals/{proposal_id}/extract",
        json={"document_id": document_id},
    )
    assert ext_res.status_code == status.HTTP_200_OK
    ext_data = ext_res.json()["data"]
    project_id = ext_data["project_id"]
    assert project_id.startswith("PRJ-")
    assert ext_data["status"] in [ProposalStatus.EXTRACTED.value, ProposalStatus.VALIDATION_REQUIRED.value]

    # 5. Fetch Project Details (GET /api/v1/projects/{id})
    prj_res = client.get(f"/api/v1/projects/{project_id}")
    assert prj_res.status_code == status.HTTP_200_OK
    prj_data = prj_res.json()["data"]
    assert prj_data["project_id"] == project_id
    assert prj_data["financials"]["requested_amount_paise"] > 0

    # 6. Run Portfolio Optimization (POST /api/v1/optimization/runs)
    opt_res = client.post(
        "/api/v1/optimization/runs",
        json={
            "budget_paise": 1000_000_000,  # ₹10 Crore
            "project_ids": [project_id],
            "weights": {
                "need": 0.3,
                "marginal_impact": 0.3,
                "cost_efficiency": 0.2,
                "evidence": 0.1,
                "scalability": 0.05,
                "equity": 0.03,
                "risk_penalty": 0.02,
            },
            "constraints": {
                "max_allocation_per_project_paise": 1000_000_000,
                "regional_equity_enabled": True,
            },
        },
    )
    assert opt_res.status_code == status.HTTP_201_CREATED
    opt_data = opt_res.json()["data"]
    opt_run_id = opt_data["run_id"]
    assert opt_run_id.startswith("OPT-")
    assert opt_data["status"] == OptimizationStatus.COMPLETED.value

    # Conservation Invariant Check
    assert opt_data["allocated_paise"] + opt_data["unallocated_paise"] == 1000_000_000

    # 7. Run Mid-Cycle Capital Reallocation (POST /api/v1/reallocation/runs)
    realloc_res = client.post(
        "/api/v1/reallocation/runs",
        json={
            "previous_run_id": opt_run_id,
            "budget_paise": 1000_000_000,
            "performance_updates": [
                {
                    "project_id": project_id,
                    "progress_percent": 85.0,
                    "actual_spend_paise": 200_000_000,
                }
            ],
            "weights": {
                "need": 0.3,
                "marginal_impact": 0.3,
                "cost_efficiency": 0.2,
                "evidence": 0.1,
                "scalability": 0.05,
                "equity": 0.03,
                "risk_penalty": 0.02,
            },
            "constraints": {"regional_equity_enabled": True},
        },
    )
    assert realloc_res.status_code == status.HTTP_201_CREATED
    realloc_data = realloc_res.json()["data"]
    realloc_run_id = realloc_data["run_id"]
    assert realloc_run_id.startswith("REA-")
    assert realloc_data["previous_run_id"] == opt_run_id

    # 8. Query Audit Trail (GET /api/v1/audit/events)
    audit_res = client.get("/api/v1/audit/events?page=1&page_size=50")
    assert audit_res.status_code == status.HTTP_200_OK
    audit_data = audit_res.json()["data"]
    assert len(audit_data) >= 4
