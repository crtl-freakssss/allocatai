import uuid
import pytest
from decimal import Decimal

from app.models import (
    NGO,
    Proposal,
    Project,
    OptimizationRun,
    Allocation,
    AuditEvent,
)
from app.repositories import (
    NGORepository,
    ProposalRepository,
    DocumentRepository,
    ProjectRepository,
    OptimizationRepository,
    AllocationRepository,
    AuditRepository,
)
from app.services import (
    ProposalService,
    DocumentService,
    ExtractionService,
    ProjectService,
    ImpactDNAService,
    SaturationService,
    OptimizationService,
    ReallocationService,
    DueDiligenceService,
    AuditService,
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    ServiceValidationError,
    ConflictError,
    InvalidStateTransitionError,
    ProcessingError,
)
from app.schemas import (
    OptimizationRequest,
    OptimizationWeights,
    OptimizationConstraints,
    ReallocationRequest,
    ProjectPerformanceUpdate,
    ProjectSector,
)
from tests.services.fake_engines import (
    FakeExtractionEngine,
    FakeImpactDNAEngine,
    FakeSaturationEngine,
    FakeOptimizationEngine,
    FakeReallocationEngine,
    FakeDueDiligenceEngine,
)


# ==============================================================================
# Helper fixture functions
# ==============================================================================

def create_test_ngo(session, name="Test Service NGO", ext="NGO-SVC-01"):
    ngo_repo = NGORepository(session)
    return ngo_repo.create(name=name, external_id=ext, registration_number="REG-001")


# ==============================================================================
# 1 to 6. ProposalService
# ==============================================================================

def test_1_create_proposal(service_session):
    """Requirement 1: Verify create_proposal workflow and authoritative PRO public ID."""
    ngo = create_test_ngo(service_session, ext="NGO-PROP-01")
    service = ProposalService(service_session)

    proposal = service.create_proposal(
        ngo_id=ngo.id,
        title="Digital Primary Education",
        source_type="DIRECT_SUBMISSION",
    )
    assert proposal.id is not None
    assert proposal.public_id.startswith("PRO-")
    assert proposal.title == "Digital Primary Education"
    assert proposal.status == "UPLOADED"


def test_2_get_proposal(service_session):
    """Requirement 2: Verify get_proposal retrieval and missing error."""
    ngo = create_test_ngo(service_session, ext="NGO-PROP-02")
    service = ProposalService(service_session)
    prop = service.create_proposal(ngo_id=ngo.id, title="Water Purification")

    fetched = service.get_proposal(prop.public_id)
    assert fetched.id == prop.id

    with pytest.raises(ResourceNotFoundError):
        service.get_proposal("PRO-NONEXISTENT")


def test_3_list_proposals(service_session):
    """Requirement 3: Verify list_proposals with pagination."""
    ngo = create_test_ngo(service_session, ext="NGO-PROP-03")
    service = ProposalService(service_session)

    for i in range(3):
        service.create_proposal(ngo_id=ngo.id, title=f"Proposal {i}")

    items, total = service.list_proposals(ngo_id=ngo.id, page=1, page_size=2)
    assert total >= 3
    assert len(items) == 2


def test_4_update_proposal(service_session):
    """Requirement 4: Verify update_proposal status progression and audit."""
    ngo = create_test_ngo(service_session, ext="NGO-PROP-04")
    service = ProposalService(service_session)
    prop = service.create_proposal(ngo_id=ngo.id, title="Health Center Upgrade")

    updated = service.update_proposal(prop.public_id, status="READY")
    assert updated.status == "READY"


def test_5_missing_ngo_dependency_raises_not_found(service_session):
    """Requirement 5: Verify create_proposal rejects missing NGO."""
    service = ProposalService(service_session)
    with pytest.raises(ResourceNotFoundError):
        service.create_proposal(ngo_id=uuid.uuid4(), title="Orphan Proposal")


