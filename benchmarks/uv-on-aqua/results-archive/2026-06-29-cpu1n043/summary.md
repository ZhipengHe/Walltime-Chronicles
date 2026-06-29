# uv on Aqua — 2026-06-29 (cpu1n043)

Headline: **the same-FS rule holds at cpu-ml scale.** Same-FS Lustre and Weka warm are within ~12% of each other this run (Lustre median 4.49 s, Weka median 4.77 s); cross-FS is **~9× same-FS warm**. The cross-FS trap signature — 0 hardlinks plus uv's `Failed to hardlink` warning — fires as expected.

Second archive of the bench. Pairs with `results-archive/2026-06-25-cpu1n033/` (first archive, 4 days earlier on a different node) to demonstrate the rule holds across days/nodes; per-cell numbers shift within the variance the design's "Doesn't claim" section already warned about.

## Run context

- Job `<jobid>` on `cpu1n043`, wall `29:10`, CPU `08:00`.
- Resource: 8 cpu / 64 GB / `cpu_batch_exec`. Walltime ask: 60 min.
- Hardware: AMD EPYC 9684X 96-core (Genoa-X w/ V-Cache), 1510 GB RAM (same SKU as cpu1n033).
- Filesystems: Lustre `<lustre-client>`, Weka `<weka-client>`, both on InfiniBand.
- Tooling: uv `0.11.23` (`8bec1053…edb7a2`), hyperfine `1.20.0` (`a298729d…d080b6`).
- Workload: `cpu-ml` (53 packages, ~25k files, ~1.2 GB). `uv.lock` sha256 `b64e55ee…b98f`.
- Session seed `<seed>`; randomized execution order: `lustre → crossfs → weka`.

> Source: `session-meta.txt` (inside `redacted.tar.zst`).

## Timing (hyperfine, 5 reps per cell)

| Cell | Cold mean ± σ (median) | Cold rsd | Warm mean ± σ (median) | Warm rsd |
|---|---|---|---|---|
| `lustre`  | 13.79 ± 1.08 s (**13.63**) | 7.8% | 4.33 ± 0.74 s (**4.49**) | 17.0% |
| `weka`    | 15.63 ± 0.24 s (**15.64**) | 1.5% | 4.83 ± 0.13 s (**4.77**) | 2.7% |
| `crossfs` | 52.47 ± 1.90 s (**52.43**) | 3.6% | 40.25 ± 3.00 s (**38.40**) | 7.5% |

- Cold reports median (robust to the first-rep page-cache outlier).
- Warm reports mean after `--warmup 1` (first rep absorbed).
- **The lustre warm mean (4.33 s) is dragged DOWN by one anomalously-fast rep at 3.08 s** (range 3.08–4.93 s). Lustre's median (4.49 s) and Weka's median (4.77 s) are within 6% — essentially equivalent today. The ~18% Weka-over-Lustre advantage seen in `2026-06-25-cpu1n033/` did not reproduce, consistent with the design's load-time-dependence caveat.
- Cross-FS cold + warm are tightly clustered around the prior-archive numbers (52.47 vs 53.82 cold; 40.25 vs 38.61 warm).

> Sources: `bench-<cell>-cold.json`, `bench-<cell>-warm.json` (keys `mean`, `median`, `stddev`). Hyperfine stdout in `bench-<cell>-<phase>.log`.

## Phase decomposition (single cold rep, `uv --verbose`)

| Cell | Prepared | Installed |
|---|---|---|
| `lustre`  | 9.43 s  | 4.54 s  |
| `weka`    | 9.83 s  | 5.79 s  |
| `crossfs` | 9.59 s  | **42.87 s** ← copy-fallback dominates |

- "Prepared" = download + extract from wheel cache. "Installed" = link cache → venv.
- crossfs install is ~9× weka install — the FS-perf cost cleanly separated from network.

> Source: `verbose-<cell>.log`, grep `^(Prepared|Installed)`.

## System-time signal (single cold rep, `/usr/bin/time -v`)

| Cell | User | System | Wall | CPU% |
|---|---|---|---|---|
| `lustre`  | 3.02 s | 7.43 s  | 13.17 s | 79% |
| `weka`    | 3.02 s | 3.20 s  | 15.34 s | 40% |
| `crossfs` | 3.36 s | 14.57 s | 51.62 s | 34% |

