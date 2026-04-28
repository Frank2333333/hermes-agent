---
title: "Tools"
description: "Tool surface retained in the enterprise CLI and API server build"
---

# Tools

The enterprise build keeps tools centered on local and internal workflows.

## Primary categories

| Category | Tools |
|---|---|
| Core work | `terminal`, `process`, `read_file`, `write_file`, `patch`, `search_files` |
| Controlled web and browser | `web_extract`, browser tools |
| Analysis and media | `vision_analyze`, `image_generate`, `text_to_speech` |
| Agent workflow | `todo`, `memory`, `session_search`, `clarify`, `delegate_task`, `cronjob` |
| Execution | `execute_code` |

## Removed from the supported surface

These capabilities are not part of the enterprise build:

- outbound messaging via `send_message`
- mixture-of-agents (`moa`)
- RL training (`rl_*`)
- Home Assistant tools
- Feishu document and drive tools

See the toolset reference for the supported presets and compatibility-only names.
