# Aqua Cheatsheet

Replace `<job-id>`, `<username>`, `<name>`, `<pkg>` and `<url>` with your own, brackets included. `ABCDEF1234` stands for your project code.

---

## :material-lan-connect: Connecting

| Command | What it does |
|---|---|
| `ssh <username>@aqua.qut.edu.au` | Log in; needs QUT network or QUT VPN |
| `hostname` | `aquarius01` or `aquarius02` on a login node, `cpu1nNNN` or `gpu1nNNN` on a compute node |
| `tmux new -s <name>` | Start a session that survives a disconnect |
| `tmux attach -t <name>` | Reattach; `Ctrl-b` then `d` detaches |
| `tmux ls` | Sessions on this login node |
| `code tunnel` | VS Code from inside an interactive job; Remote SSH is blocked on Aqua |
| `exit` | Leave a session or an interactive job |

## :material-swap-horizontal: Transferring

| Command | What it does |
|---|---|
| `scp <file> <username>@aqua.qut.edu.au:~/<dir>/` | Copy one file up |
| `scp <username>@aqua.qut.edu.au:~/<file> .` | Copy one file down |
| `rsync -avz ./<dir>/ aqua:~/<dir>/` | Sync a directory, skipping what already matches |
| `rsync -avz --dry-run ./<dir>/ aqua:~/<dir>/` | Show what a sync would do |
| `rsync -avz --exclude='.DS_Store' --exclude='._*' ./<dir>/ aqua:~/<dir>/` | Sync from macOS without Finder's metadata |
| `sftp <username>@aqua.qut.edu.au` | Interactive transfer: `cd`, `get`, `put` |
| `wget -nc <url>` | Download onto Aqua rather than through your laptop |
| `dos2unix <file>` | Fix Windows line endings after transferring a script |

| Endpoint | What it is |
|---|---|
| `eresdtn01.qut.edu.au` | Data transfer node, SFTP, for WinSCP |
| `\\hpc-fs\<username>` | Home, mounted on Windows |
| `\\hpc-fs\work` | Work, mounted on Windows |
| `smb://hpc-fs/<username>` | Home, mounted on macOS |
| `smb://hpc-fs/work` | Work, mounted on macOS |

## :material-console-line: Job commands

| Command | What it does |
|---|---|
| `qsub <script>.pbs` | Submit; prints the job id |
| `qsub -I -l select=... -l walltime=... -P ABCDEF1234` | Interactive job; the shell opens on a compute node |
| `qsub -W depend=afterok:<job-id> <script>.pbs` | Submit, held until that job ends with 0 |
| `qstat -u $USER` | Your queued and running jobs |
| `qstat -xu $USER` | Yours including finished ones |
| `qstat -f <job-id>` | Every attribute of one job |
| `qstat -xf <job-id>` | The same after it finished; kept about four days |
| `qstat -f <job-id> \| grep comment` | Why a queued job has not started |
| `qstat -u $USER -Esw` | Comments for all your queued jobs at once |
| `qstat -T` | Estimated start; top-ranked jobs only, your own only |
| `qstat -t '<job-id>[]'` | Subjobs of an array; add `x` for finished ones |
| `qstat -fw '<job-id>[]' \| grep array_state_count` | An array's tally by state |
| `qstat -Q` | Queues and their totals |
| `qjobs` | eResearch's own summary of your jobs |
| `qdel <job-id>` | Cancel; resets the queue wait the job had earned |
| `qdel '<job-id>[3]'` | Cancel one subjob of an array |
| `qalter -l walltime=04:00:00 <job-id>` | Change a queued job's walltime; users can only lower it |
| `qhold <job-id>` / `qrls <job-id>` | Hold and release your own job |
| `pbsnodeinfo` | Every node's current use |
| `qmgr -c "print server" \| grep job_sort_formula` | The formula that ranks the queue |

## :material-package-variant: Software

| Command | What it does |
|---|---|
| `module spider <name>` | Search for software and its versions |
| `module load <name>/<version>` | Load an exact version |
| `module list` | What is loaded now |
| `module purge` | Unload everything |
| `uv init --bare --pin-python --python 3.13` | New project: `pyproject.toml` and `.python-version` |
| `uv add <pkg>` | Add a dependency; updates `uv.lock` and installs |
| `uv sync --frozen` | Rebuild `.venv` exactly as `uv.lock` says |
| `uv run <command>` | Run inside the project environment, no activation |
| `conda init` | Once, after installing Miniforge, then open a new shell |
| `apptainer pull docker://<image>` | Fetch a container image |
| `apptainer exec <image>.sif <command>` | Run one command inside it |
| `apptainer shell <image>.sif` | Open a shell inside it |

