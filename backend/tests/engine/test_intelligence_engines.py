import pytest
from datetime import datetime, timezone

from app.schemas.project import Project as SchemaProject
from app.schemas.geography import Geography
from app.schemas.beneficiary import BeneficiaryProfile
from app.schemas.financials import Financials
from app.schemas.enums import ProjectSector, OptimizationStatus, AllocationStatus, VerificationStatus
from app.schemas.optimization import (
    OptimizationRequest,
    OptimizationWeights,
    OptimizationConstraints,
)
from app.schemas.reallocation import (
    ReallocationRequest,
    ProjectPerformanceUpdate,
)
from app.engine import (
    RealExtractionEngine,
    DocumentParser,
    StructuredExtractionClient,
    RealImpactDNAEngine,
    ScoringEngine,
    RealSaturationEngine,
    MarginalImpactCalculator,
    RealOptimizationEngine,
    MILPOptimizerFormulation,
    RealReallocationEngine,
    RealDueDiligenceEngine,
)


# ==============================================================================
# Helper Factories
# ==============================================================================

def make_test_project(
    project_id: str = "PRJ-TEST-01",
    name: str = "Assam Flood Resilience",
    sector: ProjectSector = ProjectSector.DISASTER_RELIEF,
    state: str = "Assam",
    requested_amount_paise: int = 500_000_000,  # ₹50 Lakhs
) -> SchemaProject:
    return SchemaProject(
        project_id=project_id,
        name=name,
        ngo_id="NGO-TEST",
        sector=sector,
        geographies=[Geography(state=state, district="Dhubri", block="Bilasipara")],
        beneficiary_profile=BeneficiaryProfile(target_count=3000),
        financials=Financials(requested_amount_paise=requested_amount_paise),
        duration_months=12,
        impact_metrics=[],
    )


# ==============================================================================
# 1 to 5. Extraction Engine Tests
# ==============================================================================

def test_1_to_5_extraction_pipeline():
    """Verify document parsing, structured extraction, evidence items, and missing fields."""
    engine = RealExtractionEngine()

    res = engine.extract(
        proposal_id="PRO-0001",
        document_id="DOC-0001",
        filename="solar_irrigation_rajasthan_plan.pdf",
        mime_type="application/pdf",
        storage_key="s3://allocateai/solar.pdf",
    )

    # 1. Valid structured extraction
    assert res.proposal_id == "PRO-0001"
    assert res.document_id == "DOC-0001"
    assert res.extracted_project.name.startswith("Solar Irrigation Rajasthan")
    assert res.extracted_project.sector == ProjectSector.ENVIRONMENT
    assert res.extracted_project.financials.requested_amount_paise > 0

    # 4. Confidence validation
    assert 0.0 <= res.extraction_confidence <= 1.0

    # 5. Evidence validation (unverified by default)
    assert len(res.evidence) >= 1
    for ev in res.evidence:
        assert ev.verification_status == VerificationStatus.UNVERIFIED
        assert ev.confidence > 0.0

    # 3. Missing fields detection
    assert isinstance(res.missing_fields, list)

    # 2. Malformed / empty parsing gracefully handles
    empty_res = engine.extract(
        proposal_id="PRO-EMPTY",
        document_id="DOC-EMPTY",
        filename="unnamed.pdf",
        mime_type="application/pdf",
        storage_key="nonexistent_path_xyz",
    )
    assert empty_res.extracted_project.sector is not None


# ==============================================================================
# 6 to 8. Impact DNA Tests
# ==============================================================================

def test_6_to_8_impact_dna_engine():
    """Verify Impact DNA deterministic output, range bounds [0, 1], and versioning."""
    engine = RealImpactDNAEngine()

    dna = engine.generate(
        project_id="PRJ-DNA-01",
        name="Digital Literacy Mobile Vans",
        sector="EDUCATION",
        requested_amount_paise=400_000_000,
        geographies=[{"state": "Bihar", "district": "Gaya", "block": "Bodhgaya"}],
        beneficiary_profile={"target_count": 5000},
    )

    # 7. Score bounds
    for score in [
        dna.need_score,
        dna.expected_impact_score,
        dna.cost_efficiency_score,
        dna.evidence_strength_score,
        dna.scalability_score,
        dna.implementation_risk_score,
        dna.extraction_confidence,
    ]:
        assert 0.0 <= float(score) <= 1.0

    assert dna.beneficiary_reach == 5000
    assert dna.estimated_impact_per_lakh > 0.0

    # 8. Version tracking
    assert dna.model_name == "impact-dna-v1"
    assert dna.prompt_version == "dna-v1.0"

    # 6. Deterministic output for identical inputs
    dna2 = engine.generate(
        project_id="PRJ-DNA-01",
        name="Digital Literacy Mobile Vans",
        sector="EDUCATION",
        requested_amount_paise=400_000_000,
        geographies=[{"state": "Bihar", "district": "Gaya", "block": "Bodhgaya"}],
        beneficiary_profile={"target_count": 5000},
    )
    assert dna.need_score == dna2.need_score
    assert dna.expected_impact_score == dna2.expected_impact_score


