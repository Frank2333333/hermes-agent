from toolsets import resolve_toolset


def test_enterprise_web_toolset_exposes_only_extract():
    assert resolve_toolset("web") == ["web_extract"]


def test_enterprise_cli_toolset_hides_web_search_and_send_message():
    hermes_cli_tools = set(resolve_toolset("hermes-cli"))

    assert "web_search" not in hermes_cli_tools
    assert "send_message" not in hermes_cli_tools
    assert "web_extract" in hermes_cli_tools
