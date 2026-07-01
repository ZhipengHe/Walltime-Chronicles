# uv on Aqua — 2026-07-01 (gpu1n012)

Headline: **the same-FS rule holds at gpu-ml scale (6.2 GB venv, ~26 k files, cu126 torch).** Same-FS Lustre and Weka warm cluster within ~10 % (Lustre median 4.23 s, Weka median 4.72 s); cross-FS warm is **~9× same-FS**. PyTorch's bundled CUDA runtime resolves inside the venv on all three cells — the "no `module load CUDA` needed" claim behind gpu-ml's docs story is empirically verified on H100 for the first time in this bench.

First gpu-ml archive. Pairs with the two prior cpu-ml archives (`2026-06-25-cpu1n033/`, `2026-06-29-cpu1n043/`) to show the same-FS rule scales from ~1.2 GB cpu-only to ~6.2 GB CUDA-bundled — per-cell numbers shift with workload magnitude but the direction and the trap signature don't.

## Run context

- Job `<jobid>` on `gpu1n012`, wall `48:39`, CPU `25:46`.
- Resource: 8 cpu / 64 GB / 1 GPU / `gpu_batch_exec`. Walltime ask: 90 min. GPU pinned to `gpu_id=H100`.
- Hardware: Intel Xeon Platinum 8468, 1006 GB RAM, NVIDIA H100 80 GB HBM3.
- Filesystems: Lustre `<lustre-client>`, Weka `<weka-client>`, both on InfiniBand.
- Tooling: uv `0.11.23` (`8bec1053…edb7a2`), hyperfine `1.20.0` (`a298729d…d080b6`).
- Workload: `gpu-ml` (71 packages resolved, 68 installed on Linux, ~26 k files, ~6.2 GB). `uv.lock` sha256 `bac22cfa…4c03`.
- Session seed `<seed>`; randomized execution order: `weka → lustre → crossfs`.

> Source: `session-meta.txt` (inside `redacted.tar.zst`).

## Timing (hyperfine, 5 reps per cell)

| Cell | Cold mean ± σ (median) | Cold rsd | Warm mean ± σ (median) | Warm rsd |
|---|---|---|---|---|
| `lustre`  | 49.72 ± 0.31 s (**49.63**) | 0.6 % | 4.31 ± 0.23 s (**4.23**) | 5.3 % |
| `weka`    | 54.51 ± 0.25 s (**54.53**) | 0.5 % | 4.72 ± 0.09 s (**4.72**) | 2.0 % |
| `crossfs` | 92.86 ± 0.35 s (**92.81**) | 0.4 % | 42.20 ± 1.21 s (**42.17**) | 2.9 % |

- Cold reports median (robust to the first-rep page-cache outlier).
- Warm reports mean after `--warmup 1` (first rep absorbed).
- **Cold is ~3× longer than the cpu-ml archives** — dominated by ~3.3 GB of NVIDIA CUDA + torch wheel downloads (torch 804 MiB, cudnn 674 MiB, cublas 375 MiB, nccl 276 MiB, cusparselt 274 MiB, cusparse 207 MiB, cufft 191 MiB, triton 189 MiB, cusolver 151 MiB, nvshmem 133 MiB).
- **Warm same-FS is within ~10 % of cpu-ml's ~4.4–5.1 s** despite gpu-ml's 5× larger footprint. Warm install cost is FS-syscall-dominated, not size-dominated — the cache is already populated, so only the link-into-venv step runs.
- **Lustre-vs-Weka warm gap flipped in Lustre's favor this run** (Lustre 4.23 s vs Weka 4.72 s median). Archive-1 (cpu-ml, 2026-06-25) had Weka ~15 % faster warm; this run and archive-2 (cpu-ml, 2026-06-29) show the gap is load-time-dependent — don't over-index on either FS being intrinsically faster at cpu-ml / gpu-ml scale.
- Cross-FS ~9× same-FS warm — the trap holds cleanly at gpu-ml scale.

> Sources: `bench-<cell>-cold.json`, `bench-<cell>-warm.json` (keys `mean`, `median`, `stddev`). Hyperfine stdout in `bench-<cell>-<phase>.log`.

