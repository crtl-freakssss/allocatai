import pytest
from pydantic import ValidationError

from app.schemas import (
    # Enums
    ProjectSector,
    ProposalStatus,
    VerificationStatus,
    ConfidenceLevel,
    DueDiligenceRisk,
    OptimizationStatus,
    AllocationStatus,
    AuditEventType,
    ReasonCode,
    # Domain Models
    Geography,
    BeneficiaryProfile,
    Financials,
    ImpactMetric,
    Project,
    ImpactDNA,
    SaturationResult,
    MarginalImpactResult,
    DEFAULT_INCREMENT_PAISE,
    Allocation,
    OptimizationWeights,
    OptimizationConstraints,
    OptimizationRequest,
    OptimizationResult,
    ProjectPerformanceUpdate,
    ReallocationRequest,
    ReallocationResult,
    DueDiligenceCheck,
    DueDiligenceReport,
    EvidenceItem,
    ExtractionResult,
    # API Schemas
    CreateProposalRequest,
    CreateProposalResponse,
    ProposalResponse,
    ExtractProposalRequest,
    ExtractProposalResponse,
    CreateDocumentResponse,
    DocumentResponse,
    AuditEventCreate,
    AuditEventResponse,
    # Envelopes
    PaginationMeta,
    ResponseMeta,
    ApiResponse,
    ApiCollectionResponse,
    FieldErrorItem,
    ErrorBody,
    ApiErrorResponse,
)


# ==============================================================================
# 1. Enums - Valid Contract Values
# ==============================================================================

def test_1_enums_accept_valid_contract_values():
    """Requirement 1: Verify every enum accepts valid contract values."""
    assert ProjectSector("EDUCATION") == ProjectSector.EDUCATION
    assert ProjectSector("HEALTHCARE") == ProjectSector.HEALTHCARE
    assert ProjectSector("OTHER") == ProjectSector.OTHER

    assert ProposalStatus("UPLOADED") == ProposalStatus.UPLOADED
    assert ProposalStatus("READY") == ProposalStatus.READY

    assert VerificationStatus("VERIFIED") == VerificationStatus.VERIFIED
    assert VerificationStatus("FLAGGED") == VerificationStatus.FLAGGED

    assert ConfidenceLevel("HIGH") == ConfidenceLevel.HIGH
    assert ConfidenceLevel("UNKNOWN") == ConfidenceLevel.UNKNOWN

    assert DueDiligenceRisk("LOW") == DueDiligenceRisk.LOW
    assert DueDiligenceRisk("CRITICAL") == DueDiligenceRisk.CRITICAL

    assert OptimizationStatus("QUEUED") == OptimizationStatus.QUEUED
    assert OptimizationStatus("COMPLETED") == OptimizationStatus.COMPLETED

    assert AllocationStatus("PROPOSED") == AllocationStatus.PROPOSED
    assert AllocationStatus("REALLOCATED") == AllocationStatus.REALLOCATED

    assert AuditEventType("PROPOSAL_CREATED") == AuditEventType.PROPOSAL_CREATED
    assert AuditEventType("ERROR_OCCURRED") == AuditEventType.ERROR_OCCURRED

    assert ReasonCode("HIGH_NEED") == ReasonCode.HIGH_NEED
    assert ReasonCode("DUE_DILIGENCE_FLAG") == ReasonCode.DUE_DILIGENCE_FLAG


# ==============================================================================
# 2. Enums - Invalid Values Rejected
# ==============================================================================

def test_2_enums_reject_invalid_values():
    """Requirement 2: Verify invalid enum values are rejected."""
    with pytest.raises(ValueError):
        ProjectSector("NON_EXISTENT_SECTOR")

    with pytest.raises(ValueError):
        ProposalStatus("PENDING")

    with pytest.raises(ValueError):
        VerificationStatus("APPROVED")

    with pytest.raises(ValueError):
        DueDiligenceRisk("EXTREME")

    with pytest.raises(ValueError):
        OptimizationStatus("PAUSED")

    with pytest.raises(ValueError):
        AllocationStatus("DECLINED")

    with pytest.raises(ValueError):
        ReasonCode("INVALID_REASON")


