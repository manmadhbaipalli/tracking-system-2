from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.health_service import get_health_status

router = APIRouter(prefix="/api/v1/health", tags=["Health"])


@router.get(
    "/live",
    summary="Liveness check",
    description="Check if the application is alive.",
)
async def liveness():
    return {"status": "UP"}


@router.get(
    "/ready",
    summary="Readiness check",
    description="Check if the application is ready to handle requests.",
)
async def readiness(db: AsyncSession = Depends(get_db)):
    health = await get_health_status(db)
    status_code = 200 if health["status"] == "UP" else 503
    return JSONResponse(status_code=status_code, content=health)
