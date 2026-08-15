"""
Clinexa — SQLAlchemy ORM Models
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey,
    Integer, Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    full_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint("status IN ('processing', 'ready', 'failed')", name="reports_status_check"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    report_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="processing")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    pages: Mapped[list[ReportPage]] = relationship("ReportPage", back_populates="report", cascade="all, delete-orphan")
    parameters: Mapped[list[HealthParameter]] = relationship("HealthParameter", back_populates="report", cascade="all, delete-orphan")
    chunks: Mapped[list[DocumentChunk]] = relationship("DocumentChunk", back_populates="report", cascade="all, delete-orphan")


class ReportPage(Base):
    __tablename__ = "report_pages"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    report_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    used_ocr: Mapped[bool] = mapped_column(Boolean, default=False)

    report: Mapped[Report] = relationship("Report", back_populates="pages")


class HealthParameter(Base):
    __tablename__ = "health_parameters"
    __table_args__ = (
        CheckConstraint("status IN ('NORMAL', 'HIGH', 'LOW', 'UNKNOWN')", name="health_parameters_status_check"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    report_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False, index=True)
    parameter: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ref_min: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    ref_max: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    report: Mapped[Report] = relationship("Report", back_populates="parameters")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    report_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # embedding stored as raw JSONB for ORM; actual vector column managed by migration
    # embedding: vector(384) is created via migration 001_initial_schema.sql

    report: Mapped[Report] = relationship("Report", back_populates="chunks")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    messages: Mapped[list[ChatMessage]] = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="chat_messages_role_check"),
        CheckConstraint("risk_level IN ('low', 'medium', 'high')", name="chat_messages_risk_check"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[ChatSession] = relationship("ChatSession", back_populates="messages")


class HealthTrend(Base):
    __tablename__ = "health_trends"
    __table_args__ = (
        UniqueConstraint("user_id", "parameter", name="health_trends_user_parameter_uq"),
        CheckConstraint("direction IN ('increasing', 'decreasing', 'stable')", name="health_trends_direction_check"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False, index=True)
    parameter: Mapped[str] = mapped_column(Text, nullable=False)
    data_points: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    direction: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RequestLog(Base):
    __tablename__ = "request_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("auth.users.id", ondelete="SET NULL"), nullable=True)
    endpoint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rag_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    llm_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    safety_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_cost_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 6), nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
