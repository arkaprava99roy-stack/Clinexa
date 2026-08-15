"""
Clinexa — Chat Service (Phase 5)

Manages chat sessions and message execution via Multi-Agent Orchestrator.
Persists chat history in `chat_sessions` and `chat_messages` tables.
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.core.config import settings

log = logging.getLogger(__name__)


def _get_supabase():
    from supabase import create_client
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


class ChatService:
    @staticmethod
    async def create_session(user_id: str, title: Optional[str] = None) -> str:
        session_id = str(uuid.uuid4())
        supabase = _get_supabase()
        supabase.table("chat_sessions").insert({
            "id": session_id,
            "user_id": user_id,
            "title": title or "Health Consultation",
        }).execute()
        log.info("chat_service.created_session session_id=%s user_id=%s", session_id, user_id)
        return session_id

    @staticmethod
    async def process_message(
        session_id: str,
        user_id: str,
        content: str,
    ) -> Dict[str, Any]:
        supabase = _get_supabase()

        # Verify session ownership
        sess = supabase.table("chat_sessions").select("id").eq("id", session_id).eq("user_id", user_id).execute()
        if not sess.data:
            raise ValueError("Chat session not found or unauthorized")

        # 1. Save user message
        user_msg_id = str(uuid.uuid4())
        supabase.table("chat_messages").insert({
            "id": user_msg_id,
            "session_id": session_id,
            "user_id": user_id,
            "role": "user",
            "content": content,
        }).execute()

        # 2. Run Multi-Agent Orchestrator
        from app.agents.orchestrator import Orchestrator
        orchestrator = Orchestrator()
        result = await orchestrator.run(query=content, user_id=user_id)

        # 3. Save assistant message
        ai_msg_id = str(uuid.uuid4())
        supabase.table("chat_messages").insert({
            "id": ai_msg_id,
            "session_id": session_id,
            "user_id": user_id,
            "role": "assistant",
            "content": result["content"],
            "citations": result.get("citations", []),
            "risk_level": result.get("risk_level", "low"),
        }).execute()

        # Update session timestamp
        supabase.table("chat_sessions").update({
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", session_id).execute()

        return {
            "id": ai_msg_id,
            "role": "assistant",
            "content": result["content"],
            "citations": result.get("citations", []),
            "risk_level": result.get("risk_level", "low"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    async def get_messages(session_id: str, user_id: str) -> List[Dict[str, Any]]:
        supabase = _get_supabase()
        res = supabase.table("chat_messages")\
            .select("id, role, content, citations, risk_level, created_at")\
            .eq("session_id", session_id)\
            .eq("user_id", user_id)\
            .order("created_at", desc=False)\
            .execute()
        return res.data or []
