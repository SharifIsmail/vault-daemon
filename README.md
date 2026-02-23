# vault-daemon

Minimal Docker container that supervises a single `loop.sh` script. You edit the script, the container reloads it automatically.

Built for running automation out of an Obsidian vault, but works with any mounted directory.

## How it works

A `supervisor.sh` entrypoint watches `loop.sh` via inotify:

- **File changed** — waits `RELOAD_TIMEOUT` seconds, then restarts `loop.sh`
- **Crash** (non-zero exit) — restarts after `CRASH_DELAY` seconds
- **Clean exit** (exit 0) — supervisor stops
- **SIGTERM to loop.sh only** — background children (`nohup`) survive reloads

If no `loop.sh` exists on first run, a default template is copied in.

## Setup

```bash
git clone https://github.com/SharifIsmail/vault-daemon.git
cd vault-daemon
cp .env.example .env   # edit DAEMON_PATH
docker compose up -d --build
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DAEMON_PATH` | — | Host directory mounted to `/daemon` |
| `RELOAD_TIMEOUT` | `10` | Seconds to wait after file change before restart |
| `CRASH_DELAY` | `5` | Seconds to wait before restarting after a crash |

## What's in the image

- Ubuntu 24.04
- Python 3.14 (via [uv](https://github.com/astral-sh/uv))
- `uv` / `uvx` for isolated Python environments
- `curl`, `jq`, `bash`, `inotify-tools`
- `network_mode: host` — full access to localhost services
