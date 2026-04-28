"""Tests for None-safe `.message.content` handling in retained tools."""

import types

import pytest

from agent.auxiliary_client import extract_content_or_reasoning


def _make_response(content, **msg_attrs):
    message = types.SimpleNamespace(content=content, tool_calls=None, **msg_attrs)
    choice = types.SimpleNamespace(message=message)
    return types.SimpleNamespace(choices=[choice])


@pytest.mark.parametrize("content", [None, "  Hello world  "])
def test_basic_content_guard_examples(content):
    response = _make_response(content)
    guarded = (response.choices[0].message.content or "").strip()
    expected = "" if content is None else "Hello world"
    assert guarded == expected


def test_extract_content_or_reasoning_prefers_reasoning_when_content_missing():
    response = _make_response(None, reasoning="Step 1: analyze the problem...")
    assert extract_content_or_reasoning(response) == "Step 1: analyze the problem..."


def test_retained_source_files_do_not_use_bare_content_strip():
    for rel_path in [
        "tools/web_tools.py",
        "tools/vision_tools.py",
        "tools/skills_guard.py",
        "tools/session_search_tool.py",
    ]:
        with open(rel_path, encoding="utf-8") as handle:
            src = handle.read()
        assert ".message.content.strip()" not in src, rel_path
