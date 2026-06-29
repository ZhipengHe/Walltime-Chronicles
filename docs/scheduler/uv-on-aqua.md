# uv on Aqua: Cache + Envs Placement

!!! warning "Stub — full content coming in a later session"
    [Lesson 2](../tutorials/lesson-2.md#for-uv-users-same-fs-rule) carries the short version (the same-FS rule + the recommended `/scratch` setup). This page will expand it with the empirical evidence, the three placement patterns, the cross-FS trap, and the wider HPC-community context.

## Planned outline

- The **same-FS rule** + why it exists (uv hardlinks cache → venv; cross-FS hardlinks raise `EXDEV`)
- **Aqua's filesystem capability matrix** (Lustre `/home`, Weka `/scratch`, Weka `$TMPDIR`, cross-FS)
- **Empirical** warm-install numbers (~5 s same-FS vs ~40 s cross-FS) — sourced from the in-repo bench archive at [`benchmarks/uv-on-aqua/`](https://github.com/ZhipengHe/Walltime-Chronicles/tree/main/benchmarks/uv-on-aqua)
- **Three placement patterns** with full setup:
    - (a) Quick start — everything on `/home`
    - (b) Active project — cache + venv on `/scratch` (Weka)
    - (c) Batch jobs — cache + venv on `$TMPDIR`
- **What to leave on `/home`** (uv-managed Python installs, `uv tool install` outputs)
- **Common traps**: mixing cache + venv across filesystems; the `UV_LINK_MODE=symlink` footgun
- **Wider community context**: no `module load uv` on Aqua; the [long-running uv HPC issue #7642](https://github.com/astral-sh/uv/issues/7642); negative-signal coverage at NCI Gadi / Pawsey Setonix / DRAC

[← Back to Lesson 2: Tooling Setup](../tutorials/lesson-2.md)