- System time = FS-syscall cost. Lustre ~2.3× Weka; crossfs ~4.6× Weka (matches the prior archive's ~2.1× and ~4.2× ratios).

> Source: `time-<cell>.stderr`.

## Filesystem-layout signal (post-install)

| Cell | Files | Hardlinks | Ratio | Footprint (no-deref / deref) | `Failed to hardlink` count |
|---|---|---|---|---|---|
| `lustre`  | 24,990 | 24,797 | 0.9923 | 1.16 GB / 1.19 GB | 0 |
| `weka`    | 24,990 | 24,797 | 0.9923 | 1.15 GB / 1.18 GB | 0 |
| `crossfs` | 24,990 | **0**  | 0.0000 | 1.15 GB / 1.18 GB | **1** |

- Same-FS cells: 99.23% hardlink ratio (identical to prior archive).
- crossfs: 0 hardlinks, 1 `Failed to hardlink` warning — trap signature.

> Source: `aux-<cell>.json`.

## The cross-FS warning, verbatim

```text
warning: Failed to hardlink files; falling back to full copy. This may lead to degraded performance.
         If the cache and target directories are on different filesystems, hardlinking may not be supported.
         If this is intentional, set `export UV_LINK_MODE=copy` or use `--link-mode=copy` to suppress this warning.
```

> Source: `uv-output-crossfs.log` and the head of `verbose-crossfs.log`.

## Verification

Each cell ran `python -c "import torch; print(torch.__version__)"` after install. All three cells:

```text
torch: 2.12.1+cpu
cuda_available: False
```

> Source: `verify-<cell>.txt`.

## What this run does and doesn't claim

- **Does claim** — at cpu-ml scale, the same-FS rule is empirically valid on Aqua: Lustre ≈ Weka ≪ cross-FS. The ~9× cross-FS penalty is consistent across both archives.
- **Does claim** — the hardened sanitize pipeline (per CodeRabbit review) works end-to-end on the Aqua side: redacted bundle's tar headers normalized to `0/0`, all 6 self-verify counts at 0.
- **Doesn't claim** — that Weka is reliably faster than Lustre warm. This archive's lustre warm has a 3.08 s outlier that flips the mean comparison; medians are essentially tied. The prior archive showed Weka ~18% faster warm. Both are within the band the design called out as load-time-dependent.
- **Doesn't claim** — anything about gpu-ml (cu126 wheels, ~5–7 GB). `[workload.gpu-ml]` in `config.toml` is reserved with `lock_hash_expected = ""`; the prologue halts cleanly if anyone tries to run it before pinning a lockfile sha.

## Reproducing this run

From this directory (or the bench README):

```bash
# On an Aqua login shell, in benchmarks/uv-on-aqua/
qsub -N uv-bench-cpu-ml -q cpu_batch \
     -l select=1:ncpus=8:mem=64GB -l walltime=01:00:00 \
     -j oe -o $HOME/uv-bench/run.out -W block=true \
     scripts/run-bench.sh
```

The PBS-job prologue verifies the `uv.lock` sha256 against the per-workload pinned value (`config.toml [workload.cpu-ml].lock_hash_expected`) before any cell runs — a mismatch halts the run before timing data is captured. `session_epilogue` propagates `tar` + `_sanitize-archive.sh` exit codes so a failed bundling step exits non-zero rather than printing `=== bench complete ===` with no archive.

## Archive

`redacted.tar.zst` (zstd -19, tracked in git) bundles every file referenced above plus `cache-prepop-<cell>.log` and `time-<cell>.stdout`. `manifest.sha256` verifies its integrity. The redacted bundle is produced by `scripts/_sanitize-archive.sh`; the raw bundle (`raw.tar.zst` + `raw.manifest.sha256`) is gitignored and kept on disk for forensic cross-checks.

This is the first archive produced **entirely on the Aqua side** — `session_epilogue` invoked the sanitize step automatically after bundling. The prior archive (`2026-06-25-cpu1n033/`) had its bundling done on the same Aqua node but its sanitize step run locally on macOS; the workflow has converged.
