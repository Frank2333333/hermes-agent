---
title: "API Server"
description: "Expose Hermes through an internal OpenAI-compatible HTTP API"
---

# API Server

The enterprise build keeps `api_server` as the supported always-on runtime.

## Start the server

```bash
hermes gateway run
```

## Intended use

- Internal chat frontends
- Enterprise web applications
- Trusted automation clients
- Local development against an OpenAI-compatible interface

## Notes

- Bind to localhost or internal interfaces only.
- Keep model access behind your enterprise allowlist.
- Public webhook and public messaging integrations are not part of this build.