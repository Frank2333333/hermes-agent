---
sidebar_position: 3
title: "Built-in Tools Reference"
description: "Enterprise Hermes built-in tools"
---

# Built-in Tools Reference

This branch only documents the supported enterprise tool surface.

## Supported toolsets

| Toolset | Representative tools |
|---|---|
| `browser` | `browser_navigate`, `browser_click`, `browser_snapshot`, `browser_type`, `browser_scroll`, `browser_console`, `browser_vision` |
| `clarify` | `clarify` |
| `code_execution` | `execute_code` |
| `cronjob` | `cronjob` |
| `delegation` | `delegate_task` |
| `file` | `read_file`, `write_file`, `patch`, `search_files` |
| `image_gen` | `image_generate` |
| `memory` | `memory` |
| `session_search` | `session_search` |
| `skills` | `skills_list`, `skill_view`, `skill_manage` |
| `terminal` | `terminal`, `process` |
| `todo` | `todo` |
| `tts` | `text_to_speech` |
| `vision` | `vision_analyze` |
| `web` | `web_extract` |

## Compatibility-only toolsets

The following names may still appear in older configs, but they are not active in this enterprise build:

- `messaging`
- `moa`
- `rl`
- `homeassistant`
- `feishu_doc`
- `feishu_drive`

## MCP tools

MCP-provided tools still appear dynamically when enabled by enterprise policy. See [MCP](/docs/user-guide/features/mcp).