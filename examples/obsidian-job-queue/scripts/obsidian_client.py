"""High-level Obsidian API client for the daemon.

Wraps the lower-level obsidian_api.py, reading credentials from env vars.
"""

import json
import os
import sys

# Add the obsidian_api module to path
sys.path.insert(0, "/daemon/.claude/skills/obsidian-vault-access/scripts")
from obsidian_api import obsidian_cmd  # noqa: E402

ENDPOINT = os.environ.get("OBSIDIAN_API_URL", "http://127.0.0.1:9999")
TOKEN = os.environ.get("OBSIDIAN_API_TOKEN", "")


def is_available() -> bool:
    """Check if the Obsidian API is reachable."""
    try:
        obsidian_cmd(ENDPOINT, TOKEN, "vault", timeout=5)
        return True
    except Exception:
        return False


def read_content(path: str) -> str:
    """Read the full content of a vault file."""
    return obsidian_cmd(ENDPOINT, TOKEN, "read", params={"file": path})


def read_property(name: str, path: str) -> str:
    """Read a single YAML property from a vault file."""
    return obsidian_cmd(ENDPOINT, TOKEN, "property:read", params={"name": name, "file": path})


def list_files(folder: str) -> list[str]:
    """List files in a vault folder. Returns list of relative paths."""
    raw = obsidian_cmd(ENDPOINT, TOKEN, "files", params={"folder": folder})
    return [line for line in raw.strip().splitlines() if line]


def _parse_tsv(raw: str) -> dict[str, str]:
    """Parse tab-separated key\\tvalue lines into a dict."""
    result = {}
    for line in raw.strip().splitlines():
        parts = line.split("\t", 1)
        if len(parts) == 2:
            result[parts[0]] = parts[1]
    return result


def get_file_mtime(path: str) -> int:
    """Get file modification time (Unix ms) from Obsidian API."""
    raw = obsidian_cmd(ENDPOINT, TOKEN, "file", params={"file": path})
    data = _parse_tsv(raw)
    return int(data.get("modified", 0))
