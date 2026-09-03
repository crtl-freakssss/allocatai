import uuid
from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError

from app.db.identifiers import generate_public_id
from app.models import ProjectGeography, Allocation
from app.repositories import (
    OrganizationRepository,
    UserRepository,
    NGORepository,
    ProposalRepository,
    DocumentRepository,
    ProjectRepository,
    ImpactDNARepository,
    SaturationRepository,
    DueDiligenceRepository,
    OptimizationRepository,
    AllocationRepository,
    ReallocationRepository,
    AuditRepository,
)


# ==============================================================================
# 1. Organization create / get
# ==============================================================================

def test_1_organization_create_and_get(repo_session):
    """Requirement 1: Verify organization creation and retrieval by UUID."""
    repo = OrganizationRepository(repo_session)
    org = repo.create(name="Reliance Foundation")
    assert org.id is not None
    assert org.name == "Reliance Foundation"

    fetched = repo.get_by_id(org.id)
    assert fetched is not None
    assert fetched.name == "Reliance Foundation"
    assert repo.exists(org.id) is True


# ==============================================================================
# 2. User create / get by email
# ==============================================================================

def test_2_user_create_and_get_by_email(repo_session):
    """Requirement 2: Verify user creation and retrieval by unique email."""
    org_repo = OrganizationRepository(repo_session)
    user_repo = UserRepository(repo_session)

    org = org_repo.create(name="Azim Premji Philanthropic Initiatives")
    user = user_repo.create(
        email="program.director@appi.org",
        organization_id=org.id,
        name="Sanjay Roy",
    )
    assert user.id is not None
    assert user.email == "program.director@appi.org"

    fetched = user_repo.get_by_email("program.director@appi.org")
    assert fetched is not None
    assert fetched.id == user.id
    assert fetched.name == "Sanjay Roy"
    assert user_repo.exists_by_email("program.director@appi.org") is True


# ==============================================================================
# 3. NGO create / get by external ID
# ==============================================================================

def test_3_ngo_create_and_get_by_external_id(repo_session):
    """Requirement 3: Verify NGO creation and retrieval by external_id."""
    ngo_repo = NGORepository(repo_session)
    ngo = ngo_repo.create(
        name="Teach For India",
        external_id="NGO-TFI-001",
        registration_number="REG-MH-2009-4412",
    )
    assert ngo.id is not None
    assert ngo.external_id == "NGO-TFI-001"

    fetched = ngo_repo.get_by_external_id("NGO-TFI-001")
    assert fetched is not None
    assert fetched.name == "Teach For India"
    assert fetched.registration_number == "REG-MH-2009-4412"


# ==============================================================================
# 4 & 5. Proposal create, get by public ID, and pagination
# ==============================================================================

def test_4_proposal_create_and_get_by_public_id(repo_session):
    """Requirement 4: Verify Proposal creation and retrieval by public ID."""
    ngo_repo = NGORepository(repo_session)
    ngo = ngo_repo.create(name="Akshaya Patra Foundation", external_id="NGO-AP-001")

    prop_repo = ProposalRepository(repo_session)
    pub_id = generate_public_id("PRO", 101)
    prop = prop_repo.create(
        public_id=pub_id,
        ngo_id=ngo.id,
        title="Mid-day Meals Nutrition Scaling 2026",
        status="UPLOADED",
        source_type="DIRECT_SUBMISSION",
    )
    assert prop.public_id == pub_id

    fetched = prop_repo.get_by_public_id(pub_id)
    assert fetched is not None
    assert fetched.title == "Mid-day Meals Nutrition Scaling 2026"
    assert prop_repo.exists_by_public_id(pub_id) is True


