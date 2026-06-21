# Batch-Cooking PBS Scripts with a Bash Pan

!!! tip "Companion pages"
    - :material-microscope: [PBS Brew Inspector](PBS-Brew-Inspector.md) — after the batch runs, use this to read the resource-usage tea leaves and tune the next batch.
    - :material-timer-sand: [Guess, Request, Regret: The Art of Walltime](../scheduler/The-Art-of-Walltime.md) — size the `walltime=` line below from real data instead of from vibes.
    - :material-server-network: [Know Your Nodes](../scheduler/Know-Your-Nodes.md) — pick the GPU tier (H100 / A100 / MIG slice) before you commit to a `gpu_id`.

## :material-pot-mix: What's Cooking?

So, you have multiple experiments, each with their own little quirks, and you want to run them one after another on the HPC without babysitting each one like a helicopter parent hovering over a toddler's first steps? Welcome to **batch-cooking PBS jobs** — where bash scripts are your pan, experiments are the ingredients, and you're the chef who's finally learned to prep everything in advance.

This script is basically a recipe that saves your sanity:

- Grabs a timestamp so your job names never clash (because "job_1" vs "job_1" is a fight nobody wins).
- Prepares a fresh PBS submission script (like meal-prepping but for compute time).
- Sets up your environment (modules + virtualenv, the usual kitchen hygiene).
- Dumps in your experiments, one by one, and gives them a nice little echo wrapper so you can actually read the logs without developing eye strain.
- Submits it all in one go with `qsub` and lets you get on with your life.

**Result:** *one tidy `.pbs` file, logs clearly marked, and no more waking up at 2 a.m. in a cold sweat wondering if you accidentally ran `Example_Experiment_1.sh` twice.*

!!! question "Why not PBS arrays?"
    You might be wondering: "Why not use PBS job arrays instead of this sequential approach?" Fair question — both patterns have their place.

    **Sequential (this recipe) is better when:**

    - **Experiment dependencies** — later experiments need results from earlier ones
    - **Resource sharing** — all experiments share the same loaded environment and data
    - **Simpler debugging** — one log file to rule them all, easier to trace issues
    - **Memory efficiency** — load large datasets once, reuse across experiments
    - **Queue limitations** — some systems limit concurrent array jobs, especially for GPU resources

    **PBS arrays win when:**

    - **True parallelisation** — independent experiments running simultaneously
    - **Fault tolerance** — one failed experiment doesn't kill the others
    - **Resource flexibility** — different experiments need different resources

    Think of it as assembly-line cooking (this method) vs. multiple chefs working simultaneously (PBS arrays).

---

## :material-notebook-edit-outline: How To Customise

Six steps to fit the recipe to your kitchen. Each tab covers one piece of the script you'll most likely want to change.

=== ":material-format-list-bulleted: 1. Ingredients"

    **Selecting your experiments.** Add or remove experiment scripts in the `EXPERIMENTS=(...)` array. This is your tasting menu — change it freely.

    ```bash
    #!/bin/bash

    # List of experiments to run
    # Add or remove experiments by modifying this array
    EXPERIMENTS=(
        "exp_script/Example_Experiment_0.sh"
        "exp_script/Example_Experiment_1.sh"
        "exp_script/Example_Experiment_2.sh"
        # "exp_script/My_New_Experiment.sh"  # Uncomment to add new experiments
        # "path/to/another/experiment.sh"
    )
    ```

=== ":material-tag: 2. Naming"

    **Unique job names so runs don't collide.** A timestamp guarantees uniqueness.

    ```bash
    # Create a unique timestamp once
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    JOB_NAME="task_${TIMESTAMP}"
    PBS_SCRIPT="submit_job_${TIMESTAMP}.pbs"
    ```

    Customisations:

    - Change `task_` to something meaningful like `training_` or `analysis_`
    - Modify the timestamp format by changing `%Y%m%d_%H%M%S`

