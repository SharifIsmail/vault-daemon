#!/usr/bin/env bash
set -euo pipefail

LOOP_SCRIPT="/daemon/loop.sh"
DEFAULT_LOOP="/usr/local/bin/default-loop.sh"
RELOAD_FLAG="/daemon/.reload"
PID_FILE="/daemon/.loop.pid"
RELOAD_TIMEOUT="${RELOAD_TIMEOUT:-10}"
CRASH_DELAY="${CRASH_DELAY:-5}"

WATCHER_PID=""

cleanup() {
    echo "[supervisor] shutting down"
    # Kill watcher if running
    if [[ -n "$WATCHER_PID" ]] && kill -0 "$WATCHER_PID" 2>/dev/null; then
        kill "$WATCHER_PID" 2>/dev/null || true
        wait "$WATCHER_PID" 2>/dev/null || true
    fi
    # Kill loop.sh if running
    if [[ -f "$PID_FILE" ]]; then
        local pid
        pid=$(<"$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null || true
        fi
    fi
    rm -f "$RELOAD_FLAG" "$PID_FILE"
    exit 0
}

trap cleanup SIGTERM SIGINT

# Copy default files if missing
if [[ ! -f "$LOOP_SCRIPT" ]]; then
    echo "[supervisor] no loop.sh found, copying default template"
    cp "$DEFAULT_LOOP" "$LOOP_SCRIPT"
fi
if [[ ! -f /daemon/README.md ]]; then
    cp /usr/local/bin/default-readme.md /daemon/README.md
fi

# Clean stale dotfiles
rm -f "$RELOAD_FLAG" "$PID_FILE"

# Start file watcher in background
start_watcher() {
    while true; do
        # Watch for modify and move_self (covers in-place writes and atomic save-then-rename)
        inotifywait -qq -e modify -e move_self "$LOOP_SCRIPT" 2>/dev/null || true
        echo "[supervisor] loop.sh changed, scheduling reload in ${RELOAD_TIMEOUT}s"
        sleep "$RELOAD_TIMEOUT"
        # Signal reload by writing flag and killing loop.sh
        touch "$RELOAD_FLAG"
        if [[ -f "$PID_FILE" ]]; then
            local pid
            pid=$(<"$PID_FILE")
            if kill -0 "$pid" 2>/dev/null; then
                echo "[supervisor] sending SIGTERM to loop.sh (pid $pid)"
                kill -TERM "$pid" 2>/dev/null || true
            fi
        fi
    done
}

start_watcher &
WATCHER_PID=$!
echo "[supervisor] started file watcher (pid $WATCHER_PID)"

# Main loop: run loop.sh, handle exit conditions
while true; do
    echo "[supervisor] starting loop.sh"
    bash "$LOOP_SCRIPT" &
    LOOP_PID=$!
    echo "$LOOP_PID" > "$PID_FILE"

    # Wait for loop.sh to exit
    set +e
    wait "$LOOP_PID"
    EXIT_CODE=$?
    set -e
    rm -f "$PID_FILE"

    if [[ -f "$RELOAD_FLAG" ]]; then
        echo "[supervisor] reload triggered, restarting loop.sh"
        rm -f "$RELOAD_FLAG"
        continue
    elif [[ "$EXIT_CODE" -eq 0 ]]; then
        echo "[supervisor] loop.sh exited cleanly (exit 0), stopping"
        cleanup
    else
        echo "[supervisor] loop.sh crashed (exit $EXIT_CODE), restarting in ${CRASH_DELAY}s"
        sleep "$CRASH_DELAY"
    fi
done
