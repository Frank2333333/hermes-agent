---
title: "Toolsets Reference"
description: "Enterprise toolsets retained in the CLI and API server build"
---

# Toolsets Reference

The enterprise build keeps the toolset surface intentionally small.

## Supported presets

| Toolset | Purpose |
|---|---|
| `hermes-cli` | Default CLI preset |
| `hermes-api-server` | Default internal API server preset |
| `web` | Controlled web extraction |
| `browser` | Browser automation |
| `terminal` | Terminal and process tools |
| `file` | Read, write, patch, and search |
| `code_execution` | Sandboxed code execution |
| `vision` | Image analysis |
| `image_gen` | Image generation |
| `tts` | Text-to-speech |
| `skills` | Skill discovery and management |
| `todo` | Task planning |
| `memory` | Persistent memory |
| `session_search` | Session search |
| `clarify` | Clarifying questions |
| `delegation` | Subagent delegation |
| `cronjob` | Scheduled task management |

## Compatibility-only names

The following names may still appear in older configs and are ignored or resolve to no active tools in the enterprise build:

- `messaging`
- `moa`
- `rl`
- `homeassistant`
- `feishu_doc`
- `feishu_drive`

## Notes

- Legacy platform presets such as `hermes-telegram` and `hermes-homeassistant` are not part of the supported enterprise surface.
- Dynamic MCP toolsets still appear as `mcp-<server>` when enabled through enterprise policy.
