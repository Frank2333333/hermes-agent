---
title: "Installation"
description: "Install the Hermes enterprise build"
---

# Installation

## 1. Install dependencies

```bash
uv sync --extra dev
```

## 2. Start Hermes

```bash
hermes
```

## 3. Configure your model endpoint

Use `hermes model` and point Hermes at an allowlisted OpenAI-compatible endpoint.

## 4. Optional internal API runtime

```bash
hermes gateway run
```

## Not included in this build

- Public messaging platform setup
- Webhook setup
- Consumer cloud routing flows