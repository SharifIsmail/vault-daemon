# Daemon

Edit `loop.sh` in Obsidian. It restarts automatically on save.

## Writing loop.sh

Working directory: `/daemon` (this folder). Relative paths resolve here.

Available tools: `bash`, `curl`, `jq`, `python` (3.14), `uv`, `uvx`

Check for reload at the top of each iteration (otherwise a long `sleep` delays the restart):

```bash
[[ -f /daemon/.reload ]] && exit 1
```

Use `uv run` / `uvx` for Python dependencies:

```bash
uvx some-tool
uv run --with requests python my_script.py
```

Use `nohup` for anything that should survive a reload:

```bash
nohup some-long-task &
```

`exit 0` stops the loop. Any other exit (or crash) restarts it after 5 seconds.

## Example (the default loop.sh)

```bash
TICK_INTERVAL=60

while true; do
    [[ -f /daemon/.reload ]] && exit 1  # exit fast on reload

    echo "[loop.sh] tick at $(date -Iseconds)"

    # your automation here

    sleep "$TICK_INTERVAL"
done
```

The reload check goes first so edits take effect without waiting for `sleep` to finish. Everything between the check and `sleep` runs once per tick.

## Logs

```bash
docker logs -f vault-daemon
```

## How it works

This folder is mounted at `/daemon` inside the `vault-daemon` container. A supervisor process runs `loop.sh` and watches it with inotify. On file change, it waits 10 seconds then sends SIGTERM to loop.sh only (not its children), and restarts it.
