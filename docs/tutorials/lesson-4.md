# Lesson 4: Your First Batch Job

!!! quote "Mission Statement"
    *"Write down what you want, hand it to PBS, and go do something else."* 📬

Lesson 3 ended on a question: am I waiting on the machine, or is it waiting on me? This lesson is for the work where nobody should be waiting at all. The request and the commands go into a file, PBS runs that file on a compute node whenever one is free, and the results are there when you come back. First a five-line script that shows what a job actually sees, then a film recommender trained on 32 million real ratings, on a GPU, with nobody watching.

## 📋 What You'll Accomplish

By the end of this 15–20 minute lesson, you'll have:

- [ ] **Written a job script** — `#PBS` lines for the request, ordinary shell for the work
- [ ] **Submitted it and found it again** — `qsub`, `qstat`, and the log files it leaves behind
- [ ] **Seen what a job's shell starts with** — and why every real script begins with `cd` and runs through its project
- [ ] **Trained a recommender on a GPU with nobody watching** — results in files, logs beside them
- [ ] **Taken a job back** — `qdel`, for the one you did not mean to send

!!! info "You need Lessons 2 and 3"
    Everything below assumes the `~/hello-aqua` project from [Lesson 2](lesson-2.md), with PyTorch added in [Lesson 3](lesson-3.md), and that `qsub -I` feels familiar.

---

## 📄 Part 1: From session to script (~4 min)

### Step 1: Put the request in a file

In Lesson 3 you typed the request after `qsub -I` and PBS gave you a shell. A batch job asks for the same things, written at the top of a file instead:

=== "Lesson 3: typed"
    ```bash
    qsub -I -l select=1:ncpus=4:mem=8GB -l walltime=01:00:00
    ```

=== "Lesson 4: in a file"
    ```bash
    #PBS -l select=1:ncpus=4:mem=8GB
    #PBS -l walltime=01:00:00
    ```

Same resources, same syntax. The only thing that changed is where the request lives.

!!! info "What a PBS script is"
    A PBS script is an ordinary shell script with a header. Lines that start with `#PBS` are instructions to PBS: what to call the job, how much to give it, when to email you. PBS reads them when you run `qsub`. The shell skips them as comments, then runs everything below on the compute node, top to bottom.

    The five lines in the next step are all a first job needs.

??? info "Other `#PBS` directives"
    | Directive | What it does |
    |---|---|
    | `-N name` | Job name; also names the `.o` and `.e` log files |
    | `-l select=N:ncpus=C:mem=M[:ngpus=G]` | Resources: chunks, cores, memory, GPUs |
    | `-l walltime=hh:mm:ss` | Maximum run time before PBS stops the job |
    | `-l place=scatter` | Spread chunks across different nodes |
    | `-q queue` | Submit to a named queue instead of letting PBS route the job |
    | `-m abe` | Email on abort, begin and end (`n` for none) |
    | `-M address` | Where that email goes |
    | `-o path`, `-e path` | Where the output and error logs are written |
    | `-j oe` | Join the error log into the output log |
    | `-v VAR=value` | Pass an environment variable into the job |
    | `-J 1-N` | Job array: N copies, each with its own `$PBS_ARRAY_INDEX` |
    | `-W depend=afterok:jobid` | Start only after another job finishes successfully |
    | `-c w=N` | Checkpoint every N minutes |
    | `-r y` / `-r n` | Whether PBS may rerun the job after a node failure |

    Every directive also works as an option on the `qsub` command line. `man qsub` on Aqua lists the full set.

### Step 2: Write the first script

This one does no real work. It asks for one core for five minutes and reports what the job can see, which turns out to be the most useful thing a first job can do. On the login node:

```bash
mkdir -p ~/hello-aqua/jobs && cd ~/hello-aqua/jobs
nano first.pbs
```

