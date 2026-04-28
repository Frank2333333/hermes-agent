# Hermes API Server

This document describes the HTTP API exposed by `gateway/platforms/api_server.py`.

It is intended for:

- Web frontends
- Backend-for-frontend services
- Internal automation clients
- OpenAI-compatible chat UIs

The API server exposes two groups of endpoints:

- OpenAI-compatible endpoints under `/v1/...`
- Hermes cron management endpoints under `/api/jobs...`

## 1. Base URL and startup

Default bind:

```text
http://127.0.0.1:8642
```

Common environment variables:

- `API_SERVER_ENABLED=true`
- `API_SERVER_HOST=127.0.0.1`
- `API_SERVER_PORT=8642`
- `API_SERVER_KEY=<strong-random-secret>`
- `API_SERVER_MODEL_NAME=<advertised-model-name>`

Important behavior:

- Binding to a network-accessible host such as `0.0.0.0` requires `API_SERVER_KEY`.
- If `API_SERVER_KEY` is empty and the server is only bound locally, requests are accepted without auth.
- The server refuses to start on a network-accessible host without a usable API key.

## 2. Authentication

Most endpoints use Bearer authentication:

```http
Authorization: Bearer <API_SERVER_KEY>
```

Authentication is required for:

- `GET /v1/models`
- `POST /v1/chat/completions`
- `POST /v1/responses`
- `GET /v1/responses/{response_id}`
- `DELETE /v1/responses/{response_id}`
- `POST /v1/runs`
- `GET /v1/runs/{run_id}/events`
- All `/api/jobs...` endpoints

No auth is required for:

- `GET /health`
- `GET /health/detailed`
- `GET /v1/health`

If auth fails, the server returns:

```json
{
  "error": {
    "message": "Invalid API key",
    "type": "invalid_request_error",
    "code": "invalid_api_key"
  }
}
```

## 3. Common request rules

- Request bodies must be valid JSON.
- Default request body size limit is 1 MB.
- Supported headers include:
  - `Authorization`
  - `Content-Type`
  - `Idempotency-Key`
  - `X-Hermes-Session-Id`
- The API supports text and image inputs.
- File/document parts are not supported on these endpoints.

Multimodal content rules:

- Text-only content may be sent as a plain string.
- Image content may use:
  - `http://...`
  - `https://...`
  - `data:image/...`
- Non-image `data:` payloads are rejected.
- Uploaded file parts such as `file`, `input_file`, and document-style inputs are rejected.

## 4. Error envelope

OpenAI-style errors are returned in this shape:

```json
{
  "error": {
    "message": "Human-readable error",
    "type": "invalid_request_error",
    "param": "messages[0].content",
    "code": "invalid_content_part"
  }
}
```

Fields:

- `message`: error text
- `type`: error category
- `param`: request field when applicable
- `code`: machine-readable code when applicable

Common status codes:

- `400`: invalid request
- `401`: invalid or missing API key
- `403`: disallowed operation
- `404`: resource not found
- `429`: too many concurrent runs
- `500`: internal server error

## 5. Health endpoints

### `GET /health`

Simple health check.

Example response:

```json
{
  "status": "ok",
  "platform": "hermes-agent"
}
```

### `GET /v1/health`

Alias of `/health`.

### `GET /health/detailed`

Detailed runtime status.

Example response:

```json
{
  "status": "ok",
  "platform": "hermes-agent",
  "gateway_state": "running",
  "platforms": {
    "api_server": true
  },
  "active_agents": 0,
  "exit_reason": null,
  "updated_at": "2026-04-28T08:12:00+00:00",
  "pid": 12345
}
```

## 6. Model discovery

### `GET /v1/models`

Returns a single advertised model entry for Hermes.

Example response:

```json
{
  "object": "list",
  "data": [
    {
      "id": "hermes-agent",
      "object": "model",
      "created": 1777363200,
      "owned_by": "hermes",
      "permission": [],
      "root": "hermes-agent",
      "parent": null
    }
  ]
}
```

## 7. Chat Completions API

### `POST /v1/chat/completions`

OpenAI-compatible chat endpoint.

