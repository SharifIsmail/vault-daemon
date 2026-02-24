# Daemon

Edit `loop.sh` in Obsidian. It restarts automatically on save.

## Architecture

```
loop.sh (bash, runs every 60s)
  ├── scripts/scheduler.py       → scans jobs.d/, enqueues when conditions met
  ├── scripts/queue_processor.py  → picks oldest from queue/, runs Claude, moves to done/
  └── helpers:
      ├── scripts/cron_match.py       → cron expression evaluation
      ├── scripts/frontmatter.py      → YAML frontmatter read/write
      └── scripts/obsidian_client.py  → wraps obsidian_api.py
```

## jobs.d/ spec

Each `.md` file in `jobs.d/` is a job definition. YAML frontmatter controls scheduling; the body is the task prompt sent to Claude.

### Frontmatter fields

| Field | Type | Description |
|---|---|---|
| `schedule` | string | 5-field cron expression (e.g. `"0 9 * * *"` = 9am daily) |
| `watch` | string or list | Vault paths to monitor for changes via Obsidian API |
| `match` | string | Regex filter — only trigger if watched file content matches |
| `match_property` | string | `name=value` filter on a YAML property of the watched file |
| `enabled` | bool | Set to `false` to disable (default: true) |
| `last_run` | string | ISO timestamp, set automatically after each run |
| `last_status` | string | `done` or `error`, set automatically |

### Example: cron job

```markdown
---
schedule: "0 9 * * 1"
---
Summarize this week's daily notes and append a summary to Weekly/{{date}}.md
```

### Example: file-watch job

```markdown
---
watch:
  - Inbox/tasks.md
match: "- \\[ \\]"
---
Process any unchecked tasks in the inbox.
```

## Queue lifecycle

1. **Scheduler** copies a job from `jobs.d/` to `queue/<timestamp>--<name>.md` with `status: queued`
2. **Queue processor** picks the oldest queued file, sets `status: running`, builds a prompt, runs `claude -p`
3. On completion: sets `status: done` (or `error`), records `exit_code`, `duration`, `result`, moves to `queue/done/`
4. Updates the source job's `last_run` and `last_status`

One job runs per tick (60 seconds).

## Folder structure

```
/daemon/
├── loop.sh              ← main loop (bash)
├── heartbeat.md         ← updated each tick
├── README.md
├── scripts/             ← Python automation
│   ├── scheduler.py
│   ├── queue_processor.py
│   ├── cron_match.py
│   ├── frontmatter.py
│   └── obsidian_client.py
├── jobs.d/              ← job definitions (editable in Obsidian)
├── queue/               ← pending tasks
│   └── done/            ← completed tasks
├── .claude/
│   ├── CLAUDE.md        ← project instructions (auto-loaded by Claude Code)
│   └── skills/          ← Claude skills (auto-discovered by Claude Code)
└── .mtimes.json         ← mtime state for file-watch triggers
```

## Writing loop.sh

Working directory: `/daemon` (this folder). Relative paths resolve here.

Available tools: `bash`, `curl`, `jq`, `python` (3.14), `uv`, `uvx`, `claude`

Check for reload at the top of each iteration (otherwise a long `sleep` delays the restart):

```bash
[[ -f /daemon/.reload ]] && exit 1
```

Use `uv run` / `uvx` for Python dependencies:

```bash
uvx some-tool
uv run --with requests python my_script.py
```

`exit 0` stops the loop. Any other exit (or crash) restarts it after 5 seconds.

## Logs

```bash
docker logs -f vault-daemon
```

## How it works

This folder is mounted at `/daemon` inside the `vault-daemon` container. A supervisor process runs `loop.sh` and polls its content hash every 2 seconds. On change, it waits 10 seconds (for you to finish editing), then sends SIGTERM to loop.sh only (not its children), and restarts it.
