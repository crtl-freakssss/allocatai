"""Deterministic seed data generator for AllocateAI hackathon demo.

Populates PostgreSQL database with realistic CSR portfolio entries across 6 states:
- 1 Organization & 1 Admin User
- 5 Statutory NGOs
- 18 Candidate Projects across 6 Indian states & sectors
- Pre-calculated Impact DNA & Regional Saturation records
- 2 Sample Optimization solver runs (Scenario 1: Unconstrained, Scenario 2: Regional Equity Enabled)
- 1 Capital Reallocation snapshot
- Append-only audit trail
"""

import sys
import os
import uuid

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import SessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.models.ngo import NGO
from app.models.proposal import Proposal
from app.models.document import Document
from app.models.project import Project
from app.models.project_geography import ProjectGeography
from app.models.impact_dna import ImpactDNA
from app.models.saturation_result import SaturationResult
from app.models.optimization_run import OptimizationRun
from app.models.allocation import Allocation
from app.models.audit_event import AuditEvent
from app.schemas.enums import (
    ProposalStatus,
    OptimizationStatus,
    AllocationStatus,
    ReasonCode,
    AuditEventType,
)


def seed_database() -> None:
    session = SessionLocal()
    try:
        print("Cleaning existing database tables...")
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

        print("Seeding Organization & Admin User...")
        org = Organization(
            name="Consortium for Corporate Social Responsibility",
        )
        session.add(org)
        session.flush()

        user = User(
            organization_id=org.id,
            email="csr.director@consortium.org",
            name="Rajesh Sharma",
        )
        session.add(user)
        session.flush()

        print("Seeding 5 Statutory NGOs...")
        ngo_data = [
            ("NGO-0001", "Global Hope Foundation", "REG-GHF-2026"),
            ("NGO-0002", "Asha Jyoti Rural Trust", "REG-AJT-2026"),
            ("NGO-0003", "Rural Upliftment Sansthan", "REG-RUS-2026"),
            ("NGO-0004", "Clean Energy India Society", "REG-CEI-2026"),
            ("NGO-0005", "Himalayan Aid Society", "REG-HAS-2026"),
        ]
        ngos = []
        for ext_id, name, reg_no in ngo_data:
            n = NGO(
                name=name,
                external_id=ext_id,
                registration_number=reg_no,
            )
            session.add(n)
            ngos.append(n)
        session.flush()

        print("Seeding 18 Candidate Projects across 6 Indian States...")
        # 18 projects across 6 states: Maharashtra, Bihar, Assam, Gujarat, Jharkhand, Uttar Pradesh
        projects_specs = [
            # High Score, Saturated Region (Maharashtra)
            ("PRJ-0001", "Mumbai Advanced Cancer Diagnostic Hub", "HEALTHCARE", "Maharashtra", "Mumbai", 1000_000_000, 0.88, 0.75),
            ("PRJ-0002", "Pune Digital Vocational Skill Lab", "LIVELIHOOD", "Maharashtra", "Pune", 500_000_000, 0.82, 0.72),
            ("PRJ-0003", "Thane Urban Tree Canopy & Waste Recycling", "ENVIRONMENT", "Maharashtra", "Thane", 300_000_000, 0.75, 0.70),

            # Saturated Region (Gujarat)
            ("PRJ-0004", "Ahmedabad Solar Micro-Grid Grid", "ENVIRONMENT", "Gujarat", "Ahmedabad", 800_000_000, 0.84, 0.68),
            ("PRJ-0005", "Surat Textile Workers Health Clinic", "HEALTHCARE", "Gujarat", "Surat", 400_000_000, 0.80, 0.65),

            # High Need, Underserved Region (Bihar)
            ("PRJ-0006", "Bihar Primary School Infrastructure Renewal", "EDUCATION", "Bihar", "Gaya", 600_000_000, 0.94, 0.22),
            ("PRJ-0007", "Patna Rural Maternal Care Vans", "HEALTHCARE", "Bihar", "Patna", 500_000_000, 0.91, 0.25),
            ("PRJ-0008", "Muzaffarpur Agricultural Farmer Training", "RURAL_DEVELOPMENT", "Bihar", "Muzaffarpur", 350_000_000, 0.86, 0.28),

            # High Need, Underserved Region (Assam)
            ("PRJ-0009", "Assam Flood Resilience & Clean Water Stations", "DISASTER_RELIEF", "Assam", "Dhubri", 700_000_000, 0.95, 0.18),
            ("PRJ-0010", "Guwahati Tribal Girls Digital Education", "EDUCATION", "Assam", "Kamrup", 400_000_000, 0.89, 0.20),
            ("PRJ-0011", "Silchar Artisan Weaving Livelihoods", "LIVELIHOOD", "Assam", "Cachar", 250_000_000, 0.83, 0.22),

            # High Need, Underserved Region (Jharkhand)
            ("PRJ-0012", "Ranchi Tribal Community Health Centers", "HEALTHCARE", "Jharkhand", "Ranchi", 650_000_000, 0.92, 0.19),
            ("PRJ-0013", "Dhanbad Clean Drinking Water Purifiers", "ENVIRONMENT", "Jharkhand", "Dhanbad", 450_000_000, 0.87, 0.24),

            # High Need, Moderate Saturation (Uttar Pradesh)
            ("PRJ-0014", "Varanasi Heritage Handloom Skill Center", "LIVELIHOOD", "Uttar Pradesh", "Varanasi", 400_000_000, 0.81, 0.38),
            ("PRJ-0015", "Gorakhpur Malnutrition Eradication Drive", "POVERTY_HUNGER", "Uttar Pradesh", "Gorakhpur", 550_000_000, 0.93, 0.35),
            ("PRJ-0016", "Lucknow Smart Classroom Infrastructure", "EDUCATION", "Uttar Pradesh", "Lucknow", 500_000_000, 0.85, 0.42),
            ("PRJ-0017", "Kanpur Industrial Effluent Treatment Pilot", "ENVIRONMENT", "Uttar Pradesh", "Kanpur", 350_000_000, 0.78, 0.45),
            ("PRJ-0018", "Ayodhya Rural Sanitation & Toilets", "RURAL_DEVELOPMENT", "Uttar Pradesh", "Ayodhya", 300_000_000, 0.82, 0.40),
        ]

        seeded_projects = []
        for idx, (pub_id, name, sector, state, district, req_paise, need_score, sat_idx) in enumerate(projects_specs):
            ngo = ngos[idx % len(ngos)]

            # Proposal & Document
            prop_id = f"PRO-{idx+1:04d}"
            p_model = Proposal(
                public_id=prop_id,
                ngo_id=ngo.id,
                title=f"Proposal for {name}",
                status=ProposalStatus.READY.value,
                source_type="PDF_UPLOAD",
            )
            session.add(p_model)
            session.flush()

            doc_id = f"DOC-{idx+1:04d}"
            d_model = Document(
                public_id=doc_id,
                proposal_id=p_model.id,
                filename=f"{pub_id.lower()}_proposal.pdf",
                mime_type="application/pdf",
                storage_key=f"uploads/{prop_id}/{pub_id.lower()}.pdf",
                file_size_bytes=1024 * 500,
                sha256=uuid.uuid5(uuid.NAMESPACE_DNS, pub_id).hex + uuid.uuid5(uuid.NAMESPACE_DNS, name).hex,
            )
            session.add(d_model)
            session.flush()

            # Project
            prj = Project(
                public_id=pub_id,
                proposal_id=p_model.id,
                ngo_id=ngo.id,
                name=name,
                sector=sector,
                requested_amount=req_paise,
                current_funding=0,
                duration_months=12,
                description=f"Seeded CSR intervention: {name} in {district}, {state}.",
                schema_version="project-v1",
            )
            session.add(prj)
            session.flush()

            geo = ProjectGeography(
                project_id=prj.id,
                state=state,
                district=district,
                block="Central",
            )
            session.add(geo)
            session.flush()

            # Impact DNA
            dna = ImpactDNA(
                public_id=f"DNA-{idx+1:04d}",
                project_id=prj.id,
                need_score=need_score,
                expected_impact_score=min(0.98, need_score * 0.95 + 0.05),
                cost_efficiency_score=0.82,
                evidence_strength_score=0.85,
                scalability_score=0.80,
                implementation_risk_score=0.15,
                beneficiary_reach=max(1000, req_paise // 50_000),
                estimated_impact_per_lakh=round(need_score * 45.0, 2),
                extraction_confidence=0.95,
                missing_fields={"missing": []},
                model_name="impact-dna-v1",
                prompt_version="dna-v1.0",
                schema_version="impact-dna-v1",
            )
            session.add(dna)

            # Saturation
            sat = SaturationResult(
                project_id=prj.id,
                state=state,
                sector=sector,
                saturation_index=sat_idx,
                need_score=need_score,
                existing_csr_amount=int(sat_idx * 50_000_000_000),
                beneficiary_coverage=sat_idx * 0.9,
                confidence=0.90,
                calculation_version="sat-v1",
            )
            session.add(sat)
            seeded_projects.append(prj)

        session.flush()

        print("Seeding Sample Optimization Run (Scenario 1: Marginal Impact Objective)...")
        opt_run = OptimizationRun(
            public_id="OPT-0001",
            status=OptimizationStatus.COMPLETED.value,
            budget_paise=3_000_000_000,  # ₹30 Crore
            weights={"need": 0.3, "marginal_impact": 0.3, "cost_efficiency": 0.2, "evidence": 0.1, "scalability": 0.05, "equity": 0.03, "risk_penalty": 0.02},
            constraints={"regional_equity_enabled": True},
            calculation_versions={"solver": "scipy-milp-v1", "scoring": "scoring-v1", "saturation": "sat-v1", "marginal": "marginal-v1"},
            input_snapshot={"budget_paise": 3_000_000_000, "project_ids": [p.public_id for p in seeded_projects]},
            result_snapshot={"allocated_paise": 3_000_000_000, "unallocated_paise": 0, "total_predicted_impact": 1850.50},
        )
        session.add(opt_run)
        session.flush()

        # Seed sample allocations for top 6 projects
        for rank, prj in enumerate(seeded_projects[:6], start=1):
            alloc = Allocation(
                optimization_run_id=opt_run.id,
                project_id=prj.id,
                allocated_amount=prj.requested_amount,
                marginal_score=0.85,
                base_score=0.88,
                saturation_index=0.25,
                reason_codes={"codes": [ReasonCode.HIGH_NEED.value, ReasonCode.LOW_SATURATION.value]},
                rank=rank,
                status=AllocationStatus.PROPOSED.value,
            )
            session.add(alloc)

        print("Seeding Audit Trail Event...")
        audit = AuditEvent(
            public_id="AUD-0001",
            event_type=AuditEventType.OPTIMIZATION_COMPLETED.value,
            actor_id=user.id,
            entity_type="optimization_runs",
            entity_id=opt_run.id,
            request_id="req_seed_demo_001",
            run_id="OPT-0001",
            payload={"solver_status": "COMPLETED", "allocated_paise": 3_000_000_000},
        )
        session.add(audit)

        session.commit()
        print("Database successfully populated with deterministic hackathon demo dataset!")
        print(f"Total Projects: {len(seeded_projects)} across 6 states.")

    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