```bash title="first.pbs"
#!/bin/bash
#PBS -N first
#PBS -l select=1:ncpus=1:mem=1GB
#PBS -l walltime=00:05:00
#PBS -m abe

echo "host      $(hostname)"
echo "pwd       $(pwd)"
echo "workdir   $PBS_O_WORKDIR"
echo "python    $(which python 2>&1)"
echo "cores     $NCPUS"
```

!!! note "Command breakdown"
    - `#!/bin/bash` → the shell that runs the body
    - `-N first` → the job's name in `qstat`, and the start of its log file names
    - `-l select=...`, `-l walltime=...` → the request, exactly as in Lesson 3
    - `-m abe` → email when the job **a**borts, **b**egins and **e**nds
    - everything after the header → runs on the compute node, top to bottom

!!! warning "`#PBS` lines are not shell"
    PBS reads them before any shell exists, so shell variables inside them are not expanded: `#PBS -N job_$USER` names the job, literally, `job_$USER`.

### Step 3: Submit it and look

```bash
qsub first.pbs
```

!!! example "Expected output"
    ```text
    12345678.aqua
    ```

That line is the job ID, and `qsub` has already returned: the job is PBS's problem now, not your terminal's. Check on it:

```bash
qstat -u $USER
```

!!! example "Expected output"
    ```text
    aqua:
                                                                     Req'd  Req'd   Elap
    Job ID               Username Queue    Jobname    SessID NDS TSK Memory Time  S Time
    -------------------- -------- -------- ---------- ------ --- --- ------ ----- - -----
    12345678.aqua        your-us* cpu_bat* first         --    1   1    1gb 00:05 Q   --
    ```

`S` is the state: `Q` while it waits for a node, `R` while it runs. Even a five-minute, one-core job can sit in `Q` for a few minutes when the batch queue is busy; this one waited four and then ran for one second. Once it finishes it drops off this list, and two new files appear next to the script:

```bash
ls
```

!!! example "Expected output"
    ```text
    first.e12345678  first.o12345678  first.pbs
    ```

### Step 4: Read what the job saw

```bash
cat first.o*
```

!!! example "Expected output"
    ```text
    host      cpu1n047
    pwd       /mnt/hpccs01/home/your-username
    workdir   /mnt/hpccs01/home/your-username/hello-aqua/jobs
    python    /bin/python
    cores     1

    PBS Job 12345678.aqua
    CPU time         : 00:00:00
    Wall time        : 00:00:01
    Mem usage        : 0kb

    --- Job Runtime Information at ...
    (about thirty more lines: the job's full record)
    ```

The first five lines are the script's. Three of them are worth a second look:

1. **`pwd` is your home directory**, not `~/hello-aqua/jobs` where you ran `qsub`. Every job starts at home. (The path looks long because `/home` on Aqua is a shortcut to `/mnt/hpccs01/home`.)
2. **`python` is the system one**, `/bin/python`, which is Python 3.9, not your project's 3.13. A job's shell has nothing activated, whatever your own shell had.
3. **`workdir` is where you submitted from.** PBS remembers it in `$PBS_O_WORKDIR`, precisely so the script can go back there.

!!! info "The summary under your output"
    Everything from `PBS Job` down is added by Aqua, not by your script: CPU time, wall time and memory the job used, then its full record (request, node, paths, exit status). Every `.o` file ends this way. Your own output is always above it. The `.e` file is there too, empty, because nothing went to standard error.

That is why every real job script starts with the same two moves: `cd "$PBS_O_WORKDIR"`, and run the program through its project.

---

## 🎬 Part 2: Train a recommender on a GPU, unattended (~8 min)

### Step 1: What the job does