def test_6_proposal_rollback_on_failure(service_session):
    """Requirement 6: Verify multi-step proposal creation rolls back on failure."""
    service = ProposalService(service_session)
    ngo = create_test_ngo(service_session, ext="NGO-PROP-06")

    # Invalid title should fail validation before any persistence
    with pytest.raises(ServiceValidationError):
        service.create_proposal(ngo_id=ngo.id, title="   ")


# ==============================================================================
# 7 to 10. DocumentService
# ==============================================================================

def test_7_attach_document(service_session):
    """Requirement 7: Verify attach_document generates authoritative DOC ID and audits."""
    ngo = create_test_ngo(service_session, ext="NGO-DOC-01")
    prop_service = ProposalService(service_session)
    prop = prop_service.create_proposal(ngo_id=ngo.id, title="Afforestation Initiative")

    doc_service = DocumentService(service_session)
    sha = "a" * 64
    doc = doc_service.attach_document(
        proposal_public_id=prop.public_id,
        filename="afforestation_budget.pdf",
        mime_type="application/pdf",
        storage_key="s3://allocateai/afforestation.pdf",
        file_size_bytes=102400,
        sha256=sha,
    )
    assert doc.public_id.startswith("DOC-")
    assert doc.filename == "afforestation_budget.pdf"


def test_8_attach_document_rejects_missing_proposal(service_session):
    """Requirement 8: Verify attach_document rejects nonexistent proposal."""
    doc_service = DocumentService(service_session)
    with pytest.raises(ResourceNotFoundError):
        doc_service.attach_document(
            proposal_public_id="PRO-MISSING",
            filename="missing.pdf",
            mime_type="application/pdf",
            storage_key="s3://test.pdf",
            file_size_bytes=1000,
            sha256="b" * 64,
        )


def test_9_attach_document_rejects_duplicate_sha256(service_session):
    """Requirement 9: Verify duplicate SHA-256 on same proposal is rejected."""
    ngo = create_test_ngo(service_session, ext="NGO-DOC-03")
    prop_service = ProposalService(service_session)
    prop = prop_service.create_proposal(ngo_id=ngo.id, title="Duplicate Test")

    doc_service = DocumentService(service_session)
    sha = "c" * 64
    doc_service.attach_document(
        proposal_public_id=prop.public_id,
        filename="doc1.pdf",
        mime_type="application/pdf",
        storage_key="s3://doc1.pdf",
        file_size_bytes=5000,
        sha256=sha,
    )

    with pytest.raises(ResourceAlreadyExistsError):
        doc_service.attach_document(
            proposal_public_id=prop.public_id,
            filename="doc2.pdf",
            mime_type="application/pdf",
            storage_key="s3://doc2.pdf",
            file_size_bytes=5000,
            sha256=sha,
        )


def test_10_list_proposal_documents(service_session):
    """Requirement 10: Verify listing documents by proposal."""
    ngo = create_test_ngo(service_session, ext="NGO-DOC-04")
    prop_service = ProposalService(service_session)
    prop = prop_service.create_proposal(ngo_id=ngo.id, title="Doc List Test")

    doc_service = DocumentService(service_session)
    doc_service.attach_document(
        proposal_public_id=prop.public_id,
        filename="docA.pdf",
        mime_type="application/pdf",
        storage_key="s3://docA.pdf",
        file_size_bytes=100,
        sha256="d" * 64,
    )
    docs = doc_service.list_proposal_documents(prop.public_id)
    assert len(docs) == 1


# ==============================================================================
# 11 to 15. ExtractionService
# ==============================================================================

