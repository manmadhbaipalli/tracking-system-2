import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.utils.circuit_breaker import get_all_circuit_breakers

logger = logging.getLogger(__name__)


async def check_database(session: AsyncSession) -> dict:
    """Check database connectivity."""
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "UP"}
    except Exception as exc:
        logger.error("Database health check failed: %s", str(exc))
        return {"status": "DOWN", "error": str(exc)}


def check_circuit_breakers() -> dict:
    """Get status of all circuit breakers."""
    breakers = get_all_circuit_breakers()
    return {name: cb.get_status() for name, cb in breakers.items()}


async def get_health_status(session: AsyncSession) -> dict:
    """Get comprehensive health status."""
    db_status = await check_database(session)
    cb_status = check_circuit_breakers()

    overall = "UP" if db_status["status"] == "UP" else "DOWN"

    return {
        "status": overall,
        "checks": {
            "database": db_status,
            "circuit_breakers": cb_status,
        },
    }
