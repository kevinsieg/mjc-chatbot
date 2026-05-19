"""Read Markdown knowledge files from DATA_DIR for the home page viewer."""

from pathlib import Path

from app.db_util import get_data_dir

MAX_FILE_BYTES = 512_000


def load_knowledge_markdown_files() -> list[dict[str, str]]:
    """Return relative path and UTF-8 content for each *.md under DATA_DIR."""
    root = Path(get_data_dir()).resolve()
    if not root.is_dir():
        raise RuntimeError(f"DATA_DIR is not a directory: {root}")
    paths = sorted(root.rglob("*.md"))
    if not paths:
        raise RuntimeError(f"No .md files found under {root}")
    out: list[dict[str, str]] = []
    for path in paths:
        rel = path.resolve().relative_to(root).as_posix()
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            raise RuntimeError(f"Markdown file too large ({rel}): {size} bytes")
        out.append({"path": rel, "content": path.read_text(encoding="utf-8")})
    return out