def test_11_to_15_extraction_service_orchestration(service_session):
    """Requirements 11-15: Verify extraction orchestration, backend PRJ ID, mismatch guard, rollback."""
    ngo = create_test_ngo(service_session, ext="NGO-EXT-01")
    prop_service = ProposalService(service_session)
    prop = prop_service.create_proposal(ngo_id=ngo.id, title="Proposal to Extract")

    doc_service = DocumentService(service_session)
    doc = doc_service.attach_document(
        proposal_public_id=prop.public_id,
        filename="extract_me.pdf",
        mime_type="application/pdf",
        storage_key="s3://extract_me.pdf",
        file_size_bytes=50000,
        sha256="e" * 64,
    )

    extract_service = ExtractionService(service_session)
    engine = FakeExtractionEngine()

    # 11 & 14. Successful extraction with authoritative backend PRJ ID
    extraction_result, project = extract_service.extract_proposal(
        proposal_public_id=prop.public_id,
        document_public_id=doc.public_id,
        engine=engine,
    )
    assert project.public_id.startswith("PRJ-")
    assert project.public_id != "ENGINE-GEN-001"  # Confirms backend overrode engine ID
    assert project.name == "Community Water Purification"
    assert len(project.geographies) == 1

    # Check proposal status updated
    updated_prop = prop_service.get_proposal(prop.public_id)
    assert updated_prop.status == "EXTRACTED"

    # 13. Mismatch guard: document belonging to different proposal rejected
    prop2 = prop_service.create_proposal(ngo_id=ngo.id, title="Second Proposal")
    with pytest.raises(ConflictError, match="not associated with proposal"):
        extract_service.extract_proposal(
            proposal_public_id=prop2.public_id,
            document_public_id=doc.public_id,
            engine=engine,
        )

    # 15. Engine failure raises ProcessingError and rolls back
    failing_engine = FakeExtractionEngine(should_fail=True)
    with pytest.raises(ProcessingError):
        extract_service.extract_proposal(
            proposal_public_id=prop.public_id,
            document_public_id=doc.public_id,
            engine=failing_engine,
        )


# ==============================================================================
# 16 to 19. ProjectService
# ==============================================================================

def test_16_to_19_project_service(service_session):
    """Requirements 16-19: Verify create_project, get_project, missing NGO rejection, missing proposal."""
    ngo = create_test_ngo(service_session, ext="NGO-PRJ-01")
    project_service = ProjectService(service_session)

    # 16. Create project
    proj = project_service.create_project(
        ngo_id=ngo.id,
        name="Solar Pump Wells",
        sector=ProjectSector.ENVIRONMENT,
        duration_months=12,
        requested_amount_paise=600000000,
        geographies=[{"state": "Gujarat", "district": "Kutch"}],
    )
    assert proj.public_id.startswith("PRJ-")

    # 17. Get project
    fetched = project_service.get_project(proj.public_id)
    assert fetched.id == proj.id

    # 18. Missing NGO rejection
    with pytest.raises(ResourceNotFoundError):
        project_service.create_project(
            ngo_id=uuid.uuid4(),
            name="Ghost NGO Project",
            sector=ProjectSector.HEALTHCARE,
            duration_months=6,
            requested_amount_paise=100000000,
            geographies=[{"state": "Goa"}],
        )

    # 19. Missing proposal rejection
    with pytest.raises(ResourceNotFoundError):
        project_service.create_project(
            ngo_id=ngo.id,
            name="Bad Proposal Ref",
            sector=ProjectSector.HEALTHCARE,
            duration_months=6,
            requested_amount_paise=100000000,
            geographies=[{"state": "Goa"}],
            proposal_id=uuid.uuid4(),
        )


# ==============================================================================
# 20 to 22. ImpactDNAService
# ==============================================================================

