# Hermes Agent Enterprise Build

This branch is a hardened enterprise/intranet edition of Hermes Agent.

## Scope

Only these entrypoints are supported:

- `hermes` CLI
- `api_server`

Only self-hosted or intranet OpenAI-compatible model endpoints are supported.

## Removed In This Build

- Public and consumer messaging platforms
- Public model providers and OAuth login flows
- `send_message`
- `web_extract`
- Cloud browser and cloud extraction backends
- Non-allowlisted remote MCP endpoints

## Deployment Rules

- Set `model.provider: custom`
- Set `model.base_url` to `localhost`, a private RFC1918 address, or an explicitly allowlisted host
- Configure `enterprise.network_allowlist.hosts` and `enterprise.network_allowlist.cidrs` as needed
- Keep `api_server` bound to localhost or internal interfaces only

## Quick Start

```bash
hermes
hermes model
hermes gateway setup
```

The example configuration files in this branch are already trimmed for intranet deployment:

- `.env.example`
- `cli-config.yaml.example`

## Notes

This branch intentionally diverges from the upstream public distribution. Documentation, code paths, and tests are being reduced toward a minimal internal-only deployment surface.