---

## :material-format-list-checks: Directives

| Directive | Effect |
|---|---|
| `#PBS -N <name>` | Job name, and the prefix of the log files |
| `#PBS -l select=1:ncpus=4:mem=8GB` | Resources, per chunk |
| `#PBS -l walltime=01:00:00` | Hard limit; PBS kills the job at it |
| `#PBS -l place=pack` | Chunks on one node; `scatter` spreads them, `group=cpu_id` keeps one CPU kind |
| `#PBS -P ABCDEF1234` | Project code |
| `#PBS -m abe` | Mail on begin, end and abort |
| `#PBS -M <address>` | Send that mail somewhere other than the default |
| `#PBS -j oe` | One log file instead of `.o` and `.e` |
| `#PBS -J 1-8` | Array of 8 subjobs; `1-100:2` steps, `1-100%10` caps how many run |
| `#PBS -c w=30` | Requeue at the walltime; `USR1` to the shell about every 30 minutes |
| `-W depend=afterok:<job-id>` | As a `#PBS` line with a literal id; on the command line when the id is in a variable |

## :material-tune-variant: The select line

| Part | Values on Aqua |
|---|---|
| `select=<n>` | Chunks; `ncpus` and `mem` are per chunk, not totals |
| `ncpus=<n>` | Cores |
| `mem=<n>GB` | Memory, always with a unit |
| `ngpus=<n>` | GPUs, or MIG slices on an interactive queue |
| `gpu_id=` | `H100`, `A100`, or omit for either |
| `cpu_id=` | `any`, `AMD-25-17`, `AMD-25-1`, `AMD-23-49`, `Intel-6-143` |
| `mpiprocs=<n>` | MPI ranks per chunk |
| `+` | Not supported on Aqua |

## :material-server: Queues

| Queue | Walltime | Memory | Cores | GPUs |
|---|---|---|---|---|
| `cpu_batch_exec` | 10 min to 48 h | 1 GB to 16384 GB | 1 to 2048 | — |
| `cpu_inter_exec` | 10 min to 12 h | 1 GB to 34 GB | 1 to 8 | — |
| `gpu_batch_exec` | 10 min to 48 h | 1 GB to 1920 GB | 1 to 256 | 1 to 8 |
| `gpu_inter_exec` | 10 min to 12 h | 1 GB to 68 GB | 1 to 12 | 1 to 2 |
| `cpu_batch_exlm` | 10 min to 48 h | 1479 GB to 6015 GB | 1 to 180 | — |

| You ask for | PBS routes it to |
|---|---|
| `-I` | An interactive queue |
| `mem` above 1.5 TB | `cpu_batch_exlm` |
| `ngpus` of 1 or more | A GPU queue |
| Anything else | `cpu_batch_exec` |

Interactive limits apply across all of your interactive jobs at once, not per job.

## :material-chip: Nodes

| Tier | Hostnames | Cores | RAM | GPUs |
|---|---|---|---|---|
| CPU batch | `cpu1n002` to `cpu1n050` | 188 | 1478 GB | — |
| CPU interactive | `cpu1n001` | 376 logical | 1478 GB | — |
| Large memory | `mem1n001` | 180 | 6014 GB | — |
| GPU H100 batch | `gpu1n002` to `gpu1n014` | 168 | 974 GB | 4 × H100 80 GB |
| GPU A100 batch | 5 nodes | 120 to 124 | 974 GB | 8 × A100 40 GB |
| GPU interactive | 2 nodes | 168 / 124 | 974 GB | 44 MIG slices |

One GPU's fair share of its host is about 42 cores and 240 GB on an H100, about 15 cores and 120 GB on an A100.

## :material-folder-network: Filesystems

| Path | Backed up | Speed | For |
|---|---|---|---|
| `/home/$USER` | Yes | Good | Scripts, configs, small personal data |
| `/scratch/$USER/` | No; swept after 30 days idle | Ultra-fast | Active analysis, heavy reads and writes |
| `/work/<project>/` | Yes | Good | Shared project data; requested by ticket |
| `/work/datasets/` | Yes | Good | Datasets shared across the cluster |
| `$TMPDIR` | No; deleted with the job | Ultra-fast | Per-job intermediates, copied back before the end |

