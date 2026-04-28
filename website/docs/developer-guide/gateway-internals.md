---
sidebar_position: 7
title: "Gateway Internals"
description: "How the enterprise gateway boots, routes sessions, and serves the internal API surface"
---

# Gateway Internals

The enterprise build keeps the gateway focused on two internal surfaces:

- `local`
- `api_server`

Legacy messaging-platform code paths are intentionally disabled or filtered at config load time.

## Key Files

| File | Purpose |
|------|---------|
| `gateway/run.py` | `GatewayRunner` main loop, session routing, command dispatch |
| `gateway/session.py` | `SessionStore` persistence and session key helpers |
| `gateway/config.py` | Gateway config models, legacy platform compatibility, enterprise filtering |
| `gateway/platforms/api_server.py` | Internal REST/SSE API server adapter |
| `gateway/platforms/base.py` | Shared adapter primitives |
| `gateway/hooks.py` | Hook discovery, loading, and lifecycle dispatch |
| `gateway/status.py` | Profile-scoped process and lock management |

## Architecture

```text
GatewayRunner
  |- local session handling
  |- api_server adapter
  |- slash command dispatch
  |- AIAgent creation
  `- SessionStore persistence
```

## Session Flow

1. A local or API request is normalized into gateway session context.
2. `GatewayRunner._handle_message()` resolves the session key and loads history.
3. Slash commands are dispatched before agent creation when applicable.
4. `AIAgent` runs with the platform toolset resolved from enterprise config.
5. The response is persisted and returned to the caller.

## Platform Filtering

`gateway.config.Platform` still contains legacy enum values so historical configs and old serialized data can be read safely.

At runtime, the enterprise build immediately filters platform mappings down to:

- `local`
- `api_server`

That keeps old config files from crashing startup while removing unsupported surfaces from active use.

## Delivery Model

The enterprise build does not support cross-platform delivery, channel directory lookups, or outbound messaging bridges.

- Cron jobs keep their output local.
- MCP no longer exposes messaging send/list helpers.
- API traffic stays inside `api_server`.

## Hooks

Gateway hooks still run for internal lifecycle events such as:

- `gateway:startup`
- `session:start`
- `session:end`
- `agent:start`
- `agent:end`
- `command:*`

## Notes

- Prefer `hermes_cli.platforms` for the supported platform registry.
- Do not add new public messaging adapters in this branch.
- If legacy platform values appear in config, preserve load compatibility and ignore them at runtime.
