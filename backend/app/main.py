from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Delivery Complaint AI Consultant API",
        description=(
            "Contest-ready FastAPI backend for delivery complaint intake, "
            "call script preparation, STT transcript ingestion, incident classification, "
            "and responsible-party routing with structured JSON outputs."
        ),
        version="0.4.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
