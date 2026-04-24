from enterprise_policy import get_enterprise_url_block, invalidate_enterprise_policy_cache


def test_enterprise_policy_allows_private_targets(tmp_path, monkeypatch):
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    (hermes_home / "config.yaml").write_text(
        "enterprise:\n"
        "  enabled: true\n"
        "  network_allowlist:\n"
        "    hosts: []\n"
        "    cidrs: []\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    invalidate_enterprise_policy_cache()

    assert get_enterprise_url_block("http://10.1.2.3:8000/v1") is None


def test_enterprise_policy_blocks_public_targets(tmp_path, monkeypatch):
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    (hermes_home / "config.yaml").write_text(
        "enterprise:\n"
        "  enabled: true\n"
        "  network_allowlist:\n"
        "    hosts: []\n"
        "    cidrs: []\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    invalidate_enterprise_policy_cache()

    blocked = get_enterprise_url_block("https://example.com")

    assert blocked is not None
    assert "enterprise.network_allowlist" in blocked["source"]


def test_enterprise_policy_allows_allowlisted_host_without_dns(tmp_path, monkeypatch):
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    (hermes_home / "config.yaml").write_text(
        "enterprise:\n"
        "  enabled: true\n"
        "  network_allowlist:\n"
        "    hosts:\n"
        "      - docs.intra.example.com\n"
        "    cidrs: []\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    invalidate_enterprise_policy_cache()

    assert get_enterprise_url_block("https://docs.intra.example.com/path") is None