## Phase decomposition (single cold rep, `uv --verbose`)

| Cell | Prepared | Installed |
|---|---|---|
| `weka`    | 46.66 s | 7.27 s  |
| `lustre`  | 45.98 s | 3.58 s  |
| `crossfs` | 45.36 s | **46.53 s** ← copy-fallback dominates |

- "Prepared" = download + extract from wheel cache. "Installed" = link cache → venv.
- Prepared is steady across cells (~46 s network + extract), same order of magnitude as cpu-ml prepare (~10 s) scaled by the ~3.3 GB extra wheel volume.
- Same-FS install ratio Lustre : Weka = 0.49 — Lustre installs **faster** than Weka this run. Opposite of the cpu-ml era Probe D+E ordering; attribute to Weka load at run time. The ~1.7× system-CPU gap Lustre still carries is present in the next table.
- crossfs install is **~13× same-FS Lustre install and ~6× same-FS Weka install** — the FS-perf cost cleanly separated from network.

> Source: `verbose-<cell>.log`, grep `^(Prepared|Installed)`.

## System-time signal (single cold rep, `/usr/bin/time -v`)

| Cell | User | System | Wall (est.) | CPU% (est.) |
|---|---|---|---|---|
| `weka`    | 35.95 s | 7.08 s  | ~55 s | ~78 % |
| `lustre`  | 35.86 s | 12.16 s | ~50 s | ~96 % |
| `crossfs` | 36.20 s | 23.89 s | ~93 s | ~65 % |

- System time = FS-syscall cost. Lustre ~1.7× Weka; crossfs ~3.4× Weka (cpu-ml archive-2 ratios were 2.3× and 4.6× — same shape, tighter here because the bigger workload gives the FS more work regardless of which one).
- **User time is nearly identical across cells (~36 s)** — dominated by wheel-extract CPU (68 packages, several hundred-MiB binary wheels). FS choice touches system time, not user time.
- Absolute system time is ~2× cpu-ml archive-2 across the board — proportional to file count × per-file-syscall cost.

> Source: `time-<cell>.stderr`.

## Filesystem-layout signal (post-install)

| Cell | Files | Hardlinks | Ratio | Footprint (no-deref / deref) | `Failed to hardlink` count |
|---|---|---|---|---|---|
| `lustre`  | 25,923 | 25,671 | 0.9903 | 6.21 GB / 6.24 GB | 0 |
| `weka`    | 25,923 | 25,671 | 0.9903 | 6.20 GB / 6.23 GB | 0 |
| `crossfs` | 25,923 | **0**  | 0.0000 | 6.20 GB / 6.23 GB | **1** |

- Same-FS cells: 99.03 % hardlink ratio (cpu-ml was 99.23 %). The ~250 non-hardlinked regular files per venv are the per-package metadata + `RECORD` + `.pyc` files uv writes on install — proportional to package count.
- crossfs: 0 hardlinks, 1 `Failed to hardlink` warning — trap signature identical to cpu-ml.
- File count ~26 k, only ~1 k more than cpu-ml's ~25 k — the extra ~18 NVIDIA CUDA wheels contribute mostly big shared objects (`.so`) plus a few dozen metadata files per package, not thousands. (The `config.toml` comment's "~8 k files" estimate is an artefact of an early guess; the reality is ~26 k.)

> Source: `aux-<cell>.json`.

## The cross-FS warning, verbatim

```text
warning: Failed to hardlink files; falling back to full copy. This may lead to degraded performance.
         If the cache and target directories are on different filesystems, hardlinking may not be supported.
         If this is intentional, set `export UV_LINK_MODE=copy` or use `--link-mode=copy` to suppress this warning.
```

Same wording as the cpu-ml archives. On Aqua that message means "cache and venv are on different filesystems" almost every time.

> Source: `uv-output-crossfs.log`.

## Verification

### Python-side

Every cell ran `python -c "import torch; ..."` after install:

```text
torch: 2.12.1+cu126
cuda_available: True
device: cuda:0
```

`x = torch.zeros(1).cuda()` succeeded (returned `device: cuda:0`) on all three cells.

> Source: `verify-<cell>.txt`.

