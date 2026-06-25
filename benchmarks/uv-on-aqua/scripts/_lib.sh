#!/bin/bash
# Sourced by run-bench.sh. Defines cell config + per-cell measurement functions.
# Functions expect the following env vars to be set by the caller:
#   UV, HF, WORKLOAD, RESULTS_DIR, REPO, ARCHIVE_BASE
#   COLD_REPS, WARM_REPS, HYPERFINE_COLD_WARMUP, HYPERFINE_WARM_WARMUP
#   INCLUDE_CELLS (array), SESSION_SEED, VERIFY_CUDA

# Pinned tool + lockfile identities. Override via env if the binaries are rotated.
UV_HASH_EXPECTED="${UV_HASH_EXPECTED:-8bec1053d461e6b62f062419e62daa65ab7430884829d6fafcb7157b76edb7a2}"
HYPERFINE_HASH_EXPECTED="${HYPERFINE_HASH_EXPECTED:-a298729daf3b670198b6988a0489289e0044174c8734a172659495dd09d080b6}"
LOCK_HASH_EXPECTED="${LOCK_HASH_EXPECTED:-b64e55eee8c28496d2cafd82ec1e5c6d998bcb3d38072c3853efca5c1a99b98f}"

# Resolve cell label to (CACHE, VENV) paths. Sets $CACHE and $VENV.
cell_paths() {
  local label="$1"
  case "$label" in
    lustre)
      CACHE="$HOME/.cache/uv-bench/lustre"
      VENV="$HOME/uv-bench/venv-lustre"
      ;;
    weka)
      CACHE="/scratch/$USER/uv-bench/cache-weka"
      VENV="/scratch/$USER/uv-bench/venv-weka"
      ;;
    crossfs)
      CACHE="$HOME/.cache/uv-bench/lustre-for-crossfs"
      VENV="/scratch/$USER/uv-bench/venv-crossfs-weka"
      ;;
    *)
      echo "ERROR: unknown cell label '$label'" >&2
      return 1
      ;;
  esac
}

# Capture session-meta.txt: identity pins, FS provenance, node context.
# Halts the run if the lockfile sha256 does not match LOCK_HASH_EXPECTED.
session_prologue() {
  local meta="$RESULTS_DIR/session-meta.txt"
  mkdir -p "$RESULTS_DIR"

  {
    echo "=== session prologue ==="
    hostname
    date -u +%Y-%m-%dT%H:%M:%SZ
    echo "PBS_JOBID: ${PBS_JOBID:-unset}"
    echo "PBS_O_HOST: ${PBS_O_HOST:-unset}"
    echo

    echo "=== module + env hygiene ==="
    module purge 2>&1 || true
    unset LD_LIBRARY_PATH
    echo "LOADEDMODULES: ${LOADEDMODULES:-<unset>}"
    echo "LD_LIBRARY_PATH: ${LD_LIBRARY_PATH:-<unset>}"
    echo

    echo "=== tool identities ==="
    local uv_hash hf_hash lock_hash
    uv_hash=$(sha256sum "$UV" | awk '{print $1}')
    hf_hash=$(sha256sum "$HF" | awk '{print $1}')
    lock_hash=$(sha256sum "workloads/$WORKLOAD/uv.lock" | awk '{print $1}')

    echo "uv: $($UV --version) at $UV"
    echo "uv sha256:          $uv_hash"
    echo "uv sha256 expected: $UV_HASH_EXPECTED"
    [ "$uv_hash" = "$UV_HASH_EXPECTED" ] || echo "WARNING: uv sha256 mismatch (continuing — uv may be a different point release)"
    echo

    echo "hyperfine: $($HF --version) at $HF"
    echo "hyperfine sha256:          $hf_hash"
    echo "hyperfine sha256 expected: $HYPERFINE_HASH_EXPECTED"
    [ "$hf_hash" = "$HYPERFINE_HASH_EXPECTED" ] || echo "WARNING: hyperfine sha256 mismatch"
    echo

    echo "uv.lock ($WORKLOAD) sha256:          $lock_hash"
    echo "uv.lock ($WORKLOAD) sha256 expected: $LOCK_HASH_EXPECTED"
    if [ "$lock_hash" != "$LOCK_HASH_EXPECTED" ]; then
      echo "ERROR: uv.lock sha256 mismatch — halting"
      return 1
    fi
    echo

    echo "=== filesystem provenance ==="
    df -h "$HOME" /scratch "${TMPDIR:-/tmp}" /tmp 2>/dev/null
    [ -r /sys/module/lustre/version ] && echo "lustre kernel: $(cat /sys/module/lustre/version)"
    command -v lfs >/dev/null && lfs --version 2>&1 | head -1
    command -v weka >/dev/null && weka version 2>&1 | head -3
    echo

    echo "=== node + PBS context ==="
    uname -a
    echo "cpu model:    $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | xargs)"
    echo "memory total: $(awk '/MemTotal/ {printf "%.1f GB", $2/1024/1024}' /proc/meminfo)"
    qstat -Q 2>&1 | head -15
    echo

    echo "=== seed + execution plan ==="
    echo "session seed:    $SESSION_SEED"
    echo "execution order: ${CELL_ORDER[*]}"
  } > "$meta" 2>&1

  local rc
  rc=$(grep -c "^ERROR" "$meta" 2>/dev/null || echo 0)
  cat "$meta"
  [ "$rc" -eq 0 ]
}

