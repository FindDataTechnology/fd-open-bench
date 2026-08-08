# API package
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")

# Import routers to register routes
from app.api import agents, datasets, goldens, evaluations, evaluators

__all__ = ["router", "agents", "datasets", "goldens", "evaluations", "evaluators"]