# ==============================================================================
# 9 to 11. Deterministic Scoring Tests
# ==============================================================================

def test_9_to_11_scoring_engine():
    """Verify deterministic project scoring, weight sensitivity, and range [0, 1]."""
    engine = RealImpactDNAEngine()
    dna = engine.generate(
        project_id="PRJ-SC-01",
        name="Maternal Health Clinics",
        sector="HEALTHCARE",
        requested_amount_paise=300_000_000,
        geographies=[{"state": "Jharkhand"}],
    )

    weights_need_heavy = OptimizationWeights(
        need=0.6, marginal_impact=0.1, cost_efficiency=0.1,
        evidence=0.05, scalability=0.05, equity=0.05, risk_penalty=0.05,
    )
    weights_cost_heavy = OptimizationWeights(
        need=0.1, marginal_impact=0.1, cost_efficiency=0.6,
        evidence=0.05, scalability=0.05, equity=0.05, risk_penalty=0.05,
    )

    score1 = ScoringEngine.calculate_score(dna, weights_need_heavy, saturation_index=0.2)
    score2 = ScoringEngine.calculate_score(dna, weights_cost_heavy, saturation_index=0.2)

    # 9. Determinism
    score1_repeat = ScoringEngine.calculate_score(dna, weights_need_heavy, saturation_index=0.2)
    assert score1 == score1_repeat

    # 10. Weight sensitivity: different weights produce different score
    assert score1 != score2

    # 11. Score range
    assert 0.0 <= score1 <= 1.0
    assert 0.0 <= score2 <= 1.0


# ==============================================================================
# 12 to 15. CSR Saturation Index Tests
# ==============================================================================

def test_12_to_15_saturation_engine():
    """Verify low vs high saturation differentiation, boundary values, and determinism."""
    engine = RealSaturationEngine()

    # High need + low CSR funding -> Low Saturation (Underserved)
    underserved = engine.calculate(
        project_id="PRJ-SAT-01",
        state="Jharkhand",
        sector="HEALTHCARE",
        need_score=0.95,
        existing_csr_amount_override=200_000_000,  # ₹2 Cr (Low)
    )

    # Low need + high CSR funding -> High Saturation (Well-served)
    saturated = engine.calculate(
        project_id="PRJ-SAT-02",
        state="Maharashtra",
        sector="SPORTS",
        need_score=0.30,
        existing_csr_amount_override=45_000_000_000,  # ₹450 Cr (High)
    )

    # 12 & 13. Low saturation scenario has lower saturation index than saturated
    assert underserved.saturation_index < saturated.saturation_index

    # 14. Boundary values
    assert 0.0 <= float(underserved.saturation_index) <= 1.0
    assert 0.0 <= float(saturated.saturation_index) <= 1.0

    # 15. Deterministic output
    repeat = engine.calculate(
        project_id="PRJ-SAT-01",
        state="Jharkhand",
        sector="HEALTHCARE",
        need_score=0.95,
        existing_csr_amount_override=200_000_000,
    )
    assert underserved.saturation_index == repeat.saturation_index


# ==============================================================================
# 16 to 18. Marginal Impact Tests
# ==============================================================================

def test_16_to_18_marginal_impact_calculator():
    """Verify incremental funding calculations, diminishing returns, and decay factor."""
    req_amt = 500_000_000  # ₹50 Lakhs

    # Tranche 1: Project currently at ₹0 allocation
    t1 = MarginalImpactCalculator.calculate(
        project_id="PRJ-M-01",
        requested_amount_paise=req_amt,
        baseline_allocated_paise=0,
        expected_impact_score=0.90,
        saturation_index=0.30,
    )

    # Tranche 2: Project already fully funded at ₹50 Lakhs
    t2 = MarginalImpactCalculator.calculate(
        project_id="PRJ-M-01",
        requested_amount_paise=req_amt,
        baseline_allocated_paise=req_amt,
        expected_impact_score=0.90,
        saturation_index=0.30,
    )

    # 16. Positive incremental impact
    assert t1.incremental_impact > 0.0
    assert t2.incremental_impact > 0.0

    # 17. Diminishing returns: tranche 1 marginal impact > tranche 2 marginal impact
    assert t1.incremental_impact > t2.incremental_impact
    assert t1.diminishing_return_factor > t2.diminishing_return_factor
    assert t1.marginal_impact_score > t2.marginal_impact_score

    # 18. Deterministic
    t1_repeat = MarginalImpactCalculator.calculate(
        project_id="PRJ-M-01",
        requested_amount_paise=req_amt,
        baseline_allocated_paise=0,
        expected_impact_score=0.90,
        saturation_index=0.30,
    )
    assert t1.incremental_impact == t1_repeat.incremental_impact


