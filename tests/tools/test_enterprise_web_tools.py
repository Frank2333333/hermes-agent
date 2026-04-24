import json
import importlib
import sys
import types


def test_web_search_disabled_in_enterprise(monkeypatch):
    firecrawl_stub = types.ModuleType("firecrawl")
    firecrawl_stub.Firecrawl = object
    monkeypatch.setitem(sys.modules, "firecrawl", firecrawl_stub)
    web_tools = importlib.import_module("tools.web_tools")
    monkeypatch.setattr(web_tools, "is_enterprise_enabled", lambda: True)

    result = json.loads(web_tools.web_search_tool("test"))

    assert result["success"] is False
    assert "disabled in the enterprise build" in result["error"]