def test_5_proposal_pagination(repo_session):
    """Requirement 5: Verify Proposal pagination with deterministic total and slice."""
    ngo_repo = NGORepository(repo_session)
    ngo = ngo_repo.create(name="Pagination NGO", external_id="NGO-PAG-001")

    prop_repo = ProposalRepository(repo_session)
    for i in range(1, 6):
        prop_repo.create(
            public_id=generate_public_id("PRO", 200 + i),
            ngo_id=ngo.id,
            title=f"Proposal {i}",
            status="READY",
        )

    # Page 1 with size 2
    items_p1, total = prop_repo.list(ngo_id=ngo.id, page=1, page_size=2)
    assert total == 5
    assert len(items_p1) == 2

    # Page 2 with size 2
    items_p2, _ = prop_repo.list(ngo_id=ngo.id, page=2, page_size=2)
    assert len(items_p2) == 2
    assert items_p1[0].id != items_p2[0].id


# ==============================================================================
# 6 & 7. Document create, proposal lookup, SHA-256 lookup
# ==============================================================================

def test_6_and_7_document_create_and_sha256_lookup(repo_session):
    """Requirements 6 & 7: Verify Document persistence, proposal grouping, and SHA-256 query."""
    ngo_repo = NGORepository(repo_session)
    ngo = ngo_repo.create(name="Doc NGO", external_id="NGO-DOC-001")

    prop_repo = ProposalRepository(repo_session)
    prop = prop_repo.create(
        public_id=generate_public_id("PRO", 301),
        ngo_id=ngo.id,
        title="Healthcare Center Upgrade",
    )

    doc_repo = DocumentRepository(repo_session)
    doc_pub_id = generate_public_id("DOC", 301)
    sha = "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
    doc = doc_repo.create(
        public_id=doc_pub_id,
        proposal_id=prop.id,
        filename="detailed_budget.xlsx",
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        storage_key="s3://allocateai-docs/budget_301.xlsx",
        file_size_bytes=1048576,
        sha256=sha,
    )
    assert doc.id is not None

    by_prop = doc_repo.get_by_proposal(prop.id)
    assert len(by_prop) == 1
    assert by_prop[0].public_id == doc_pub_id

    by_sha = doc_repo.get_by_sha256(sha)
    assert by_sha is not None
    assert by_sha.public_id == doc_pub_id


# ==============================================================================
# 8 & 9. Project create, public ID lookup, geography persistence
# ==============================================================================

def test_8_and_9_project_create_and_geography_persistence(repo_session):
    """Requirements 8 & 9: Verify Project creation, public ID lookup, and geography persistence."""
    ngo_repo = NGORepository(repo_session)
    ngo = ngo_repo.create(name="Project NGO", external_id="NGO-PRJ-001")

    proj_repo = ProjectRepository(repo_session)
    proj_pub_id = generate_public_id("PRJ", 401)
    proj = proj_repo.create(
        public_id=proj_pub_id,
        ngo_id=ngo.id,
        name="Clean Drinking Water Solar Kiosks",
        sector="ENVIRONMENT",
        duration_months=18,
        requested_amount=750000000,  # ₹75 Lakhs in paise
        current_funding=100000000,
        schema_version="v1",
    )
    assert proj.public_id == proj_pub_id

    # Add geographies
    geo1 = proj_repo.add_geography(proj.id, state="Rajasthan", district="Barmer", block="Chohtan")
    geo2 = proj_repo.add_geography(proj.id, state="Rajasthan", district="Jaisalmer")
    assert geo1.id is not None
    assert geo2.id is not None

    fetched = proj_repo.get_by_public_id(proj_pub_id)
    assert fetched is not None
    assert len(fetched.geographies) == 2
    assert fetched.requested_amount == 750000000


# ==============================================================================
# 10. ImpactDNA create and project query
# ==============================================================================

