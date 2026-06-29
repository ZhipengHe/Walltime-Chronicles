#!/bin/bash
# Entrypoint for the uv-on-aqua benchmark.
# Submit via:
#   qsub -N uv-bench-cpu-ml -q cpu_batch \
#        -l select=1:ncpus=8:mem=64GB -l walltime=01:00:00 \
#        -j oe -o $HOME/uv-bench/run.out -W block=true \
#        scripts/run-bench.sh

set -uo pipefail

# Under PBS, BASH_SOURCE[0] points to a staged copy in the spool dir, so
# prefer PBS_O_WORKDIR (qsub's invocation directory) when set.
if [ -n "${PBS_O_WORKDIR:-}" ]; then
  BENCH_ROOT="$PBS_O_WORKDIR"
else
  BENCH_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

if [ ! -f "$BENCH_ROOT/config.toml" ] || [ ! -d "$BENCH_ROOT/scripts" ]; then
  echo "ERROR: BENCH_ROOT=$BENCH_ROOT doesn't look like the benchmark directory" >&2
  echo "Submit from benchmarks/uv-on-aqua/:" >&2
  echo "  cd benchmarks/uv-on-aqua && qsub scripts/run-bench.sh" >&2
  exit 1
fi

REPO="$(cd "$BENCH_ROOT/../.." && pwd)"
cd "$BENCH_ROOT"

# Tool paths (override via env if your install lives elsewhere)
UV="${UV:-$HOME/.local/bin/uv}"
HF="${HF:-$HOME/.local/bin/hyperfine}"

# Fail fast if a required binary is missing so we don't burn a PBS slot
# before the per-cell work tries to run.
for tool_entry in "uv:$UV" "hyperfine:$HF"; do
  tool_name="${tool_entry%%:*}"
  tool_path="${tool_entry#*:}"
  if [ ! -x "$tool_path" ]; then
    echo "ERROR: $tool_name not executable at $tool_path" >&2
    echo "  Install hyperfine via scripts/install-hyperfine.sh," >&2
    echo "  and ensure uv is at \$HOME/.local/bin/uv (or override via UV=...)." >&2
    exit 1
  fi
done

# Pick a workload. v1 ships cpu-ml only; gpu-ml is defined in config.toml for later.
WORKLOAD="${WORKLOAD:-cpu-ml}"

# Need Python 3.11+ for tomllib. Prefer uv's managed Python; fall back to system python3.
if ! command -v python3 >/dev/null; then
  echo "ERROR: python3 not on PATH" >&2
  exit 1
fi
PYTHON3="${PYTHON3:-$( "$UV" python find 3.13 2>/dev/null || command -v python3 )}"
if ! "$PYTHON3" -c "import tomllib" 2>/dev/null; then
  echo "ERROR: $PYTHON3 lacks tomllib (need Python 3.11+)" >&2
  exit 1
fi

# Load config.toml into env. The helper emits `export KEY=VALUE` lines.
eval "$( "$PYTHON3" scripts/_toml_to_env.py config.toml base )"
eval "$( "$PYTHON3" scripts/_toml_to_env.py config.toml "workload.$WORKLOAD" )"

# INCLUDE_CELLS arrived as a space-separated string; convert to bash array.
read -ra INCLUDE_CELLS <<< "$INCLUDE_CELLS"

# Intermediate results dir (gitignored; lives under RESULTS_BASE per config).
# Expand leading ~ to $HOME so paths work in PBS context.
RESULTS_BASE="${RESULTS_BASE/#\~/$HOME}"
RESULTS_DIR="$RESULTS_BASE/results-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$RESULTS_DIR"
echo "Results dir: $RESULTS_DIR"

# Per-session seed for the cell-execution shuffle. Override with SESSION_SEED.
SESSION_SEED="${SESSION_SEED:-$$}"

# Source the helpers (cell paths + per-cell measurement functions + epilogue).
source "$BENCH_ROOT/scripts/_lib.sh"

# Build CELL_ORDER from INCLUDE_CELLS + seed.
cell_randomize

# Capture identity pins, FS provenance, node context. Halt on lockfile mismatch.
if ! session_prologue; then
  echo "Prologue failed; not running cells." >&2
  exit 1
fi

# Per-cell execution loop (see design §5.4 for the 11-step shape this implements).
for cell in "${CELL_ORDER[@]}"; do
  echo
  echo "============================================="
  echo "=== cell: $cell ==="
  echo "============================================="
  cell_cold     "$cell" || echo "cold failed for $cell — continuing"
  cell_warm     "$cell" || echo "warm failed for $cell — continuing"
  cell_aux      "$cell" || echo "aux failed for $cell — continuing"
  cell_resource "$cell" || echo "resource failed for $cell — continuing"
  cell_phase    "$cell" || echo "phase failed for $cell — continuing"
  cell_verify   "$cell" || echo "verify failed for $cell — continuing"
  cell_cleanup  "$cell"
done

# Bundle results into the tracked archive. session_epilogue propagates tar
# and sanitize failures — if either step fails the bench exits non-zero
# rather than printing "complete" with no usable archive.
if ! session_epilogue; then
  echo "ERROR: archive bundling/sanitization failed" >&2
  exit 1
fi

echo
echo "=== bench complete ==="
