---
title: "MCP"
description: "Enterprise MCP support for conversation access, events, and approvals"
---

# MCP

The enterprise build keeps MCP focused on internal conversation access.

## Exposed MCP tools

| Tool | Purpose |
|---|---|
| `conversations_list` | List known conversations |
| `conversation_get` | Fetch one conversation summary |
| `messages_read` | Read persisted messages |
| `attachments_fetch` | Fetch attachment content |
| `events_poll` | Poll for new conversation events |
| `events_wait` | Long-poll for the next event |
| `permissions_list_open` | List pending approvals |
| `permissions_respond` | Resolve a pending approval |

## Not exposed in this build

The enterprise build does not expose platform messaging helpers through MCP.

- `messages_send`
- `channels_list`

## Notes

- MCP reads from Hermes session storage directly.
- Approval workflows remain available.
- Outbound messaging and channel discovery are intentionally disabled.
