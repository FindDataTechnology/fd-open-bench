"""API routes package."""

from fastapi import APIRouter, Depends

from app.api.routes import agents, datasets, evaluations, evaluators, benchmarks, batches
from app.core.auth import verify_api_token

api_router = APIRouter(dependencies=[Depends(verify_api_token)])

api_router.include_router(agents.router)
api_router.include_router(datasets.router)
api_router.include_router(evaluations.router)
api_router.include_router(evaluators.router)
api_router.include_router(benchmarks.router)
api_router.include_router(batches.router)

__all__ = ['api_router']
