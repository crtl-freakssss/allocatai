import logging
from sqlalchemy import text
from app.db.session import SessionLocal
from app.repositories import NGORepository, ProjectRepository
from app.services import (
    ProposalService,
    ProjectService,
    ImpactDNAService,
    DueDiligenceService,
)
from app.engine import RealImpactDNAEngine, RealDueDiligenceEngine
from app.schemas.enums import ProjectSector

logger = logging.getLogger("allocateai.seed")

DEMO_PROJECTS = [
    {
        "name": "Assam Rural Clean Drinking Water Station",
        "sector": ProjectSector.HEALTHCARE.value,
        "requested_amount_paise": 25_00_00_000 * 100, # ₹25 Lakhs -> 250,000,000 paise
        "duration_months": 12,
        "state": "Assam",
        "district": "Kamrup",
        "description": "Installation of community-level solar-powered water filtration units across 15 flood-prone villages in Kamrup."
    },
    {
        "name": "Bihar Digital Literacy & STEM Labs for Girls",
        "sector": ProjectSector.EDUCATION.value,
        "requested_amount_paise": 50_00_00_000 * 100, # ₹50 Lakhs
        "duration_months": 24,
        "state": "Bihar",
        "district": "Gaya",
        "description": "Establishing smart classrooms and mobile STEM labs targeting 5,000 adolescent girls in rural Gaya."
    },
    {
        "name": "Jharkhand Tribal Women Handloom Co-operative",
        "sector": ProjectSector.GENDER_EQUALITY.value,
        "requested_amount_paise": 30_00_00_000 * 100, # ₹30 Lakhs
        "duration_months": 18,
        "state": "Jharkhand",
        "district": "Ranchi",
        "description": "Capacity building and direct market linkages for 800 indigenous women artisans."
    },
    {
        "name": "Odisha Coastal Mangrove & Ecosystem Restoration",
        "sector": ProjectSector.ENVIRONMENT.value,
        "requested_amount_paise": 40_00_00_000 * 100, # ₹40 Lakhs
        "duration_months": 24,
        "state": "Odisha",
        "district": "Kendrapara",
        "description": "Restoration of 120 hectares of degraded mangrove buffer zones along cyclone-vulnerable coastline."
    },
    {
        "name": "Rajasthan Solar Agriculture & Drip Irrigation",
        "sector": ProjectSector.RURAL_DEVELOPMENT.value,
        "requested_amount_paise": 60_00_00_000 * 100, # ₹60 Lakhs
        "duration_months": 12,
        "state": "Rajasthan",
        "district": "Barmer",
        "description": "Deploying 50 solar water pumps and micro-drip irrigation systems for smallholder desert farmers."
    },
    {
        "name": "Madhya Pradesh Youth Vocational Skill Center",
        "sector": ProjectSector.LIVELIHOOD.value,
        "requested_amount_paise": 35_00_00_000 * 100, # ₹35 Lakhs
        "duration_months": 12,
        "state": "Madhya Pradesh",
        "district": "Jhabua",
        "description": "Certified vocational training in green construction and electronics repair for unemployed tribal youth."
    }
]

def seed_demo_data_if_needed() -> None:
    """Populates candidate NGOs, Projects, ImpactDNA vectors, and DueDiligence reports into PostgreSQL."""
    with SessionLocal() as session:
        proj_repo = ProjectRepository(session)
        ngo_repo = NGORepository(session)
        prop_service = ProposalService(session)
        proj_service = ProjectService(session)
        impact_dna_service = ImpactDNAService(session)
        due_dil_service = DueDiligenceService(session)

        dna_engine = RealImpactDNAEngine()
        dd_engine = RealDueDiligenceEngine()

        # Check existing count
        existing_projects, total = proj_repo.list(page=1, page_size=1)
        if total > 0:
            logger.info(f"Database already contains {total} projects. Ensuring seed NGO due diligence report...")
            ngo = ngo_repo.get_by_external_id("NGO-SEED-001")
            if ngo:
                try:
                    due_dil_service.get_latest_report(ngo.id)
                except Exception:
                    due_dil_service.evaluate_ngo(ngo.id, engine=dd_engine, request_id="seed_dd_eval")
            return

        logger.info("Database is empty. Populating candidate demo projects and engine records...")
        
        # 1. Create or get primary NGO
        ngo = ngo_repo.get_by_external_id("NGO-SEED-001")
        if not ngo:
            ngo = ngo_repo.create(
                name="Pratham Development Foundation",
                external_id="NGO-SEED-001",
                registration_number="REG-ALLOCATEAI-SEED"
            )
            session.commit()

        # Generate seed NGO due diligence report
        due_dil_service.evaluate_ngo(ngo.id, engine=dd_engine, request_id="seed_dd_eval")

        # 2. Seed projects & generate Impact DNA vectors
        for idx, item in enumerate(DEMO_PROJECTS, start=1):
            prop = prop_service.create_proposal(
                ngo_id=ngo.id,
                title=f"Proposal for {item['name']}",
                source_type="DIRECT_SUBMISSION",
                request_id=f"req_seed_prop_{idx}"
            )
            session.commit()

            proj = proj_service.create_project(
                ngo_id=ngo.id,
                name=item["name"],
                sector=item["sector"],
                duration_months=item["duration_months"],
                requested_amount_paise=item["requested_amount_paise"],
                current_funding_paise=0,
                proposal_id=prop.id,
                geographies=[{
                    "state": item["state"],
                    "district": item["district"],
                    "block": "Central Block"
                }],
                description=item["description"],
                request_id=f"req_seed_proj_{idx}"
            )
            session.commit()

            # Generate Impact DNA vector
            impact_dna_service.generate_dna(proj.public_id, engine=dna_engine, request_id=f"req_seed_dna_{idx}")

        logger.info(f"Successfully seeded {len(DEMO_PROJECTS)} candidate projects, Impact DNA vectors, and NGO Due Diligence into PostgreSQL.")