# ==============================================================================
# 3. Geography Validation
# ==============================================================================

def test_3_geography_validation():
    """Requirement 3: Verify Geography state min/max length and optional district/block."""
    geo = Geography(state="Maharashtra", district="Pune", block="Haveli")
    assert geo.state == "Maharashtra"
    assert geo.district == "Pune"
    assert geo.block == "Haveli"

    geo_state_only = Geography(state="Rajasthan")
    assert geo_state_only.district is None
    assert geo_state_only.block is None

    # Empty state rejected
    with pytest.raises(ValidationError):
        Geography(state="")

    # State exceeding 100 chars rejected
    with pytest.raises(ValidationError):
        Geography(state="M" * 101)


# ==============================================================================
# 4. BeneficiaryProfile Validation
# ==============================================================================

def test_4_beneficiary_profile_validation():
    """Requirement 4: Verify BeneficiaryProfile accepts non-negative target count and default lists."""
    profile = BeneficiaryProfile(target_count=5000)
    assert profile.target_count == 5000
    assert profile.groups == []
    assert profile.age_ranges == []
    assert profile.vulnerable_groups == []

    # Negative target_count rejected
    with pytest.raises(ValidationError):
        BeneficiaryProfile(target_count=-1)


# ==============================================================================
# 5 & 6. Financials Validation
# ==============================================================================

def test_5_financials_rejects_zero_or_negative_requested_amount():
    """Requirement 5: Verify Financials rejects zero or negative requested amount."""
    with pytest.raises(ValidationError):
        Financials(requested_amount_paise=0)

    with pytest.raises(ValidationError):
        Financials(requested_amount_paise=-1000)


def test_6_financials_accepts_zero_current_and_other_funding():
    """Requirement 6: Verify Financials accepts zero for current and other funding."""
    fin = Financials(
        requested_amount_paise=50000000,  # ₹5,00,000 in paise
        current_funding_paise=0,
        other_funding_paise=0,
    )
    assert fin.requested_amount_paise == 50000000
    assert fin.current_funding_paise == 0
    assert fin.other_funding_paise == 0


# ==============================================================================
# 7 & 8. Project Validation
# ==============================================================================

def test_7_project_rejects_invalid_duration():
    """Requirement 7: Verify Project duration must be strictly greater than zero."""
    with pytest.raises(ValidationError):
        Project(
            project_id="PRJ-0001",
            name="Rural Sanitation",
            ngo_id="NGO-0001",
            sector=ProjectSector.HEALTHCARE,
            geographies=[Geography(state="Bihar")],
            beneficiary_profile=BeneficiaryProfile(target_count=1000),
            financials=Financials(requested_amount_paise=100000000),
            duration_months=0,  # invalid
        )


def test_8_project_rejects_invalid_sector():
    """Requirement 8: Verify Project rejects invalid sector string."""
    with pytest.raises(ValidationError):
        Project(
            project_id="PRJ-0001",
            name="Solar micro-grids",
            ngo_id="NGO-0001",
            sector="INFRASTRUCTURE",  # not a valid ProjectSector
            geographies=[Geography(state="Gujarat")],
            beneficiary_profile=BeneficiaryProfile(target_count=500),
            financials=Financials(requested_amount_paise=200000000),
            duration_months=12,
        )


# ==============================================================================
# 9 & 10. ImpactDNA Validation
# ==============================================================================

def test_9_impact_dna_rejects_scores_below_zero():
    """Requirement 9: Verify ImpactDNA rejects score below 0."""
    with pytest.raises(ValidationError):
        ImpactDNA(
            dna_id="DNA-0001",
            project_id="PRJ-0001",
            need_score=-0.05,  # invalid
            expected_impact_score=0.8,
            cost_efficiency_score=0.8,
            evidence_strength_score=0.8,
            scalability_score=0.8,
            implementation_risk_score=0.2,
            beneficiary_reach=5000,
            estimated_impact_per_lakh=15.0,
            extraction_confidence=0.95,
            model_name="gemini-1.5-pro",
            prompt_version="v1.0",
        )


