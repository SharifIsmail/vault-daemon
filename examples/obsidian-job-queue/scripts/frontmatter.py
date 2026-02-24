"""Read and write YAML frontmatter in Markdown files.

Requires PyYAML: `uv run --with pyyaml python3 -m frontmatter ...`
"""

import yaml


def read(path: str) -> tuple[dict, str]:
    """Parse a Markdown file into (frontmatter_dict, body_string).

    Returns ({}, body) if no frontmatter block is present.
    """
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---"):
        return {}, text

    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    fm_raw = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    props = yaml.safe_load(fm_raw) or {}
    return props, body


def write(path: str, props: dict, body: str) -> None:
    """Write frontmatter + body to a Markdown file."""
    with open(path, "w", encoding="utf-8") as f:
        if props:
            f.write("---\n")
            yaml.dump(props, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            f.write("---\n")
        if body:
            f.write(body)


def update(path: str, updates: dict) -> None:
    """Read-merge-write: update frontmatter fields without touching body."""
    props, body = read(path)
    props.update(updates)
    write(path, props, body)
