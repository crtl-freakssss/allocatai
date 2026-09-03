import pytest
from app.schemas.project import Project as SchemaProject
from app.schemas.geography import Geography
from app.schemas.financials import Financials
from app.schemas.beneficiary import BeneficiaryProfile
from app.schemas.impact_dna import ImpactDNA as SchemaImpactDNA
from app.schemas.enums import ProjectSector, OptimizationStatus, AllocationStatus
from app.schemas.optimization import (
    OptimizationRequest,
    OptimizationWeights,
    OptimizationConstraints,
)
from app.engine.scoring.scorer import ScoringEngine
from app.engine.saturation.engine import RealSaturationEngine
from app.engine.marginal_impact.calculator import MarginalImpactCalculator
from app.engine.optimizer.formulation import MILPOptimizerFormulation
from app.engine.optimizer.engine import RealOptimizationEngine


def make_test_project(
    pid: str, name: str, sector: ProjectSector, state: str, req_paise: int
) -> SchemaProject:
    return SchemaProject(
        project_id=pid,
        name=name,
        ngo_id="NGO-QUANT-TEST",
        sector=sector,
        geographies=[Geography(state=state, district="Central", block="Block-1")],
        beneficiary_profile=BeneficiaryProfile(target_count=max(1000, req_paise // 50_000)),
        financials=Financials(requested_amount_paise=req_paise),
        duration_months=12,
        impact_metrics=[],
    )


@pytest.fixture
def quant_weights():
    return OptimizationWeights(
        need=0.3,
        marginal_impact=0.3,
        cost_efficiency=0.2,
        evidence=0.1,
        scalability=0.05,
        equity=0.03,
        risk_penalty=0.02,
    )


def test_1_scoring_engine_utility_weighting(quant_weights):
    """1. Verify ScoringEngine computes multi-attribute utility score in [0.0, 1.0]."""
    dna = SchemaImpactDNA(
        dna_id="DNA-0001",
        project_id="PRJ-0001",
        need_score=0.90,
        expected_impact_score=0.85,
        cost_efficiency_score=0.80,
        evidence_strength_score=0.88,
        scalability_score=0.75,
        implementation_risk_score=0.10,
        beneficiary_reach=5000,
        estimated_impact_per_lakh=45.0,
        missing_fields=[],
        extraction_confidence=0.95,
        model_name="impact-dna-v1",
        prompt_version="dna-v1.0",
    )

    score = ScoringEngine.calculate_score(
        impact_dna=dna,
        weights=quant_weights,
        saturation_index=0.20,
    )
    assert 0.0 <= score <= 1.0
    assert score > 0.60


def test_2_saturation_engine_state_benchmarks():
    """2. Verify RealSaturationEngine calculates explainable saturation index."""
    sat_engine = RealSaturationEngine()
    res_bihar = sat_engine.calculate(
        project_id="PRJ-0002",
        state="Bihar",
        sector="EDUCATION",
        need_score=0.92,
    )
    res_mh = sat_engine.calculate(
        project_id="PRJ-0003",
        state="Maharashtra",
        sector="HEALTHCARE",
        need_score=0.70,
    )

    assert 0.0 < res_bihar.saturation_index < 1.0
    assert 0.0 < res_mh.saturation_index < 1.0
    # Bihar (high need, lower benchmark) has lower saturation index than Maharashtra
    assert res_bihar.saturation_index < res_mh.saturation_index


def test_3_marginal_impact_diminishing_returns():
    """3. Verify MarginalImpactCalculator models diminishing returns decay over incremental funding."""
    calc = MarginalImpactCalculator()

    # Initial funding tranche (0 allocated)
    res_0 = calc.calculate(
        project_id="PRJ-0004",
        requested_amount_paise=1000_000_000,
        baseline_allocated_paise=0,
        expected_impact_score=0.90,
        saturation_index=0.30,
    )

    # Later funding tranche (100% funded)
    res_100 = calc.calculate(
        project_id="PRJ-0004",
        requested_amount_paise=1000_000_000,
        baseline_allocated_paise=1000_000_000,
        expected_impact_score=0.90,
        saturation_index=0.30,
    )

    assert res_0.marginal_impact_score > res_100.marginal_impact_score
    assert res_0.incremental_impact > res_100.incremental_impact


def test_4_integer_paise_budget_conservation(quant_weights):
    """4. Verify strict integer paise conservation: sum(allocated) + unallocated == budget ALWAYS."""
    opt_engine = RealOptimizationEngine()
    projects = [
        make_test_project("PRJ-01", "P1", ProjectSector.HEALTHCARE, "Maharashtra", 600_000_000),
        make_test_project("PRJ-02", "P2", ProjectSector.EDUCATION, "Bihar", 400_000_000),
        make_test_project("PRJ-03", "P3", ProjectSector.ENVIRONMENT, "Assam", 500_000_000),
    ]

    for budget in [300_000_000, 700_000_000, 1500_000_000, 2000_000_000]:
        req = OptimizationRequest(
            budget_paise=budget,
            project_ids=[p.project_id for p in projects],
            weights=quant_weights,
            constraints=OptimizationConstraints(regional_equity_enabled=True),
        )
        res = opt_engine.optimize(
            projects=projects,
            impact_dna_map={},
            saturation_map={},
            request=req,
            run_id="OPT-CONSERVE-TEST",
        )

        total_allocated = sum(a.allocated_amount_paise for a in res.allocations)
        assert total_allocated == res.allocated_paise
        assert res.allocated_paise + res.unallocated_paise == budget


def test_5_critical_marginal_impact_prioritization(quant_weights):
    """5. CRITICAL RECOMPUTE TEST:
    Project A: Higher static base score (0.85), but saturated region (sat=0.80) -> low marginal impact.
    Project B: Lower static base score (0.75), but underserved region (sat=0.15) -> high marginal impact.
    Verify optimizer prefers Project B for additional funding due to higher marginal utility.
    """
    opt_engine = RealOptimizationEngine()

    prj_a = make_test_project("PRJ-A-SATURATED", "Mumbai Clinic", ProjectSector.HEALTHCARE, "Maharashtra", 500_000_000)
    prj_b = make_test_project("PRJ-B-UNDERSERVED", "Bihar School", ProjectSector.EDUCATION, "Bihar", 500_000_000)

    # Supply explicit DNA and Saturation to force high static score for A, but high marginal impact for B
    dna_a = SchemaImpactDNA(
        dna_id="DNA-A", project_id="PRJ-A-SATURATED",
        need_score=0.70, expected_impact_score=0.85, cost_efficiency_score=0.85,
        evidence_strength_score=0.85, scalability_score=0.80, implementation_risk_score=0.10,
        beneficiary_reach=5000, estimated_impact_per_lakh=40.0, missing_fields=[], extraction_confidence=0.95,
        model_name="dna-v1", prompt_version="v1",
    )
    dna_b = SchemaImpactDNA(
        dna_id="DNA-B", project_id="PRJ-B-UNDERSERVED",
        need_score=0.95, expected_impact_score=0.75, cost_efficiency_score=0.75,
        evidence_strength_score=0.75, scalability_score=0.75, implementation_risk_score=0.10,
        beneficiary_reach=5000, estimated_impact_per_lakh=40.0, missing_fields=[], extraction_confidence=0.95,
        model_name="dna-v1", prompt_version="v1",
    )

    sat_a = RealSaturationEngine().calculate("PRJ-A-SATURATED", "Maharashtra", "HEALTHCARE", need_score=0.70, existing_csr_amount_override=45_000_000_000)
    sat_b = RealSaturationEngine().calculate("PRJ-B-UNDERSERVED", "Bihar", "EDUCATION", need_score=0.95, existing_csr_amount_override=2_000_000_000)

    budget = 300_000_000  # ₹3 Crore (Tranche 1 of B takes ₹2.5 Cr, remaining ₹50 Lakhs goes to A)

    req = OptimizationRequest(
        budget_paise=budget,
        project_ids=["PRJ-A-SATURATED", "PRJ-B-UNDERSERVED"],
        weights=quant_weights,
        constraints=OptimizationConstraints(regional_equity_enabled=False),
    )

    res = opt_engine.optimize(
        projects=[prj_a, prj_b],
        impact_dna_map={"PRJ-A-SATURATED": dna_a, "PRJ-B-UNDERSERVED": dna_b},
        saturation_map={"PRJ-A-SATURATED": sat_a, "PRJ-B-UNDERSERVED": sat_b},
        request=req,
        run_id="OPT-MARGINAL-TEST",
    )

    alloc_map = {a.project_id: a.allocated_amount_paise for a in res.allocations}

    # Under Marginal Impact optimization, Project B (underserved) gets funded over Project A
    assert alloc_map["PRJ-B-UNDERSERVED"] > alloc_map["PRJ-A-SATURATED"]


def test_6_deterministic_solver_repeatability(quant_weights):
    """6. Verify deterministic repeated optimization produces identical allocation vectors."""
    opt_engine = RealOptimizationEngine()
    projects = [
        make_test_project("PRJ-R1", "Project 1", ProjectSector.HEALTHCARE, "Maharashtra", 400_000_000),
        make_test_project("PRJ-R2", "Project 2", ProjectSector.EDUCATION, "Bihar", 600_000_000),
    ]

    req = OptimizationRequest(
        budget_paise=600_000_000,
        project_ids=[p.project_id for p in projects],
        weights=quant_weights,
        constraints=OptimizationConstraints(regional_equity_enabled=True),
    )

    res1 = opt_engine.optimize(projects, {}, {}, req, "RUN-1")
    res2 = opt_engine.optimize(projects, {}, {}, req, "RUN-2")

    alloc1 = [a.allocated_amount_paise for a in res1.allocations]
    alloc2 = [a.allocated_amount_paise for a in res2.allocations]

    assert alloc1 == alloc2
    assert res1.allocated_paise == res2.allocated_paise


def test_7_optimizer_does_not_call_llm(monkeypatch, quant_weights):
    """7. Verify mathematical optimizer engine runs without calling LLMClient."""
    def fake_llm_call(*args, **kwargs):
        raise RuntimeError("LLM should never be called during quant optimization!")

    monkeypatch.setattr("app.ai.client.LLMClient.generate_structured_output", fake_llm_call)

    opt_engine = RealOptimizationEngine()
    prj = make_test_project("PRJ-NO-LLM", "No LLM", ProjectSector.ENVIRONMENT, "Assam", 300_000_000)
    dna = SchemaImpactDNA(
        dna_id="DNA-NO-LLM", project_id="PRJ-NO-LLM",
        need_score=0.90, expected_impact_score=0.85, cost_efficiency_score=0.80,
        evidence_strength_score=0.80, scalability_score=0.75, implementation_risk_score=0.10,
        beneficiary_reach=3000, estimated_impact_per_lakh=40.0, missing_fields=[], extraction_confidence=0.95,
        model_name="dna-v1", prompt_version="v1",
    )
    sat = RealSaturationEngine().calculate("PRJ-NO-LLM", "Assam", "ENVIRONMENT", need_score=0.90)

    req = OptimizationRequest(
        budget_paise=300_000_000,
        project_ids=["PRJ-NO-LLM"],
        weights=quant_weights,
        constraints=OptimizationConstraints(),
    )

    res = opt_engine.optimize([prj], {"PRJ-NO-LLM": dna}, {"PRJ-NO-LLM": sat}, req, "RUN-NO-LLM")
    assert res.allocated_paise == 300_000_000