def test_10_impact_dna_rejects_scores_above_one():
    """Requirement 10: Verify ImpactDNA rejects score above 1."""
    with pytest.raises(ValidationError):
        ImpactDNA(
            dna_id="DNA-0001",
            project_id="PRJ-0001",
            need_score=0.8,
            expected_impact_score=1.05,  # invalid
            cost_efficiency_score=0.8,
            evidence_strength_score=0.8,
            scalability_score=0.8,
            implementation_risk_score=0.2,
            beneficiary_reach=5000,
            estimated_impact_per_lakh=15.0,
            extraction_confidence=0.95,
            model_name="gemini-1.5-pro",
            prompt_version="v1.0",
        )


# ==============================================================================
# 11. SaturationResult Score Validation
# ==============================================================================

def test_11_saturation_result_score_validation():
    """Requirement 11: Verify SaturationResult validates bounds on scores and money."""
    sat = SaturationResult(
        project_id="PRJ-0001",
        state="Maharashtra",
        sector=ProjectSector.EDUCATION,
        saturation_index=0.45,
        need_score=0.85,
        existing_csr_amount_paise=1500000000,
        estimated_beneficiary_coverage=0.40,
        confidence=0.90,
    )
    assert sat.saturation_index == 0.45
    assert sat.existing_csr_amount_paise == 1500000000

    # saturation_index > 1 rejected
    with pytest.raises(ValidationError):
        SaturationResult(
            project_id="PRJ-0001",
            state="Maharashtra",
            sector=ProjectSector.EDUCATION,
            saturation_index=1.1,
            need_score=0.5,
            existing_csr_amount_paise=0,
            estimated_beneficiary_coverage=0.5,
            confidence=0.8,
        )


# ==============================================================================
# 12. MarginalImpactResult Validation
# ==============================================================================

def test_12_marginal_impact_result_validation():
    """Requirement 12: Verify MarginalImpactResult structure and default increment."""
    res = MarginalImpactResult(
        project_id="PRJ-0001",
        baseline_budget_paise=50000000,
        projected_budget_paise=60000000,
        baseline_impact=100.0,
        projected_impact=118.5,
        incremental_impact=18.5,
        impact_per_lakh=18.5,
        marginal_impact_score=0.74,
        diminishing_return_factor=0.92,
    )
    assert res.increment_paise == DEFAULT_INCREMENT_PAISE
    assert res.diminishing_return_factor == 0.92

    # Negative increment rejected
    with pytest.raises(ValidationError):
        MarginalImpactResult(
            project_id="PRJ-0001",
            increment_paise=0,
            baseline_budget_paise=0,
            projected_budget_paise=1000000,
            baseline_impact=0.0,
            projected_impact=10.0,
            incremental_impact=10.0,
            impact_per_lakh=10.0,
            marginal_impact_score=0.5,
            diminishing_return_factor=0.5,
        )


# ==============================================================================
# 13 & 14. OptimizationWeights Normalization
# ==============================================================================

def test_13_optimization_weights_accepts_valid_normalized_weights():
    """Requirement 13: Verify OptimizationWeights accepts weights summing to 1.0."""
    weights = OptimizationWeights(
        need=0.25,
        marginal_impact=0.25,
        cost_efficiency=0.15,
        evidence=0.15,
        scalability=0.10,
        equity=0.05,
        risk_penalty=0.05,
    )
    assert weights.need == 0.25


def test_14_optimization_weights_rejects_invalid_normalization():
    """Requirement 14: Verify OptimizationWeights rejects weights that do not sum to 1.0."""
    with pytest.raises(ValidationError, match="must sum to 1.0"):
        OptimizationWeights(
            need=0.5,
            marginal_impact=0.5,
            cost_efficiency=0.5,  # Sum = 1.5
            evidence=0.0,
            scalability=0.0,
            equity=0.0,
            risk_penalty=0.0,
        )


# ==============================================================================
# 15. OptimizationConstraints Validation
# ==============================================================================

def test_15_optimization_constraints_reject_negative_monetary_values():
    """Requirement 15: Verify constraints reject negative budget thresholds."""
    with pytest.raises(ValidationError):
        OptimizationConstraints(max_allocation_per_project_paise=-500)


# ==============================================================================
# 16 & 17. OptimizationRequest Validation
# ==============================================================================

