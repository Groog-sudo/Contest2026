from fastapi import APIRouter

from app.api.v1.endpoints import assessments, calls, documents, health, leads

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(calls.router, prefix="/calls", tags=["calls"])
api_router.include_router(assessments.router, prefix="/assessments", tags=["assessments"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
