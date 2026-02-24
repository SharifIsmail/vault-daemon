"""Queue processor: pick the oldest queued task and run it via Claude.

Picks one .md from queue/, runs Claude with the task body as prompt,
records results in frontmatter, and moves to queue/done/.
"""

import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, "/daemon/scripts")
import frontmatter

QUEUE_DIR = "/daemon/queue"
DONE_DIR = "/daemon/queue/done"


def _build_prompt(props: dict, body: str) -> str:
    """Build the prompt sent to Claude.

    CLAUDE.md and skills are auto-loaded by Claude Code from /daemon/.claude/.
    We only need to pass trigger context and the task body.
    """
    parts = []

    triggered_by = props.get("triggered_by", "")
    if triggered_by:
        parts.append(f"This task was triggered by: {triggered_by}")

    source = props.get("source", "")
    if source:
        parts.append(f"Source job: {source}")

    parts.append(body.strip())

    return "\n\n".join(parts)


def run():
    """Process the oldest queued task."""
    if not os.path.isdir(QUEUE_DIR):
        return

    os.makedirs(DONE_DIR, exist_ok=True)

    # Find oldest queued .md file (exclude done/ subdirectory)
    candidates = []
    for f in os.listdir(QUEUE_DIR):
        path = os.path.join(QUEUE_DIR, f)
        if not f.endswith(".md") or not os.path.isfile(path):
            continue
        try:
            props, _ = frontmatter.read(path)
        except Exception:
            continue
        if props.get("status") in ("queued", None):
            candidates.append((os.path.getmtime(path), f, path))

    if not candidates:
        return

    candidates.sort()
    _, fname, task_path = candidates[0]

    print(f"[queue] processing {fname}")

    # Mark as running
    props, body = frontmatter.read(task_path)
    now = datetime.now(timezone.utc)
    frontmatter.update(task_path, {
        "status": "running",
        "started_at": now.isoformat(),
    })

    # Build prompt and run Claude
    prompt = _build_prompt(props, body)
    start = time.monotonic()

    try:
        result = subprocess.run(
            ["claude", "-p", "--dangerously-skip-permissions", prompt],
            capture_output=True,
            text=True,
            timeout=300,
            cwd="/daemon",
        )
        exit_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired:
        exit_code = -1
        stdout = ""
        stderr = "Timeout after 300s"
    except Exception as e:
        exit_code = -1
        stdout = ""
        stderr = str(e)

    elapsed = round(time.monotonic() - start, 1)
    finished = datetime.now(timezone.utc)

    # Truncate result for frontmatter
    output = stdout.strip()
    if len(output) > 500:
        output = output[:500] + "..."

    status = "done" if exit_code == 0 else "error"

    frontmatter.update(task_path, {
        "status": status,
        "finished_at": finished.isoformat(),
        "duration[sec]": elapsed,
        "exit_code": exit_code,
        "result": output or stderr[:500],
    })

    # Move to done/
    done_path = os.path.join(DONE_DIR, fname)
    shutil.move(task_path, done_path)
    print(f"[queue] {fname} -> done/ ({status}, {elapsed}s)")

    # Update source job's last_run/last_status
    source = props.get("source", "")
    if source:
        source_path = os.path.join("/daemon/jobs.d", source)
        if os.path.exists(source_path):
            try:
                frontmatter.update(source_path, {
                    "last_run": finished.isoformat(),
                    "last_status": status,
                })
            except Exception as e:
                print(f"[queue] failed to update source {source}: {e}")


if __name__ == "__main__":
    run()
