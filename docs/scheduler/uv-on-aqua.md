# uv on Aqua: Cache + Envs Placement

[uv](https://docs.astral.sh/uv/) is fast on Aqua — when you keep its cache and your virtual environments on the **same filesystem**. Cross-filesystem, uv falls back to slow byte-by-byte copy and prints a warning. This page is the deep-dive companion to [Lesson 2's short version](../tutorials/lesson-2.md#for-uv-users-same-fs-rule): the capability matrix, the empirical evidence, the three placement patterns, the traps, and the wider HPC-community context.

!!! tip "Companion pages"
    - :material-school: [Lesson 2: Tooling Setup](../tutorials/lesson-2.md) — the 14-line operational version of this rule, plus the install + verify flow.
    - :material-flask: [Bench archive](https://github.com/ZhipengHe/Walltime-Chronicles/tree/main/benchmarks/uv-on-aqua) — methodology, harness, and the raw timing data for the numbers below.
    - :material-server-network: [Know Your Nodes — Storage internals](Know-Your-Nodes.md#storage-internals) — the broader filesystem picture (Lustre 5 PB, Weka 1 PB, 30-day scratch sweep).
    - :material-link-variant: [uv cache concepts](https://docs.astral.sh/uv/concepts/cache/) — the upstream doc that names the same-FS rule.

---

## :material-key-variant: The same-FS rule

uv links files from its cache into every virtual environment instead of copying them. Linking only works when **the cache and the venv live on the same filesystem**. Cross-filesystem, uv falls back to slow byte-by-byte copies.

On Aqua, the filesystems you'll touch:

|                       | Lustre `/home` | Weka `/scratch` | Cross-FS |
|-----------------------|:--------------:|:---------------:|:--------:|
| Hardlink (`ln`)       | ✓              | ✓               | ✗ `EXDEV` |
| Reflink / CoW         | ✗              | ✗               | —        |
| Symlink (`ln -s`)     | ✓              | ✓               | ✓        |
| Copy (`cp`)           | ✓              | ✓               | ✓        |

!!! info "How uv chooses"
    On Linux, uv's default link mode is `clone` (copy-on-write). Neither Lustre nor Weka supports CoW, so uv falls back: `clone` → `hardlink` → `copy`. Within one filesystem, hardlink succeeds and install is fast; across filesystems, hardlink fails with `EXDEV` and uv copies byte-for-byte.

That's the whole story. The rest of this page is empirical evidence, copy-pasteable setup for the three sensible placements, and the traps that look like fixes but aren't.

---

## :material-flask: The evidence

Two bench runs on `cpu_batch` nodes, four days apart, different physical hosts (`cpu1n033` and `cpu1n043`). Same workload — 53 packages, ~25k files, ~1.2 GB; identical `uv.lock` sha256. Three cells per run: same-FS Lustre, same-FS Weka, cross-FS Lustre→Weka. Five [hyperfine](https://github.com/sharkdp/hyperfine) reps per cell, randomized execution order.

### Headline: cross-FS is ~8–9× same-FS, both runs

| Cell | 2026-06-25 (`cpu1n033`) | 2026-06-29 (`cpu1n043`) |
|---|:---:|:---:|
| `lustre` cold (median)  | 16.04 s | 13.63 s |
| `weka` cold (median)    | 15.78 s | 15.64 s |
| `crossfs` cold (median) | **53.82 s** | **52.43 s** |
| `lustre` warm (mean)    | 5.94 s | 4.33 s* |
| `weka` warm (mean)      | **4.71 s** | 4.83 s |
| `crossfs` warm (mean)   | **38.61 s** | **40.25 s** |
| Cross-FS / same-FS warm | **~8×** | **~8–9×** |

<!-- markdownlint-disable MD033 -->
<small>\* <em>Archive-2 Lustre warm has one anomalously-fast rep (3.08 s) pulling the mean down; median is 4.49 s — within ~6% of Weka's 4.77 s median.</em></small>
<!-- markdownlint-enable MD033 -->

The cross-FS penalty (~8–9× warm) reproduced cleanly across both runs — that's the rule, empirically. **The same-FS Weka-vs-Lustre gap is small and load-time-dependent**: in the first run Weka edged Lustre by ~20% warm; in the second the medians sat within ~6%. Treat them as equivalent in practice and pick whichever fits your storage strategy.

### Where the cost goes

`uv --verbose` decomposes each install into phases. The relevant ones (single cold rep per cell):

| Cell | Prepared (download + extract) | Installed (link cache → venv) |
|---|:---:|:---:|
| `weka` (archive 1)    | 10.30 s | 5.78 s |
| `lustre` (archive 2)  | 9.43 s  | 4.54 s |
| `crossfs` (archive 2) | 9.59 s  | **42.87 s** ← copy fallback |

"Prepared" is steady across cells (network-dominated). The full cost difference shows up in "Installed" — the link-vs-copy step.

### The filesystem signal

After each install, counting links on the venv:

| Cell | Files | Hardlinks | Ratio | `Failed to hardlink` count |
|---|:---:|:---:|:---:|:---:|
| `lustre` or `weka` (either FS) | 24,990 | 24,797 | **0.9923** | 0 |
| `crossfs` | 24,990 | **0** | 0.0000 | **1** |

Both same-FS cells dedup ~99.2% of files via hardlink. The cross-FS cell has zero hardlinks and prints uv's user-facing warning, verbatim:

```text
warning: Failed to hardlink files; falling back to full copy. This may lead to degraded performance.
         If the cache and target directories are on different filesystems, hardlinking may not be supported.
         If this is intentional, set `export UV_LINK_MODE=copy` or use `--link-mode=copy` to suppress this warning.
```

If you see that line in your own `uv sync` output, hardlinking failed — on Aqua, that almost always means cache and venv are on different filesystems. Confirm with `df $UV_CACHE_DIR` and `df <project>/.venv`.

!!! tip "Reproducing the bench"
    The harness, archives, and re-run instructions are in [`benchmarks/uv-on-aqua/`](https://github.com/ZhipengHe/Walltime-Chronicles/tree/main/benchmarks/uv-on-aqua). One `qsub` line re-runs the whole sweep in about 30 minutes on a `cpu_batch` node.

---

## :material-source-branch: Three placement patterns

Three ways to keep cache and venv on the same filesystem. Pick by where your project lives and how you run it.

| Pattern | Cache | Venv | When to pick |
|---|---|---|---|
| **(a) Quick start** | `~/.cache/uv` | `<project>/.venv` | One-off scripts; ≤1 GB envs; no setup |
| **(b) Active project** ⭐ | `/scratch/$USER/...` | `/scratch/$USER/...` | Active iterative work; ML stacks; daily use |
| **(c) Batch job** | `$TMPDIR/...` | `$TMPDIR/...` | PBS jobs; reproducible install from `uv.lock` |

### :material-laptop: (a) Quick start — everything on `/home`

No setup. Cache lives at `~/.cache/uv`, your project's `.venv` lands on `/home` (Lustre), both same-FS so hardlinks work.

```bash
cd ~/projects/my-project
uv venv && uv sync
```

Fine for occasional or small projects (≤1 GB envs). Lustre handles many-small-files less smoothly than Weka — you'll notice the first install is a touch slower and more time-variable than the Weka equivalent in pattern (b). Upgrade when you start stacking many envs or working with multi-GB scientific stacks.

### :material-flash: (b) Active project — cache + venv both on `/scratch` (Weka) ⭐

The recommended default for everyday work. Weka is fast for many-small-files workloads and `/scratch/$USER` has room for normal use.

Put `UV_CACHE_DIR` on `/scratch` once:

```bash
# Once, in ~/.bashrc:
export UV_CACHE_DIR="/scratch/${USER}/uv/cache"
```

Then either keep the **project itself on `/scratch`** (the venv lands beside it — same FS, no further setup):

```bash
cd /scratch/${USER}/my-project
uv venv && uv sync
```

…or keep the **source on `/home`** (e.g. a git repo you want backed up) and put only the venv on `/scratch`. Two equivalent ways:

```bash
# Option 1 — UV_PROJECT_ENVIRONMENT (uv's native knob)
cd ~/projects/my-project
export UV_PROJECT_ENVIRONMENT="/scratch/${USER}/uv/envs/my-project"
uv sync

# Option 2 — symlink .venv to /scratch (editors and `source .venv/bin/activate` keep working)
cd ~/projects/my-project
mkdir -p /scratch/${USER}/uv/envs/my-project
ln -s /scratch/${USER}/uv/envs/my-project .venv
uv venv && uv sync
```

Both options put the venv on Weka, satisfying the same-FS rule because the cache is also on Weka. Option 1's export only lasts for the current shell, though — see [the `env.sh` pattern](#envsh-pattern) below for making it stick (and for the team-project-on-`/work` variant).

!!! warning "Set a 30-day reminder"
    `/scratch` is purged after **30 days of inactivity** (Aqua's policy, not uv's). Touch `/scratch/${USER}/uv/` monthly, or just rebuild the env from `uv.lock` when you come back. Don't keep anything irreplaceable on scratch.

### :material-rocket-launch: (c) Batch jobs — cache + venv on `$TMPDIR`

Inside a PBS job, the fastest tier is the compute node's `$TMPDIR` (Weka-backed, per-job, auto-cleaned at exit). Cache and venv are both ephemeral by design — you rebuild from `uv.lock` each job.

```bash
# Inside your PBS script:
export UV_CACHE_DIR="$TMPDIR/.uv-cache"
export UV_PROJECT_ENVIRONMENT="$TMPDIR/.venv"
cd /scratch/${USER}/my-project   # or wherever pyproject.toml + uv.lock live
uv sync --frozen                  # exact lockfile install, no resolver
python script.py
# everything in $TMPDIR vanishes when the job ends
```

!!! tip "Why `--frozen`?"
    `uv sync --frozen` installs **exactly** what's in `uv.lock` without re-running the resolver. Deterministic, fast, reproducible across nodes. Commit `uv.lock` to git so this works at all.

This pattern trades cold-install time (~16 s on a fresh node) for cleanliness — the venv vanishes when the job exits, no risk of leaving stale envs behind. Pairs naturally with [Recipe 8's checkpoint chain](Walltime-by-Recipe.md#recipe-8-long-pipeline-with-chained-jobs) when your training run spans multiple PBS stages.

---

## :material-power: Enable + activate in one line — the `env.sh` pattern {#envsh-pattern}

Pattern (b)'s `UV_PROJECT_ENVIRONMENT` export works, but it's an env var you have to re-export **every session** — and there's no way around that: uv has no config-file knob for the venv path. Not in `uv.toml`, not in `pyproject.toml`, and `UV_*` variables in `.env` files don't affect uv itself. The env var is the only interface, and Aqua has no `direnv` to auto-set it per-directory.

The fix: commit a small `env.sh` next to your project and make `source` do everything — set the uv variables *and* activate the venv, so `python` and `jupyter` work directly with no `uv run` prefix.

```bash
# env.sh — commit this next to your pyproject.toml
export UV_CACHE_DIR="/scratch/${USER}/uv/cache"
export UV_PROJECT_ENVIRONMENT="/scratch/${USER}/uv/envs/my-project"

# uv itself (per-user install) — make sure it's on PATH in batch jobs too
case ":${PATH}:" in
    *":${HOME}/.local/bin:"*) ;;
    *) export PATH="${HOME}/.local/bin:${PATH}" ;;
esac

# Activate the venv if this user has installed it already
if [ -f "${UV_PROJECT_ENVIRONMENT}/bin/activate" ]; then
    source "${UV_PROJECT_ENVIRONMENT}/bin/activate"
else
    echo "env.sh: no venv at ${UV_PROJECT_ENVIRONMENT}" >&2
    echo "env.sh: first-time install:  cd <project> && uv sync --frozen" >&2
fi
```

One line, everywhere — interactive shells, PBS job scripts, the terminal you launch Jupyter from:

```bash
source /work/my-team/my-project/env.sh
python train.py                    # venv python, no `uv run` needed
uv add scipy                       # still routes to the scratch venv
deactivate                         # works as usual
```

Because the script exports the uv variables *before* activating, `uv sync` / `uv add` keep targeting the scratch venv even while it's active — you get both interfaces at once.

### Why this shines for team projects on `/work`

`/work` is Lustre, team-writable, and not purged — the right place for shared source. But a shared `.venv` in the project directory would be a mess: one user's `uv sync` clobbers another's, and the venv sits on Lustre while everyone's cache is on Weka (hello, cross-FS trap). The `env.sh` pattern splits it cleanly:

| What | Where | Scope |
|---|---|---|
| `pyproject.toml` + `uv.lock` | `/work/<team>/<project>/` (Lustre) | Team-shared, in git |
| `env.sh` | `/work/<team>/<project>/` (Lustre) | Team-shared, in git |
| uv cache | `/scratch/$USER/uv/cache/` (Weka) | Per-user |
| venv | `/scratch/$USER/uv/envs/<project>/` (Weka) | Per-user |

`$USER` expands at `source` time, so the **same committed file** gives every team member their own Weka venv — same-FS rule satisfied per-user, reproducibility guaranteed by the committed `uv.lock`. A new teammate's onboarding is two lines:

```bash
source /work/<team>/<project>/env.sh   # prints the install hint
cd /work/<team>/<project> && uv sync --frozen
```

The same file works unchanged for a personal project on `/home` — only the venv location in the export changes, the mechanics don't.

!!! tip "Auto-activate when you `cd` in (optional)"
    Don't just export `UV_PROJECT_ENVIRONMENT` globally in `~/.bashrc` — it silently hijacks **every other uv project** you touch into the same venv. If you want hands-free activation, scope it to the project directory with a `PROMPT_COMMAND` hook:

    ```bash
    # ~/.bashrc — poor-man's direnv, scoped to one project tree
    _myproject_uv_env() {
        case "$PWD" in
            /work/my-team/my-project*)
                export UV_PROJECT_ENVIRONMENT="/scratch/$USER/uv/envs/my-project" ;;
            *)
                if [ "${UV_PROJECT_ENVIRONMENT:-}" = "/scratch/$USER/uv/envs/my-project" ]; then
                    unset UV_PROJECT_ENVIRONMENT
                fi ;;
        esac
    }
    PROMPT_COMMAND="_myproject_uv_env${PROMPT_COMMAND:+;$PROMPT_COMMAND}"
    ```

    PBS batch jobs never run `PROMPT_COMMAND` — job scripts still need the explicit `source env.sh` line. That's a feature: the job script documents its own environment.

---

## :material-pin: What to leave on `/home`

Some uv state is **write-once user data**, not cache. Don't redirect it to scratch — the cost of re-downloading after a scratch purge dwarfs the Lustre slowness.

| Path | What lives there | Approx. size |
|---|---|---|
| `~/.local/share/uv/python/` | uv-managed Python installs | ~108 MB per Python version |
| `~/.local/share/uv/tools/` | `uv tool install` outputs | a few MB per tool |
| `~/.config/uv/` | uv's config | < 1 KB |

These are small, persistent, and rebuilt rarely. Leave them on Lustre.

---

## :material-traffic-cone: Common traps

### Mixing `/scratch` cache with `/home` venv (or vice versa)

The biggest footgun. Setting `UV_CACHE_DIR=/scratch/$USER/uv/cache` while leaving your venv at `~/projects/my-project/.venv` puts cache on Weka and venv on Lustre — uv falls back to **cross-filesystem copy mode** (the 8–9× warm-install slowdown shown in the bench evidence above).

The rule is "cache and venv together," not "cache on scratch always." If you switch the cache, switch the venv too (or use the symlink / `UV_PROJECT_ENVIRONMENT` workarounds in pattern (b)).

!!! danger "How to spot this in your own runs"
    Watch for `warning: Failed to hardlink files; falling back to full copy.` in `uv sync` output. That's almost always the cross-FS trap firing — confirm with `df` on the cache and venv paths.

### The "symlink your cache to scratch" advice

If you've read the [QMUL HPC uv tutorial](https://blog.hpc.qmul.ac.uk/uv-tutorial/) you may have seen this:

> You may wish to symlink this location to your scratch if this gets too large.

That reclaims **disk space** but doesn't speed anything up. uv resolves the symlink before linking — if `~/.cache/uv` symlinks to `/scratch/...` while your venv is on `/home`, uv still tries `/scratch/...` → `/home` hardlinks, hits `EXDEV`, falls back to copy. Use the explicit `UV_CACHE_DIR` export in pattern (b) instead; same disk-space outcome, plus actual speed.

### `UV_LINK_MODE=symlink` to "force linking across filesystems"

Symlinks **do** work across filesystems. So why not set `UV_LINK_MODE=symlink` and skip the same-FS rule entirely? Astral's [link-mode docs](https://docs.astral.sh/uv/reference/settings/#link-mode) say no, in bold:

> **WARNING**: The use of symlink link mode is discouraged, as they create tight coupling between the cache and the target environment. For example, clearing the cache (`uv cache clean`) will break all installed packages by way of removing the underlying source files. Use symlinks with caution.

Stick to keeping cache + venv on the same filesystem. The symlink mode is a footgun that turns `uv cache clean` into a fleet-of-broken-envs event.

---

## :material-earth: The wider community

There is **no `module load uv` on Aqua** (`module spider uv` only returns R-package false hits like `ruv`). The uv binary is installed per-user via the [Astral curl installer](https://docs.astral.sh/uv/getting-started/installation/) — that's what Lesson 2's [install step](../tutorials/lesson-2.md#uv-the-default) documents.

This isn't an Aqua oversight. uv's HPC patterns are unsettled across the board:

- **The canonical thread**: [uv issue #7642 — "Using uv on HPC Clusters"](https://github.com/astral-sh/uv/issues/7642) has been open since September 2024 with no Astral resolution. Patterns surfaced there — per-project `UV_PROJECT_ENVIRONMENT`, `.venv` symlinks to scratch, the inode-quota panic on some clusters — are user-contributed workarounds, not vendor guidance.
- **Australian HPC centres**: searches across [NCI Gadi](https://opus.nci.org.au/) docs and [Pawsey Setonix](https://pawsey.atlassian.net/) docs return **zero results for uv** as of mid-2026. Their Python documentation covers `pip` + system modules + conda. Aqua isn't behind here — it's typical.
- **DRAC (Compute Canada)**: an admin commented in the [#7642 thread](https://github.com/astral-sh/uv/issues/7642) that DRAC discussed supporting uv and decided not to — too many `uv run`–related issues for their model.

So: the patterns on this page are derived from primary-source filesystem probes on Aqua and the bench above. They're what works today, not what QUT eResearch or Astral have officially blessed. The same-FS rule itself is in Astral's own [cache concepts doc](https://docs.astral.sh/uv/concepts/cache/) — that part is settled.

---

## :material-arrow-right-circle: Where next

- :material-school: [Lesson 2: Tooling Setup](../tutorials/lesson-2.md) — the operational 14-line version, plus uv / Miniforge / micromamba install flows.
- :material-flask: [Bench archive on GitHub](https://github.com/ZhipengHe/Walltime-Chronicles/tree/main/benchmarks/uv-on-aqua) — full methodology, harness scripts, and the two redacted archives' raw data.
- :material-server-network: [Know Your Nodes — Storage internals](Know-Your-Nodes.md#storage-internals) — the broader Lustre / Weka picture, 30-day scratch sweep, `$TMPDIR` behaviour.
- :material-chef-hat: [Walltime by Recipe — Recipe 8 (chained jobs)](Walltime-by-Recipe.md#recipe-8-long-pipeline-with-chained-jobs) — pairs naturally with pattern (c) when a job exceeds 48 h.
- :material-link-variant: [uv cache concepts (Astral)](https://docs.astral.sh/uv/concepts/cache/) — the upstream doc behind the same-FS rule.
- :material-link-variant: [QUT eResearch — Filesystem and data management](https://docs.eres.qut.edu.au/hpc-filesystem)[^1] — the canonical line on `/home`, `/scratch`, `/work` policy.

[^1]: Access only in QUT network. Please use VPN to access the documentation when off-campus.