def test_10_impact_dna_create_and_project_query(repo_session):
    """Requirement 10: Verify 1-to-1 ImpactDNA persistence and project relationship."""
    ngo_repo = NGORepository(repo_session)
    ngo = ngo_repo.create(name="DNA NGO", external_id="NGO-DNA-001")

    proj_repo = ProjectRepository(repo_session)
    proj = proj_repo.create(
        public_id=generate_public_id("PRJ", 501),
        ngo_id=ngo.id,
        name="Maternal Health Clinic",
        sector="HEALTHCARE",
        duration_months=12,
        requested_amount=300000000,
        schema_version="v1",
    )

    dna_repo = ImpactDNARepository(repo_session)
    dna_pub_id = generate_public_id("DNA", 501)
    dna = dna_repo.create(
        public_id=dna_pub_id,
        project_id=proj.id,
        need_score=Decimal("0.88000"),
        expected_impact_score=Decimal("0.92000"),
        cost_efficiency_score=Decimal("0.85000"),
        evidence_strength_score=Decimal("0.80000"),
        scalability_score=Decimal("0.75000"),
        implementation_risk_score=Decimal("0.15000"),
        beneficiary_reach=4500,
        estimated_impact_per_lakh=Decimal("38.5000"),
        missing_fields={"unverified_cost_line": False},
        extraction_confidence=Decimal("0.94000"),
        model_name="gemini-1.5-pro",
        prompt_version="v1.2",
    )
    assert dna.id is not None

    fetched = dna_repo.get_by_project_id(proj.id)
    assert fetched is not None
    assert fetched.public_id == dna_pub_id
    assert fetched.beneficiary_reach == 4500


# ==============================================================================
# 11. Saturation create and queries
# ==============================================================================

def test_11_saturation_create_and_queries(repo_session):
    """Requirement 11: Verify SaturationResult persistence, state/sector filters, and latest query."""
    ngo_repo = NGORepository(repo_session)
    ngo = ngo_repo.create(name="Sat NGO", external_id="NGO-SAT-001")

    proj_repo = ProjectRepository(repo_session)
    proj = proj_repo.create(
        public_id=generate_public_id("PRJ", 601),
        ngo_id=ngo.id,
        name="Vocational Skill Training",
        sector="LIVELIHOOD",
        duration_months=6,
        requested_amount=200000000,
        schema_version="v1",
    )

    sat_repo = SaturationRepository(repo_session)
    sat = sat_repo.create(
        project_id=proj.id,
        state="Odisha",
        sector="LIVELIHOOD",
        saturation_index=Decimal("0.28000"),
        need_score=Decimal("0.82000"),
        existing_csr_amount=500000000,
        beneficiary_coverage=Decimal("0.35000"),
        confidence=Decimal("0.89000"),
    )
    assert sat.id is not None

    latest = sat_repo.get_latest_for_project(proj.id)
    assert latest is not None
    assert latest.saturation_index == Decimal("0.28000")

    by_state = sat_repo.list_by_state("Odisha")
    assert len(by_state) >= 1

    by_sector = sat_repo.list_by_sector("LIVELIHOOD")
    assert len(by_sector) >= 1


# ==============================================================================
# 12. Due Diligence create and NGO lookup
# ==============================================================================

def test_12_due_diligence_create_and_ngo_query(repo_session):
    """Requirement 12: Verify DueDiligenceReport persistence and NGO query."""
    ngo_repo = NGORepository(repo_session)
    ngo = ngo_repo.create(name="DD NGO", external_id="NGO-DD-001")

    dd_repo = DueDiligenceRepository(repo_session)
    pub_id = generate_public_id("DD", 701)
    rep = dd_repo.create(
        public_id=pub_id,
        ngo_id=ngo.id,
        overall_status="VERIFIED",
        risk_level="LOW",
        checks={"12a_80g": "VALID", "darpan_id": "VALID"},
        flags=[],
        missing_documents=[],
    )
    assert rep.id is not None

    latest = dd_repo.get_latest_for_ngo(ngo.id)
    assert latest is not None
    assert latest.public_id == pub_id
    assert latest.risk_level == "LOW"


# ==============================================================================
# 13, 14, 15, 16. OptimizationRun create, update, result snapshot, immutability
# ==============================================================================

