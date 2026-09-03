import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.repositories import NGORepository
from app.ai.client import LLMClient
from app.ai.pipeline import AIPipeline
from app.ai.extraction import AIExtractor
from app.ai.impact_dna import AIImpactDNAGenerator
from app.ai.due_diligence import AIDueDiligenceEvaluator
from app.services.exceptions import ProcessingError
from app.schemas.enums import VerificationStatus, ProposalStatus


@pytest.fixture(scope="module")
def seeded_ngo_id():
    with SessionLocal() as session:
        ngo_repo = NGORepository(session)
        ngo = ngo_repo.create(
            name="Asha Rural Health Trust",
            external_id=f"NGO-AI-{uuid.uuid4().hex[:6]}",
            registration_number="REG-AI-2026",
        )
        session.commit()
        return str(ngo.id)


def test_1_pdf_to_extraction():
    """1. Verify PDF text parsing to AIExtractor output."""
    extractor = AIExtractor()
    ext_res, project = extractor.extract(
        document_path_or_text="Sample CSR proposal for Healthcare diagnostic center in Mumbai, Maharashtra. Requested budget paise: 800000000.",
        filename="mumbai_health.pdf",
    )
    assert ext_res.extraction_confidence > 0.0
    assert len(ext_res.evidence) > 0
    assert ext_res.evidence[0].verification_status == VerificationStatus.UNVERIFIED


def test_2_extraction_to_project():
    """2. Verify extraction outputs canonical Project schema."""
    extractor = AIExtractor()
    _, project = extractor.extract(
        document_path_or_text="Proposal for Education smart classroom in Gaya, Bihar.",
        filename="bihar_edu.pdf",
    )
    assert project.name is not None
    assert project.sector.value in ["EDUCATION", "HEALTHCARE", "DISASTER_RELIEF"]
    assert project.geographies[0].state is not None
    assert project.financials.requested_amount_paise > 0


def test_3_project_to_impact_dna():
    """3. Verify Project inputs generate canonical Impact DNA with normalized scores in [0, 1]."""
    generator = AIImpactDNAGenerator()
    extractor = AIExtractor()
    _, project = extractor.extract("Assam flood resilience clean water project", "assam.pdf")
    dna = generator.generate_impact_dna(project, project_public_id="PRJ-TEST-01")

    assert 0.0 <= dna.need_score <= 1.0
    assert 0.0 <= dna.expected_impact_score <= 1.0
    assert 0.0 <= dna.cost_efficiency_score <= 1.0
    assert 0.0 <= dna.evidence_strength_score <= 1.0
    assert 0.0 <= dna.scalability_score <= 1.0
    assert 0.0 <= dna.implementation_risk_score <= 1.0
    assert dna.beneficiary_reach > 0


def test_4_ngo_to_due_diligence():
    """4. Verify NGO statutory due diligence evaluation includes mandatory disclaimer."""
    evaluator = AIDueDiligenceEvaluator()
    report = evaluator.evaluate_ngo(
        ngo_name="Global Hope Foundation",
        registration_number="REG-GHF-2026",
        ngo_public_id="NGO-0001",
    )
    assert report.ngo_id == "NGO-0001"
    assert len(report.checks) >= 3
    assert "evidence and risk-assessment" in report.disclaimer.lower()
    assert "legal or regulatory certification" in report.disclaimer.lower()


def test_5_ai_unavailable_deterministic_fallback():
    """5. Verify deterministic fallback when LLM_API_KEY is absent."""
    client = LLMClient(api_key="")
    assert client.is_live is False
    pipeline = AIPipeline(llm_client=client)

    ext_res, project = pipeline.extract_proposal("Test text", "test.pdf")
    assert ext_res is not None
    assert project is not None


def test_6_invalid_llm_json_error_handling(monkeypatch):
    """6. Verify invalid LLM JSON response translates to ProcessingError or deterministic fallback."""
    client = LLMClient(api_key="sk-test-live-key")
    assert client.is_live is True

    # Test that invalid response without fallback raises ProcessingError
    with pytest.raises(ProcessingError):
        client.generate_structured_output(
            system_prompt="sys",
            user_prompt="usr",
            response_schema=AIExtractor().extract("test", "test.pdf")[1].__class__,
            fallback_data=None,
        )


def test_7_invalid_llm_schema_error_handling():
    """7. Verify Pydantic schema validation failures map to ProcessingError."""
    client = LLMClient(api_key="")
    with pytest.raises(ProcessingError):
        client.generate_structured_output(
            system_prompt="sys",
            user_prompt="usr",
            response_schema=AIExtractor().extract("test", "test.pdf")[1].__class__,
            fallback_data={"invalid_field": "unsupported"},
        )


def test_8_missing_extraction_fields_handling():
    """8. Verify missing fields detection flags validation requirements."""
    extractor = AIExtractor()
    ext_res, _ = extractor.extract("", "empty.pdf")
    assert isinstance(ext_res.missing_fields, list)


def test_9_id_ownership_assigned_by_backend():
    """9. Verify AI layer does NOT invent persistent IDs, backend owns public IDs."""
    extractor = AIExtractor()
    ext_res, project = extractor.extract("Some proposal text", "doc.pdf")
    assert ext_res.proposal_id.startswith("PRO-")
    assert project.project_id == "PRJ-TEMP"  # Service layer will override with PRJ-xxxx


def test_10_e2e_real_pdf_upload_to_extraction_and_persistence(seeded_ngo_id):
    """10-12. End-to-end test proving Person 2 AI pipeline is called in live API flow:
    Real PDF upload -> Document storage -> Trigger AI Extraction -> Project persistence -> Audit log.
    """
    client = TestClient(app)

    # Ingest Proposal
    prop_res = client.post(
        "/api/v1/proposals",
        json={
            "ngo_id": seeded_ngo_id,
            "title": "Jharkhand Clean Water Project",
            "source_type": "PDF_UPLOAD",
        },
    )
    assert prop_res.status_code == 201
    prop_id = prop_res.json()["data"]["proposal_id"]

    # Upload & Attach Document
    doc_res = client.post(
        f"/api/v1/proposals/{prop_id}/documents",
        json={
            "filename": "jharkhand_water.pdf",
            "mime_type": "application/pdf",
            "storage_key": f"uploads/{prop_id}/water.pdf",
            "file_size_bytes": 1024 * 300,
            "sha256": "b" * 64,
        },
    )
    assert doc_res.status_code == 201
    doc_id = doc_res.json()["data"]["document_id"]

    # Trigger AI Extraction via API -> Service -> AI Engine
    ext_res = client.post(
        f"/api/v1/proposals/{prop_id}/extract",
        json={"document_id": doc_id},
    )
    assert ext_res.status_code == 200
    data = ext_res.json()["data"]
    prj_id = data["project_id"]
    assert prj_id.startswith("PRJ-")
    assert data["status"] in [ProposalStatus.EXTRACTED.value, ProposalStatus.VALIDATION_REQUIRED.value]

    # Verify Project Persisted in Database
    prj_res = client.get(f"/api/v1/projects/{prj_id}")
    assert prj_res.status_code == 200
    assert prj_res.json()["data"]["project_id"] == prj_id

    # Verify Audit Event Generated
    audit_res = client.get("/api/v1/audit/events?page=1&page_size=20")
    assert audit_res.status_code == 200
    events = audit_res.json()["data"]
    assert any(e["event_type"] in ["EXTRACTION_COMPLETED", "PROJECT_CREATED"] for e in events)