def test_16_optimization_request_rejects_zero_or_negative_budget():
    """Requirement 16: Verify OptimizationRequest rejects non-positive budget."""
    weights = OptimizationWeights(
        need=0.2, marginal_impact=0.2, cost_efficiency=0.2,
        evidence=0.2, scalability=0.1, equity=0.05, risk_penalty=0.05
    )
    constraints = OptimizationConstraints()

    with pytest.raises(ValidationError):
        OptimizationRequest(
            budget_paise=0,
            project_ids=["PRJ-0001"],
            weights=weights,
            constraints=constraints,
        )


def test_17_optimization_request_rejects_empty_project_list():
    """Requirement 17: Verify OptimizationRequest rejects empty project list."""
    weights = OptimizationWeights(
        need=0.2, marginal_impact=0.2, cost_efficiency=0.2,
        evidence=0.2, scalability=0.1, equity=0.05, risk_penalty=0.05
    )
    constraints = OptimizationConstraints()

    with pytest.raises(ValidationError):
        OptimizationRequest(
            budget_paise=100000000,
            project_ids=[],  # min_length=1
            weights=weights,
            constraints=constraints,
        )


# ==============================================================================
# 18 & 19. Allocation Validation
# ==============================================================================

def test_18_allocation_rejects_invalid_rank():
    """Requirement 18: Verify Allocation rejects rank <= 0."""
    with pytest.raises(ValidationError):
        Allocation(
            project_id="PRJ-0001",
            allocated_amount_paise=100000000,
            marginal_impact_score=0.85,
            base_score=0.90,
            saturation_index=0.30,
            reason_codes=[ReasonCode.HIGH_NEED],
            rank=0,  # must be gt=0
        )


def test_19_allocation_rejects_invalid_score():
    """Requirement 19: Verify Allocation rejects out-of-bounds score."""
    with pytest.raises(ValidationError):
        Allocation(
            project_id="PRJ-0001",
            allocated_amount_paise=100000000,
            marginal_impact_score=1.2,  # le=1
            base_score=0.90,
            saturation_index=0.30,
            reason_codes=[ReasonCode.HIGH_NEED],
            rank=1,
        )


# ==============================================================================
# 20. OptimizationResult Budget Invariant
# ==============================================================================

def test_20_optimization_result_validates_budget_invariant():
    """Requirement 20: Verify allocated_paise + unallocated_paise == budget_paise."""
    weights = OptimizationWeights(
        need=0.2, marginal_impact=0.2, cost_efficiency=0.2,
        evidence=0.2, scalability=0.1, equity=0.05, risk_penalty=0.05
    )
    constraints = OptimizationConstraints()
    alloc = Allocation(
        project_id="PRJ-0001",
        allocated_amount_paise=80000000,
        marginal_impact_score=0.85,
        base_score=0.90,
        saturation_index=0.25,
        reason_codes=[ReasonCode.HIGH_NEED],
        rank=1,
    )

    # Valid conservation: 80,000,000 + 20,000,000 == 100,000,000
    valid_res = OptimizationResult(
        run_id="OPT-0001",
        status=OptimizationStatus.COMPLETED,
        budget_paise=100000000,
        allocated_paise=80000000,
        unallocated_paise=20000000,
        allocations=[alloc],
        total_predicted_impact=142.5,
        average_saturation=0.25,
        underserved_region_allocation_share=0.80,
        weights=weights,
        constraints=constraints,
        calculation_versions={"solver": "scipy-milp-v1"},
        created_at="2026-09-03T12:00:00Z",
    )
    assert valid_res.budget_paise == 100000000

    # Violated invariant: 80,000,000 + 10,000,000 != 100,000,000
    with pytest.raises(ValidationError, match="Budget invariant violated"):
        OptimizationResult(
            run_id="OPT-0001",
            status=OptimizationStatus.COMPLETED,
            budget_paise=100000000,
            allocated_paise=80000000,
            unallocated_paise=10000000,  # Missing 10,000,000
            allocations=[alloc],
            total_predicted_impact=142.5,
            average_saturation=0.25,
            underserved_region_allocation_share=0.80,
            weights=weights,
            constraints=constraints,
            calculation_versions={"solver": "scipy-milp-v1"},
            created_at="2026-09-03T12:00:00Z",
        )


