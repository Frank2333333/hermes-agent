# Security Policy

This branch is maintained as an enterprise intranet build.

## Deployment Assumptions

- No public internet exposure
- No public or consumer messaging platforms
- No public SaaS model providers
- Only self-hosted or intranet OpenAI-compatible model endpoints
- Only allowlisted intranet URLs for model, browser, web extraction, and remote MCP traffic

## Reporting

Report security issues through your internal enterprise process for this fork.

## Hardening Requirements

- Bind `api_server` to localhost or private interfaces only
- Keep `enterprise.enabled: true`
- Maintain explicit `enterprise.network_allowlist.hosts`
- Maintain explicit `enterprise.network_allowlist.cidrs`
- Do not re-enable removed public integrations in production

## Out Of Scope

The public upstream trust model, public platform adapters, and cloud-provider guidance do not apply to this enterprise branch.