Millions of small files in `/home` slow Lustre for everyone; unpack and build on `/scratch`.

## :material-application-variable: Environment variables

| Variable | Holds |
|---|---|
| `$PBS_O_WORKDIR` | The directory `qsub` ran in |
| `$PBS_JOBID` | This job's id |
| `$PBS_JOBNAME` | The `-N` name |
| `$NCPUS` | Cores PBS gave the job |
| `$TMPDIR` | This job's scratch directory |
| `$CUDA_VISIBLE_DEVICES` | The GPUs PBS gave the job |
| `$PBS_ARRAY_INDEX` | This subjob's index |
| `$PBS_ARRAY_ID` | The parent array's id |
| `$PBS_NODEFILE` | File listing the nodes the job is running on |
| `$PBS_QUEUE` | The queue PBS routed the job to |
| `$OMP_NUM_THREADS` | Threads per process, if you set it |

---

## :material-state-machine: Job states

| State | Meaning |
|---|---|
| `Q` | Queued, waiting to run |
| `R` | Running |
| `H` | Held: by `qhold`, by a dependency, or by PBS after repeated failures |
| `B` | An array with at least one subjob started |
| `E` | Exiting after running |
| `F` | Finished, whether it succeeded, failed or was deleted |
| `S` | Suspended by PBS |
| `M` | Moved to another server |
| `T` | In transition |
| `W` | Waiting for a `-a` start time |

## :material-exit-run: Exit statuses

| Status | Meaning |
|---|---|
| `0` | The last command succeeded; read `.e` anyway |
| `1`, `2` | Your program failed; the end of `.e` says why |
| `-18` | Aqua's checkpoint hook requeued it at the walltime; expected with `-c` |
| `-20` | The node failed; PBS queued the job again |
| `-29` | PBS stopped it at the walltime |
| `137` | PBS stopped it at the memory limit |
| `143` | Someone ran `qdel` |

## :material-comment-alert: Queue comments

| Comment | Meaning |
|---|---|
| `Insufficient amount of resource: ncpus` / `mem` / `ngpus` | Nothing that size is free yet; wait, or ask for less |
| `Insufficient amount of resource: qlist` | No node tagged for your queue had room this cycle |
| `Queue gpu per-user limit reached on resource ngpus` | Your own running jobs hold the per-user GPUs |
| `Job would cross dedicated time boundary` | It would still be running at the next maintenance window |
| `Queue long job limit has been reached` | Too many of your jobs in the long queue |
| `Scheduler user rate limit. Deferring until next scheduler run` | You submitted faster than the scheduler accepts |
| `Can Never Run: Insufficient amount of server resource` | A licence the software needs is not free |
| `Job held, too many failed attempts to run` | PBS failed to start it repeatedly; you cannot release this one |

## :material-close-octagon: Rejected at submission

| Message | Cause |
|---|---|
| `Illegal attribute or resource value select.mem` | Memory missing a unit, in the wrong unit, or negative |
| `Illegal attribute or resource value Resource_List.ncpus` | Something wrong with `ncpus` or its `select` line |
| `You cannot explicitly request 0 gpus when specifying gpu_id` | Naming a `gpu_id` means asking for at least one GPU |
| `cpu_id=... must be one of {...}` | Not a `cpu_id` Aqua has; the message lists the set |
| `ROUTER: Unable to initialise node` | `+` used in the `select` line |

## :material-bug: Failed while running

| Message | Cause |
|---|---|
| `bad interpreter: No such file or directory` | Windows line endings; run `dos2unix` |
| `module: command not found` | Shebang missing, misspelled, or with a blank line above it; use `#!/bin/bash -l` |
| `conda: command not found` | Inspect the shell's conda initialization and merge the required setup into the existing configuration. Preserve customizations; back up `.bashrc` and obtain explicit approval before any overwrite. |
| `Lmod has detected the following error` | No such module name or version; check `module spider` |
| `Bus error (core dumped)` | Touched memory it was not given; raise `mem` |
| `Illegal instruction` | Self-compiled software whose vector instructions this node lacks |
| `installed in '/home/<username>/.local/bin' which is not on PATH` | Add that directory to `PATH` in `.bashrc` |

---

## :material-file-code: Templates

### Batch job

One program, run unattended, with the job's own record kept beside the output.

