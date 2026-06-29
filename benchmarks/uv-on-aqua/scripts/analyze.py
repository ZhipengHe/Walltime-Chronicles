"""Aggregate hyperfine JSON outputs from one run into a CSV + markdown summary.

Stub. Schema is deferred until the first real bench run lands in
`results-archive/`; once a few archives exist, adapt the column set and the
summary table to match what was actually captured.

Expected eventual columns per cell:
    cell, cold_median_s, cold_mean_s, cold_stddev_s, cold_min_s, cold_max_s,
    warm_mean_s, warm_median_s, warm_stddev_s, warm_min_s, warm_max_s,
    regular_files, hardlink_ratio, warn_count, bytes_no_deref, system_time_s

Usage (planned):
    uv run python scripts/analyze.py results-archive/2026-06-25-cpu1n040/
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
    print(f"analyze.py: stub. Archive {archive_dir} exists.", file=sys.stderr)
    print("Schema will be implemented once the first real bench archive lands.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
