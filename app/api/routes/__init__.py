"""API routes package."""

from fastapi import APIRouter
from app.api.routes import agents, datasets, evaluations, evaluators, auth

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(agents.router)
api_router.include_router(datasets.router)
api_router.include_router(evaluations.router)
api_router.include_router(evaluators.router)

__all__ = ['api_router']
