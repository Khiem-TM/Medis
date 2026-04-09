from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy import text
from redis.asyncio import Redis

from app.config import settings
from app.api.v1 import api_router
from app.database import AsyncSessionLocal
from app.redis_client import get_redis_pool
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────── #
    logger.info("Medis API v1.0.0")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info("Swagger UI: http://localhost:8000/docs")

    # Test PostgreSQL
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        logger.info("PostgreSQL connected")
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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Lỗi hệ thống. Vui lòng thử lại sau."},
    )


@app.get("/", tags=["Health Check"])
async def root():
    return {"status": "ok", "message": "MediSmart API đang chạy"}


@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