def test_13_to_16_optimization_run_persistence_and_immutability(repo_session):
    """Requirements 13-16: Verify OptimizationRun, status updates, result saving, and immutability."""
    opt_repo = OptimizationRepository(repo_session)
    pub_id = generate_public_id("OPT", 801)

    # 13. Create run
    run = opt_repo.create(
        public_id=pub_id,
        budget_paise=1000000000,  # ₹1 Cr
        weights={"need": 0.4, "impact": 0.6},
        constraints={"max_project": 500000000},
        calculation_versions={"milp": "v1.0"},
        input_snapshot={"project_ids": ["PRJ-0001", "PRJ-0002"]},
        status="QUEUED",
    )
    assert run.id is not None
    assert run.status == "QUEUED"

    # 14. Update status to RUNNING
    run = opt_repo.update_status(run, "RUNNING")
    assert run.status == "RUNNING"

    # 15. Save result snapshot and complete
    result_snap = {"allocations": [{"project_id": "PRJ-0001", "amount": 500000000}]}
    run = opt_repo.save_result_snapshot(
        run,
        result_snapshot=result_snap,
        total_predicted_impact=Decimal("240.5000"),
        mark_completed=True,
    )
    assert run.status == "COMPLETED"
    assert run.completed_at is not None
    assert run.total_predicted_impact == Decimal("240.5000")

    # 16. Immutability protection: mutating completed run must fail
    with pytest.raises(ValueError, match="already COMPLETED and immutable"):
        opt_repo.save_result_snapshot(run, {"illegal": "overwrite"})

    with pytest.raises(ValueError, match="input snapshot is immutable"):
        opt_repo.mutate_input_snapshot(run, {"new_projects": []})

    with pytest.raises(ValueError, match="Cannot transition run"):
        opt_repo.update_status(run, "QUEUED")


# ==============================================================================
# 17, 18, 19. Allocation creation, bulk creation, and run lookup
# ==============================================================================

def test_17_to_19_allocations_and_bulk_create(repo_session):
    """Requirements 17-19: Verify Allocation creation, bulk insert, and optimization run query."""
    ngo_repo = NGORepository(repo_session)
    ngo = ngo_repo.create(name="Alloc NGO", external_id="NGO-ALL-001")

    proj_repo = ProjectRepository(repo_session)
    p1 = proj_repo.create(
        public_id=generate_public_id("PRJ", 901),
        ngo_id=ngo.id,
        name="Project A",
        sector="EDUCATION",
        duration_months=12,
        requested_amount=500000000,
        schema_version="v1",
    )
    p2 = proj_repo.create(
        public_id=generate_public_id("PRJ", 902),
        ngo_id=ngo.id,
        name="Project B",
        sector="HEALTHCARE",
        duration_months=12,
        requested_amount=500000000,
        schema_version="v1",
    )

    opt_repo = OptimizationRepository(repo_session)
    run = opt_repo.create(
        public_id=generate_public_id("OPT", 901),
        budget_paise=1000000000,
        weights={},
        constraints={},
        calculation_versions={},
        input_snapshot={},
        status="RUNNING",
    )

    alloc_repo = AllocationRepository(repo_session)

    # 17. Single create
    a1 = alloc_repo.create(
        optimization_run_id=run.id,
        project_id=p1.id,
        allocated_amount=500000000,
        marginal_score=Decimal("0.89000"),
        base_score=Decimal("0.91000"),
        saturation_index=Decimal("0.25000"),
        reason_codes={"codes": ["HIGH_NEED"]},
        rank=1,
    )
    assert a1.id is not None

    # 18. Bulk create
    a2 = Allocation(
        optimization_run_id=run.id,
        project_id=p2.id,
        allocated_amount=500000000,
        marginal_score=Decimal("0.85000"),
        base_score=Decimal("0.88000"),
        saturation_index=Decimal("0.30000"),
        reason_codes={"codes": ["HIGH_IMPACT"]},
        rank=2,
        status="PROPOSED",
    )
    alloc_repo.bulk_create([a2])
    assert a2.id is not None

    # 19. List by optimization run
    run_allocs = alloc_repo.list_by_optimization_run(run.id)
    assert len(run_allocs) == 2
    assert run_allocs[0].rank == 1
    assert run_allocs[1].rank == 2