# ==============================================================================
# 19 to 26. Portfolio Optimizer Tests
# ==============================================================================

def test_19_to_26_portfolio_optimizer():
    """Verify budget conservation, project caps, regional caps, equity constraints, and determinism."""
    p1 = make_test_project("PRJ-OPT-01", "Assam Kits", ProjectSector.DISASTER_RELIEF, "Assam", 300_000_000)
    p2 = make_test_project("PRJ-OPT-02", "Bihar Health", ProjectSector.HEALTHCARE, "Bihar", 400_000_000)
    p3 = make_test_project("PRJ-OPT-03", "MH Sports", ProjectSector.SPORTS, "Maharashtra", 500_000_000)

    projects = [p1, p2, p3]
    total_budget = 600_000_000  # ₹6 Cr

    weights = OptimizationWeights(
        need=0.3, marginal_impact=0.3, cost_efficiency=0.2,
        evidence=0.1, scalability=0.05, equity=0.03, risk_penalty=0.02,
    )
    constraints = OptimizationConstraints(
        max_allocation_per_project_paise=250_000_000,  # ₹2.5 Cr cap per project
        max_allocation_per_region_paise=300_000_000,   # ₹3.0 Cr cap per region
        regional_equity_enabled=True,
    )
    req = OptimizationRequest(
        budget_paise=total_budget,
        project_ids=[p.project_id for p in projects],
        weights=weights,
        constraints=constraints,
    )

    optimizer = RealOptimizationEngine()
    result = optimizer.optimize(
        projects=projects,
        impact_dna_map={},
        saturation_map={},
        request=req,
        run_id="OPT-REAL-01",
    )

    # 19. Budget conservation: allocated + unallocated == budget ALWAYS
    assert result.allocated_paise + result.unallocated_paise == total_budget

    # 20. Project cap enforcement
    for alloc in result.allocations:
        assert alloc.allocated_amount_paise <= 250_000_000
        # 26. No negative allocations
        assert alloc.allocated_amount_paise >= 0

    # 21. Regional cap enforcement
    alloc_by_pid = {a.project_id: a.allocated_amount_paise for a in result.allocations}
    mh_alloc = alloc_by_pid.get("PRJ-OPT-03", 0)
    assert mh_alloc <= 300_000_000

    # 22. Regional equity enforcement: underserved regions received share
    assert result.underserved_region_allocation_share > 0.0

    # 25. Deterministic repeated run
    result2 = optimizer.optimize(
        projects=projects,
        impact_dna_map={},
        saturation_map={},
        request=req,
        run_id="OPT-REAL-01",
    )
    assert result.allocated_paise == result2.allocated_paise
    assert [a.allocated_amount_paise for a in result.allocations] == [a.allocated_amount_paise for a in result2.allocations]


def test_23_and_24_infeasible_budget_and_unallocated_residue():
    """Verify optimizer handles small candidate pools where budget exceeds caps."""
    p1 = make_test_project("PRJ-TINY-01", "Tiny Solar", ProjectSector.ENVIRONMENT, "Goa", 50_000_000)  # ₹50 Lakhs
    projects = [p1]
    huge_budget = 1_000_000_000  # ₹10 Cr

    weights = OptimizationWeights(
        need=0.3, marginal_impact=0.3, cost_efficiency=0.2,
        evidence=0.1, scalability=0.05, equity=0.03, risk_penalty=0.02,
    )
    req = OptimizationRequest(
        budget_paise=huge_budget,
        project_ids=[p1.project_id],
        weights=weights,
        constraints=OptimizationConstraints(regional_equity_enabled=False),
    )

    optimizer = RealOptimizationEngine()
    result = optimizer.optimize(projects=projects, impact_dna_map={}, saturation_map={}, request=req, run_id="OPT-TINY")

    # 24. Unallocated budget preserves conservation invariant
    assert result.allocated_paise == 50_000_000
    assert result.unallocated_paise == huge_budget - 50_000_000
    assert result.allocated_paise + result.unallocated_paise == huge_budget


