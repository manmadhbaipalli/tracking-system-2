from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from app.models.request_log import RequestLog
from typing import Optional, List
from datetime import datetime


class RequestLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_request_log(
        self,
        correlation_id: str,
        method: str,
        endpoint: str,
        status_code: int,
        response_time_ms: int,
        user_id: Optional[int] = None
    ) -> RequestLog:
        """Create a new request log entry."""
        request_log = RequestLog(
            correlation_id=correlation_id,
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            response_time_ms=response_time_ms,
            user_id=user_id
        )
        self.session.add(request_log)
        await self.session.commit()
        await self.session.refresh(request_log)
        return request_log

    async def get_by_correlation_id(self, correlation_id: str) -> Optional[RequestLog]:
        """Get request log by correlation ID."""
        result = await self.session.execute(
            select(RequestLog).where(RequestLog.correlation_id == correlation_id)
        )
        return result.scalar_one_or_none()

    async def get_user_request_logs(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[RequestLog]:
        """Get request logs for a specific user."""
        result = await self.session.execute(
            select(RequestLog)
            .where(RequestLog.user_id == user_id)
            .order_by(RequestLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_recent_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[RequestLog]:
        """Get recent request logs with optional time filtering."""
        query = select(RequestLog)

        if start_time:
            query = query.where(RequestLog.created_at >= start_time)
        if end_time:
            query = query.where(RequestLog.created_at <= end_time)

        query = query.order_by(RequestLog.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_error_logs(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[RequestLog]:
        """Get request logs with error status codes (4xx, 5xx)."""
        result = await self.session.execute(
            select(RequestLog)
            .where(RequestLog.status_code >= 400)
            .order_by(RequestLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()