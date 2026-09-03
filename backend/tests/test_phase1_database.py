import os
import uuid
from decimal import Decimal
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from alembic.config import Config

from app.config.settings import get_settings
from app.db.base import Base
from app.db.identifiers import generate_public_id
from app.models import (
    Organization,
    User,
    NGO,
    Proposal,
    Document,
    Project,
    ProjectGeography,
    ImpactDNA,
    SaturationResult,
    DueDiligenceReport,
    OptimizationRun,
    Allocation,
    ReallocationRun,
    AuditEvent,
)

settings = get_settings()

EXPECTED_TABLES = {
    "organizations",
    "users",
    "ngos",
    "proposals",
    "documents",
    "projects",
    "project_geographies",
    "impact_dna",
    "saturation_results",
    "due_diligence_reports",
    "optimization_runs",
    "allocations",
    "reallocation_runs",
    "audit_events",
}


@pytest.fixture(scope="module")
def db_engine():
    """Create test engine connected to the PostgreSQL database."""
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Provide a transactional database session for each test that rolls back."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


def test_1_all_models_import():
    """Requirement 1: Verify all 14 models import cleanly and register on Base.metadata."""
    registered = set(Base.metadata.tables.keys())
    for tbl in EXPECTED_TABLES:
        assert tbl in registered, f"Table '{tbl}' missing from Base.metadata"


def test_2_alembic_config_import():
    """Requirement 2: Verify Alembic configuration loads and discovers metadata."""
    backend_dir = os.path.dirname(os.path.dirname(__file__))
    ini_path = os.path.join(backend_dir, "alembic.ini")
    assert os.path.exists(ini_path), f"alembic.ini not found at {ini_path}"
    cfg = Config(ini_path)
    assert cfg is not None
    assert cfg.get_main_option("script_location") == "alembic"


def test_3_all_expected_tables_exist_in_postgres(db_engine):
    """Requirements 3 & 4: Verify migration executed and all 14 tables exist in PostgreSQL."""
    inspector = inspect(db_engine)
    pg_tables = set(inspector.get_table_names())
    for tbl in EXPECTED_TABLES:
        assert tbl in pg_tables, f"Table '{tbl}' does not exist in PostgreSQL schema"


def test_5_primary_keys_exist_and_are_uuid(db_engine):
    """Requirement 5: Verify primary keys exist and use UUID data type."""
    inspector = inspect(db_engine)
    for tbl in EXPECTED_TABLES:
        pk_constraint = inspector.get_pk_constraint(tbl)
        assert pk_constraint is not None, f"Table '{tbl}' missing primary key constraint"
        pk_cols = pk_constraint.get("constrained_columns", [])
        assert pk_cols == ["id"], f"Table '{tbl}' primary key is not 'id'"

        columns = {c["name"]: c for c in inspector.get_columns(tbl)}
        id_type = str(columns["id"]["type"]).upper()
        assert "UUID" in id_type, f"Table '{tbl}'.id is not UUID type (found {id_type})"


def test_6_foreign_keys_exist(db_engine):
    """Requirement 6: Verify all required foreign key constraints exist."""
    inspector = inspect(db_engine)

    # users -> organizations
    user_fks = inspector.get_foreign_keys("users")
    assert any(fk["referred_table"] == "organizations" and fk["constrained_columns"] == ["organization_id"] for fk in user_fks)

    # proposals -> ngos
    prop_fks = inspector.get_foreign_keys("proposals")
    assert any(fk["referred_table"] == "ngos" and fk["constrained_columns"] == ["ngo_id"] for fk in prop_fks)

    # documents -> proposals
    doc_fks = inspector.get_foreign_keys("documents")
    assert any(fk["referred_table"] == "proposals" and fk["constrained_columns"] == ["proposal_id"] for fk in doc_fks)

    # projects -> ngos & proposals
    proj_fks = inspector.get_foreign_keys("projects")
    assert any(fk["referred_table"] == "ngos" and fk["constrained_columns"] == ["ngo_id"] for fk in proj_fks)
    assert any(fk["referred_table"] == "proposals" and fk["constrained_columns"] == ["proposal_id"] for fk in proj_fks)

    # allocations -> optimization_runs & projects
    alloc_fks = inspector.get_foreign_keys("allocations")
    assert any(fk["referred_table"] == "optimization_runs" and fk["constrained_columns"] == ["optimization_run_id"] for fk in alloc_fks)
    assert any(fk["referred_table"] == "projects" and fk["constrained_columns"] == ["project_id"] for fk in alloc_fks)

    # reallocation_runs -> optimization_runs
    realloc_fks = inspector.get_foreign_keys("reallocation_runs")
    assert any(fk["referred_table"] == "optimization_runs" and fk["constrained_columns"] == ["previous_optimization_id"] for fk in realloc_fks)