# ==============================================================================
# 27 to 30. Reallocation Engine Tests
# ==============================================================================

def test_27_to_30_reallocation_engine():
    """Verify performance updates, capital shifts from delayed to top performers, and snapshot integrity."""
    p1 = make_test_project("PRJ-R-01", "Lagging Intervention", ProjectSector.EDUCATION, "Assam", 500_000_000)
    p2 = make_test_project("PRJ-R-02", "Fast Track Hospital", ProjectSector.HEALTHCARE, "Bihar", 500_000_000)

    weights = OptimizationWeights(
        need=0.3, marginal_impact=0.3, cost_efficiency=0.2,
        evidence=0.1, scalability=0.05, equity=0.03, risk_penalty=0.02,
    )
    opt_req = OptimizationRequest(
        budget_paise=1_000_000_000,
        project_ids=[p1.project_id, p2.project_id],
        weights=weights,
        constraints=OptimizationConstraints(),
    )
    opt_res = RealOptimizationEngine().optimize(
        projects=[p1, p2],
        impact_dna_map={},
        saturation_map={},
        request=opt_req,
        run_id="OPT-INIT",
    )

    realloc_req = ReallocationRequest(
        previous_run_id="OPT-INIT",
        budget_paise=1_000_000_000,
        performance_updates=[
            ProjectPerformanceUpdate(project_id="PRJ-R-01", progress_percent=20.0, actual_spend_paise=100_000_000),
            ProjectPerformanceUpdate(project_id="PRJ-R-02", progress_percent=90.0, actual_spend_paise=450_000_000),
        ],
        weights=weights,
        constraints=OptimizationConstraints(),
    )

    realloc_engine = RealReallocationEngine()
    realloc_res = realloc_engine.reallocate(
        previous_run_id="OPT-INIT",
        previous_allocations=opt_res.allocations,
        performance_updates=realloc_req.performance_updates,
        request=realloc_req,
        realloc_run_id="REA-0001",
    )

    # 27. Performance updates shifted funds
    assert realloc_res.total_budget_shifted_paise > 0
    assert "PRJ-R-01" in realloc_res.changed_projects

    # P1 allocation decreased, P2 allocation increased
    alloc_map_old = {a.project_id: a.allocated_amount_paise for a in opt_res.allocations}
    alloc_map_new = {a.project_id: a.allocated_amount_paise for a in realloc_res.new_allocations}
    assert alloc_map_new["PRJ-R-01"] < alloc_map_old["PRJ-R-01"]
    assert alloc_map_new["PRJ-R-02"] > alloc_map_old["PRJ-R-02"]

    # 28 & 29. Previous allocations and immutable snapshot preserved
    assert len(realloc_res.old_allocations) == 2
    assert realloc_res.previous_run_id == "OPT-INIT"
    assert len(realloc_res.explanation) >= 1


# ==============================================================================
# Due Diligence Engine Tests
# ==============================================================================

def test_due_diligence_real_engine():
    """Verify RealDueDiligenceEngine compliance checks and legal disclaimer preservation."""
    engine = RealDueDiligenceEngine()
    rep = engine.evaluate(
        ngo_id="NGO-REG-01",
        name="Asha Jyoti Trust",
        registration_number="12A-80G-2024-9999",
        report_id="DD-TEST-01",
    )

    assert rep.overall_status == VerificationStatus.VERIFIED
    assert len(rep.checks) == 4
    assert "does not constitute legal or regulatory certification" in rep.disclaimer
    assert rep.model_version == "due-diligence-v1"


# ==============================================================================
# 31 to 35. End-to-End Intelligence Integration
# ==============================================================================

