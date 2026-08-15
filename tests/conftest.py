"""
Clinexa — pytest configuration and shared fixtures.
"""
from __future__ import annotations

import os
import pytest
from dotenv import load_dotenv

# Load .env from backend directory so settings are available in tests
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"), override=False)


@pytest.fixture(scope="session", autouse=True)
def check_env():
    """Warn (not fail) if required env vars are absent."""
    missing = [k for k in ("SUPABASE_URL", "SUPABASE_ANON_KEY") if not os.environ.get(k)]
    if missing:
        import warnings
        warnings.warn(f"Integration tests require: {missing}. They will be skipped.")
