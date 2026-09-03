from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.proposals import router as proposals_router
from app.api.v1.projects import router as projects_router
from app.api.v1.optimization import router as optimization_router
from app.api.v1.reallocation import router as reallocation_router
from app.api.v1.due_diligence import router as due_diligence_router
from app.api.v1.audit import router as audit_router

api_router = APIRouter()

# Register core v1 routes
api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(proposals_router, prefix="/proposals", tags=["Proposals"])
api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
api_router.include_router(optimization_router, prefix="/optimization", tags=["Optimization"])
api_router.include_router(reallocation_router, prefix="/reallocation", tags=["Reallocation"])
api_router.include_router(due_diligence_router, prefix="/due-diligence", tags=["Due Diligence"])
api_router.include_router(audit_router, prefix="/audit", tags=["Audit"])
