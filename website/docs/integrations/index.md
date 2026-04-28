---
title: "Integrations"
sidebar_label: "Overview"
sidebar_position: 0
---

# Integrations

The enterprise build keeps integrations focused on internal deployment.

## Supported categories

- AI model endpoints reachable through your enterprise allowlist
- MCP servers approved by enterprise policy
- Browser automation backends you control
- Internal API server clients that speak the OpenAI-compatible API
- IDE/editor integrations through ACP

## Internal runtime surfaces

- `hermes` CLI
- `hermes gateway run` for the retained API server runtime
- ACP-compatible editor clients

## Not part of this build

- Public messaging platforms
- Webhook-driven public ingress
- Home Assistant tooling
- RL training and OpenRouter-dependent multi-agent tooling

See [API Server](/docs/user-guide/features/api-server), [MCP](/docs/user-guide/features/mcp), and [Built-in Tools Reference](/docs/reference/tools-reference) for the supported surface.