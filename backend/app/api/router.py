from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    alerts,
    auth,
    dashboard,
    disease,
    farms,
    health,
    irrigation,
    models,
    recommendations,
    sensors,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(disease.router)
api_router.include_router(irrigation.router)
api_router.include_router(models.router)
api_router.include_router(sensors.router)
api_router.include_router(alerts.router)
api_router.include_router(dashboard.router)
api_router.include_router(farms.router)
api_router.include_router(recommendations.router)
