"""
Clinexa — User Service
get_or_create profile, user lookups.
"""
from __future__ import annotations

from typing import Optional

import structlog
from supabase import create_client

from app.core.config import settings

log = structlog.get_logger(__name__)


def _get_supabase():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


class UserService:

    @staticmethod
    async def get_or_create_profile(user_id: str, full_name: Optional[str] = None) -> dict:
        """Fetch profile or create it if the trigger missed it."""
        supabase = _get_supabase()

        resp = supabase.table("profiles")\
            .select("*")\
            .eq("id", user_id)\
            .execute()

        if resp.data:
            return resp.data[0]

        # Create profile
        data = {"id": user_id}
        if full_name:
            data["full_name"] = full_name

        insert_resp = supabase.table("profiles").insert(data).execute()
        log.info("profile.created", user_id=user_id)
        return insert_resp.data[0] if insert_resp.data else data

    @staticmethod
    async def update_profile(user_id: str, full_name: Optional[str], preferred_language: Optional[str]) -> dict:
        """Update a user's profile."""
        supabase = _get_supabase()

        updates = {}
        if full_name is not None:
            updates["full_name"] = full_name
        if preferred_language is not None:
            updates["preferred_language"] = preferred_language

        resp = supabase.table("profiles")\
            .update(updates)\
            .eq("id", user_id)\
            .execute()

        return resp.data[0] if resp.data else {}