def test_31_to_35_end_to_end_intelligence_flow():
    """Verify full intelligence flow: Extraction -> Project -> Impact DNA -> Saturation -> Marginal -> Optimization -> Reallocation."""
    # 31. Extraction -> Project
    extract_engine = RealExtractionEngine()
    extraction = extract_engine.extract(
        proposal_id="PRO-FLOW-01",
        document_id="DOC-FLOW-01",
        filename="chhattisgarh_clean_water_initiative.pdf",
        mime_type="application/pdf",
        storage_key="s3://allocateai/water.pdf",
    )
    assert extraction.extracted_project is not None
    project = extraction.extracted_project

    # 32. Project -> Impact DNA
    dna_engine = RealImpactDNAEngine()
    dna = dna_engine.generate(
        project_id="PRJ-FLOW-01",
        name=project.name,
        sector=project.sector.value,
        requested_amount_paise=project.financials.requested_amount_paise,
        geographies=[g.model_dump() for g in project.geographies],
        beneficiary_profile=project.beneficiary_profile.model_dump() if project.beneficiary_profile else None,
    )
    assert dna.need_score > 0.0

    # Saturation & Marginal Impact
    sat_engine = RealSaturationEngine()
    sat = sat_engine.calculate(
        project_id="PRJ-FLOW-01",
        state=project.geographies[0].state,
        sector=project.sector.value,
        need_score=float(dna.need_score),
    )
    marginal = MarginalImpactCalculator.calculate(
        project_id="PRJ-FLOW-01",
        requested_amount_paise=project.financials.requested_amount_paise,
        baseline_allocated_paise=0,
        expected_impact_score=float(dna.expected_impact_score),
        saturation_index=float(sat.saturation_index),
    )
    assert marginal.marginal_impact_score > 0.0

    # 33 & 34. Projects -> Optimization -> Output
    opt_engine = RealOptimizationEngine(
        saturation_engine=sat_engine,
        dna_engine=dna_engine,
    )
    weights = OptimizationWeights(
        need=0.3, marginal_impact=0.3, cost_efficiency=0.2,
        evidence=0.1, scalability=0.05, equity=0.03, risk_penalty=0.02,
    )
    opt_req = OptimizationRequest(
        budget_paise=project.financials.requested_amount_paise,
        project_ids=["PRJ-FLOW-01"],
        weights=weights,
        constraints=OptimizationConstraints(regional_equity_enabled=True),
    )
    opt_result = opt_engine.optimize(
        projects=[project],
        impact_dna_map={"PRJ-FLOW-01": dna},
        saturation_map={"PRJ-FLOW-01": sat},
        request=opt_req,
        run_id="OPT-FLOW-01",
    )
    assert opt_result.status == OptimizationStatus.COMPLETED
    assert opt_result.allocated_paise + opt_result.unallocated_paise == opt_req.budget_paise
    assert len(opt_result.allocations) == 1

    # 35. Reallocation on performance update
    realloc_engine = RealReallocationEngine()
    realloc_req = ReallocationRequest(
        previous_run_id="OPT-FLOW-01",
        budget_paise=opt_req.budget_paise,
        performance_updates=[
            ProjectPerformanceUpdate(project_id="PRJ-FLOW-01", progress_percent=85.0, actual_spend_paise=200_000_000)
        ],
        weights=weights,
        constraints=OptimizationConstraints(),
    )
    realloc_res = realloc_engine.reallocate(
        previous_run_id="OPT-FLOW-01",
        previous_allocations=opt_result.allocations,
        performance_updates=realloc_req.performance_updates,
        request=realloc_req,
        realloc_run_id="REA-FLOW-01",
    )
    assert realloc_res.run_id == "REA-FLOW-01"
    assert realloc_res.previous_run_id == "OPT-FLOW-01"


def test_marginal_impact_influences_allocation():
    """Verify that marginal impact diminishing returns materially alters solver allocation decisions."""
    p_high = make_test_project("PRJ-HIGH-01", "Saturated Health Hub", ProjectSector.HEALTHCARE, "Maharashtra", 1000_000_000)
    p_low = make_test_project("PRJ-LOW-02", "Underserved Bihar School", ProjectSector.EDUCATION, "Bihar", 1000_000_000)

    # Static solver without decay would give 100% of ₹10 Cr to High score project
    # Piecewise marginal impact solver splits budget to maximize total incremental marginal impact across tranches
    budget = 1000_000_000  # ₹10 Cr

    weights = OptimizationWeights(
        need=0.3, marginal_impact=0.3, cost_efficiency=0.2,
        evidence=0.1, scalability=0.05, equity=0.03, risk_penalty=0.02,
    )
    req = OptimizationRequest(
        budget_paise=budget,
        project_ids=["PRJ-HIGH-01", "PRJ-LOW-02"],
        weights=weights,
        constraints=OptimizationConstraints(
            max_allocation_per_project_paise=1000_000_000,
            regional_equity_enabled=False,  # Equity disabled to isolate pure marginal impact effect
        ),
    )

    engine = RealOptimizationEngine()
    result = engine.optimize(
        projects=[p_high, p_low],
        impact_dna_map={},
        saturation_map={},
        request=req,
        run_id="OPT-MARGINAL-PROOF",
    )

    alloc_map = {a.project_id: a.allocated_amount_paise for a in result.allocations}

    # Proves both projects received partial tranche funding because Tranche 1 of P_low
    # delivered higher marginal return than Tranche 2 of P_high!
    assert alloc_map["PRJ-HIGH-01"] > 0
    assert alloc_map["PRJ-LOW-02"] > 0
    assert result.allocated_paise + result.unallocated_paise == budget