# ==============================================================================
# 21. Reallocation Request Validation
# ==============================================================================

def test_21_reallocation_request_validation():
    """Requirement 21: Verify ReallocationRequest validates budget and updates."""
    weights = OptimizationWeights(
        need=0.2, marginal_impact=0.2, cost_efficiency=0.2,
        evidence=0.2, scalability=0.1, equity=0.05, risk_penalty=0.05
    )
    constraints = OptimizationConstraints()
    update = ProjectPerformanceUpdate(
        project_id="PRJ-0001",
        progress_percent=85.0,
        actual_spend_paise=40000000,
    )

    req = ReallocationRequest(
        previous_run_id="OPT-0001",
        budget_paise=50000000,
        performance_updates=[update],
        weights=weights,
        constraints=constraints,
    )
    assert req.previous_run_id == "OPT-0001"

    # Progress > 100 rejected
    with pytest.raises(ValidationError):
        ProjectPerformanceUpdate(project_id="PRJ-0001", progress_percent=105.0)


# ==============================================================================
# 22. Due Diligence Confidence Validation
# ==============================================================================

def test_22_due_diligence_confidence_validation():
    """Requirement 22: Verify DueDiligenceCheck confidence bounds [0, 1]."""
    check = DueDiligenceCheck(
        check_name="fcra_validity",
        status=VerificationStatus.VERIFIED,
        confidence=0.98,
        checked_at="2026-09-03T12:00:00Z",
    )
    assert check.confidence == 0.98

    # Confidence > 1 rejected
    with pytest.raises(ValidationError):
        DueDiligenceCheck(
            check_name="fcra_validity",
            status=VerificationStatus.VERIFIED,
            confidence=1.5,
            checked_at="2026-09-03T12:00:00Z",
        )


# ==============================================================================
# 23. Evidence Confidence Validation
# ==============================================================================

def test_23_evidence_confidence_validation():
    """Requirement 23: Verify EvidenceItem confidence bounds [0, 1]."""
    item = EvidenceItem(
        evidence_id="EVD-0001",
        source_type="AUDITED_FINANCIALS",
        claim="Annual audit shows clean opinion",
        confidence=0.95,
        verification_status=VerificationStatus.VERIFIED,
    )
    assert item.confidence == 0.95

    with pytest.raises(ValidationError):
        EvidenceItem(
            evidence_id="EVD-0001",
            source_type="AUDITED_FINANCIALS",
            claim="Clean opinion",
            confidence=-0.1,
            verification_status=VerificationStatus.VERIFIED,
        )


# ==============================================================================
# 24. ExtractionResult Validation
# ==============================================================================

def test_24_extraction_result_validation():
    """Requirement 24: Verify ExtractionResult embeds valid Project and Evidence."""
    project = Project(
        project_id="PRJ-0001",
        name="Digital Classrooms",
        ngo_id="NGO-0001",
        sector=ProjectSector.EDUCATION,
        geographies=[Geography(state="Karnataka")],
        beneficiary_profile=BeneficiaryProfile(target_count=3000),
        financials=Financials(requested_amount_paise=150000000),
        duration_months=24,
    )
    evidence = [
        EvidenceItem(
            evidence_id="EVD-0001",
            source_type="PROPOSAL_PDF",
            claim="Beneficiary count is 3000",
            extracted_value="3000",
            confidence=0.92,
            verification_status=VerificationStatus.UNVERIFIED,
        )
    ]

    result = ExtractionResult(
        proposal_id="PRO-0001",
        document_id="DOC-0001",
        extracted_project=project,
        evidence=evidence,
        missing_fields=[],
        warnings=[],
        extraction_confidence=0.92,
        model_name="gemini-1.5-pro",
        prompt_version="prompt-v1.4",
    )
    assert result.extracted_project.name == "Digital Classrooms"
    assert result.evidence[0].confidence == 0.92


# ==============================================================================
# 25, 26, 27. API Envelopes Serialization
# ==============================================================================