# ==============================================================================
# 20. Project deletion restricted when referenced by allocation
# ==============================================================================

def test_20_project_deletion_restricted_by_allocation(repo_session):
    """Requirement 20: Verify project cannot be hard-deleted while referenced by an allocation."""
    ngo_repo = NGORepository(repo_session)
    ngo = ngo_repo.create(name="Restrict NGO", external_id="NGO-RES-001")

    proj_repo = ProjectRepository(repo_session)
    proj = proj_repo.create(
        public_id=generate_public_id("PRJ", 950),
        ngo_id=ngo.id,
        name="Undeletable Project",
        sector="SPORTS",
        duration_months=6,
        requested_amount=100000000,
        schema_version="v1",
    )

    opt_repo = OptimizationRepository(repo_session)
    run = opt_repo.create(
        public_id=generate_public_id("OPT", 950),
        budget_paise=100000000,
        weights={},
        constraints={},
        calculation_versions={},
        input_snapshot={},
        status="RUNNING",
    )

    alloc_repo = AllocationRepository(repo_session)
    alloc_repo.create(
        optimization_run_id=run.id,
        project_id=proj.id,
        allocated_amount=100000000,
        marginal_score=Decimal("0.90000"),
        base_score=Decimal("0.90000"),
        saturation_index=Decimal("0.10000"),
        reason_codes={},
        rank=1,
    )

    # Attempting to delete project should trigger database IntegrityError via RESTRICT foreign key
    with pytest.raises(IntegrityError):
        proj_repo.delete(proj, flush=True)
    repo_session.rollback()


# ==============================================================================
# 21. Reallocation run persistence
# ==============================================================================

def test_21_reallocation_run_persistence(repo_session):
    """Requirement 21: Verify ReallocationRun creation and reference to prior optimization."""
    opt_repo = OptimizationRepository(repo_session)
    base_run = opt_repo.create(
        public_id=generate_public_id("OPT", 980),
        budget_paise=2000000000,
        weights={},
        constraints={},
        calculation_versions={},
        input_snapshot={},
        status="COMPLETED",
    )

    realloc_repo = ReallocationRepository(repo_session)
    realloc_pub_id = generate_public_id("REA", 980)
    realloc = realloc_repo.create(
        public_id=realloc_pub_id,
        previous_optimization_id=base_run.id,
        budget_paise=1500000000,
        performance_snapshot={"delays_noted": True},
        calculation_versions={"realloc_engine": "v1.0"},
    )
    assert realloc.id is not None
    assert realloc.previous_optimization_id == base_run.id

    fetched = realloc_repo.get_by_public_id(realloc_pub_id)
    assert fetched is not None
    assert fetched.budget_paise == 1500000000


# ==============================================================================
# 22, 23, 24, 25. AuditEvent create, retrieval, update blocked, delete blocked
# ==============================================================================

def test_22_to_25_audit_events_append_only(repo_session):
    """Requirements 22-25: Verify AuditEvent creation, retrieval, and blocked update/delete."""
    audit_repo = AuditRepository(repo_session)
    pub_id = generate_public_id("AUD", 990)

    # 22. Create
    event = audit_repo.create(
        public_id=pub_id,
        event_type="OPTIMIZATION_STARTED",
        payload={"budget_paise": 5000000000},
        run_id="OPT-0001",
    )
    assert event.id is not None

    # 23. Retrieve
    fetched = audit_repo.get_by_public_id(pub_id)
    assert fetched is not None
    assert fetched.event_type == "OPTIMIZATION_STARTED"
    assert fetched.payload["budget_paise"] == 5000000000

    # 24. Update blocked
    with pytest.raises(NotImplementedError, match="strictly append-only"):
        audit_repo.update(fetched, {"payload": {}})

    # 25. Delete blocked
    with pytest.raises(NotImplementedError, match="strictly append-only"):
        audit_repo.delete(fetched)