Supported request fields:

- `model`: optional
- `messages`: required
- `stream`: optional boolean
- `tools`: accepted for fingerprinting/idempotency compatibility
- `tool_choice`: accepted for fingerprinting/idempotency compatibility

Headers:

- `Authorization: Bearer <key>` when auth is enabled
- `Idempotency-Key: <key>` optional
- `X-Hermes-Session-Id: <session-id>` optional

Behavior:

- All `system` messages are merged into one ephemeral system prompt.
- `user` and `assistant` messages become conversation history.
- The last user message is treated as the main input.
- If `X-Hermes-Session-Id` is provided, server-side history is loaded from `state.db` instead of trusting the request history.
- Session continuation via `X-Hermes-Session-Id` is only allowed when `API_SERVER_KEY` is configured.

### Non-streaming example

Request:

```http
POST /v1/chat/completions
Authorization: Bearer <API_SERVER_KEY>
Content-Type: application/json
Idempotency-Key: 1f5f08d5-7dcb-4e4d-a872-8a2ac7f58927
```

```json
{
  "model": "hermes-agent",
  "messages": [
    {
      "role": "system",
      "content": "You are an internal support assistant."
    },
    {
      "role": "user",
      "content": "Summarize the deployment steps."
    }
  ]
}
```

Response:

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1777363200,
  "model": "hermes-agent",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 123,
    "completion_tokens": 45,
    "total_tokens": 168
  }
}
```

Response headers:

- `X-Hermes-Session-Id: <session-id>`

### Streaming behavior

When `stream=true`, the endpoint returns Server-Sent Events with:

- Standard OpenAI chat completion chunks in `data: ...`
- `data: [DONE]` on completion
- Optional custom event:
  - `event: hermes.tool.progress`

The custom tool progress event is Hermes-specific and is not part of the OpenAI spec.

Example stream fragments:

```text
data: {"id":"chatcmpl-...","object":"chat.completion.chunk","choices":[{"delta":{"role":"assistant"}}]}

data: {"id":"chatcmpl-...","object":"chat.completion.chunk","choices":[{"delta":{"content":"Hello"}}]}

event: hermes.tool.progress
data: {"tool":"read_file","emoji":"file","label":"Reading file"}

data: {"id":"chatcmpl-...","object":"chat.completion.chunk","choices":[{"delta":{},"finish_reason":"stop"}],"usage":{"prompt_tokens":123,"completion_tokens":45,"total_tokens":168}}

data: [DONE]
```

## 8. Responses API

### `POST /v1/responses`

OpenAI-style Responses API with Hermes session chaining.

Supported request fields:

- `input`: required; string or array
- `instructions`: optional
- `previous_response_id`: optional
- `conversation`: optional conversation alias
- `conversation_history`: optional explicit history array
- `store`: optional boolean, default `true`
- `stream`: optional boolean
- `truncation`: optional; `"auto"` keeps only the latest 100 history entries
- `model`: optional
- `tools`: accepted for fingerprinting/idempotency compatibility

Rules:

- `conversation` and `previous_response_id` are mutually exclusive.
- If both `conversation_history` and `previous_response_id` are present, `conversation_history` wins.
- If `store=true`, the completed response is saved for:
  - `GET /v1/responses/{response_id}`
  - `previous_response_id` chaining
  - `conversation` alias chaining

### Non-streaming example

Request:

```json
{
  "input": "List the risks of exposing this service directly to the internet.",
  "instructions": "Answer for an internal platform team.",
  "store": true
}
```

Response:

```json
{
  "id": "resp_1234567890abcdef",
  "object": "response",
  "status": "completed",
  "created_at": 1777363200,
  "model": "hermes-agent",
  "output": [
    {
      "type": "message",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "..."
        }
      ]
    }
  ],
  "usage": {
    "input_tokens": 123,
    "output_tokens": 45,
    "total_tokens": 168
  }
}
```

### Response chaining example

First request:

```json
{
  "conversation": "tenant-42-chat-7",
  "input": "Remember that this service runs behind nginx."
}
```

Follow-up request:

```json
{
  "conversation": "tenant-42-chat-7",
  "input": "Now describe the reverse-proxy implications."
}
```

The second call automatically chains to the latest stored response for that conversation alias.

### Streaming behavior

When `stream=true`, the endpoint emits SSE events with these event types:

- `response.created`
- `response.output_text.delta`
- `response.output_text.done`
- `response.output_item.added`
- `response.output_item.done`
- `response.completed`
- `response.failed`

Hermes uses these to stream:

- assistant text
- tool calls as `function_call`
- tool results as `function_call_output`

Example stream sequence:

```text
event: response.created
data: {"type":"response.created","response":{"id":"resp_...","status":"in_progress"}}

