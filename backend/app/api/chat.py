"""
Clinexa — Chat API Router
POST /api/chat/sessions
POST /api/chat/sessions/{session_id}/messages
GET  /api/chat/sessions/{session_id}/messages
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.auth import CurrentUser, get_current_user

log = structlog.get_logger(__name__)
router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────────

class CreateSessionResponse(BaseModel):
    session_id: str


class Citation(BaseModel):
    report_id: str
    report_name: str
    page: int


class SendMessageRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    role: str
    content: str
    citations: Optional[List[Citation]] = None
    risk_level: str = "low"


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    citations: Optional[List[Citation]] = None
    risk_level: Optional[str] = None
    created_at: datetime


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/sessions", status_code=status.HTTP_201_CREATED, response_model=CreateSessionResponse)
async def create_session(current_user: CurrentUser = Depends(get_current_user)):
    """Create a new chat session."""
    from app.services.chat_service import ChatService
    session_id = await ChatService.create_session(user_id=current_user.user_id)
    return CreateSessionResponse(session_id=session_id)


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: str,
    body: SendMessageRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Send a user message and receive an AI response."""
    from app.services.chat_service import ChatService
    try:
        result = await ChatService.process_message(
            session_id=session_id,
            user_id=current_user.user_id,
            content=body.content,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "not_found", "message": str(exc)}},
        )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "not_found", "message": "Chat session not found."}},
        )
    return result


@router.get("/sessions/{session_id}/messages", response_model=List[MessageOut])
async def get_messages(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Return all messages in a chat session."""
    from app.services.chat_service import ChatService
    messages = await ChatService.get_messages(
        session_id=session_id,
        user_id=current_user.user_id,
    )
    if messages is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "not_found", "message": "Chat session not found."}},
        )
    return messages