# ==============================================================================
# 26. Foreign key violations are not silently ignored
# ==============================================================================

def test_26_foreign_key_violations_raise_integrity_error(repo_session):
    """Requirement 26: Verify foreign key violations raise IntegrityError."""
    user_repo = UserRepository(repo_session)
    fake_org_id = uuid.uuid4()

    # User with non-existent organization ID
    with pytest.raises(IntegrityError):
        user_repo.create(email="ghost@fakeorg.org", organization_id=fake_org_id)
    repo_session.rollback()


# ==============================================================================
# 27. Unique constraint behavior
# ==============================================================================

def test_27_unique_constraint_raises_integrity_error(repo_session):
    """Requirement 27: Verify inserting duplicate unique keys raises IntegrityError."""
    ngo_repo = NGORepository(repo_session)
    ngo_repo.create(name="Original NGO", external_id="NGO-UNIQUE-01")

    # Duplicate external_id
    with pytest.raises(IntegrityError):
        ngo_repo.create(name="Duplicate NGO", external_id="NGO-UNIQUE-01")
    repo_session.rollback()


# ==============================================================================
# 28. Deterministic pagination
# ==============================================================================

def test_28_deterministic_pagination(repo_session):
    """Requirement 28: Verify repeated queries with same page/page_size return identical order."""
    org_repo = OrganizationRepository(repo_session)
    for i in range(5):
        org_repo.create(name=f"Deterministic Org {i}")

    items1, total1 = org_repo.list(page=1, page_size=3)
    items2, total2 = org_repo.list(page=1, page_size=3)

    assert total1 == total2
    assert [x.id for x in items1] == [x.id for x in items2]


# ==============================================================================
# 29 & 30. Repository session does not commit & remains usable
# ==============================================================================

def test_29_and_30_repository_session_cooperation(repo_session):
    """Requirements 29 & 30: Verify repositories do not commit transaction and session remains usable."""
    org_repo = OrganizationRepository(repo_session)
    org = org_repo.create(name="Uncommitted Organization")

    # The transaction should NOT be committed; it remains active
    assert repo_session.is_active is True

    # Session remains completely usable for subsequent queries
    fetched = org_repo.get_by_id(org.id)
    assert fetched is not None
    assert fetched.name == "Uncommitted Organization"


# ==============================================================================
# 31. Realistic End-to-End Entity Relationships
# ==============================================================================

