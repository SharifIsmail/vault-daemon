"""Scheduler: scan jobs.d/ and enqueue jobs whose conditions are met.

Conditions:
  - schedule: cron expression — enqueue if current minute matches and last_run
    is not within the current minute
  - watch: list of vault paths — enqueue if any watched file's mtime changed
    since last check; optional match/match_property filters
"""

import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/daemon/scripts")
import cron_match
import frontmatter

JOBS_DIR = "/daemon/jobs.d"
QUEUE_DIR = "/daemon/queue"
MTIMES_FILE = "/daemon/.mtimes.json"


def _load_mtimes() -> dict:
    if os.path.exists(MTIMES_FILE):
        return json.loads(open(MTIMES_FILE).read())
    return {}


def _save_mtimes(mtimes: dict) -> None:
    with open(MTIMES_FILE, "w") as f:
        json.dump(mtimes, f)


def _enqueue(job_path: str, job_name: str, triggered_by: str) -> str:
    """Copy a job file to queue/ with metadata."""
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d-%H%M%S")
    queue_name = f"{ts}--{job_name}"
    dest = os.path.join(QUEUE_DIR, queue_name)

    shutil.copy2(job_path, dest)
    frontmatter.update(dest, {
        "source": job_name,
        "triggered_by": triggered_by,
        "queued_at": now.isoformat(),
        "status": "queued",
    })
    print(f"[scheduler] enqueued {queue_name} (trigger: {triggered_by})")
    return dest


def _check_cron(job_path: str, job_name: str, props: dict, now: datetime) -> bool:
    """Check if a cron-scheduled job should fire."""
    schedule = props.get("schedule")
    if not schedule:
        return False

    if not cron_match.matches_now(schedule, now):
        return False

    # Skip if already ran this minute
    last_run = props.get("last_run")
    if last_run:
        if isinstance(last_run, str):
            try:
                lr = datetime.fromisoformat(last_run)
                if lr.replace(second=0, microsecond=0) == now.replace(second=0, microsecond=0):
                    return False
            except ValueError:
                pass

    _enqueue(job_path, job_name, f"schedule: {schedule}")
    return True


def _check_triggers(job_path: str, job_name: str, props: dict, mtimes: dict, first_run: bool) -> bool:
    """Check if any watched files have changed."""
    watch = props.get("watch")
    if not watch:
        return False

    if isinstance(watch, str):
        watch = [watch]

    # Import obsidian client lazily (may not be available)
    try:
        import obsidian_client
    except Exception as e:
        print(f"[scheduler] obsidian client unavailable: {e}")
        return False

    match_pattern = props.get("match")
    match_property = props.get("match_property")
    triggered = False

    for path in watch:
        try:
            mtime = obsidian_client.get_file_mtime(path)
        except Exception:
            continue

        key = f"{job_name}:{path}"
        old_mtime = mtimes.get(key)
        mtimes[key] = mtime

        if first_run or old_mtime is None:
            # Seed silently on first run
            continue

        if mtime == old_mtime:
            continue

        # Apply optional filters
        if match_pattern or match_property:
            try:
                content = obsidian_client.read_content(path)
                if match_pattern and not re.search(match_pattern, content):
                    continue
                if match_property:
                    name, expected = match_property.split("=", 1)
                    val = obsidian_client.read_property(name.strip(), path).strip()
                    if val != expected.strip():
                        continue
            except Exception:
                continue

        _enqueue(job_path, job_name, f"watch: {path}")
        triggered = True

    return triggered


def run():
    """Main scheduler entry point."""
    if not os.path.isdir(JOBS_DIR):
        return

    os.makedirs(QUEUE_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)

    mtimes = _load_mtimes()
    first_run = not os.path.exists(MTIMES_FILE)

    jobs = sorted(f for f in os.listdir(JOBS_DIR) if f.endswith(".md"))
    if not jobs:
        return

    for fname in jobs:
        job_path = os.path.join(JOBS_DIR, fname)
        job_name = fname
        try:
            props, _ = frontmatter.read(job_path)
        except Exception as e:
            print(f"[scheduler] error reading {fname}: {e}")
            continue

        if props.get("enabled") is False:
            continue

        _check_cron(job_path, job_name, props, now)
        _check_triggers(job_path, job_name, props, mtimes, first_run)

    _save_mtimes(mtimes)


if __name__ == "__main__":
    run()
