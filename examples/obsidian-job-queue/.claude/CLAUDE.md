You are running inside the vault-daemon container. Your working directory is /daemon.

## Obsidian API

Endpoint and token are already configured as environment variables:

- `OBSIDIAN_API_URL` — the API base URL
- `OBSIDIAN_API_TOKEN` — the bearer token (permanent)

Use these directly. Do not ask for credentials.

## Python helper

The Obsidian API Python helper is at:
  /daemon/.claude/skills/obsidian-vault-access/scripts/obsidian_api.py

You can also use it via `uv run --with pyyaml` for scripts that need PyYAML.