```bash
#!/bin/bash
#PBS -N my_job
#PBS -l select=1:ncpus=4:mem=8GB
#PBS -l walltime=01:00:00
#PBS -P ABCDEF1234
#PBS -m abe
set -e
cd "$PBS_O_WORKDIR"
status=0
uv run python my_program.py || status=$?
qstat -xf "$PBS_JOBID" > "resource_usage_$PBS_JOBID" || echo "Warning: job accounting could not be saved" >&2
exit "$status"
```

For a GPU: `#PBS -l select=1:ncpus=12:ngpus=1:mem=64GB:gpu_id=H100`

### Array

One script, many runs. The index picks each run's input and output. A rerun skips a member only when its final output and completion marker both exist.

```bash
#PBS -J 1-8
```

```bash
set -e
mkdir -p results
out="results/run_${PBS_ARRAY_INDEX}.nc"
[ -f "$out" ] && [ -f "${out}.done" ] && exit 0
partial="results/run_${PBS_ARRAY_INDEX}.partial_${PBS_JOBID}.nc"
uv run python my_program.py --seed "$PBS_ARRAY_INDEX" --out "$partial"
test -s "$partial"
mv -- "$partial" "$out"
touch "${out}.done"
```

This assumes the program exits successfully only after completing and validating its work; the nonempty-file check alone does not validate scientific results. It writes to a temporary path on the same filesystem, publishes the final file only after success, and then creates the marker. Failed runs retain their partial file for diagnosis. Reuse markers only for retries with unchanged inputs and configuration, use a new results directory for changed work, and avoid concurrent executions of the same member.

| Turning the index into work | |
|---|---|
| `f=$(sed -n "${PBS_ARRAY_INDEX}p" files.txt)` | A file from a list |
| `args=$(sed -n "${PBS_ARRAY_INDEX}p" settings.txt)` | A row of settings |
| `from=$(( (PBS_ARRAY_INDEX - 1) * 10 + 1 ))` | A slice of ten |

### Chained jobs

Stages that must happen in order, each submitted now but starting only when the one before it ends.

```bash
A=$(qsub stage_a.pbs)
qsub -W depend=afterok:$A stage_b.pbs     # only if A ends with 0
qsub -W depend=afterany:$A report.pbs     # when A ends, either way
```

A dependent job sits in `H` until its condition is met, and the server deletes it if the condition can never be met.

### Checkpointed job

Work that outlives one walltime. PBS takes the job back at the limit and runs the script again, so the program has to resume itself.

```bash
#!/bin/bash
#PBS -N my_job
#PBS -l select=1:ncpus=2:mem=1GB
#PBS -l walltime=48:00:00
#PBS -P ABCDEF1234
#PBS -c w=30
#PBS -m abe
cd "$PBS_O_WORKDIR"
trap 'echo "USR1 $(date +%T)"' USR1
trap 'echo "USR2 $(date +%T)"' USR2
uv run python my_program.py --checkpoints checkpoints
```

PBS requeues at the walltime and runs the script again from the top, up to 21 attempts. The program must save as it goes, resume from its own checkpoint, and aim at a total rather than a duration.

---

## :material-tune: Sizing the next request

| Command | What it does |
|---|---|
| `grep -A3 "PBS Job" <name>.o*` | CPU time, wall time and memory of a finished job |
| `qstat -xf <job-id> \| grep -E "resources_used\|Resource_List"` | Used against requested |

| Line | CPU job | GPU job |
|---|---|---|
| `walltime` | Used plus room; never under 10 minutes | Same |
| `ncpus` | CPU Usage % × cores requested, rounded up | Generous, up to one GPU's share |
| `mem` | Memory Usage Max plus room | Generous, up to one GPU's share |
| Healthy | Both gauges near 80% | GPU Usage unchanged; low core and memory gauges normal |

---

## :material-link-variant: Elsewhere

| Resource | Where |
|---|---|
| Job gauges, per job | [HPC Monitoring Dashboard](https://hpc-monitoring.eres.qut.edu.au)[^1] |
| Notebooks, managed | [QUT JupyterHub](https://jupyterhub.eres.qut.edu.au)[^1] |
| Official documentation | [QUT eResearch docs](https://docs.eres.qut.edu.au/about-aqua)[^1] |
| Tickets: a shared `/work` folder, or anything broken | [eResearch Help Centre](http://qut.to/eresearch-support) |
| Wording to credit eResearch in papers | [Acknowledgements in papers](https://docs.eres.qut.edu.au/acknowledgements-in-papers)[^1] |

[^1]: Access only in QUT network. Please use VPN to access the documentation when off-campus.
