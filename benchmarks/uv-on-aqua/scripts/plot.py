"""Render bar charts of cold + warm install times per cell.

Stub. Defer to analyze.py output once that schema settles.

Usage (planned):
    uv run python scripts/plot.py results-archive/2026-06-25-cpu1n040/
"""

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <archive-dir>", file=sys.stderr)
        return 2
    archive_dir = Path(sys.argv[1])
    if not archive_dir.is_dir():
        print(f"not a directory: {archive_dir}", file=sys.stderr)
        return 2
    print(f"plot.py: stub. Archive {archive_dir} exists.", file=sys.stderr)
    print("Implement once analyze.py settles its schema.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
