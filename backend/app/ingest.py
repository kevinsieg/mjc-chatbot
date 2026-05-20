"""CLI entry: index Markdown files into pgvector (run as `python -m app.ingest`)."""

import sys
from pathlib import Path

from app.db_util import ensure_schema_at_startup
from app.settings import get_data_dir
from app.rag_service import ingest_markdown_dir


def main() -> None:
    """Ensure schema then ingest every `*.md` under DATA_DIR."""
    ensure_schema_at_startup()
    root = Path(get_data_dir()).resolve()
    n = ingest_markdown_dir(root)
    print(f"Ingest OK: {n} chunks stored under {root}.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"INGEST FAILED: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
