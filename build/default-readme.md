# Daemon

This folder is mounted inside the `vault-daemon` container at `/daemon`. The container runs `loop.sh` continuously and watches it for changes.

## loop.sh

This is your automation script. Write whatever you want it to do — it runs in a `while true` loop. The container provides `bash`, `curl`, `jq`, `python` (3.14), `uv`, and `uvx`.

### Editing

Edit `loop.sh` directly in Obsidian. The container detects the change and restarts the script automatically (after a 10-second grace period).

### Exit behavior

| Scenario | What happens |
|----------|-------------|
| `exit 0` | Supervisor stops — container goes idle until restarted |
| `exit 1` (or any non-zero) | Supervisor restarts loop.sh after 5 seconds |
| File changed | Supervisor sends SIGTERM to loop.sh, then restarts it |

### Reload check pattern

Add this at the top of your loop iterations so the script exits promptly on reload instead of waiting for a long `sleep` to finish:

```bash
[[ -f /daemon/.reload ]] && exit 1
```

### Background processes

`kill` only targets loop.sh itself, not its children. If you launch something with `nohup`, it survives reloads:

```bash
nohup some-long-task &
```

### Python

Use `uv run` or `uvx` for isolated Python execution without polluting the container:

```bash
uvx some-tool
uv run --with requests python my_script.py
```

## Logs

```bash
docker logs -f vault-daemon
```