[MovieLens](https://grouplens.org/datasets/movielens/) is a public collection of film ratings that people gave on a real website; the `ml-32m` release holds 32 million of them. The job trains a **matrix factorisation** recommender, the method every recommender course starts with: each user and each film gets a short list of numbers, and a user's predicted rating for a film comes from multiplying the two lists together. Training nudges those numbers until the predictions match the ratings people actually gave. Ten percent of the ratings are held back to measure how far off it is, and at the end it writes the ten best films that each of the first 1,000 users has not rated yet.

Each training step looks up and multiplies tens of thousands of those number lists at once, which is exactly the work a GPU is built for.

### Step 2: Prepare the project on the login node

Everything that needs the network happens here, before the job: the GPU build of PyTorch, the script, and the data.

**Point PyTorch at the GPU build.** Lesson 3 told `~/hello-aqua` to take PyTorch from the CPU-only index. In `~/hello-aqua/pyproject.toml`, change that index to the CUDA build, so the two blocks read:

```toml
[[tool.uv.index]]
name = "pytorch-cu130"
url = "https://download.pytorch.org/whl/cu130"
explicit = true

[tool.uv.sources]
torch = { index = "pytorch-cu130" }
```

```bash
cd ~/hello-aqua
uv sync
```

!!! example "Expected output"
    ```text
    Resolved 35 packages in 424ms
    Prepared 20 packages in 33.05s
    Uninstalled 1 package in 4.72s
    Installed 20 packages in 6.22s
     + cuda-bindings==13.4.1
     + cuda-pathfinder==1.8.1
     + cuda-toolkit==13.0.3.0
     + nvidia-cublas==13.1.1.3
     + nvidia-cuda-cupti==13.0.85
     + nvidia-cuda-nvrtc==13.0.88
     + nvidia-cuda-runtime==13.0.96
     + nvidia-cudnn-cu13==9.24.0.43
     + nvidia-cufft==12.0.0.61
     + nvidia-cufile==1.15.1.6
     + nvidia-curand==10.4.0.35
     + nvidia-cusolver==12.0.4.66
     + nvidia-cusparse==12.6.3.3
     + nvidia-cusparselt-cu13==0.8.1
     + nvidia-nccl-cu13==2.30.7
     + nvidia-nvjitlink==13.4.52
     + nvidia-nvshmem-cu13==3.4.5
     + nvidia-nvtx==13.0.85
     - torch==2.14.0+cpu
     + torch==2.14.0+cu130
     + triton==3.8.0
    ```

`uv sync` notices the new index, locks the CUDA build in `uv.lock`, and swaps it in: out goes `torch==2.14.0+cpu`, in comes `torch==2.14.0+cu130` with the CUDA libraries it brings along. It takes under a minute, and the environment grows to about 5 GB. pandas, already here from Lesson 2, stays as it is.

**Fetch the script and the data.**

```bash
wget https://raw.githubusercontent.com/ZhipengHe/Walltime-Chronicles/main/docs/tutorials/scripts/movielens_recommender.py

# --epochs 0 downloads and unpacks MovieLens, then exits. Once only.
uv run python movielens_recommender.py --epochs 0
```

!!! example "Expected output"
    ```text
    host      aquarius01
    device    cpu  threads 1  seed 0
    download  https://huggingface.co/datasets/nasserCha/movielens_ratings_32m/resolve/main/ratings.csv
    checked   ratings.csv  matches GroupLens's checksum
    download  https://huggingface.co/datasets/nasserCha/movielens_ratings_32m/resolve/main/movies.csv
    checked   movies.csv  matches GroupLens's checksum
    done      data ready in data/movielens/ml-32m; nothing trained (--epochs 0)
    ```

About a minute and 880 MB later, the data is in `~/hello-aqua/data/movielens/ml-32m/`.

!!! info "Where the data comes from"
    MovieLens 32M is published by [GroupLens](https://grouplens.org/datasets/movielens/32m/), a research lab at the University of Minnesota. Its licence allows research use, not commercial use, and asks that publications cite it; the full terms are in the dataset's README, linked from that page. The script downloads the two files it needs from a copy on Hugging Face and checks each one against the checksum GroupLens publishes, so a damaged or altered copy is refused.

[Download the script](scripts/movielens_recommender.py), or read it here:

??? example "`movielens_recommender.py`"

    ```python title="movielens_recommender.py"
    --8<-- "docs/tutorials/scripts/movielens_recommender.py"
    ```

### Step 3: Write the job script

```bash title="~/hello-aqua/movielens_recommender.pbs"
#!/bin/bash
#PBS -N movielens_recommender
#PBS -l select=1:ncpus=4:ngpus=1:mem=16GB
#PBS -l walltime=00:05:00
#PBS -m abe

cd "$PBS_O_WORKDIR"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
uv run python movielens_recommender.py
```

!!! note "Command breakdown"
    - `ngpus=1` → one GPU, which sends the job to the GPU batch queue. Batch jobs get a **whole card**, not the MIG slices of Lesson 3's interactive queue: whichever A100 or H100 is free, unless you add `:gpu_id=H100` or `:gpu_id=A100` to choose
    - `cd "$PBS_O_WORKDIR"` → back to `~/hello-aqua`, where the project, the script and the data are
    - `nvidia-smi ...` → one line in the log saying which card PBS handed you
    - `uv run python ...` → runs the script through the project, so it gets the CUDA build of PyTorch from `uv.lock`, not the system Python Part 1 found

PBS also sets `CUDA_VISIBLE_DEVICES`, so the program sees only its own card, even on a node that has eight.

!!! note "Where the numbers came from"
    Generous on purpose for a first job: the run below used about 3 GB of its 16 GB and under 30 seconds of its 5 minutes. Asking for less gets a job started sooner and leaves the rest for everyone else; how to trim a request from what a job used is [Lesson 6](lesson-6.md).

### Step 4: Submit and walk away

```bash
qsub movielens_recommender.pbs
```

That is the whole ceremony. The job no longer needs your connection: log out, lose the Wi-Fi, close the laptop, and it carries on. Your `tmux` session from Lesson 3 is still the right place to edit, submit and check on it.

!!! warning "GPU jobs can wait"
    Whole GPUs are the most wanted thing on Aqua, so a GPU batch job can sit in `Q` for a while when the cards are busy. One GPU and a short walltime are the easiest request to fit in; the begin email tells you when it has started.

!!! info "The emails"
    `-m abe` needs no address: without an `-M` line, PBS still mails you, from `root <eresearch@qut.edu.au>`, with the subject `PBS JOB <job-id>`. The begin email is short; the end email carries the exit status and what the job used:

    ```text
    PBS Job Id: 12345678.aqua
    Job Name:   movielens_recommender
    Execution terminated
    Exit_status=0
    resources_used.cpupercent=...
    resources_used.mem=...
    resources_used.ngpus=1
    resources_used.walltime=...
    ```

    `Exit_status=0` means the script finished without an error. Anything else is [Lesson 5](lesson-5.md)'s business.

### Step 5: Read the results

When the end email arrives:

```bash
ls
```

!!! example "Expected output"
    ```text
    data
    jobs
    movielens_recommender.e12345679
    movielens_recommender.o12345679
    movielens_recommender.pbs
    movielens_recommender.py
    pyproject.toml
    recommendations.csv
    results.json
    uv.lock
    ```

The recommendations:

```bash
head -11 recommendations.csv
```

!!! example "Expected output"
    ```text
    userId,rank,title,predicted_rating
    1,1,Safe (1995),4.7
    1,2,"Aguirre: The Wrath of God (Aguirre, der Zorn Gottes) (1972)",4.69
    1,3,Beauty and the Beast (La belle et la bête) (1946),4.68
    1,4,"Conformist, The (Conformista, Il) (1970)",4.65
    1,5,Double Indemnity (1944),4.64
    1,6,His Girl Friday (1940),4.64
    1,7,"Bride of Frankenstein, The (Bride of Frankenstein) (1935)",4.62
    1,8,Tokyo Story (Tôkyô monogatari) (1953),4.61
    1,9,"Passion of Joan of Arc, The (Passion de Jeanne d'Arc, La) (1928)",4.58
    1,10,Twin Peaks (1989),4.58
    ```

The summary:

```bash
cat results.json
```

!!! example "Expected output"
    ```json
    {
      "ratings": 32000204,
      "dim": 64,
      "reg": 0.05,
      "epochs": 5,
      "device": "cuda",
      "gpu": "NVIDIA H100 80GB HBM3",
      "threads": 4,
      "seed": 0,
      "test_rmse": 0.7739,
      "elapsed_s": 14.4,
      "peak_rss_mb": 3113,
      "peak_gpu_mb": 2441,
      "job_id": "12345679.aqua"
    }
    ```

`test_rmse` is how far off the predictions were, in stars, on ratings the model never saw. `gpu`, `elapsed_s`, `peak_rss_mb` and `peak_gpu_mb` say what the job used, which is where Lesson 6 starts.

And the log:

```bash
cat movielens_recommender.o*
```

!!! example "Expected output"
    ```text
    name, memory.total [MiB], driver_version
    NVIDIA H100 80GB HBM3, 81559 MiB, 580.178.04
    host      gpu1n014
    device    cuda (NVIDIA H100 80GB HBM3)  threads 4  seed 0
    data      32,000,204 ratings, 200,948 users, 84,432 films
    epoch   1/5  train RMSE 0.8096  test RMSE 0.8141     0.9s
    epoch   2/5  train RMSE 0.7929  test RMSE 0.7928     0.7s
    epoch   3/5  train RMSE 0.7688  test RMSE 0.7830     0.7s
    epoch   4/5  train RMSE 0.7565  test RMSE 0.7774     0.7s
    epoch   5/5  train RMSE 0.7462  test RMSE 0.7739     0.7s
    wrote     top 10 films for 1,000 users -> recommendations.csv
    done      test RMSE 0.7739  in 14.4s  -> results.json

    PBS Job 12345679.aqua
    CPU time         : 00:00:18
    Wall time        : 00:00:27
    Mem usage        : 1255568kb

    --- Job Runtime Information at ...
    ```

!!! tip "Results go in files; logs are logs"
    Nobody reads a batch job's screen, so a batch program should write what it produces to files it names, like `recommendations.csv` and `results.json`. The `.o` and `.e` files are for progress and errors. A program that only prints its answer leaves that answer in a file named after a job ID.

---

## 🧭 Part 3: Keeping track, and taking one back (~3 min)

### Step 1: Jobs in the queue, and jobs that are done

`qstat -u $USER` lists your jobs that are waiting or running. Finished jobs drop off it, but PBS remembers them:

```bash
qstat -xu $USER
```

!!! example "Expected output"
    ```text
    aqua:
                                                                     Req'd  Req'd   Elap
    Job ID               Username Queue    Jobname    SessID NDS TSK Memory Time  S Time
    -------------------- -------- -------- ---------- ------ --- --- ------ ----- - -----
    12345678.aqua        your-us* cpu_bat* first      28153*   1   1    1gb 00:05 F 00:00
    12345679.aqua        your-us* gpu_bat* movielens* 19836*   1   4   16gb 00:05 F 00:00
    ```

`F` means finished. `Elap Time` is how long each one ran, in hours and minutes, so both of these show `00:00`: neither needed a full minute.

### Step 2: Take one back

Submitted the wrong thing? Forgot to fetch the data, or typed the wrong walltime? Take it back before it wastes a node:

```bash
qsub movielens_recommender.pbs      # the one you did not mean to send
qdel <job-id>
qstat -u $USER
```

!!! example "Expected output"
    ```text
    12345680.aqua
    ```

That one line is `qsub`'s. `qdel` prints nothing when it works, and `qstat -u $USER` prints nothing when you have no jobs left, so silence is the good outcome here.

`qdel` removes a queued job before it starts, and stops a running one where it is. Whatever a stopped job had already written stays on disk, and its `.o` file still ends with Aqua's summary. In `qstat -xu` it shows up as `F` like any other finished job; its record (`qstat -xf <job-id>`) says `Exit_status = 143`, which means it was stopped from outside, not that your script failed.

!!! tip "Interactive or batch?"
    Lesson 3 asked who is waiting on whom. Now you have the other half of the answer:

    - **Changing something and looking at the result**, over and over: interactive.
    - **Anything you would otherwise sit and watch**, anything that runs longer than you want to stay logged in, anything you will run again with different inputs: write it down as a job script.

---

## 🎯 Key Takeaways

!!! success "You now know"

    📄 **A job script is the whole request** — `#PBS` lines for PBS, ordinary shell for the work

    🏠 **A job starts at home with nothing activated** — so scripts `cd "$PBS_O_WORKDIR"` and run through the project

    🎮 **`ngpus=1` in batch gets a whole GPU** — with the CUDA build of PyTorch locked in the project

    🚶 **Submitted means independent** — the job runs without your connection, and email tells you when it moves

    📂 **Results go in files, logs go in `.o` and `.e`**

    🧭 **`qstat` to find a job, `qstat -x` for finished ones, `qdel` to take one back**

---

## 🔗 What's Next?

→ **[Lesson 5: When Jobs Fail](lesson-5.md)** — for the day the log says something other than `done`.

What a job actually used, and how to ask for the right amount next time, is [Lesson 6](lesson-6.md); [PBS Brew Inspector](../pbs-scripts/PBS-Brew-Inspector.md) shows it for every job you have run.

!!! question "Stuck?"
    - **`qsub` rejects the script?** A typo in a `#PBS` line, or a request above the queue's limits. The error names the problem.
    - **The GPU job sits in `Q` for a long time?** The cards are busy. It will start; a shorter walltime can help it fit in sooner.
    - **The log says the device is `cpu`, or CUDA is not available?** `pyproject.toml` still points PyTorch at the CPU index. Switch it as in Part 2, Step 2, and run `uv sync` again.
    - **The log says CUDA out of memory?** Make each step smaller: add `--batch 16384` to the `uv run` line.
    - **The fetch stops with a checksum error?** The download was cut short, or the copy changed. Delete `data/movielens/` and run the fetch again.
    - **The job tries to download MovieLens?** The `--epochs 0` fetch in Part 2 was skipped, or the job ran from a different directory than the data. Fetch once on the login node, and submit from `~/hello-aqua`.
    - **No log files appeared?** They land in the directory you ran `qsub` from, once the job ends.
    - **No email?** Look for `PBS JOB` from `eresearch@qut.edu.au`, including your junk folder, and check the script has `#PBS -m abe`. To send it to another address, add `#PBS -M you@example.com`.

---

## 📝 Quick Reference

=== "Job script"
    ```bash
    #!/bin/bash
    #PBS -N my_job
    #PBS -l select=1:ncpus=4:mem=8GB             # CPU job
    ##PBS -l select=1:ncpus=4:ngpus=1:mem=32GB   # GPU job instead
    #PBS -l walltime=01:00:00
    #PBS -m abe

    cd "$PBS_O_WORKDIR"
    uv run python my_program.py
    ```

=== "Commands"
    ```bash
    qsub my_job.pbs          # submit; prints the job ID
    qstat -u $USER           # your queued and running jobs
    qstat -xu $USER          # ...including finished ones
    qdel <job-id>            # take a job back, queued or running
    ```

=== "Inside a job"
    ```bash
    $PBS_O_WORKDIR           # the directory you ran qsub from
    $PBS_JOBID               # this job's ID
    $NCPUS                   # cores PBS gave the job
    $CUDA_VISIBLE_DEVICES    # the GPU(s) PBS gave the job
    ```

=== "movielens_recommender.py knobs"
    ```bash
    python movielens_recommender.py --epochs 0                  # fetch the data and exit
    python movielens_recommender.py --epochs 10                 # longer run
    python movielens_recommender.py --dim 128                   # bigger model, more GPU memory
    python movielens_recommender.py --batch 16384               # smaller steps, less GPU memory
    python movielens_recommender.py --limit 100000              # first 100k ratings, fine on a CPU
    ```
