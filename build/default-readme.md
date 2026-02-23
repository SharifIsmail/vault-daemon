# Daemon

Edit `loop.sh` in Obsidian. It restarts automatically on save.

## Writing loop.sh

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

## Logs

```bash
docker logs -f vault-daemon
```

## How it works

This folder is mounted at `/daemon` inside the `vault-daemon` container. A supervisor process runs `loop.sh` and watches it with inotify. On file change, it waits 10 seconds then sends SIGTERM to loop.sh only (not its children), and restarts it.
