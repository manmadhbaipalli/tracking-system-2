from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.circuit_breaker import get_all_states
from app.schemas.health import LivenessResponse, ReadinessResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "/live",
    response_model=LivenessResponse,
    summary="Liveness probe",
    description="Always returns 200 OK if the process is running.",
)
async def liveness() -> LivenessResponse:
    """Liveness probe — always returns 200 OK when the process is alive."""
    return LivenessResponse(status="ok")


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    responses={
        503: {"model": ReadinessResponse, "description": "Service not ready"},
    },
)
async def readiness(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    Readiness probe — verifies database connectivity and reports circuit breaker states.

    Returns 200 when the database is reachable, 503 when it is not.
    """
    db_status = "connected"
    overall_status = "ok"

    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"
        overall_status = "degraded"

    cb_states = get_all_states()
    response_body = ReadinessResponse(
        status=overall_status,
        database=db_status,
        circuit_breakers=cb_states,
    )

    http_status = status.HTTP_200_OK if overall_status == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=response_body.model_dump(), status_code=http_status)


@router.get(
    "/circuit-breakers",
    summary="Circuit breaker states",
    description="Returns the current state of all registered circuit breakers.",
)
async def circuit_breakers() -> dict[str, str]:
    """Return the state (CLOSED/OPEN/HALF_OPEN) of all named circuit breakers."""
    return get_all_states()