event: response.output_text.delta
data: {"type":"response.output_text.delta","delta":"Hello"}

event: response.output_item.added
data: {"type":"response.output_item.added","item":{"type":"function_call","name":"read_file"}}

event: response.output_item.added
data: {"type":"response.output_item.added","item":{"type":"function_call_output","call_id":"call_123","output":"..."}} 

event: response.completed
data: {"type":"response.completed","response":{"id":"resp_...","status":"completed"}}
```

## 9. Stored response retrieval

### `GET /v1/responses/{response_id}`

Returns the stored `response` object previously created with `store=true`.

Success response:

```json
{
  "id": "resp_1234567890abcdef",
  "object": "response",
  "status": "completed",
  "created_at": 1777363200,
  "model": "hermes-agent",
  "output": [
    {
      "type": "message",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "..."
        }
      ]
    }
  ],
  "usage": {
    "input_tokens": 123,
    "output_tokens": 45,
    "total_tokens": 168
  }
}
```

If missing:

```json
{
  "error": {
    "message": "Response not found: resp_...",
    "type": "invalid_request_error",
    "param": null,
    "code": null
  }
}
```

### `DELETE /v1/responses/{response_id}`

Deletes a stored response.

Success response:

```json
{
  "id": "resp_1234567890abcdef",
  "object": "response",
  "deleted": true
}
```

## 10. Structured runs API

### `POST /v1/runs`

Starts an async run and returns immediately.

Supported request fields:

- `input`: required
- `instructions`: optional
- `previous_response_id`: optional
- `conversation_history`: optional
- `session_id`: optional

Success response:

```json
{
  "run_id": "run_1234567890abcdef",
  "status": "started"
}
```

Status code:

- `202 Accepted`

Notes:

- The server enforces a maximum of 10 concurrent runs.
- If the limit is exceeded, the API returns `429`.
- Run event streams are retained for about 300 seconds if not consumed.

### `GET /v1/runs/{run_id}/events`

Streams structured lifecycle events over SSE.

Event payloads are emitted as plain `data: ...` SSE frames. Each payload has an `event` field inside the JSON body.

Possible event values:

- `message.delta`
- `tool.started`
- `tool.completed`
- `reasoning.available`
- `run.completed`
- `run.failed`

Example stream fragments:

```text
data: {"event":"message.delta","run_id":"run_...","timestamp":1777363200.0,"delta":"Hello"}

data: {"event":"tool.started","run_id":"run_...","timestamp":1777363201.0,"tool":"read_file","preview":"Reading file"}

data: {"event":"tool.completed","run_id":"run_...","timestamp":1777363201.4,"tool":"read_file","duration":0.4,"error":false}

