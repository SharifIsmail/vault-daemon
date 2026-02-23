#!/usr/bin/env bash
# vault-daemon loop.sh — edit this file in Obsidian (Daemon/loop.sh)
# The supervisor restarts this script automatically when the file changes.
#
# Pattern: check for .reload at the top of each iteration so the loop
# exits promptly when the supervisor signals a reload.

TICK_INTERVAL=60

while true; do
    # Exit early if a reload is pending (supervisor will restart us)
    [[ -f /daemon/.reload ]] && exit 1

    echo "[loop.sh] tick at $(date -Iseconds)"

    # --- Add your automation below ---

    # Example: source scripts from an agents.d/ folder
    # for script in /daemon/agents.d/*.sh; do
    #     [[ -f "$script" ]] && bash "$script"
    # done

    sleep "$TICK_INTERVAL"
done
