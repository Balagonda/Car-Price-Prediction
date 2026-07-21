import time
import psutil
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None
        )
        
        try:
            response = await call_next(request)
            process_time = time.perf_counter() - start_time
            memory_usage = psutil.Process().memory_info().rss / (1024 * 1024) # MB
            
            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_s=round(process_time, 4),
                memory_mb=round(memory_usage, 2)
            )
            return response
            
        except Exception as exc:
            process_time = time.perf_counter() - start_time
            memory_usage = psutil.Process().memory_info().rss / (1024 * 1024) # MB
            
            logger.exception(
                "request_failed",
                exc_info=exc,
                duration_s=round(process_time, 4),
                memory_mb=round(memory_usage, 2)
            )
            raise
