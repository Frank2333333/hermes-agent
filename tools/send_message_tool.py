"""Enterprise build: outbound messaging is removed."""

from __future__ import annotations

import json
import re
from typing import Optional, Tuple


SEND_MESSAGE_SCHEMA = {
    "name": "send_message",
    "description": "Disabled in the enterprise build.",
    "parameters": {
        "type": "object",
        "properties": {},
    },
}


_NUMERIC_TOPIC_RE = re.compile(r"^\s*(-?\d+)(?::(\d+))?\s*$")


def tool_error(message: str) -> str:
    return json.dumps({"error": message})


def send_message_tool(args, **kw):
    return tool_error(
        "send_message is disabled in the enterprise build. "
        "Consumer and public messaging integrations have been removed."
    )


def _parse_target_ref(platform_name: str, target_ref: str) -> Tuple[Optional[str], Optional[str], bool]:
    if platform_name in {"telegram", "discord"}:
        match = _NUMERIC_TOPIC_RE.fullmatch(target_ref)
        if match:
            return match.group(1), match.group(2), True
    if target_ref.lstrip("-").isdigit():
        return target_ref, None, True
    return None, None, False


def _derive_forum_thread_name(message: str) -> str:
    first_line = (message or "").strip().splitlines()
    if not first_line:
        return "New Post"
    title = first_line[0].strip().lstrip("#").strip()
    return title[:80] if title else "New Post"


async def _send_to_platform(platform, pconfig, chat_id, message, thread_id=None, media_files=None):
    return {
        "error": (
            "Outbound platform delivery is disabled in the enterprise build. "
            "Only local CLI, api_server, and webhook entrypoints are supported."
        )
    }
