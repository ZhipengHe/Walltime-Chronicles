# PBS Brew Inspector: Tasting Notes from Your Job History

> *Or: a user-friendly and informative alternative to `qjobs -x`.*

!!! tip "Companion pages"
    - :material-server-network: [Know Your Nodes](../scheduler/Know-Your-Nodes.md) — the hardware behind each queue (so you know what 100% GPU utilisation *could* look like).
    - :material-timer-sand: [Guess, Request, Regret: The Art of Walltime](../scheduler/The-Art-of-Walltime.md) — turn the efficiency numbers below into smarter walltime requests.
    - :material-school: QUT eResearch — [Basic commands on the HPC](https://docs.eres.qut.edu.au/hpc-basic-command-line#useful-commands-on-the-hpc)[^1] (the source for `qjobs` and friends).

!!! question "Why not use the built-in `qjobs -x` on Aqua?"
    `qjobs -x` ships with Aqua and lists the historical jobs for your user — `qjobs -h` shows the flags. But the output is dense, untyped, and doesn't compute any of the efficiency metrics you actually care about (walltime usage %, CPU saturation, GPU utilisation, memory footprint). This script wraps the same `qstat -H` / `qstat -fx` calls that `qjobs` makes and prints the metrics, the averages, and the takeaways in a single table.

## :material-microscope: What's in Your Computational Brew?

You've been submitting jobs for weeks, crossing your fingers and hoping for the best — but do you actually know what's happening under the hood? Are you wasting resources like a novice chef burning through expensive ingredients, or are you efficiently crafting computational masterpieces?

`pbs_brew_inspector.sh` is your personal sommelier for PBS jobs — swirling, sniffing, and analysing the complex flavours of your computational brews. This script extracts the subtle notes of resource usage and efficiency from your completed jobs, helping you perfect your next batch instead of stumbling around in the dark.

Think of it as your lab notebook for computational experiments, but one that actually tells you the truth about how your recipes performed, what ingredients they consumed, and whether you're a resource efficiency genius or… well, let's find out.

## :material-flask-outline: The Tasting Menu

When you run `pbs_brew_inspector.sh`, you're not just getting a boring list of numbers — you're getting a full sensory analysis of your computational performance. Here's what's on the tasting menu:

- **Walltime Profile:** how long your jobs ran versus how long you requested.
- **CPU Intensity:** single-note or complex multi-core symphonies.
- **Memory Usage:** light and crisp or rich and heavy.
- **GPU Utilisation:** the spicy kick of accelerated computing.
- **Efficiency Metrics:** the perfect balance of resource requests.

## :material-chef-hat: Brewing Instructions

Six single-letter filters; combine them freely (e.g. `-gb` for GPU batch, `-cl` for CPU large-memory). All flags are inclusive — `-c -g` shows everything.

=== ":material-server: -c CPU jobs"

    ```bash
    bash ./pbs_brew_inspector.sh -c
    ```

    Shows every CPU-only job: batch (`cpu_batch_exec`), interactive (`cpu_inter_exec`), large memory (`cpu_batch_exlm`), persistent (`cpu_inter_pers`).

=== ":material-expansion-card: -g GPU jobs"

    ```bash
    bash ./pbs_brew_inspector.sh -g
    ```

    Shows every GPU job: batch (`gpu_batch_exec`) and interactive (`gpu_inter_exec`).

=== ":material-package-variant: -b Batch only"

    ```bash
    bash ./pbs_brew_inspector.sh -b
    ```

    CPU + GPU batch queues only — the bread-and-butter long-running jobs.

=== ":material-monitor-shimmer: -i Interactive"

    ```bash
    bash ./pbs_brew_inspector.sh -i
    ```

    The interactive queues only — short, hand-driven sessions.

=== ":material-database: -l Large memory"

    ```bash
    bash ./pbs_brew_inspector.sh -l
    ```

    The large-memory queue (`cpu_batch_exlm`) only — anything ≥1479 GB / job.

=== ":material-pipe: -p Persistent"

    ```bash
    bash ./pbs_brew_inspector.sh -p
    ```

    The watchdog queue (`cpu_inter_pers`) — 1 CPU / 4 GB / up to 368 h. Useful if you ran orchestration jobs.

=== ":material-account: -U other user"

    ```bash
    bash ./pbs_brew_inspector.sh -U otheruser -gb
    ```

    Inspect another user's history (their permissions allowing). Combine with any of the filter flags above.

### What the table looks like

```text
> bash ./pbs_brew_inspector.sh -gb   # Example output for GPU batch jobs

Resource Usage Report -- $USER @ Wed May 14 02:47:54 PM AEST 2025
================================================================================================================================================================
JobID        Wall_Time   Wall_Limit  CPU_Time    CPU%        Mem(GB)    Mem_Limit  Mem_Use%  GPU_Util% GPU_Mem%   GPUs     CPUs       Nodes    Queue
================================================================================================================================================================
3890***.aqua 01:07:53    48:00:00    02:40:13    295%        2.69       64GB       4.2%      72%       4%         1        8          1        gpu_batch_exec
3890***.aqua 02:04:52    48:00:00    07:35:42    504%        5.48       64GB       8.6%      47%       12%        1        8          1        gpu_batch_exec
3905***.aqua 01:35:54    48:00:00    03:57:29    364%        3.32       64GB       5.2%      58%       8%         1        8          1        gpu_batch_exec
3921***.aqua 20:04:13    24:00:00    21:36:23    160%        11.68      64GB       18.2%     39.7%     28%        1        8          1        gpu_batch_exec
================================================================================================================================================================
AVERAGE      06:13:13    42:00:00    -           330.8%      5.79       -          9.1%      54.2%     13.0%      -        -          -        -

Job Statistics:
--------------
Total Jobs: 4
Jobs with GPU: 4
Jobs CPU-only: 0

Average Resource Efficiency:
  CPU Usage: 330.8%
  Memory Usage: 9.1%
  Walltime Usage: 23.4%

GPU Jobs Metrics (average of 4 GPU jobs):
  GPU Utilisation: 54.2%
  GPU Memory Usage: 13.0%
```

!!! warning "Widen your terminal to see it all!"
    The output table spans over 160 characters — that's pretty wide! To avoid missing any columns, give your terminal a good stretch. Go on, maximise that window — you'll get the full picture, literally.

## :material-chart-line: Reading Your Tasting Notes

Now comes the fun part — decoding what these numbers are actually telling you. Think of this as learning to read the secret language of resource efficiency:

1. **Walltime Efficiency** — In the example above, jobs used only ~**23.4%** of the requested walltime. Cut the next request by 2–3× and the queue will love you back (see [Art of Walltime](../scheduler/The-Art-of-Walltime.md) for the formal recipe).
2. **Memory Utilisation** — **9.1%** of allocated memory means you over-ordered by ~10×. Drop `mem=` to something matching your peak + a small safety margin; smaller requests start sooner.
3. **GPU Utilisation Patterns** — **54.2%** average GPU utilisation is "OK, not great". You're feeding the card half the time and idling the rest — often a data-pipeline / `num_workers` problem rather than a model problem.
4. **CPU Efficiency** — **`CPU% = 330.8%`** on 8 allocated CPUs means ~**3.3 cores worth of CPU time** averaged over the walltime, across all 8. Since PBS allocates whole cores, the realistic next request is **4 ncpus** (round 3.3 up, leaves a little headroom) — same throughput, smaller footprint, faster queue.

!!! info "What `CPU%` actually measures"
    PBS reports `cpupercent` as `(total CPU time used / walltime) × 100`. On a job that pegs all 8 cores for the entire walltime, the number would be 800%. So divide by 100 to get "cores-worth of work averaged over walltime"; round **up** for your next ncpus request because PBS can't allocate fractions.

!!! warning "Job history limitation"
    Due to Aqua's PBS configuration, the script can only extract details of jobs from the **last 96 hours (4 days)**. Older jobs aren't in the history.

    To verify the current job-history retention period (regular users can read this):

    ```bash
    [user@aquarius02 ~]$ qmgr -c "print server job_history_duration"
    #
    # Set server attributes.
    #
    set server job_history_duration = 96:00:00
    ```

## :material-lightbulb-on: Pairing Suggestions

`pbs_brew_inspector.sh` pairs beautifully with:

- :material-timer-sand: [**Guess, Request, Regret: The Art of Walltime**](../scheduler/The-Art-of-Walltime.md) — feed the walltime-usage % into the 2× rule for sharper estimates.
- :material-server-network: [**Know Your Nodes**](../scheduler/Know-Your-Nodes.md) — when CPU% or GPU% looks low, check whether you're on the right hardware tier (an H100 idling at 50% may be wasted on a model that fits in an A100 MIG slice).
- :material-chef-hat: [**Batch-Cooking PBS Scripts**](Batch-Cooking-PBS-Scripts-with-a-Bash-Pan.md) — use these readings to tune the resource block of your next batch.

## :material-tools: Customisation Notes

Like any good recipe, you can customise this tool to your taste:

- Modify the output format for specific metrics you care about
- Add custom calculations for project-specific efficiency metrics
- Filter for specific job-name patterns or time periods
- Export the data for visualisation in your favourite plotting tool

## :material-flag-triangle: The Brew Inspector's Wisdom

The true artisan understands their ingredients. By regularly inspecting your computational brews, you'll develop an intuition for:

- How long similar jobs will take (crucial for walltime estimates)
- Which resources are your bottlenecks
- Where you're wasting computational resources
- How to optimise your code for better efficiency

> **Remember:** Analysing your past jobs isn't just about efficiency — it's about evolving from someone who throws computational ingredients at the wall to see what sticks, into a master chef who knows exactly how much of each resource will create the perfect recipe.

Stop guessing. Start brewing with confidence. Your future self (and your queue priority) will thank you.

## :material-script: Full Recipe of `pbs_brew_inspector.sh`

!!! tip "Download the script directly on the server"
    ```bash
    # by wget
    wget https://raw.githubusercontent.com/ZhipengHe/Walltime-Chronicles/main/docs/pbs-scripts/scripts/pbs_brew_inspector.sh
    # by curl
    curl -O https://raw.githubusercontent.com/ZhipengHe/Walltime-Chronicles/main/docs/pbs-scripts/scripts/pbs_brew_inspector.sh
    ```

    Move the script somewhere on your `PATH` (e.g. `~/bin/`) and make it executable so you can run it as `pbs_brew_inspector.sh` without the `bash ./` prefix:

    ```bash
    chmod +x pbs_brew_inspector.sh
    mv pbs_brew_inspector.sh ~/bin/
    pbs_brew_inspector.sh -gb
    ```

You can also download it from [this link](scripts/pbs_brew_inspector.sh) directly. The full source is below — the embedded copy is pulled from the same file shipped in the repo, so it can't drift out of sync.

???+ note "Click to expand the full script (~310 lines)"

    ```bash title="pbs_brew_inspector.sh"
    --8<-- "docs/pbs-scripts/scripts/pbs_brew_inspector.sh"
    ```

[^1]: Access only in QUT network. Please use VPN to access the documentation when off-campus.