=== ":material-cog: 3. PBS header"

    **Adjust the directives** to match your computational appetite and resource budget. Hardware ceilings live in [Know Your Nodes](../scheduler/Know-Your-Nodes.md); walltime sizing lives in [Art of Walltime](../scheduler/The-Art-of-Walltime.md).

    ```bash
    # Create PBS script
    cat > ${PBS_SCRIPT} << EOF
    #!/bin/bash
    #PBS -N ${JOB_NAME}
    #PBS -l select=1:ncpus=8:ngpus=1:mem=64GB:gpu_id=H100  # see GPU note below
    #PBS -M $USER@qut.edu.au  # Your QUT email for notifications
    #PBS -l walltime=48:00:00  # Maximum runtime — HH:MM:SS, 48h is the batch cap
    #PBS -q gpu_batch_exec
    #PBS -j oe
    #PBS -m abe  # Mail on abort, begin, end
    #PBS -o ${JOB_NAME}_output.log
    EOF
    ```

    Common modifications:

    - **Resource line.** Adjust `ncpus`, `ngpus`, `mem` per the queue's per-job ceilings.
    - **Walltime.** `48:00:00` is the batch-queue cap. Drop it for shorter runs.
    - **Queue.** `gpu_batch_exec`, `cpu_batch_exec`, `cpu_batch_exlm`, `gpu_inter_exec`, `cpu_inter_exec`, `cpu_inter_pers` — see the queue limits in [Art of Walltime](../scheduler/The-Art-of-Walltime.md).

    !!! info "Pick a `gpu_id` deliberately"
        `gpu_id=H100` targets the H100 hosts (busiest queue, fastest cards). Other valid values from a live `pbsnodes` probe: **`A100`**, **`P100`**, **`MI100`**. For inference or smaller models, an A100 (or even a [MIG slice](../scheduler/Know-Your-Nodes.md) on a `gpu_inter_exec` node) often dispatches sooner than an H100.

=== ":material-package-variant-closed: 4. Environment"

    **Modules + virtualenv** for the compute job. The escapes (`\${...}`) are intentional — they expand on the compute node at runtime, not when this script runs locally.

    ```bash
    # Add environment setup to the PBS script
    cat >> ${PBS_SCRIPT} << EOF
    # Set paths
    WORK_DIR=\${PBS_O_WORKDIR}
    DATASET_DIR=\${WORK_DIR}/dataset

    cd \${PBS_O_WORKDIR}

    # Load required modules
    module load GCCcore/13.3.0
    module load Python/3.12.3
    module load libffi/3.4.5
    module load CUDA/11.8.0

    # Create and activate virtual environment
    python -m venv env
    source env/bin/activate
    python -m pip install -r requirements.txt

    # Run experiments
    cd \${WORK_DIR}
    EOF
    ```

    !!! info "Module versions are pinned, not current"
        The example pins old versions (`CUDA/11.8.0`, `GCCcore/13.3.0`) that the recipe was originally tested against. The current cluster defaults are `CUDA/12.8.0` and `GCCcore/15.2.0`. Pinning is good practice — *unless* your code can use a newer toolchain, in which case `module avail CUDA` (and friends) will show what's available, and `module load CUDA` (no version) grabs the current default.

=== ":material-repeat: 5. Experiment loop"

    **Append each experiment with a header banner.** Makes the resulting log skimmable.

    ```bash
    # Add each experiment to the PBS script
    for exp in "${EXPERIMENTS[@]}"; do
        # Section header
        echo "echo '=============================================='" >> ${PBS_SCRIPT}
        echo "echo 'Running experiment: ${exp}'" >> ${PBS_SCRIPT}
        echo "echo '=============================================='" >> ${PBS_SCRIPT}

        # The experiment command itself
        echo "bash \${WORK_DIR}/scripts/${exp}" >> ${PBS_SCRIPT}

        # Spacer
        echo "echo ''" >> ${PBS_SCRIPT}
        echo "echo '=============================================='" >> ${PBS_SCRIPT}
        echo "echo ''" >> ${PBS_SCRIPT}
    done
    ```