def test_7_unique_constraints_exist(db_engine):
    """Requirement 7: Verify unique constraints on emails and public_ids."""
    inspector = inspect(db_engine)

    # User email unique
    user_indexes = inspector.get_indexes("users")
    email_unique = any(idx["unique"] and "email" in idx["column_names"] for idx in user_indexes)
    assert email_unique, "users.email must have unique constraint/index"

    # Entities with unique public_id
    for tbl in [
        "proposals", "documents", "projects", "impact_dna",
        "due_diligence_reports", "optimization_runs", "reallocation_runs", "audit_events"
    ]:
        indexes = inspector.get_indexes(tbl)
        pub_id_unique = any(idx["unique"] and "public_id" in idx["column_names"] for idx in indexes)
        assert pub_id_unique, f"Table '{tbl}'.public_id must have unique constraint/index"


def test_8_bigint_used_for_money_fields(db_engine):
    """Requirement 8: Verify monetary fields in paise use BIGINT, never Float or Numeric."""
    inspector = inspect(db_engine)

    money_checks = [
        ("projects", "requested_amount"),
        ("projects", "current_funding"),
        ("optimization_runs", "budget_paise"),
        ("allocations", "allocated_amount"),
        ("reallocation_runs", "budget_paise"),
        ("saturation_results", "existing_csr_amount"),
        ("documents", "file_size_bytes"),
    ]

    for tbl, col_name in money_checks:
        columns = {c["name"]: c for c in inspector.get_columns(tbl)}
        col_type = str(columns[col_name]["type"]).upper()
        assert "BIGINT" in col_type, f"{tbl}.{col_name} must be BIGINT (found {col_type})"


def test_9_numeric_used_for_score_fields(db_engine):
    """Requirement 9: Verify scores use exact NUMERIC, never floating-point."""
    inspector = inspect(db_engine)

    score_checks = [
        ("impact_dna", "need_score", 6, 5),
        ("impact_dna", "expected_impact_score", 6, 5),
        ("impact_dna", "cost_efficiency_score", 6, 5),
        ("impact_dna", "evidence_strength_score", 6, 5),
        ("impact_dna", "scalability_score", 6, 5),
        ("impact_dna", "implementation_risk_score", 6, 5),
        ("impact_dna", "extraction_confidence", 6, 5),
        ("impact_dna", "estimated_impact_per_lakh", 14, 4),
        ("saturation_results", "saturation_index", 6, 5),
        ("saturation_results", "need_score", 6, 5),
        ("saturation_results", "beneficiary_coverage", 6, 5),
        ("saturation_results", "confidence", 6, 5),
        ("allocations", "marginal_score", 6, 5),
        ("allocations", "base_score", 6, 5),
        ("allocations", "saturation_index", 6, 5),
        ("optimization_runs", "total_predicted_impact", 18, 4),
    ]

    for tbl, col_name, prec, scale in score_checks:
        columns = {c["name"]: c for c in inspector.get_columns(tbl)}
        col = columns[col_name]
        col_type = str(col["type"]).upper()
        assert "NUMERIC" in col_type, f"{tbl}.{col_name} must be NUMERIC (found {col_type})"
        assert col["type"].precision == prec, f"{tbl}.{col_name} precision expected {prec}, found {col['type'].precision}"
        assert col["type"].scale == scale, f"{tbl}.{col_name} scale expected {scale}, found {col['type'].scale}"


