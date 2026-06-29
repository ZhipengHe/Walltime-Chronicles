# uv on Aqua — Benchmark

Measures `uv sync` install timing on QUT Aqua across three filesystem configurations. Answers the question: "where should I put my uv cache and venv so install is fast, and what happens if I cross filesystems?"

## What this measures

Three cells, one workload (`cpu-ml` — realistic ML stack with CPU PyTorch). For each cell, cold + warm install timing via [hyperfine](https://github.com/sharkdp/hyperfine), plus auxiliary metrics (hardlink ratio, system CPU time, phase decomposition, file count, `Failed to hardlink` warning count).

| Cell | Cache | Venv | Same-FS? | What it tests |
|---|---|---|---|---|
| `lustre` | `$HOME/.cache/uv-bench/lustre` | `$HOME/uv-bench/venv-lustre` | yes (Lustre) | Default-user baseline (no setup needed for `$HOME` users) |
| `weka` | `/scratch/$USER/uv-bench/cache-weka` | `/scratch/$USER/uv-bench/venv-weka` | yes (Weka) | Recommended for active iterative work |
| `crossfs` | `$HOME/.cache/uv-bench/lustre-for-crossfs` | `/scratch/$USER/uv-bench/venv-crossfs-weka` | NO | Cross-FS trap (uv falls back to byte-by-byte copy) |

### Reference numbers from initial measurements

A bench run on the same hardware should reproduce these within noise. If your warm Weka comes in at, say, 12 s, something else is going on — start with the queue snapshot and the FS-provenance lines in `session-meta.txt`.

| Cell | Warm install (mean ± stddev) | Cold install (median) |
|---|---|---|
| `lustre` | 5.07 s ± 0.35 s | 16.77 s |
| `weka` | 4.42 s ± 0.21 s | 15.90 s |
| `crossfs` | 41.12 s ± 1.68 s | ~47 s (predicted) |

Warm `lustre` ≈ 15% slower than warm `weka` — driven by Lustre using ~2.4× more system CPU per syscall, which surfaces as wall-clock once network download isn't masking it. Cold install is ~17 s on either same-FS cell — network download dominates, FS choice is in the noise.

The `crossfs` cell prints `warning: Failed to hardlink files; falling back to full copy` — that's uv's user-facing signal that the cache and venv live on different filesystems. The 9–10× slowdown is the cost of falling back from `hardlink` to full byte-by-byte `copy` (Linux `EXDEV` from the kernel; cross-FS hardlinks are not allowed).

## How to run

### One-time setup on Aqua

From an Aqua login shell:

```bash
cd ~/Walltime-Chronicles/benchmarks/uv-on-aqua  # adjust to your clone path
bash scripts/install-hyperfine.sh
```

This installs hyperfine v1.20.0 to `~/.local/bin/`. The script is idempotent — verifies the existing binary's sha256 if hyperfine is already installed, downloads only if missing or stale. uv itself (v0.11.23+) is assumed to be in `~/.local/bin/` (the [`/scheduler/Know-Your-Nodes/`](../../docs/scheduler/Know-Your-Nodes.md) and related pages cover the user-binary convention).

### Run the bench

From the same directory:

```bash
qsub -N uv-bench-cpu-ml \
     -q cpu_batch \
     -l select=1:ncpus=8:mem=64GB \
     -l walltime=01:00:00 \
     -j oe -o $HOME/uv-bench/run.out \
     -W block=true \
     scripts/run-bench.sh
```

`-W block=true` makes `qsub` wait synchronously — convenient for driving from ssh. Total wall is ~30 min. Cells run in randomized order per session (seed logged with results) to absorb time-of-day Lustre/Weka load bias.

### Why 64 GB

Resource ask is uniform across all cells for cross-cell comparability. Cold install peaks at ~8 GiB cgroup memory under parallel wheel extraction (the page cache plus uv's mmap'd extract workers). Single-process RSS reported by `/usr/bin/time -v` undercounts the cgroup peak by ~50×, so don't size from that. 64 GB is the cold-safe headroom number; warm and cross-FS reps use far less but stay at this allocation for comparability.

### Why `cpu_batch`, not `cpu_inter`

`cpu_inter_exec` only accepts `qsub -I` (interactive). Batch jobs with `-q cpu_inter` get silently routed to `cpu_batch_exec` by the PBS server. We name the queue honestly: `cpu_batch`. Login-node placement is forbidden — shared, contended, and a methodology violation.

## Output

After the job lands, `results-archive/YYYY-MM-DD-<hostname>/` contains:

- `summary.md` — hand-curated summary; cites the redacted bundle for every quoted number.
- `redacted.tar.zst` — public bundle (tracked in git): every hyperfine JSON, verbose log, verify output, `time -v` capture, session-meta. zstd-compressed. Username, internal cluster IPs, CVE-matchable build strings, PBS run identifiers, and the live `qstat -Q` snapshot are replaced with placeholders per `scripts/_sanitize-archive.sh`.
- `manifest.sha256` — sha256 of `redacted.tar.zst`.
- `raw.tar.zst` + `raw.manifest.sha256` — un-redacted bundle and its sha256, kept on disk for forensic cross-checks; gitignored.

Intermediate scratch on Aqua (under `~/uv-bench/` by default — see `results_base` in `config.toml`) is gitignored. Only the redacted archive lands in git.

## Configuration

Edit `config.toml`. The knobs you're most likely to touch:

- `include_cells` — drop `"crossfs"` if you only want same-FS comparison.
- `cold_reps`, `warm_reps` — rep counts per cell (defaults: 5 each).
- `hyperfine_cold_warmup`, `hyperfine_warm_warmup` — `0` for cold (capture first-rep + report median), `1` for warm (discard OS-page-cache first-rep + report mean).
- `[workload.cpu-ml]` — PBS shape (queue, ncpus, mem, walltime). `[workload.gpu-ml]` is defined now but not run by default; switch with `WORKLOAD=gpu-ml` once a GPU bench is scheduled.

Bash reads `config.toml` via the `scripts/_toml_to_env.py` shim (Python's `tomllib` → `export KEY=VALUE` lines). Python helpers read it directly via `tomllib`.

## Re-locking the workload

`workloads/cpu-ml/uv.lock` was generated from the probe campaign and pins exact versions of all 53 packages. Re-lock periodically — once a year is a reasonable cadence — to refresh against current PyPI:

```bash
cd workloads/cpu-ml
uv lock
```

The floors in `pyproject.toml` (e.g., `torch>=2.0`, `numpy>=2.0`) guard against accidentally pulling a pre-modern-era version. After re-locking, commit the new `uv.lock` and record its sha256 in the next run's `summary.md`. The PBS-job prologue verifies `sha256sum workloads/cpu-ml/uv.lock` at session start — a mismatch halts the run rather than silently measuring against a different version set.

## Bench-locked lockfile sha256

`b64e55eee8c28496d2cafd82ec1e5c6d998bcb3d38072c3853efca5c1a99b98f` — the current `workloads/cpu-ml/uv.lock` sha256. Update this README when you re-lock.

## Caveats

- **Aqua-specific.** Lustre + Weka are the filesystems measured; results don't transfer to other clusters.
- **Single-node.** No multi-node bench.
- **v1 ships `cpu-ml` only.** GPU bench (cu126 wheels, ~5–7 GB extracted, ~8k files) is a separate future run.
- **`/dev/shm` is unusable for ML venvs on Aqua.** It's mounted `noexec`, which blocks `mmap(PROT_EXEC)` on the `.so` files uv extracts into the venv. `import torch` fails with `failed to map segment from shared object`. Documented here as a negative finding; not a bench cell.
- **File counts > byte counts for cross-FS comparisons.** Lustre `du` reports differently than Weka for identical content (up to ~22% lower on some reps). The bench reports file count, hardlink count, and hardlink ratio alongside footprint bytes.
- **Cross-FS direction shown is Lustre cache → Weka venv** (the more common user mistake: default `~/.cache/uv` while the project lives on `/scratch/`). The inverse direction (Weka cache → Lustre venv) is ~10% slower per probe but doesn't change the lesson.

## What's in the session-meta capture

Every PBS-job prologue writes `session-meta.txt` with:

- uv binary path + sha256 (halts if changed mid-session)
- hyperfine binary path + sha256
- `workloads/cpu-ml/uv.lock` sha256 (must match the bench-locked value above)
- Filesystem provenance: `df` on `$HOME`, `/scratch`, `$TMPDIR`, `/tmp`; Lustre + Weka client versions
- Node + PBS context: hostname, jobid, queue snapshot (`qstat -Q`)

These get bundled into `raw.tar.zst` alongside the timing data.