data: {"event":"run.completed","run_id":"run_...","timestamp":1777363203.2,"output":"Done","usage":{"input_tokens":123,"output_tokens":45,"total_tokens":168}}
```

The server sends keepalive comments while the stream is idle:

```text
: keepalive
```

At end of stream:

```text
: stream closed
```

## 11. Cron Jobs API

These endpoints manage Hermes cron jobs without using the CLI.

Important enterprise-build behavior:

- Job execution is supported.
- Automatic external delivery is disabled in the enterprise build.
- `deliver` values may still be stored, but delivery to platform targets is intentionally ignored at execution time.
- `local` is the safe default.

### Job object

Typical job fields returned by the API:

```json
{
  "id": "9f2b4a2d1c3e",
  "name": "daily-summary",
  "prompt": "Summarize yesterday's errors.",
  "skills": [],
  "skill": null,
  "model": null,
  "provider": null,
  "base_url": null,
  "script": null,
  "schedule": {
    "kind": "cron",
    "expr": "0 9 * * *",
    "display": "0 9 * * *"
  },
  "schedule_display": "0 9 * * *",
  "repeat": {
    "times": null,
    "completed": 0
  },
  "enabled": true,
  "state": "scheduled",
  "paused_at": null,
  "paused_reason": null,
  "created_at": "2026-04-28T08:00:00+00:00",
  "next_run_at": "2026-04-29T09:00:00+00:00",
  "last_run_at": null,
  "last_status": null,
  "last_error": null,
  "last_delivery_error": null,
  "deliver": "local",
  "origin": null
}
```

### `GET /api/jobs`

Lists jobs.

Query parameters:

- `include_disabled=true|false` optional

Response:

```json
{
  "jobs": [
    {
      "id": "9f2b4a2d1c3e",
      "name": "daily-summary"
    }
  ]
}
```

### `POST /api/jobs`

Creates a cron job.

Request body:

- `name`: required
- `schedule`: required
- `prompt`: optional, default `""`
- `deliver`: optional, default `"local"`
- `skills`: optional
- `repeat`: optional positive integer

Example:

```json
{
  "name": "daily-summary",
  "schedule": "0 9 * * *",
  "prompt": "Summarize yesterday's operational issues.",
  "deliver": "local"
}
```

Response:

```json
{
  "job": {
    "id": "9f2b4a2d1c3e",
    "name": "daily-summary",
    "schedule_display": "0 9 * * *"
  }
}
```

### `GET /api/jobs/{job_id}`

Returns one job.

### `PATCH /api/jobs/{job_id}`

Updates a job.

Allowed update fields:

- `name`
- `schedule`
- `prompt`
- `deliver`
- `skills`
- `skill`
- `repeat`
- `enabled`

Example:

```json
{
  "schedule": "every 30m",
  "prompt": "Check the latest deploy logs."
}
```

Response:

```json
{
  "job": {
    "id": "9f2b4a2d1c3e",
    "schedule_display": "every 30m"
  }
}
```

### `DELETE /api/jobs/{job_id}`

Deletes a job.

Success response:

```json
{
  "ok": true
}
```

### `POST /api/jobs/{job_id}/pause`

Pauses a job.

### `POST /api/jobs/{job_id}/resume`

Resumes a job.

### `POST /api/jobs/{job_id}/run`

Marks a job to run on the next scheduler tick.

## 12. Schedule format reference

Supported schedule formats:

- `30m` - run once in 30 minutes
- `2h` - run once in 2 hours
- `1d` - run once in 1 day
- `every 30m` - recurring interval
- `every 2h` - recurring interval
- `0 9 * * *` - cron expression
- `2026-05-01T09:00:00` - absolute timestamp

Notes:

- One-shot durations default to `repeat=1`.
- Interval and cron jobs repeat indefinitely unless `repeat` is explicitly set.

## 13. Idempotency

The API supports `Idempotency-Key` on:

- `POST /v1/chat/completions`
- `POST /v1/responses`

Hermes combines the idempotency key with a request fingerprint, so reuse only the same key for the same semantic request body.

## 14. Session continuity

There are two continuity mechanisms:

- Chat Completions:
  - Header-based continuity via `X-Hermes-Session-Id`
- Responses API:
  - Server-side chaining via `previous_response_id`
  - Alias-based chaining via `conversation`

Recommended use:

- Use `X-Hermes-Session-Id` if your frontend is built around Chat Completions.
- Use `previous_response_id` or `conversation` if your frontend is built around the Responses API.

## 15. Known limitations

- The advertised `/v1/models` list contains a single Hermes model entry.
- File/document inputs are not supported on the API server endpoints.
- Cron automatic external delivery is disabled in the enterprise build.
- The custom event `hermes.tool.progress` is Hermes-specific and only appears on streaming chat completions.
- Session continuation via `X-Hermes-Session-Id` is rejected unless API key auth is enabled.