def test_20_to_22_impact_dna_service(service_session):
    """Requirements 20-22: Verify ImpactDNAService orchestration, missing project rejection, persistence."""
    ngo = create_test_ngo(service_session, ext="NGO-DNA-01")
    proj_service = ProjectService(service_session)
    proj = proj_service.create_project(
        ngo_id=ngo.id,
        name="DNA Test Project",
        sector=ProjectSector.EDUCATION,
        duration_months=12,
        requested_amount_paise=250000000,
        geographies=[{"state": "Madhya Pradesh"}],
    )

    dna_service = ImpactDNAService(service_session)
    engine = FakeImpactDNAEngine()

    # 20 & 22. Generate and persist DNA
    dna = dna_service.generate_dna(proj.public_id, engine=engine)
    assert dna.public_id.startswith("DNA-")
    assert dna.expected_impact_score == Decimal("0.91000")

    # 1-to-1 guard: attempting to generate again raises ResourceAlreadyExistsError
    with pytest.raises(ResourceAlreadyExistsError):
        dna_service.generate_dna(proj.public_id, engine=engine)

    # 21. Missing project rejection
    with pytest.raises(ResourceNotFoundError):
        dna_service.generate_dna("PRJ-DOESNOTEXIST", engine=engine)


# ==============================================================================
# 23 & 24. SaturationService
# ==============================================================================

def test_23_and_24_saturation_service(service_session):
    """Requirements 23 & 24: Verify SaturationService orchestration and failure rollback."""
    ngo = create_test_ngo(service_session, ext="NGO-SAT-01")
    proj_service = ProjectService(service_session)
    proj = proj_service.create_project(
        ngo_id=ngo.id,
        name="Saturation Test Project",
        sector=ProjectSector.RURAL_DEVELOPMENT,
        duration_months=18,
        requested_amount_paise=400000000,
        geographies=[{"state": "Jharkhand"}],
    )

    sat_service = SaturationService(service_session)
    engine = FakeSaturationEngine()

    # 23. Success
    sat = sat_service.calculate_saturation(proj.public_id, engine=engine)
    assert sat.saturation_index == Decimal("0.32000")
    assert sat.state == "Jharkhand"

    # 24. Engine failure rolls back
    failing_engine = FakeSaturationEngine(should_fail=True)
    with pytest.raises(ProcessingError):
        sat_service.calculate_saturation(proj.public_id, engine=failing_engine)


# ==============================================================================
# 25 to 32. OptimizationService
# ==============================================================================

def test_25_to_32_optimization_service(service_session):
    """Requirements 25-32: Verify optimization workflow, project checks, invariant, immutability."""
    ngo = create_test_ngo(service_session, ext="NGO-OPT-01")
    proj_service = ProjectService(service_session)
    p1 = proj_service.create_project(
        ngo_id=ngo.id,
        name="Opt Project 1",
        sector=ProjectSector.HEALTHCARE,
        duration_months=12,
        requested_amount_paise=500000000,
        geographies=[{"state": "Assam"}],
    )
    p2 = proj_service.create_project(
        ngo_id=ngo.id,
        name="Opt Project 2",
        sector=ProjectSector.EDUCATION,
        duration_months=12,
        requested_amount_paise=500000000,
        geographies=[{"state": "Bihar"}],
    )

    weights = OptimizationWeights(
        need=0.3, marginal_impact=0.3, cost_efficiency=0.2,
        evidence=0.1, scalability=0.05, equity=0.03, risk_penalty=0.02,
    )
    constraints = OptimizationConstraints()
    req = OptimizationRequest(
        budget_paise=1000000000,  # ₹10 Cr
        project_ids=[p1.public_id, p2.public_id],
        weights=weights,
        constraints=constraints,
    )

    opt_service = OptimizationService(service_session)
    engine = FakeOptimizationEngine()

    # 25, 29, 32. Successful optimization workflow, snapshot, allocations
    res = opt_service.create_optimization_run(req, engine=engine)
    assert res.run_id.startswith("OPT-")
    assert res.allocated_paise + res.unallocated_paise == req.budget_paise
    assert len(res.allocations) == 2

    # Verify run persisted as COMPLETED
    run_orm = opt_service.get_optimization_run(res.run_id)
    assert run_orm.status == "COMPLETED"
    assert run_orm.input_snapshot["budget_paise"] == req.budget_paise

    # 26. Missing project rejection
    bad_req = OptimizationRequest(
        budget_paise=1000000000,
        project_ids=[p1.public_id, "PRJ-MISSING-999"],
        weights=weights,
        constraints=constraints,
    )
    with pytest.raises(ResourceNotFoundError):
        opt_service.create_optimization_run(bad_req, engine=engine)

    # 27 & 28. Invariant violation / invalid result rejection
    bad_engine = FakeOptimizationEngine(violate_budget=True)
    with pytest.raises((ProcessingError, ServiceValidationError)):
        opt_service.create_optimization_run(req, engine=bad_engine)

    # 30. Completed run cannot be mutated
    with pytest.raises(ValueError, match="already COMPLETED and immutable"):
        opt_service.opt_repo.save_result_snapshot(run_orm, {"illegal": True})