# Randomize INCLUDE_CELLS into CELL_ORDER using SESSION_SEED.
cell_randomize() {
  local seed="${SESSION_SEED:-$$}"
  SESSION_SEED="$seed"
  mapfile -t CELL_ORDER < <(
    printf '%s\n' "${INCLUDE_CELLS[@]}" |
      awk -v s="$seed" 'BEGIN{srand(s)} {print rand() "\t" $0}' |
      sort -k1,1n |
      cut -f2-
  )
}

# Cold hyperfine run. Wipes cache + venv per rep. Reports median.
cell_cold() {
  local cell="$1"
  cell_paths "$cell"
  export UV_CACHE_DIR="$CACHE"
  export UV_PROJECT_ENVIRONMENT="$VENV"
  mkdir -p "$(dirname "$CACHE")" "$(dirname "$VENV")"

  echo "--- cell $cell: cold (warmup=$HYPERFINE_COLD_WARMUP, reps=$COLD_REPS) ---"
  "$HF" \
    --warmup "$HYPERFINE_COLD_WARMUP" \
    --runs "$COLD_REPS" \
    --prepare 'rm -rf "$UV_CACHE_DIR" "$UV_PROJECT_ENVIRONMENT" && mkdir -p "$UV_CACHE_DIR"' \
    --export-json "$RESULTS_DIR/bench-$cell-cold.json" \
    --command-name "cold-$cell" \
    "$UV sync --frozen --project workloads/$WORKLOAD" \
    2>&1 | tee "$RESULTS_DIR/bench-$cell-cold.log" | tail -16

  echo "--- cold stats ($cell) ---"
  jq -r '.results[0] | "mean=\(.mean)s stddev=\(.stddev)s median=\(.median)s min=\(.min)s max=\(.max)s"' \
    "$RESULTS_DIR/bench-$cell-cold.json"
}

# Warm hyperfine run. Pre-populates cache once (untimed), then runs.
cell_warm() {
  local cell="$1"
  cell_paths "$cell"
  export UV_CACHE_DIR="$CACHE"
  export UV_PROJECT_ENVIRONMENT="$VENV"

  rm -rf "$UV_CACHE_DIR" && mkdir -p "$UV_CACHE_DIR"
  "$UV" sync --frozen --project "workloads/$WORKLOAD" \
    > "$RESULTS_DIR/cache-prepop-$cell.log" 2>&1
  rm -rf "$VENV"

  echo "--- cell $cell: warm (warmup=$HYPERFINE_WARM_WARMUP, reps=$WARM_REPS) ---"
  "$HF" \
    --warmup "$HYPERFINE_WARM_WARMUP" \
    --runs "$WARM_REPS" \
    --prepare 'rm -rf "$UV_PROJECT_ENVIRONMENT"' \
    --export-json "$RESULTS_DIR/bench-$cell-warm.json" \
    --command-name "warm-$cell" \
    "$UV sync --frozen --project workloads/$WORKLOAD" \
    2>&1 | tee "$RESULTS_DIR/bench-$cell-warm.log" | tail -16

  echo "--- warm stats ($cell) ---"
  jq -r '.results[0] | "mean=\(.mean)s stddev=\(.stddev)s median=\(.median)s min=\(.min)s max=\(.max)s"' \
    "$RESULTS_DIR/bench-$cell-warm.json"
}

