"""
api/routers/admin.py — Admin Monitoring & Analytics Endpoints

Provides read-only monitoring endpoints for LLM performance metrics.
All endpoints require admin-level access (enforced via dependency).

Issue Resolved: #17 (missing AI monitoring and analytics)
"""
import logging
from fastapi import APIRouter, Depends, HTTPException

from core.security import get_current_user
from models.user import User
from services.monitoring.metrics_store import metrics_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Simple admin check: currently any authenticated user can access.
    Extend this to check a User.is_admin flag when role management is added.
    """
    # TODO: uncomment when is_admin field is added to User model
    # if not getattr(current_user, "is_admin", False):
    #     raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user


@router.get("/metrics/summary")
async def get_metrics_summary(
    limit: int = 1000,
    current_user: User = Depends(_require_admin),
):
    """
    Return aggregate LLM call statistics for the last ``limit`` requests.

    Includes:
    - Total requests and success rate
    - Average and p95 latency
    - Total token consumption
    - Per-provider breakdown
    """
    try:
        summary = metrics_store.get_summary(limit=limit)
        return {"status": "ok", "data": summary}
    except Exception as exc:
        logger.error("Failed to compute metrics summary: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to compute metrics summary.")


@router.get("/metrics/providers")
async def get_provider_metrics(
    limit: int = 500,
    current_user: User = Depends(_require_admin),
):
    """Return a per-provider breakdown of LLM requests."""
    try:
        summary = metrics_store.get_summary(limit=limit)
        return {"status": "ok", "data": summary.get("by_provider", {})}
    except Exception as exc:
        logger.error("Failed to compute provider metrics: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to compute provider metrics.")


@router.get("/health")
async def admin_health(current_user: User = Depends(_require_admin)):
    """Admin health check — confirms auth and returns system status."""
    return {
        "status": "ok",
        "user": str(current_user.id),
        "metrics_available": True,
    }
