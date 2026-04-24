import pytest

from hermes_cli.auth import AuthError
from hermes_cli import runtime_provider as rp


def test_enterprise_runtime_allows_private_custom_endpoint(monkeypatch):
    monkeypatch.setattr(rp, "is_enterprise_enabled", lambda: True)
    monkeypatch.setattr(
        rp,
        "_get_model_config",
        lambda: {"provider": "custom", "base_url": "http://127.0.0.1:11434/v1"},
    )

    resolved = rp.resolve_runtime_provider(requested="custom")

    assert resolved["provider"] == "custom"
    assert resolved["base_url"] == "http://127.0.0.1:11434/v1"


def test_enterprise_runtime_blocks_public_endpoint(monkeypatch):
    monkeypatch.setattr(rp, "is_enterprise_enabled", lambda: True)
    monkeypatch.setattr(
        rp,
        "_get_model_config",
        lambda: {"provider": "custom", "base_url": "https://example.com/v1"},
    )

    with pytest.raises(AuthError):
        rp.resolve_runtime_provider(requested="custom")


def test_enterprise_runtime_rejects_public_provider(monkeypatch):
    monkeypatch.setattr(rp, "is_enterprise_enabled", lambda: True)

    with pytest.raises(AuthError):
        rp.resolve_runtime_provider(requested="anthropic")