=== ":material-rocket-launch: 6. Submit"

    **Make executable, submit, report.**

    ```bash
    # Make the PBS script executable
    chmod +x ${PBS_SCRIPT}

    # Submit the job
    qsub ${PBS_SCRIPT}

    # Provide helpful feedback to the user
    echo "Job submitted with name: ${JOB_NAME}"
    echo "You can monitor the job using: qstat -u \$USER"
    echo "Output will be saved in: ${JOB_NAME}_output.log"
    ```

    Optional additions:

    - Copy the generated `.pbs` to an archive directory
    - Append the returned job ID to a tracking file
    - Trigger a Slack / email webhook

---

## :material-chef-hat: The Complete Recipe

The script below is single-sourced from `docs/pbs-scripts/scripts/pbs_batch_cook.sh` in this repo — the version you see here is exactly the version you can download.

!!! tip "Download directly on the server"
    ```bash
    # by wget
    wget https://raw.githubusercontent.com/ZhipengHe/Walltime-Chronicles/main/docs/pbs-scripts/scripts/pbs_batch_cook.sh
    # by curl
    curl -O https://raw.githubusercontent.com/ZhipengHe/Walltime-Chronicles/main/docs/pbs-scripts/scripts/pbs_batch_cook.sh
    chmod +x pbs_batch_cook.sh
    ```

    Or download from [this link](scripts/pbs_batch_cook.sh) directly.

???+ note "Click to expand the full script"

    ```bash title="pbs_batch_cook.sh"
    --8<-- "docs/pbs-scripts/scripts/pbs_batch_cook.sh"
    ```

---

## :material-lightbulb-on: Tips from the Bash Kitchen

- :material-text-box-check: **Descriptive script names.** "exp1.sh" and "exp2.sh" are fine, but "exp_doomed_to_fail.sh" will save you time later.
- :material-arrow-decision: **Want parallel instead of sequential?** That's a different recipe — involves GNU `parallel`, PBS job arrays, and possibly a small ritual.
- :material-printer-pos-network: **Always `echo` your steps.** Your future self, debugging at midnight, will thank you.
- :material-currency-usd: **Mind your dollar signs in heredocs.** Escape PBS variables like `\${PBS_O_WORKDIR}` but leave `${TIMESTAMP}` naked. One's for the future (job runtime), one's for right now (script-write time). Like prepping tomorrow's lunch vs. cooking tonight's dinner.

## :material-tools: Troubleshooting Tips

Even the best chefs have kitchen mishaps. Here's how to handle the inevitable disasters:

- **Path Problems** — if experiments aren't running, check that paths in the `EXPERIMENTS` array match your actual directory structure (under `${PBS_O_WORKDIR}/scripts/`).
- **Script Permissions** — give the individual experiment scripts execute permission:

  ```bash
  chmod +x scripts/exp_script/Example_Experiment_*.sh
  ```

- **Dependency Hell** — if experiments have different Python requirements, consider:
    - Separate virtual environments per experiment
    - A unified `requirements.txt` covering everything
    - `pip install -r specific_requirements.txt` inside each experiment script
- **Resource Conflicts** — if experiments need wildly different resources, make separate PBS scripts instead of running them sequentially under a one-size-fits-all header.
- **Inspect after the fact** — once the job finishes, use [PBS Brew Inspector](PBS-Brew-Inspector.md) to see which experiments actually used the resources you asked for.

## :material-application-variable: Environment Variables

Inside each experiment script, these PBS-provided variables are available:

| Variable | What it is |
|---|---|
| `$PBS_O_WORKDIR` | Directory from which the job was submitted |
| `$PBS_JOBID` | The job's unique identifier (e.g. `12345.aqua`) |
| `$PBS_JOBNAME` | The job's name (in this recipe, `task_${TIMESTAMP}`) |
| `$PBS_NODEFILE` | Path to a file listing the nodes assigned to the job |
| `$PBS_QUEUE` | The queue the job is running in |