def test_10_jsonb_used_for_snapshots_and_evidence(db_engine):
    """Requirement 10: Verify PostgreSQL JSONB is used for structured snapshots/evidence."""
    inspector = inspect(db_engine)

    jsonb_checks = [
        ("impact_dna", "missing_fields"),
        ("due_diligence_reports", "checks"),
        ("due_diligence_reports", "flags"),
        ("due_diligence_reports", "missing_documents"),
        ("optimization_runs", "weights"),
        ("optimization_runs", "constraints"),
        ("optimization_runs", "calculation_versions"),
        ("optimization_runs", "input_snapshot"),
        ("optimization_runs", "result_snapshot"),
        ("allocations", "reason_codes"),
        ("reallocation_runs", "performance_snapshot"),
        ("reallocation_runs", "result_snapshot"),
        ("reallocation_runs", "calculation_versions"),
        ("audit_events", "payload"),
    ]

    for tbl, col_name in jsonb_checks:
        columns = {c["name"]: c for c in inspector.get_columns(tbl)}
        col_type = str(columns[col_name]["type"]).upper()
        assert "JSONB" in col_type, f"{tbl}.{col_name} must be JSONB (found {col_type})"


def test_11_public_id_generation_and_uniqueness(db_session):
    """Requirement 11: Verify backend standardized public ID prefixes and sequential format."""
    from app.db.identifiers import STANDARD_PREFIXES

    # Verify all contract prefixes: ORG, USR, NGO, PRO, DOC, PRJ, OPT, REA, AUD, DD, DNA
    contract_prefixes = {"ORG", "USR", "NGO", "PRO", "DOC", "PRJ", "OPT", "REA", "AUD", "DD", "DNA"}
    assert STANDARD_PREFIXES == contract_prefixes

    for prefix in contract_prefixes:
        id_1 = generate_public_id(prefix, 1)
        id_2 = generate_public_id(prefix, 2)
        id_999 = generate_public_id(prefix, 999)
        assert id_1 == f"{prefix}-0001"
        assert id_2 == f"{prefix}-0002"
        assert id_999 == f"{prefix}-0999"

    # Verify validation errors for invalid prefix or non-positive sequence
    with pytest.raises(ValueError, match="Invalid public ID prefix"):
        generate_public_id("INVALID", 1)

    with pytest.raises(ValueError, match="positive integer"):
        generate_public_id("PRJ", 0)

    with pytest.raises(ValueError, match="positive integer"):
        generate_public_id("PRJ", -5)


