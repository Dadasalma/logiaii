"""Configuration commune des tests LogiAI."""

import pytest

from logiai.api import security


@pytest.fixture(autouse=True)
def configure_test_api_keys(monkeypatch):
    """Utilise de fausses clés API pendant les tests."""
    monkeypatch.setattr(security, "API_KEY", "test-user-key")
    monkeypatch.setattr(security, "ADMIN_KEY", "test-admin-key")