def test_25_api_success_envelope_serialization():
    """Requirement 25: Verify ApiResponse generic envelope serialization."""
    resp = ApiResponse(
        data={"proposal_id": "PRO-0001", "status": "UPLOADED"},
        meta=ResponseMeta(request_id="REQ-123", schema_version="api-v1"),
    )
    serialized = resp.model_dump()
    assert serialized["data"]["proposal_id"] == "PRO-0001"
    assert serialized["meta"]["request_id"] == "REQ-123"
    assert serialized["meta"]["schema_version"] == "api-v1"
    assert "timestamp" in serialized["meta"]


def test_26_api_collection_envelope_serialization():
    """Requirement 26: Verify ApiCollectionResponse generic collection serialization with pagination."""
    resp = ApiCollectionResponse(
        data=[{"project_id": "PRJ-0001"}, {"project_id": "PRJ-0002"}],
        meta=ResponseMeta(
            request_id="REQ-123",
            schema_version="api-v1",
            pagination=PaginationMeta(page=1, page_size=20, total=2),
        ),
    )
    serialized = resp.model_dump()
    assert len(serialized["data"]) == 2
    assert serialized["meta"]["pagination"]["total"] == 2
    assert serialized["meta"]["pagination"]["page"] == 1


def test_27_api_error_envelope_serialization():
    """Requirement 27: Verify ApiErrorResponse serialization without stack traces."""
    err = ApiErrorResponse(
        error=ErrorBody(
            code="VALIDATION_ERROR",
            message="One or more fields are invalid.",
            details=[
                FieldErrorItem(field="budget_paise", reason="must be greater than zero")
            ],
            request_id="REQ-123",
        )
    )
    serialized = err.model_dump()
    assert serialized["error"]["code"] == "VALIDATION_ERROR"
    assert serialized["error"]["details"][0]["field"] == "budget_paise"
    assert serialized["error"]["request_id"] == "REQ-123"
    assert "stack" not in serialized["error"]


# ==============================================================================
# 28 & 29. Monetary Precision & Float Rejection
# ==============================================================================

def test_28_monetary_fields_remain_integers():
    """Requirement 28: Verify monetary paise fields remain integer type."""
    fin = Financials(requested_amount_paise=100000000)
    assert isinstance(fin.requested_amount_paise, int)
    assert not isinstance(fin.requested_amount_paise, float)


def test_29_invalid_monetary_float_values_are_rejected():
    """Requirement 29: Verify float monetary paise values are rejected under strict typing."""
    with pytest.raises(ValidationError):
        Financials(requested_amount_paise=1000.50)  # strict=True int rejects float


# ==============================================================================
# 30. Full Schema Import Test
# ==============================================================================

def test_30_full_schema_import_and_export():
    """Requirement 30: Verify all canonical schemas and enums import cleanly from app.schemas."""
    import app.schemas as schemas

    expected_exports = [
        "ProjectSector", "ProposalStatus", "VerificationStatus", "ConfidenceLevel",
        "DueDiligenceRisk", "OptimizationStatus", "AllocationStatus", "AuditEventType",
        "ReasonCode", "Geography", "BeneficiaryProfile", "Financials", "ImpactMetric",
        "Project", "ImpactDNA", "SaturationResult", "MarginalImpactResult",
        "DEFAULT_INCREMENT_PAISE", "Allocation", "OptimizationWeights",
        "OptimizationConstraints", "OptimizationRequest", "OptimizationResult",
        "ProjectPerformanceUpdate", "ReallocationRequest", "ReallocationResult",
        "DueDiligenceCheck", "DueDiligenceReport", "EvidenceItem", "ExtractionResult",
        "CreateProjectRequest", "ProjectResponse", "CreateProposalRequest",
        "CreateProposalResponse", "ProposalResponse", "ExtractProposalRequest",
        "ExtractProposalResponse", "CreateDocumentResponse", "DocumentResponse",
        "AuditEventCreate", "AuditEventResponse", "PaginationMeta", "ResponseMeta",
        "ApiResponse", "ApiCollectionResponse", "FieldErrorItem", "ErrorBody",
        "ApiErrorResponse", "MetaSchema", "DataEnvelope", "ErrorDetail", "ErrorEnvelope",
    ]

    for name in expected_exports:
        assert hasattr(schemas, name), f"app.schemas missing export: {name}"