def test_12_to_22_full_entity_relationships(db_session):
    """Requirements 12-22: Full integration test creating entities and verifying all relationships."""
    # 1. Organization & User
    org = Organization(name="Tata Trusts CSR")
    db_session.add(org)
    db_session.flush()

    user = User(
        organization_id=org.id,
        email="csr.lead@tatatrusts.org",
        name="Arjun Sharma",
    )
    db_session.add(user)
    db_session.flush()
    assert user.organization.name == "Tata Trusts CSR"
    assert len(org.users) == 1

    # 2. NGO
    ngo = NGO(
        external_id="NGO-IN-2024-001",
        name="Pratham Education Foundation",
        registration_number="REG-104928-MH",
    )
    db_session.add(ngo)
    db_session.flush()

    # 3. Due Diligence Report (NGO -> DueDiligenceReport) using standardized DD prefix
    dd_report = DueDiligenceReport(
        public_id=generate_public_id("DD", 1),
        ngo_id=ngo.id,
        overall_status="APPROVED",
        risk_level="LOW",
        checks={"financial_audit": "PASSED", "fcra_verified": True},
        flags=[],
        missing_documents=[],
        model_name="gemini-1.5-pro",
        model_version="v2.1",
    )
    db_session.add(dd_report)
    db_session.flush()
    assert len(ngo.due_diligence_reports) == 1

    # 4. Proposal & Document (NGO -> Proposal -> Document)
    proposal = Proposal(
        public_id=generate_public_id("PRO", 1),
        ngo_id=ngo.id,
        title="Accelerated Primary Literacy Initiative 2026",
        status="SUBMITTED",
        source_type="DIRECT_SUBMISSION",
    )
    db_session.add(proposal)
    db_session.flush()

    doc = Document(
        public_id=generate_public_id("DOC", 1),
        proposal_id=proposal.id,
        filename="project_proposal.pdf",
        mime_type="application/pdf",
        storage_key="s3://allocateai/docs/proposal_001.pdf",
        file_size_bytes=2450192,
        sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    db_session.add(doc)
    db_session.flush()
    assert len(proposal.documents) == 1
    assert proposal.documents[0].filename == "project_proposal.pdf"

    # 5. Project (Proposal -> Project, NGO -> Project)
    project = Project(
        public_id=generate_public_id("PRJ", 1),
        proposal_id=proposal.id,
        ngo_id=ngo.id,
        name="Digital Literacy in Rural Schools",
        sector="EDUCATION",
        duration_months=18,
        requested_amount=500000000,  # ₹50,00,000 in paise
        current_funding=0,
        description="Comprehensive primary education enablement across 50 schools.",
        schema_version="v1",
    )
    db_session.add(project)
    db_session.flush()
    assert project.proposal.title == "Accelerated Primary Literacy Initiative 2026"
    assert project.ngo.name == "Pratham Education Foundation"

    # 6. Project Geography (Project -> Geography)
    geo = ProjectGeography(
        project_id=project.id,
        state="Maharashtra",
        district="Pune",
        block="Haveli",
    )
    db_session.add(geo)
    db_session.flush()
    assert len(project.geographies) == 1

    # 7. Impact DNA (Project -> ImpactDNA)
    dna = ImpactDNA(
        public_id=generate_public_id("DNA", 1),
        project_id=project.id,
        need_score=Decimal("0.85200"),
        expected_impact_score=Decimal("0.91400"),
        cost_efficiency_score=Decimal("0.87500"),
        evidence_strength_score=Decimal("0.79000"),
        scalability_score=Decimal("0.93000"),
        implementation_risk_score=Decimal("0.12000"),
        beneficiary_reach=12500,
        estimated_impact_per_lakh=Decimal("45.2500"),
        missing_fields={},
        extraction_confidence=Decimal("0.96000"),
        model_name="gemini-1.5-pro",
        prompt_version="prompt-v1.4",
        schema_version="v1",
    )
    db_session.add(dna)
    db_session.flush()
    assert project.impact_dna.beneficiary_reach == 12500

    # 8. Saturation Result (Project -> SaturationResult)
    sat = SaturationResult(
        project_id=project.id,
        state="Maharashtra",
        sector="EDUCATION",
        saturation_index=Decimal("0.34000"),
        need_score=Decimal("0.85000"),
        existing_csr_amount=1500000000,  # ₹1.5 Cr in paise
        beneficiary_coverage=Decimal("0.42000"),
        confidence=Decimal("0.88000"),
        calculation_version="sat-engine-v1",
    )
    db_session.add(sat)
    db_session.flush()
    assert len(project.saturation_results) == 1

    # 9. Optimization Run & Allocation (OptimizationRun -> Allocations)
    opt_run = OptimizationRun(
        public_id=generate_public_id("OPT", 1),
        budget_paise=10000000000,  # ₹10 Cr in paise
        status="COMPLETED",
        weights={"need": 0.35, "impact": 0.40, "cost": 0.25},
        constraints={"max_per_sector": 0.5},
        calculation_versions={"solver": "scipy-milp-v1"},
        input_snapshot={"project_ids": [str(project.id)]},
        result_snapshot={"allocations": [{"project_id": str(project.id), "amount_paise": 500000000}]},
        total_predicted_impact=Decimal("942.5000"),
    )
    db_session.add(opt_run)
    db_session.flush()

    alloc = Allocation(
        optimization_run_id=opt_run.id,
        project_id=project.id,
        allocated_amount=500000000,  # ₹50 Lakhs in paise
        marginal_score=Decimal("0.89200"),
        base_score=Decimal("0.91400"),
        saturation_index=Decimal("0.34000"),
        reason_codes={"codes": ["HIGH_NEED", "LOW_SATURATION"]},
        rank=1,
        status="RECOMMENDED",
    )
    db_session.add(alloc)
    db_session.flush()
    assert len(opt_run.allocations) == 1
    assert alloc.project.name == "Digital Literacy in Rural Schools"

    # 10. Reallocation Run (Reallocation references previous optimization)
    realloc = ReallocationRun(
        public_id=generate_public_id("REA", 1),
        previous_optimization_id=opt_run.id,
        budget_paise=2000000000,  # ₹2 Cr
        performance_snapshot={"q2_delivery_rate": 0.95},
        result_snapshot={"reallocated": []},
        calculation_versions={"realloc_engine": "v1.0"},
    )
    db_session.add(realloc)
    db_session.flush()
    assert len(opt_run.reallocation_runs) == 1
    assert realloc.previous_optimization.public_id == opt_run.public_id


def test_23_reallocation_does_not_overwrite_previous_run(db_session):
    """Requirement 23: Verify reallocation creates a new record and preserves the original run."""
    opt_run = OptimizationRun(
        public_id=generate_public_id("OPT", 2),
        budget_paise=5000000000,
        status="COMPLETED",
        weights={"impact": 1.0},
        constraints={},
        calculation_versions={"v": "1.0"},
        input_snapshot={"original": True},
        result_snapshot={"allocated": 5000000000},
    )
    db_session.add(opt_run)
    db_session.flush()

    orig_input_snapshot = dict(opt_run.input_snapshot)
    orig_status = opt_run.status

    realloc = ReallocationRun(
        public_id=generate_public_id("REA", 2),
        previous_optimization_id=opt_run.id,
        budget_paise=1000000000,
        performance_snapshot={"shift": True},
        result_snapshot={"reallocated": True},
        calculation_versions={"v": "1.0"},
    )
    db_session.add(realloc)
    db_session.flush()

    # Query opt_run fresh and verify unchanged
    db_session.refresh(opt_run)
    assert opt_run.input_snapshot == orig_input_snapshot
    assert opt_run.status == orig_status
    assert realloc.id != opt_run.id


def test_24_audit_event_insertion(db_session):
    """Requirement 24: Verify append-only audit event persistence."""
    audit_id = generate_public_id("AUD", 1)
    event = AuditEvent(
        public_id=audit_id,
        event_type="OPTIMIZATION_EXECUTION_COMPLETED",
        entity_type="optimization_runs",
        entity_id=uuid.uuid4(),
        request_id="req_9876543210ab",
        run_id="OPT-0001",
        payload={"solver_duration_ms": 1420, "solver_status": "OPTIMAL"},
    )
    db_session.add(event)
    db_session.flush()

    saved = db_session.query(AuditEvent).filter_by(public_id=audit_id).first()
    assert saved is not None
    assert saved.event_type == "OPTIMIZATION_EXECUTION_COMPLETED"
    assert saved.payload["solver_status"] == "OPTIMAL"
    assert saved.created_at is not None


def test_25_project_with_allocation_cannot_be_deleted(db_session):
    """Requirement: Rule 9 - Projects participating in optimization runs cannot be hard-deleted."""
    ngo = NGO(name="Test NGO RESTRICT", external_id="NGO-RESTRICT-01")
    db_session.add(ngo)
    db_session.flush()

    project = Project(
        public_id=generate_public_id("PRJ", 99),
        ngo_id=ngo.id,
        name="Undeletable Allocated Project",
        sector="WATER",
        duration_months=12,
        requested_amount=100000000,
        schema_version="v1",
    )
    db_session.add(project)
    db_session.flush()

    opt_run = OptimizationRun(
        public_id=generate_public_id("OPT", 99),
        budget_paise=100000000,
        status="COMPLETED",
        weights={},
        constraints={},
        calculation_versions={},
        input_snapshot={},
    )
    db_session.add(opt_run)
    db_session.flush()

    alloc = Allocation(
        optimization_run_id=opt_run.id,
        project_id=project.id,
        allocated_amount=100000000,
        reason_codes={},
        rank=1,
        status="ALLOCATED",
    )
    db_session.add(alloc)
    db_session.flush()

    # Attempt to delete project while referenced by allocation
    db_session.delete(project)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
