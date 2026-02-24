#!/usr/bin/env bash
# vault-daemon loop.sh — scheduler + queue processor
# The supervisor restarts this script automatically when the file changes.

TICK_INTERVAL=60

while true; do
    [[ -f /daemon/.reload ]] && exit 1

    echo "[loop.sh] tick at $(date -Iseconds)"

    # Write heartbeat
    date '+%A, %B %-d %Y at %-I:%M:%S %p %Z' > /daemon/heartbeat.md

    # Ensure directories exist
    mkdir -p /daemon/jobs.d /daemon/queue/done /daemon/scripts

    # Run scheduler: scan jobs.d/, enqueue matching jobs
    uv run --with pyyaml python3 /daemon/scripts/scheduler.py 2>&1 || true

    # Run queue processor: pick oldest queued task, run via Claude
    uv run --with pyyaml python3 /daemon/scripts/queue_processor.py 2>&1 || true

    sleep "$TICK_INTERVAL"
done
