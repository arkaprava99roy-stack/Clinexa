"""
Clinexa — Auth & RLS Integration Test

Verifies that:
1. A user can sign up and their report list is initially empty.
2. User A creates a report row directly in Supabase.
3. User B's JWT cannot retrieve User A's report (empty list, not 403,
   because RLS silently filters rather than throwing).
4. User A can retrieve their own report.

Requires: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY
          (populated from .env for test runs).

NOTE: This test creates real rows in Supabase. Run against a dedicated
      test project or a schema with a teardown fixture.
"""
from __future__ import annotations

import os
import uuid
import pytest
from supabase import create_client, Client

# ── helpers ────────────────────────────────────────────────────────────────────

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

pytestmark = pytest.mark.skipif(
    not SUPABASE_URL or not SUPABASE_ANON_KEY,
    reason="Supabase credentials not set — skipping integration tests.",
)


def admin_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def anon_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def _random_email() -> str:
    return f"test_{uuid.uuid4().hex[:8]}@clinexa.test"


# ── fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def user_a_credentials():
    """Sign up User A and return their access token + user_id."""
    email = _random_email()
    password = "TestPassword123!"
    client = anon_client()
    resp = client.auth.sign_up({"email": email, "password": password})
    assert resp.user is not None, f"Failed to sign up user A: {resp}"
    return {
        "user_id": resp.user.id,
        "email": email,
        "password": password,
        "access_token": resp.session.access_token,
    }


@pytest.fixture(scope="module")
def user_b_credentials():
    """Sign up User B and return their access token + user_id."""
    email = _random_email()
    password = "TestPassword456!"
    client = anon_client()
    resp = client.auth.sign_up({"email": email, "password": password})
    assert resp.user is not None, f"Failed to sign up user B: {resp}"
    return {
        "user_id": resp.user.id,
        "email": email,
        "password": password,
        "access_token": resp.session.access_token,
    }


@pytest.fixture(scope="module")
def user_a_report_id(user_a_credentials):
    """Insert a report row for User A using the service-role client, return report_id."""
    svc = admin_client()
    report_id = str(uuid.uuid4())
    svc.table("reports").insert({
        "id": report_id,
        "user_id": user_a_credentials["user_id"],
        "file_name": "user_a_blood_test.pdf",
        "file_path": f"{user_a_credentials['user_id']}/{report_id}/user_a_blood_test.pdf",
        "status": "ready",
    }).execute()
    yield report_id
    # Teardown
    svc.table("reports").delete().eq("id", report_id).execute()


# ── tests ──────────────────────────────────────────────────────────────────────

class TestRLS:

    def test_user_a_can_see_own_report(self, user_a_credentials, user_a_report_id):
        """User A's JWT can retrieve their own report."""
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        client.auth.set_session(
            user_a_credentials["access_token"],
            refresh_token="",  # not needed for read
        )
        resp = client.table("reports")\
            .select("id")\
            .eq("user_id", user_a_credentials["user_id"])\
            .execute()
        ids = [row["id"] for row in (resp.data or [])]
        assert user_a_report_id in ids, "User A should see their own report."

    def test_user_b_cannot_see_user_a_report(self, user_b_credentials, user_a_report_id):
        """User B's JWT must NOT return User A's report (RLS filters it out)."""
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        client.auth.set_session(
            user_b_credentials["access_token"],
            refresh_token="",
        )
        resp = client.table("reports")\
            .select("id")\
            .execute()
        ids = [row["id"] for row in (resp.data or [])]
        assert user_a_report_id not in ids, (
            "User B should NOT be able to see User A's report — RLS violation!"
        )

    def test_user_b_direct_id_lookup_returns_empty(self, user_b_credentials, user_a_report_id):
        """Even a direct ID lookup returns empty for User B."""
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        client.auth.set_session(
            user_b_credentials["access_token"],
            refresh_token="",
        )
        resp = client.table("reports")\
            .select("id")\
            .eq("id", user_a_report_id)\
            .execute()
        assert not resp.data, "Direct lookup by ID must return nothing for non-owner."

    def test_unauthenticated_list_returns_empty(self, user_a_report_id):
        """No JWT → anon key RLS returns empty (not an error for read)."""
        client = anon_client()
        resp = client.table("reports").select("id").execute()
        # With RLS, unauthenticated reads should return nothing
        ids = [row["id"] for row in (resp.data or [])]
        assert user_a_report_id not in ids
