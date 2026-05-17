import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from sqlalchemy import text
from redis.asyncio import Redis

from app.config import settings
from app.api.v1 import api_router

from app.redis_client import get_redis_pool
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────── #
    logger.info("Medis API v1.0.0")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info("Swagger UI: http://localhost:8000/docs")

    # Test PostgreSQL + pre-warm all pool connections
    try:
        from app.database import engine
        import asyncio
        # Pre-warm all pool connections concurrently to avoid Postgres.app auth issue
        async def _ping():
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        await asyncio.gather(*[_ping() for _ in range(5)])
        logger.info("PostgreSQL connected (pool pre-warmed)")
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")

    # Test Redis
    try:
        pool = get_redis_pool()
        redis = Redis(connection_pool=pool)
        await redis.ping()
        await redis.aclose()
        logger.info("Redis connected")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")

    # Start lightweight in-process reminder scheduler (fallback when Celery not available)
    async def _reminder_loop():
        from app.tasks.reminder_tasks import (
            trigger_due_reminders,
            trigger_expire_periodic_prescriptions,
            trigger_mark_missed_intakes,
        )
        import asyncio
        tick = 0
        while True:
            try:
                await trigger_due_reminders()
                if tick % 60 == 0:  # ~every hour (60 × 60s)
                    await trigger_mark_missed_intakes()
                if tick % 1440 == 5:  # ~daily
                    await trigger_expire_periodic_prescriptions()
            except Exception as e:
                logger.error(f"Reminder scheduler error: {e}")
            tick += 1
            await asyncio.sleep(60)

    asyncio.create_task(_reminder_loop())
    logger.info("In-process reminder scheduler started")

    yield

    logger.info("Shutting down application...")


app = FastAPI(
    title="Medis API",
    description="API cho ứng dụng quản lý thuốc Medis",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    origin = request.headers.get("origin", "")
    allowed = [settings.FRONTEND_URL, "http://localhost:5173"]
    response = JSONResponse(
        status_code=500,
        content={"detail": "Lỗi hệ thống. Vui lòng thử lại sau."},
    )
    if origin in allowed:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.get("/", tags=["Health Check"])
async def root():
    return {"status": "ok", "message": "MediSmart API đang chạy"}


@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