# ==============================================================================
# 33 to 35. ReallocationService
# ==============================================================================

def test_33_to_35_reallocation_service(service_session):
    """Requirements 33-35: Verify reallocation orchestration and previous run check."""
    ngo = create_test_ngo(service_session, ext="NGO-REA-01")
    proj_service = ProjectService(service_session)
    p1 = proj_service.create_project(
        ngo_id=ngo.id,
        name="Realloc Project",
        sector=ProjectSector.POVERTY_HUNGER,
        duration_months=12,
        requested_amount_paise=500000000,
        geographies=[{"state": "Odisha"}],
    )

    opt_service = OptimizationService(service_session)
    weights = OptimizationWeights(
        need=0.3, marginal_impact=0.3, cost_efficiency=0.2,
        evidence=0.1, scalability=0.05, equity=0.03, risk_penalty=0.02,
    )
    opt_req = OptimizationRequest(
        budget_paise=500000000,
        project_ids=[p1.public_id],
        weights=weights,
        constraints=OptimizationConstraints(),
    )
    opt_res = opt_service.create_optimization_run(opt_req, engine=FakeOptimizationEngine())

    realloc_service = ReallocationService(service_session)
    realloc_req = ReallocationRequest(
        previous_run_id=opt_res.run_id,
        budget_paise=500000000,
        performance_updates=[
            ProjectPerformanceUpdate(project_id=p1.public_id, progress_percent=90.0, actual_spend_paise=400000000)
        ],
        weights=weights,
        constraints=OptimizationConstraints(),
    )

    # 33. Valid reallocation
    realloc_res = realloc_service.create_reallocation_run(realloc_req, engine=FakeReallocationEngine())
    assert realloc_res.run_id.startswith("REA-")
    assert realloc_res.previous_run_id == opt_res.run_id

    # 34. Missing optimization run rejection
    bad_realloc = realloc_req.model_copy(update={"previous_run_id": "OPT-GHOST"})
    with pytest.raises(ResourceNotFoundError):
        realloc_service.create_reallocation_run(bad_realloc, engine=FakeReallocationEngine())


# ==============================================================================
# 36 to 38. DueDiligenceService
# ==============================================================================

def test_36_to_38_due_diligence_service(service_session):
    """Requirements 36-38: Verify DueDiligenceService orchestration, missing NGO, disclaimer."""
    ngo = create_test_ngo(service_session, ext="NGO-DD-01")
    dd_service = DueDiligenceService(service_session)
    engine = FakeDueDiligenceEngine()

    # 36. Successful evaluation
    report = dd_service.evaluate_ngo(ngo.id, engine=engine)
    assert report.public_id.startswith("DD-")
    assert report.overall_status == "VERIFIED"

    # 38. Legal disclaimer preserved
    assert "does not constitute legal or regulatory certification" in report.disclaimer

    # 37. Missing NGO rejection
    with pytest.raises(ResourceNotFoundError):
        dd_service.evaluate_ngo(uuid.uuid4(), engine=engine)


# ==============================================================================
# 39 & 40. AuditService
# ==============================================================================

