"""
Clinexa Backend — Main FastAPI Application Entry Point
"""
from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, reports, chat, trends, admin
from app.core.config import settings
from app.db.database import engine, Base

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Startup / shutdown lifecycle."""
    log.info("clinexa.startup", environment=settings.ENVIRONMENT)
    yield
    log.info("clinexa.shutdown")


app = FastAPI(
    title="Clinexa API",
    description="Multi-agent AI healthcare-intelligence platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url=None,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request ID + latency logging ──────────────────────────────────────────────
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    request.state.request_id = request_id

    response = await call_next(request)

    latency_ms = int((time.perf_counter() - start) * 1000)
    log.info(
        "http.request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        latency_ms=latency_ms,
        request_id=request_id,
    )
    response.headers["X-Request-ID"] = request_id
    return response


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error(
        "unhandled_exception",
        exc=str(exc),
        path=request.url.path,
        request_id=getattr(request.state, "request_id", None),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "internal_error", "message": "An unexpected error occurred."}},
    )


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(trends.router, prefix="/api/trends", tags=["trends"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


# ── Health check (no auth required) ──────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "version": "0.1.0"}