## :material-fire: Advanced Techniques

Ready to level up your cooking skills?

### Handling failures gracefully

To prevent later experiments from being killed by an earlier crash, wrap each call in an `if`:

```bash
# Add to each experiment loop iteration
echo "if bash \${WORK_DIR}/scripts/${exp}; then" >> ${PBS_SCRIPT}
echo "  echo 'Experiment ${exp} completed successfully'" >> ${PBS_SCRIPT}
echo "else" >> ${PBS_SCRIPT}
echo "  echo 'WARNING: Experiment ${exp} failed with exit code '\$?" >> ${PBS_SCRIPT}
echo "  # Continue anyway" >> ${PBS_SCRIPT}
echo "fi" >> ${PBS_SCRIPT}
```

!!! warning "Why `'\$?` and not `$?`"
    Inside a double-quoted `echo`, `$?` would expand **at script-write time** — when the last command was the previous `echo` (always exit code `0`). Result: the generated PBS script literally contains `exit code 0` regardless of what happened. By closing the single quote and writing `'\$?`, the literal `$?` lands in the PBS script and resolves at *job runtime* to the failed command's actual exit code.

### Experiment status tracking

Collect a SUCCESS/FAILED summary at the end of the job:

```bash
# Before the experiments loop
echo "declare -A experiment_status" >> ${PBS_SCRIPT}

# Inside the loop (replacing the direct bash command)
echo "if bash \${WORK_DIR}/scripts/${exp}; then" >> ${PBS_SCRIPT}
echo "  experiment_status[\"${exp}\"]=\"SUCCESS\"" >> ${PBS_SCRIPT}
echo "else" >> ${PBS_SCRIPT}
echo "  experiment_status[\"${exp}\"]=\"FAILED\"" >> ${PBS_SCRIPT}
echo "fi" >> ${PBS_SCRIPT}

# After the experiments loop
echo "echo '============== EXPERIMENT SUMMARY ==============='" >> ${PBS_SCRIPT}
echo "for exp in \"${EXPERIMENTS[@]}\"; do" >> ${PBS_SCRIPT}
echo "  echo \"\$exp: \${experiment_status[\"\$exp\"]}\"" >> ${PBS_SCRIPT}
echo "done" >> ${PBS_SCRIPT}
echo "echo '================================================'" >> ${PBS_SCRIPT}
```

### Email notifications with results

`#PBS -m abe` already covers abort/begin/end. If you want the contents of the output log in the message body too:

```bash
# Add at the end of the generated PBS script
echo "mail -s \"Job ${JOB_NAME} Complete\" $USER@qut.edu.au < ${JOB_NAME}_output.log" >> ${PBS_SCRIPT}
```

!!! warning "`mail` availability depends on the node"
    `mail(1)` needs a configured MTA. On Aqua compute nodes this isn't guaranteed; if you don't see the result email, stick with the built-in `#PBS -m abe` notifications and review the log file directly. Your mileage may vary by queue and node tier.

---

## :material-food-variant: Happy Cooking

With this script, you can set up a batch of experiments, hit submit, and let the HPC do its thing while you focus on more interesting work — like remembering what sunlight looks like or having conversations with humans instead of error logs.

> **Remember:** A watched pot never boils, and a watched HPC job doesn't finish any faster. But at least with proper logging, you'll know exactly when it fails spectacularly.

After the job finishes, point [PBS Brew Inspector](PBS-Brew-Inspector.md) at the history to see whether you sized the resources right — that's how the next batch gets cheaper.

## :material-egg-easter: Coming Soon

- A version that uses PBS job arrays (aka "batch-cooking with timers").
- Error catching and handling — building on the "Handling failures gracefully" section above.
- Log file management like a pro (or at least, like someone who doesn't `grep` 10 GB files manually).
- Experiment templating — for when you need to run the same experiment with different flavors (parameters).
- Resource optimisation — making sure you're not using a sledgehammer to crack a nut.