### Bundled-CUDA `ldd` check — the load-bearing gpu-ml claim

Each cell's `libtorch_cuda.so` must resolve its CUDA-runtime dependencies INSIDE the venv, not to `/apps/CUDA/...` on the host. This is the whole reason gpu-ml exists as a distinct bench: the "no `module load CUDA` needed" claim in the docs relies on it, and cpu-ml can't test it (no CUDA libs to check). All three cells:

```text
libcudart.so.12   → <venv>/lib/python3.13/site-packages/torch/lib/../../nvidia/cuda_runtime/lib/libcudart.so.12
libcublas.so.12   → <venv>/lib/python3.13/site-packages/torch/lib/../../nvidia/cublas/lib/libcublas.so.12
libcublasLt.so.12 → <venv>/lib/python3.13/site-packages/torch/lib/../../nvidia/cublas/lib/libcublasLt.so.12
libcudnn.so.9     → <venv>/lib/python3.13/site-packages/torch/lib/../../nvidia/cudnn/lib/libcudnn.so.9
```

No system-CUDA rows. The bundled-CUDA claim is verified across all three filesystem placements.

> Source: `ldd-<cell>.txt`.

## What this run does and doesn't claim

- **Does claim** — at gpu-ml scale (~6.2 GB, ~26 k files, cu126 torch) on H100, the same-FS rule is empirically valid on Aqua: same-FS Lustre ≈ same-FS Weka ≪ cross-FS. The ~9× cross-FS penalty holds cleanly.
- **Does claim** — the "PyTorch's bundled CUDA runtime resolves inside the venv" claim behind the "no `module load CUDA`" story is verified. No cell's `libtorch_cuda.so` reached out to system libs.
- **Doesn't claim** — that Lustre is reliably faster than Weka warm. This archive's Lustre warm (median 4.23 s) is within one Weka σ; prior cpu-ml archive-1 showed the reverse. The same-FS gap is small, load-time-dependent, and shouldn't drive FS choice for iterative work.
- **Doesn't claim** — that gpu-ml install time predicts scientific-workload GPU perf. This bench measures install (download + extract + link). Everything downstream — CUDA kernel launch, matmul throughput, model training — is a different question.

## Reproducing this run

From the bench directory:

```bash
# On an Aqua login shell, in benchmarks/uv-on-aqua/
qsub -N uv-bench-gpu-ml -q gpu_batch \
     -l select=1:ncpus=8:ngpus=1:mem=64GB:gpu_id=H100 \
     -l walltime=01:30:00 \
     -j oe -o $HOME/uv-bench/run-gpu-ml.out \
     -M $USER@qut.edu.au -m abe \
     -W block=true -v WORKLOAD=gpu-ml \
     scripts/run-bench.sh
```

Submit-shape notes:

- `-v WORKLOAD=gpu-ml` — `run-bench.sh` reads `WORKLOAD` and picks up `[workload.gpu-ml]` from `config.toml`.
- `gpu_id=H100` in the select — pinned for reproducibility. A100 nodes exist on Aqua but H100 has more free capacity in typical off-peak windows.
- `$USER` and `$HOME` expand in the submit-time login shell; Aqua's PBS Pro does NOT expand shell env vars inside `#PBS -o`, `#PBS -e`, or `#PBS -M` directive values, so CLI-passing is required.

The PBS-job prologue verifies the `uv.lock` sha256 against `config.toml [workload.gpu-ml].lock_hash_expected` before any cell runs — a mismatch halts the run before timing data is captured. `session_epilogue` propagates `tar` + `_sanitize-archive.sh` exit codes so a failed bundling step exits non-zero rather than printing `=== bench complete ===` with no archive.

## Archive

`redacted.tar.zst` (zstd -19, tracked in git) bundles every file referenced above plus `cache-prepop-<cell>.log`, `time-<cell>.stdout`, and `ldd-<cell>.txt`. `manifest.sha256` verifies its integrity. The redacted bundle is produced by `scripts/_sanitize-archive.sh`; the raw bundle (`raw.tar.zst` + `raw.manifest.sha256`) is gitignored and kept on disk for forensic cross-checks.

First gpu-ml archive. Prior archives are cpu-ml only.
