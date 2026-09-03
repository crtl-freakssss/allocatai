import uuid
import pytest
from fastapi import status

from sqlalchemy import text
from app.db.session import SessionLocal
from app.repositories import NGORepository


@pytest.fixture(scope="module", autouse=True)
def cleanup_after_endpoints():
    """Ensure all test tables are cleanly wiped after endpoint testing to keep suite hermetic."""
    yield
    with SessionLocal() as session:
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
def seeded_ngo():
    """Seed an NGO in the database for endpoint testing."""
    session = SessionLocal()
    ngo_repo = NGORepository(session)
    ngo = ngo_repo.create(
        name="Global Hope Foundation",
        external_id=f"NGO-SEED-{uuid.uuid4().hex[:6]}",
        registration_number="REG-GHF-2026",
    )
    session.commit()
    ngo_id = ngo.id
    session.close()
    return ngo_id


# ==============================================================================
# Proposals & Documents & Extraction Endpoints
# ==============================================================================

def test_create_and_get_proposal(client, seeded_ngo):
    """Test POST /api/v1/proposals and GET /api/v1/proposals/{id}."""
    # 1. Create proposal
    payload = {
        "ngo_id": str(seeded_ngo),
        "title": "Clean Drinking Water for Marathwada",
        "source_type": "DIRECT_SUBMISSION",
    }
    resp = client.post("/api/v1/proposals", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    body = resp.json()
    assert "data" in body
    assert "meta" in body
    prop_id = body["data"]["proposal_id"]
    assert prop_id.startswith("PRO-")
    assert body["data"]["status"] == "UPLOADED"

    # 2. Get proposal by public ID
    get_resp = client.get(f"/api/v1/proposals/{prop_id}")
    assert get_resp.status_code == status.HTTP_200_OK
    get_body = get_resp.json()
    assert get_body["data"]["proposal_id"] == prop_id
    assert get_body["data"]["title"] == "Clean Drinking Water for Marathwada"

    # 3. Get nonexistent proposal returns 404
    missing_resp = client.get("/api/v1/proposals/PRO-NONEXISTENT")
    assert missing_resp.status_code == status.HTTP_404_NOT_FOUND
    assert missing_resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_create_proposal_missing_ngo(client):
    """Test POST /api/v1/proposals with invalid NGO UUID returns 404."""
    payload = {
        "ngo_id": str(uuid.uuid4()),
        "title": "Orphan Proposal",
    }
    resp = client.post("/api/v1/proposals", json=payload)
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_list_proposals(client, seeded_ngo):
    """Test GET /api/v1/proposals with pagination."""
    resp = client.get(f"/api/v1/proposals?ngo_id={seeded_ngo}&page=1&page_size=10")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert isinstance(body["data"], list)
    assert body["meta"]["pagination"]["total"] >= 1


def test_documents_lifecycle_and_extraction(client, seeded_ngo):
    """Test POST /api/v1/proposals/{id}/documents, GET documents, and POST extract."""
    # 1. Create a fresh proposal
    prop_resp = client.post(
        "/api/v1/proposals",
        json={"ngo_id": str(seeded_ngo), "title": "Extraction Test Project"},
    )
    prop_id = prop_resp.json()["data"]["proposal_id"]

    # 2. Attach document
    sha = "1" * 64
    doc_resp = client.post(
        f"/api/v1/proposals/{prop_id}/documents",
        json={
            "filename": "water_purification_specs.pdf",
            "mime_type": "application/pdf",
            "storage_key": "s3://allocateai/water_specs.pdf",
            "file_size_bytes": 102400,
            "sha256": sha,
        },
    )
    assert doc_resp.status_code == status.HTTP_201_CREATED
    doc_body = doc_resp.json()
    doc_id = doc_body["data"]["document_id"]
    assert doc_id.startswith("DOC-")

    # 3. Duplicate attachment returns 409
    dup_resp = client.post(
        f"/api/v1/proposals/{prop_id}/documents",
        json={
            "filename": "water_purification_specs.pdf",
            "mime_type": "application/pdf",
            "storage_key": "s3://allocateai/water_specs.pdf",
            "file_size_bytes": 102400,
            "sha256": sha,
        },
    )
    assert dup_resp.status_code == status.HTTP_409_CONFLICT
    assert dup_resp.json()["error"]["code"] == "RESOURCE_ALREADY_EXISTS"

    # 4. List documents
    list_resp = client.get(f"/api/v1/proposals/{prop_id}/documents")
    assert list_resp.status_code == status.HTTP_200_OK
    assert len(list_resp.json()["data"]) == 1

    # 5. Extract proposal
    extract_resp = client.post(
        f"/api/v1/proposals/{prop_id}/extract",
        json={"document_id": doc_id},
    )
    assert extract_resp.status_code == status.HTTP_200_OK
    extract_body = extract_resp.json()["data"]
    assert extract_body["proposal_id"] == prop_id
    assert extract_body["project_id"].startswith("PRJ-")
    assert extract_body["extraction_confidence"] > 0


# ==============================================================================
# Projects Endpoints
# ==============================================================================

def test_create_and_get_project(client, seeded_ngo):
    """Test POST /api/v1/projects and GET /api/v1/projects/{id}."""
    payload = {
        "name": "Solar Powered Cold Storage Units",
        "ngo_id": str(seeded_ngo),
        "sector": "RURAL_DEVELOPMENT",
        "geographies": [{"state": "Maharashtra", "district": "Nashik", "block": "Dindori"}],
        "beneficiary_profile": {"target_count": 1500},
        "financials": {
            "requested_amount_paise": 750000000,
            "current_funding_paise": 0,
        },
        "duration_months": 18,
        "description": "Post-harvest solar cooling facilities for smallholder farmers.",
    }
    resp = client.post("/api/v1/projects", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    body = resp.json()["data"]
    proj_id = body["project_id"]
    assert proj_id.startswith("PRJ-")
    assert body["name"] == "Solar Powered Cold Storage Units"

    # Get project by public ID
    get_resp = client.get(f"/api/v1/projects/{proj_id}")
    assert get_resp.status_code == status.HTTP_200_OK
    assert get_resp.json()["data"]["project_id"] == proj_id

    # List projects
    list_resp = client.get("/api/v1/projects?page=1&page_size=5")
    assert list_resp.status_code == status.HTTP_200_OK
    assert list_resp.json()["meta"]["pagination"]["total"] >= 1


# ==============================================================================
# Optimization & Reallocation Endpoints
# ==============================================================================

def test_optimization_run_workflow(client, seeded_ngo):
    """Test POST /api/v1/optimization/runs and GET /api/v1/optimization/runs/{id}."""
    # 1. Create a project to optimize
    p_resp = client.post(
        "/api/v1/projects",
        json={
            "name": "Optimized Health Camps",
            "ngo_id": str(seeded_ngo),
            "sector": "HEALTHCARE",
            "geographies": [{"state": "Assam"}],
            "beneficiary_profile": {"target_count": 2000},
            "financials": {"requested_amount_paise": 500000000},
            "duration_months": 12,
        },
    )
    proj_id = p_resp.json()["data"]["project_id"]

    # 2. Trigger optimization run
    opt_payload = {
        "budget_paise": 500000000,
        "project_ids": [proj_id],
        "weights": {
            "need": 0.3,
            "marginal_impact": 0.3,
            "cost_efficiency": 0.2,
            "evidence": 0.1,
            "scalability": 0.05,
            "equity": 0.03,
            "risk_penalty": 0.02,
        },
        "constraints": {},
    }
    opt_resp = client.post("/api/v1/optimization/runs", json=opt_payload)
    assert opt_resp.status_code == status.HTTP_201_CREATED
    opt_body = opt_resp.json()["data"]
    run_id = opt_body["run_id"]
    assert run_id.startswith("OPT-")
    assert opt_body["status"] == "COMPLETED"
    assert opt_body["allocated_paise"] == 500000000

    # 3. Get run details
    get_opt = client.get(f"/api/v1/optimization/runs/{run_id}")
    assert get_opt.status_code == status.HTTP_200_OK
    assert get_opt.json()["data"]["run_id"] == run_id
    assert len(get_opt.json()["data"]["allocations"]) == 1

    # 4. Trigger reallocation
    realloc_payload = {
        "previous_run_id": run_id,
        "budget_paise": 500000000,
        "performance_updates": [
            {
                "project_id": proj_id,
                "progress_percent": 85.0,
                "actual_spend_paise": 400000000,
            }
        ],
        "weights": opt_payload["weights"],
        "constraints": {},
    }
    realloc_resp = client.post("/api/v1/reallocation/runs", json=realloc_payload)
    assert realloc_resp.status_code == status.HTTP_201_CREATED
    realloc_body = realloc_resp.json()["data"]
    realloc_id = realloc_body["run_id"]
    assert realloc_id.startswith("REA-")


# ==============================================================================
# Due Diligence Endpoints
# ==============================================================================

def test_due_diligence_endpoints(client, seeded_ngo):
    """Test POST /api/v1/due-diligence/{ngo_id}/evaluate and GET /api/v1/due-diligence/{ngo_id}."""
    eval_resp = client.post(f"/api/v1/due-diligence/{seeded_ngo}/evaluate")
    assert eval_resp.status_code == status.HTTP_201_CREATED
    eval_body = eval_resp.json()["data"]
    assert eval_body["report_id"].startswith("DD-")
    assert eval_body["overall_status"] == "VERIFIED"
    assert "does not constitute legal or regulatory certification" in eval_body["disclaimer"]

    # Get latest
    get_resp = client.get(f"/api/v1/due-diligence/{seeded_ngo}")
    assert get_resp.status_code == status.HTTP_200_OK
    assert get_resp.json()["data"]["report_id"] == eval_body["report_id"]


# ==============================================================================
# Audit Endpoints
# ==============================================================================

def test_audit_endpoints(client):
    """Test GET /api/v1/audit/events and GET /api/v1/audit/events/{id}."""
    resp = client.get("/api/v1/audit/events?page=1&page_size=5")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert isinstance(body["data"], list)
    if body["data"]:
        event_id = body["data"][0]["public_id"]
        single_resp = client.get(f"/api/v1/audit/events/{event_id}")
        assert single_resp.status_code == status.HTTP_200_OK
        assert single_resp.json()["data"]["public_id"] == event_id
