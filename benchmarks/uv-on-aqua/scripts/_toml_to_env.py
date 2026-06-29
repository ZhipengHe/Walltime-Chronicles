"""Read a TOML config section, emit bash `export KEY=VALUE` lines.

Usage:
    python3 scripts/_toml_to_env.py config.toml base
    python3 scripts/_toml_to_env.py config.toml workload.cpu-ml

Requires Python 3.11+ for the stdlib `tomllib`.
"""

import sys
import tomllib


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <config.toml> <section>", file=sys.stderr)
        return 2
    path, section = sys.argv[1], sys.argv[2]
    with open(path, "rb") as f:
        data = tomllib.load(f)
    cur = data
    for part in section.split("."):
        cur = cur[part]
    for key, value in cur.items():
        if isinstance(value, bool):
            v = "true" if value else "false"
        elif isinstance(value, list):
            v = " ".join(str(x) for x in value)
        else:
            v = str(value)
        if any(c in v for c in " \t\"'"):
            v = "'" + v.replace("'", "'\\''") + "'"
        # Normalize hyphenated keys (e.g. `extra-flags`) to a valid shell
        # identifier — `export EXTRA-FLAGS=...` is a parse error.
        shell_key = key.upper().replace("-", "_")
        print(f"export {shell_key}={v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