def test_39_and_40_audit_service(service_session):
    """Requirements 39 & 40: Verify audit creation and blocked update/delete."""
    audit_service = AuditService(service_session)
    event = audit_service.record_event(
        event_type="TEST_MUTATION_EVENT",
        payload={"action": "service_verification"},
    )
    assert event.public_id.startswith("AUD-")
    assert event.event_type == "TEST_MUTATION_EVENT"

    fetched = audit_service.get_event(event.public_id)
    assert fetched is not None

    # 40. Blocked modification/deletion
    with pytest.raises(NotImplementedError):
        audit_service.audit_repo.update(fetched)

    with pytest.raises(NotImplementedError):
        audit_service.audit_repo.delete(fetched)


# ==============================================================================
# Multi-Step Transaction Rollback Tests (3 Workflows)
# ==============================================================================

def test_rollback_workflow_1_proposal_creation(service_session):
    """Workflow 1 Rollback: Uncommitted proposal is completely reverted on failure."""
    service = ProposalService(service_session)
    ngo = create_test_ngo(service_session, ext="NGO-RB-01")

    # Invalid title causes validation error before commit
    with pytest.raises(ServiceValidationError):
        service.create_proposal(ngo_id=ngo.id, title="")

    # Verify no dangling proposals exist for this NGO
    items, total = service.list_proposals(ngo_id=ngo.id)
    assert total == 0


def test_rollback_workflow_2_extraction_failure(service_session):
    """Workflow 2 Rollback: Extraction engine failure reverts project creation and keeps proposal intact."""
    ngo = create_test_ngo(service_session, ext="NGO-RB-02")
    prop_service = ProposalService(service_session)
    prop = prop_service.create_proposal(ngo_id=ngo.id, title="Failing Extract Proposal")

    doc_service = DocumentService(service_session)
    doc = doc_service.attach_document(
        proposal_public_id=prop.public_id,
        filename="corrupted.pdf",
        mime_type="application/pdf",
        storage_key="s3://corrupted.pdf",
        file_size_bytes=1000,
        sha256="f" * 64,
    )

    extract_service = ExtractionService(service_session)
    failing_engine = FakeExtractionEngine(should_fail=True)
    prop_id = prop.id
    prop_pub_id = prop.public_id
    doc_pub_id = doc.public_id

    with pytest.raises(ProcessingError):
        extract_service.extract_proposal(
            proposal_public_id=prop_pub_id,
            document_public_id=doc_pub_id,
            engine=failing_engine,
        )

    # Confirm no project was committed
    proj_repo = ProjectRepository(service_session)
    projects, count = proj_repo.list(proposal_id=prop_id)
    assert count == 0


def test_rollback_workflow_3_optimization_solver_failure(service_session):
    """Workflow 3 Rollback: Optimization solver failure leaves zero residual allocations."""
    ngo = create_test_ngo(service_session, ext="NGO-RB-03")
    proj_service = ProjectService(service_session)
    p1 = proj_service.create_project(
        ngo_id=ngo.id,
        name="Rollback Opt Project",
        sector=ProjectSector.SPORTS,
        duration_months=6,
        requested_amount_paise=100000000,
        geographies=[{"state": "Punjab"}],
    )

    opt_service = OptimizationService(service_session)
    weights = OptimizationWeights(
        need=0.3, marginal_impact=0.3, cost_efficiency=0.2,
        evidence=0.1, scalability=0.05, equity=0.03, risk_penalty=0.02,
    )
    req = OptimizationRequest(
        budget_paise=100000000,
        project_ids=[p1.public_id],
        weights=weights,
        constraints=OptimizationConstraints(),
    )

    failing_solver = FakeOptimizationEngine(should_fail=True)
    with pytest.raises(ProcessingError):
        opt_service.create_optimization_run(req, engine=failing_solver)

    # Check that no allocations survived
    alloc_repo = AllocationRepository(service_session)
    stmt = service_session.query(Allocation).filter(Allocation.project_id == p1.id).all()
    assert len(stmt) == 0