# Auxiliary metrics: file count, hardlink count + ratio, footprint, warning count.
# Reads the venv left over from the last warm rep; runs ONE fresh cold to grep warnings.
cell_aux() {
  local cell="$1"
  cell_paths "$cell"
  export UV_CACHE_DIR="$CACHE"
  export UV_PROJECT_ENVIRONMENT="$VENV"

  local total files syms hardlinks ratio bytes_no_deref bytes_deref warn_count
  total=$(find "$VENV" 2>/dev/null | wc -l)
  files=$(find "$VENV" -type f 2>/dev/null | wc -l)
  syms=$(find "$VENV" -type l 2>/dev/null | wc -l)
  hardlinks=$(find "$VENV" -type f -links +1 2>/dev/null | wc -l)
  if [ "$files" -gt 0 ]; then
    ratio=$(awk -v h="$hardlinks" -v f="$files" 'BEGIN{printf "%.4f", h/f}')
  else
    ratio="null"
  fi
  bytes_no_deref=$(du -sb "$VENV" 2>/dev/null | awk '{print $1}')
  bytes_deref=$(du -sLb "$VENV" 2>/dev/null | awk '{print $1}')

  rm -rf "$UV_CACHE_DIR" "$UV_PROJECT_ENVIRONMENT" && mkdir -p "$UV_CACHE_DIR"
  "$UV" sync --frozen --project "workloads/$WORKLOAD" \
    > "$RESULTS_DIR/uv-output-$cell.log" 2>&1
  warn_count=$(grep -c "Failed to hardlink" "$RESULTS_DIR/uv-output-$cell.log" || echo 0)

  {
    echo "{"
    echo "  \"cell\": \"$cell\","
    echo "  \"total_entries\": $total,"
    echo "  \"regular_files\": $files,"
    echo "  \"symlinks\": $syms,"
    echo "  \"hardlinked_files\": $hardlinks,"
    echo "  \"hardlink_ratio\": $ratio,"
    echo "  \"bytes_no_deref\": $bytes_no_deref,"
    echo "  \"bytes_deref\": $bytes_deref,"
    echo "  \"warn_count\": $warn_count"
    echo "}"
  } > "$RESULTS_DIR/aux-$cell.json"

  echo "--- aux ($cell) ---"
  cat "$RESULTS_DIR/aux-$cell.json"
}

# Resource accounting via /usr/bin/time -v (single cold rep).
cell_resource() {
  local cell="$1"
  cell_paths "$cell"
  export UV_CACHE_DIR="$CACHE"
  export UV_PROJECT_ENVIRONMENT="$VENV"

  rm -rf "$UV_CACHE_DIR" "$UV_PROJECT_ENVIRONMENT" && mkdir -p "$UV_CACHE_DIR"
  /usr/bin/time -v "$UV" sync --frozen --project "workloads/$WORKLOAD" \
    > "$RESULTS_DIR/time-$cell.stdout" \
    2> "$RESULTS_DIR/time-$cell.stderr"
  echo "--- time -v ($cell) ---"
  cat "$RESULTS_DIR/time-$cell.stderr"
}

# Phase decomposition via uv --verbose (single cold rep).
cell_phase() {
  local cell="$1"
  cell_paths "$cell"
  export UV_CACHE_DIR="$CACHE"
  export UV_PROJECT_ENVIRONMENT="$VENV"

  rm -rf "$UV_CACHE_DIR" "$UV_PROJECT_ENVIRONMENT" && mkdir -p "$UV_CACHE_DIR"
  "$UV" sync --frozen --verbose --project "workloads/$WORKLOAD" \
    > "$RESULTS_DIR/verbose-$cell.log" 2>&1
  echo "--- phase markers ($cell) ---"
  grep -E "^(Resolved|Downloaded|Prepared|Installed|Built|Cached|Audited)" \
    "$RESULTS_DIR/verbose-$cell.log" | head -30
}

# Smoke test: import the workload's load-bearing dep. For gpu-ml, also check CUDA.
cell_verify() {
  local cell="$1"
  cell_paths "$cell"

  echo "--- verify ($cell) ---"
  if [ "${VERIFY_CUDA:-false}" = "true" ]; then
    "$VENV/bin/python" -c "
import torch
print('torch:', torch.__version__)
print('cuda_available:', torch.cuda.is_available())
x = torch.zeros(1).cuda()
print('device:', x.device)
" 2>&1 | tee "$RESULTS_DIR/verify-$cell.txt"
  else
    "$VENV/bin/python" -c "
import torch
print('torch:', torch.__version__)
print('cuda_available:', torch.cuda.is_available())
" 2>&1 | tee "$RESULTS_DIR/verify-$cell.txt"
  fi
}

# Drop the venv; keep cache for the archive (so analyze can inspect later if useful).
cell_cleanup() {
  local cell="$1"
  cell_paths "$cell"
  rm -rf "$VENV"
  echo "venv removed: $VENV"
}

# Bundle results/ into a zstd archive under archive_base/<date>-<host>/.
session_epilogue() {
  local today host archive_dir
  today=$(date -u +%Y-%m-%d)
  host=$(hostname -s)
  archive_dir="$REPO/benchmarks/uv-on-aqua/$ARCHIVE_BASE/${today}-${host}"
  mkdir -p "$archive_dir"

  tar --use-compress-program='zstd -19' -cf "$archive_dir/raw.tar.zst" -C "$RESULTS_DIR" .
  (cd "$archive_dir" && sha256sum raw.tar.zst > manifest.sha256)

  echo
  echo "=== archive ==="
  echo "$archive_dir"
  ls -la "$archive_dir"
}