def test_31_realistic_end_to_end_relationships(repo_session):
    """Verify all domain relationship chains via repositories:
    - Organization -> User
    - NGO -> Proposal -> Project -> DueDiligenceReport
    - Proposal -> Document -> Project
    - Project -> Geography -> ImpactDNA -> SaturationResult -> Allocation
    - OptimizationRun -> Allocation -> ReallocationRun
    """
    # 1. Organization -> User
    org_repo = OrganizationRepository(repo_session)
    user_repo = UserRepository(repo_session)
    org = org_repo.create(name="Infosys Foundation")
    user = user_repo.create(email="csr@infosys.org", organization_id=org.id, name="Sudha Murty")
    assert user.organization.name == "Infosys Foundation"
    assert len(org.users) == 1

    # 2. NGO -> Proposal & DueDiligenceReport
    ngo_repo = NGORepository(repo_session)
    ngo = ngo_repo.create(name="Goonj", external_id="NGO-GOONJ-01")

    dd_repo = DueDiligenceRepository(repo_session)
    dd_rep = dd_repo.create(
        public_id=generate_public_id("DD", 888),
        ngo_id=ngo.id,
        overall_status="VERIFIED",
        risk_level="LOW",
        checks={"cloth_for_work": "VERIFIED"},
    )
    assert dd_rep.ngo.name == "Goonj"

    # 3. Proposal -> Document & Project
    prop_repo = ProposalRepository(repo_session)
    prop = prop_repo.create(
        public_id=generate_public_id("PRO", 888),
        ngo_id=ngo.id,
        title="Disaster Relief Material Supply",
    )

    doc_repo = DocumentRepository(repo_session)
    doc = doc_repo.create(
        public_id=generate_public_id("DOC", 888),
        proposal_id=prop.id,
        filename="goonj_relief_plan.pdf",
        mime_type="application/pdf",
        storage_key="s3://allocateai/goonj.pdf",
        file_size_bytes=204800,
        sha256="abc1234567890abcdef1234567890abcdef1234567890abcdef1234567890abc",
    )
    assert doc.proposal.title == "Disaster Relief Material Supply"

    # 4. Project -> Geography -> ImpactDNA -> SaturationResult
    proj_repo = ProjectRepository(repo_session)
    proj = proj_repo.create(
        public_id=generate_public_id("PRJ", 888),
        ngo_id=ngo.id,
        proposal_id=prop.id,
        name="Assam Flood Relief Kits",
        sector="DISASTER_RELIEF",
        duration_months=3,
        requested_amount=1000000000,
    )
    geo = proj_repo.add_geography(proj.id, state="Assam", district="Dhubri")

    dna_repo = ImpactDNARepository(repo_session)
    dna = dna_repo.create(
        public_id=generate_public_id("DNA", 888),
        project_id=proj.id,
        need_score=Decimal("0.99000"),
        expected_impact_score=Decimal("0.95000"),
        cost_efficiency_score=Decimal("0.90000"),
        evidence_strength_score=Decimal("0.88000"),
        scalability_score=Decimal("0.80000"),
        implementation_risk_score=Decimal("0.10000"),
        beneficiary_reach=20000,
        estimated_impact_per_lakh=Decimal("50.0000"),
        missing_fields={},
        extraction_confidence=Decimal("0.98000"),
        model_name="gemini-1.5-pro",
        prompt_version="v1.0",
    )

    sat_repo = SaturationRepository(repo_session)
    sat = sat_repo.create(
        project_id=proj.id,
        state="Assam",
        sector="DISASTER_RELIEF",
        saturation_index=Decimal("0.15000"),
        need_score=Decimal("0.98000"),
        existing_csr_amount=200000000,
        beneficiary_coverage=Decimal("0.20000"),
        confidence=Decimal("0.92000"),
    )

    # 5. OptimizationRun -> Allocation -> ReallocationRun
    opt_repo = OptimizationRepository(repo_session)
    opt_run = opt_repo.create(
        public_id=generate_public_id("OPT", 888),
        budget_paise=5000000000,
        weights={},
        constraints={},
        calculation_versions={},
        input_snapshot={},
        status="COMPLETED",
    )

    alloc_repo = AllocationRepository(repo_session)
    alloc = alloc_repo.create(
        optimization_run_id=opt_run.id,
        project_id=proj.id,
        allocated_amount=1000000000,
        marginal_score=Decimal("0.95000"),
        base_score=Decimal("0.96000"),
        saturation_index=Decimal("0.15000"),
        reason_codes={"codes": ["CRITICAL_NEED", "LOW_SATURATION"]},
        rank=1,
    )

    realloc_repo = ReallocationRepository(repo_session)
    realloc = realloc_repo.create(
        public_id=generate_public_id("REA", 888),
        previous_optimization_id=opt_run.id,
        budget_paise=1000000000,
        performance_snapshot={"delivery_ratio": 1.0},
        calculation_versions={"v": "1.0"},
    )

    # Assert relations
    assert proj.proposal.id == prop.id
    assert proj.ngo.id == ngo.id
    assert proj.impact_dna.id == dna.id
    assert len(proj.geographies) == 1
    assert len(proj.saturation_results) == 1
    assert len(opt_run.allocations) == 1
    assert alloc.project.name == "Assam Flood Relief Kits"
    assert realloc.previous_optimization.id == opt_run.id
