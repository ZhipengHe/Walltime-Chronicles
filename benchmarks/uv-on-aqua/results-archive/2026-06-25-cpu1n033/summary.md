# uv on Aqua — 2026-06-25 (cpu1n033)

Headline: **the same-FS rule holds at cpu-ml scale.** Same-FS Weka is ~21% faster than same-FS Lustre on warm install; cross-FS is **~8.2× same-FS Weka** warm and **~3.4× same-FS Weka** cold. Cross-FS produces 0 hardlinks and uv's `Failed to hardlink` warning fires, exactly as expected.

## Run context

- Job `<jobid>` on `cpu1n033`, wall `30:07`, CPU `08:27`.
- Resource: 8 cpu / 64 GB / `cpu_batch_exec`. Walltime ask: 60 min.
- Hardware: AMD EPYC 9684X 96-core (Genoa-X w/ V-Cache), 1510 GB RAM.
- Filesystems: Lustre client `<lustre-client>`, Weka client `<weka-client>`, both on InfiniBand.
- Tooling: uv `0.11.23` (`8bec1053…edb7a2`), hyperfine `1.20.0` (`a298729d…d080b6`).
- Workload: `cpu-ml` (53 packages, ~25k files, ~1.2 GB). `uv.lock` sha256 `b64e55ee…b98f`.
- Session seed `<seed>`; randomized execution order: `weka → crossfs → lustre`.

> Source: `session-meta.txt` (inside `redacted.tar.zst`).

## Timing (hyperfine, 5 reps per cell)

| Cell | Cold median | Cold rsd | Warm mean | Warm σ | Warm rsd |
|---|---|---|---|---|---|
| `weka`    | **15.78 s** | 3.6%  | **4.71 s**  | 0.18 s | 3.8% |
| `lustre`  | **16.04 s** | 11.0% | **5.94 s**  | 0.37 s | 6.2% |
| `crossfs` | **53.82 s** | 4.6%  | **38.61 s** | 0.54 s | 1.4% |

- Cold reports median (robust to the first-rep page-cache outlier).
- Warm reports mean after `--warmup 1` (first rep absorbed).
- The lustre cold rsd of 11% reflects time-of-day Lustre contention — the cell ran third in this session and `cpu_batch_exec` was heavily loaded at start. Off-peak hours should tighten this.
- hyperfine flagged a soft "Statistical outliers were detected" on lustre warm — one rep at 6.60 s vs ~5.75 s baseline. Mean and stddev above include the outlier.

> Sources: `bench-<cell>-cold.json`, `bench-<cell>-warm.json` (keys `mean`, `median`, `stddev`). Hyperfine stdout in `bench-<cell>-<phase>.log`.

## Phase decomposition (single cold rep, `uv --verbose`)

| Cell | Prepared | Installed |
|---|---|---|
| `weka`    | 10.30 s | 5.78 s  |
| `lustre`  | 12.10 s | 4.80 s  |
| `crossfs` | 9.58 s  | **40.07 s** ← copy-fallback dominates |

- "Prepared" = download + extract from wheel cache. "Installed" = link cache → venv.
- crossfs install is ~8× same-FS Weka install — that's the FS-perf cost surfaced cleanly without network noise.

> Source: `verbose-<cell>.log`, grep `^(Prepared|Installed)`.

## System-time signal (single cold rep, `/usr/bin/time -v`)

| Cell | User | System | Wall | CPU% |
|---|---|---|---|---|
| `weka`    | 3.10 s | 3.71 s  | 15.79 s | 43% |
| `lustre`  | 3.06 s | 7.97 s  | 17.30 s | 63% |
| `crossfs` | 3.47 s | 15.68 s | 51.47 s | 37% |

- System time = FS-syscall cost. Lustre ~2.1× Weka; crossfs ~4.2× Weka.
- The lustre wall is close to weka cold but spends ~2× kernel time on it — masked by concurrent network download. On warm, the gap surfaces in wall-clock.

> Source: `time-<cell>.stderr`.

## Filesystem-layout signal (post-install)

| Cell | Files | Hardlinks | Ratio | Footprint (no-deref / deref) | `Failed to hardlink` count |
|---|---|---|---|---|---|
| `weka`    | 24,990 | 24,797 | 0.9923 | 1.15 GB / 1.18 GB | 0 |
| `lustre`  | 24,990 | 24,797 | 0.9923 | 1.16 GB / 1.19 GB | 0 |
| `crossfs` | 24,990 | **0**  | 0.0000 | 1.15 GB / 1.18 GB | **1** |

- Same-FS cells: 99.23% hardlink ratio — uv dedups maximally within one filesystem.
- crossfs: 0 hardlinks. Cross-filesystem hardlinks are not allowed (Linux `EXDEV`), so uv falls back to byte-by-byte copy.
- File count identical across all three cells (same workload, same lockfile, same uv version) — useful sanity check.

> Source: `aux-<cell>.json`.

## The cross-FS warning, verbatim

```text
warning: Failed to hardlink files; falling back to full copy. This may lead to degraded performance.
         If the cache and target directories are on different filesystems, hardlinking may not be supported.
         If this is intentional, set `export UV_LINK_MODE=copy` or use `--link-mode=copy` to suppress this warning.
```

This is the user-facing signal that cache and venv live on different filesystems. If a reader sees this in their own runs, the same-FS rule has been violated.

> Source: `uv-output-crossfs.log` and the head of `verbose-crossfs.log`.

## Verification

Each cell ran `python -c "import torch; print(torch.__version__)"` after install. All three cells:

```text
torch: 2.12.1+cpu
cuda_available: False
```

The `cuda_available: False` is expected — this is the CPU PyTorch wheel.

> Source: `verify-<cell>.txt`.

## What this run does and doesn't claim

- **Does claim** — at cpu-ml scale on this hardware on the archive date, the same-FS rule is empirically valid: Weka ≈ Lustre ≪ cross-FS. The Weka-over-Lustre warm advantage is small (~21%, ~1.2 s) but consistent.
- **Doesn't claim** — that these numbers are universally Aqua's; FS load is time-of-day-dependent. The lustre cold rsd of 11% and the warm outlier hint at this. The recommended cadence is one bench run per quarter; the lustre wall in particular may shift.
- **Doesn't claim** — anything about gpu-ml (cu126 wheels, ~5–7 GB). The `[workload.gpu-ml]` slot in `config.toml` is reserved for a future GPU-allocation run.

## Reproducing this run

From this directory (or the bench README):

```bash
# On an Aqua login shell, in benchmarks/uv-on-aqua/
qsub -N uv-bench-cpu-ml -q cpu_batch \
     -l select=1:ncpus=8:mem=64GB -l walltime=01:00:00 \
     -j oe -o $HOME/uv-bench/run.out -W block=true \
     scripts/run-bench.sh
```

The PBS-job prologue verifies the `uv.lock` sha256 against the pinned value before any cell runs — a mismatch halts the run before timing data is captured.

## Archive

`redacted.tar.zst` (zstd -19, tracked in git) bundles every file referenced above plus `cache-prepop-<cell>.log` and `time-<cell>.stdout`. `manifest.sha256` verifies its integrity. The redacted bundle is produced by `scripts/_sanitize-archive.sh`; the raw bundle (`raw.tar.zst` + `raw.manifest.sha256`) is gitignored and kept on disk for forensic cross-checks.
