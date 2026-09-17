# Lesson 5: When Jobs Fail

!!! quote "Mission Statement"
    *"Reading PBS tea leaves and error messages"* 🔍

Lesson 4's job ended with `done` and `Exit_status=0`. Sooner or later one of yours will not. This lesson is about the other endings: what each one leaves in the logs, who stopped the job, and what to do next. None of it needs you to break anything; the endings below all come from real jobs on Aqua. It finishes with the habit that makes most failures cost you a minute instead of a day in the queue.

It is worth the fifteen minutes. In a study of 377,000 jobs over five and a half years on one supercomputer, 99.4% of the failures came from the jobs themselves, not the machine.[^1] In another, of two university clusters, jobs killed at their walltime used a third or more of all compute hours.[^2]

## 📋 What You'll Accomplish

By the end of this 15–20 minute lesson, you'll have:

- [ ] **Found where a failure leaves its evidence** — the summary at the end of `.o`, and `qstat -xf` for recent jobs
- [ ] **Told who stopped a job from the end of its logs** — a traceback, `=>> PBS: job killed`, `cgroup/OOM`, or nothing at all
- [ ] **Read the endings you will actually meet** — program errors, walltime, memory, `qdel`, a failed node
- [ ] **Read why a job is refused or still waiting** — the refusal message, the queued job's `comment`
- [ ] **Tested the code before the long run** — in an interactive GPU session, where a mistake fails in a minute

!!! info "You need Lessons 3 and 4"
    Part 1 reads the logs of the `imdb_sentiment` job from [Lesson 4](lesson-4.md), and Part 5 uses the interactive GPU session from [Lesson 3](lesson-3.md). Any batch job of your own works just as well.

---

## 🔍 Part 1: Where a failure leaves evidence (~4 min)

### Step 1: The summary at the end of `.o`

Lesson 4 showed that Aqua adds a summary to the end of every `.o` file: what the job used, then its full record. One line of that record is the verdict. On the login node:

```bash
cd ~/hello-aqua
grep Exit_status imdb_sentiment.o*
```

!!! example "Expected output"
    ```text
    Exit_status      : 0
    ```

`0` means the script's last command succeeded, which is usually, though not always, the same as "it worked" (Part 2 shows the exception). Most other endings in this lesson put a different number on that line. The `.o` file is the record that lasts: it stays for as long as you keep the file.

### Step 2: `qstat -xf` for recent jobs

PBS keeps the same record, and you can ask for it by job ID:

```bash
qstat -xf <job-id> | grep -E "Exit_status|resources_used.walltime"
```

On your Lesson 4 job, that shows `Exit_status = 0`, as long as the job ended in the last four days. On a job that was taken back with `qdel`, it looks like this:

!!! example "A job taken back with `qdel`"
    ```text
        resources_used.walltime = 00:00:11
        Exit_status = 143
    ```

PBS only remembers a job for **four days** after it ends. After that:

!!! example "For a job that ended more than four days ago"
    ```text
    qstat: Unknown Job Id 12345678.aqua
    ```

The job is not lost, only forgotten by `qstat`. Its `.o` file still has the whole record.

### Step 3: Read the end of both logs

A job writes two logs, and a failure usually shows up at the end of one of them:

```bash
tail imdb_sentiment.e*
tail -n 30 imdb_sentiment.o*
```

- **`.e`** gets errors: your program's tracebacks, and PBS's own message when it stops a job.
- **`.o`** gets your program's normal output, then Aqua's summary.

Read `.e` first, then the lines just above `PBS Job` in `.o`. The rest of this lesson is what those endings can say.

??? info "Queue states"
    | State | Meaning |
    |---|---|
    | `Q` | Queued: waiting for resources |
    | `R` | Running |
    | `H` | Held: will not start until the hold is released |
    | `E` | Exiting: finished, PBS is tidying up |
    | `F` | Finished: shown by `qstat -x` |

---

## 🐛 Part 2: Your program stopped it (~4 min)

In these endings the job started, and then something in the job itself went wrong: the program, or the script around it. PBS had nothing to do with it, and the reason is written in the job's error log.

### An error from the program

A job script that forgot `cd "$PBS_O_WORKDIR"` runs from your home directory, where the program is not:

!!! example "The job's `.e` file: the script forgot `cd`"
    ```text
    /home/your-username/.local/share/uv/python/cpython-3.13-linux-x86_64-gnu/bin/python3.13: can't open file '/mnt/hpccs01/home/your-username/my_program.py': [Errno 2] No such file or directory
    ```

`.o` has nothing above Aqua's summary, and the summary says `Exit_status : 2` after two seconds of walltime. A Python traceback usually ends a job with `1`; either way, the last line of `.e` is the reason.

**Next move:** fix it, then test the fix (Part 5) before you submit again.

!!! info "Out of memory on the GPU is this kind too"
    `CUDA out of memory` in `.e` is your program's own error, not PBS stopping the job. Lesson 4's Stuck box has the usual fix: a smaller batch.

### A failure the last command hid

This one is easy to miss. The job below runs a preparation step, and then reports that it finished:

```bash title="my_job.pbs (body)"
cd "$PBS_O_WORKDIR"
uv run python prepare_data.py
echo "all steps finished"
```

The preparation step failed:

!!! example "The job's `.e` file: the preparation step's traceback"
    ```text
    Traceback (most recent call last):
      File "/mnt/weka/scratch/your-username/my_project/prepare_data.py", line 3, in <module>
        with open("input.csv") as f:
             ~~~~^^^^^^^^^^^^^
    FileNotFoundError: [Errno 2] No such file or directory: 'input.csv'
    ```

But `.o` says `all steps finished`, and the email says `Exit_status=0`.

!!! warning "A job's exit status is its last command's"
    PBS reports how the script's last command ended, not whether everything before it worked. Here that was `echo`, and `echo` succeeded. If the exit status is `0` but a result is missing, read `.e` before trusting the `0`.

The fix is one line at the top of the script:

```bash title="my_job.pbs (body)"
set -e
cd "$PBS_O_WORKDIR"
uv run python prepare_data.py
echo "all steps finished"
```

`set -e` stops the script at the first command that fails. The same job now ends with `Exit_status=1`, and nothing claims it finished.

### An error in the job script itself

A typo in the shell part of the script, such as an unclosed `{`, fails as soon as the job starts:

!!! example "The job's error message: an unclosed `{` in the script"
    ```text
    /var/spool/PBS/mom_priv/jobs/12345678.aqua.SC: line 34: unexpected EOF while looking for matching `}'
    ```

The `.SC` file is PBS's copy of your script, so the line number is a line in your script. The exit status is `2`.

**Next move:** fix that line and submit again.

---

## ⏱️ Part 3: PBS stopped it (~4 min)

These endings are PBS enforcing what you asked for. Your program had no say, so it usually prints nothing about them.

### Walltime

A job that prints a line every ten seconds, asked for one minute:

!!! example "The job's `.o` file: output that stops, then Aqua's summary"
    ```text
    step 1 of 30
    step 2 of 30
    ...
    step 9 of 30

    PBS Job 12345678.aqua
    CPU time         : 00:00:00
    Wall time        : 00:01:26
    Mem usage        : 3168kb
    ```

!!! example "The job's `.e` file: PBS's walltime message"
    ```text
    =>> PBS: job killed: walltime 86 exceeded limit 60
    ```

The output simply stops, and `.e` says why, in seconds. The exit status is `-29`. PBS checks walltime every so often rather than every second, so a job can run a little past its limit before it is stopped.

Whatever the program wrote before that is still on disk. Whatever it would have written at the end, such as a results file, is not.

**Next move:** ask for more walltime. How much more, from what the job actually used, is [Lesson 6](lesson-6.md). If the work cannot fit in the longest walltime a queue allows, it has to be split, which is [Lesson 8](lesson-8.md).

### Memory

When a job needs more memory than its `mem=` request, PBS stops it:

!!! example "The end of the job's logs: PBS's memory message"
    ```text
    (your program's normal output, then nothing more)
    cgroup/OOM: Killed because of memory limit
    ```

The exit status is `137`, and `resources_used.mem` in the summary is close to the request. The program was killed from outside, so it printed no error of its own.

**Next move:** ask for more memory, then size it properly in [Lesson 6](lesson-6.md).

### Someone ran `qdel`

The output just stops, `.e` is empty, and the exit status is `143` (Lesson 4, Part 3). If that someone was you, there is nothing to fix.

### The node failed

Now and then a compute node drops out of PBS while jobs are running on it. PBS puts those jobs back in the queue and starts them again elsewhere. There is nothing in your logs; the job's record shows it:

!!! example "The job's record after its node failed"
    ```text
        job_state = Q
        run_count = 1
        Exit_status = -20
    ```

**Next move:** usually none, since the job runs again by itself. A job that saves checkpoints loses less when this happens ([Lesson 8](lesson-8.md)).

---

## 🚦 Part 4: PBS refused it, or has not started it (~4 min)

### Refused

A request PBS cannot accept never runs: a typo in a `#PBS` line, or more than a queue allows, such as a walltime over 48 hours. PBS says why, and the message names the problem.

**Next move:** fix the request. The limits of each queue are in [Know Your Nodes](../scheduler/Know-Your-Nodes.md#house-rules).

### Still in `Q`

A job waiting in `Q` has not failed. PBS writes down why it has not started yet:

```bash
qstat -f <job-id> | grep comment
```

!!! example "A queued job's `comment`"
    ```text
        comment = Not Running: Insufficient amount of resource: qlist
    ```

That means no node that serves this queue has room for the request right now. A GPU job may say `Insufficient amount of resource: ngpus` instead. Once the job has run, the same line only says where and when.

**Next move:** wait. A smaller or shorter request fits in sooner next time. Deleting a waiting job and submitting it again puts it at the back: the time it has already waited counts towards starting it.

### Reading an ending

Every ending in this lesson, in one place. For a job that ran, the end email, `qstat -xf` and the summary at the end of `.o` all show the same `Exit_status`, and the logs say the same thing in words.

| What you see | `Exit_status` | Who stopped it | Next move |
|---|---|---|---|
| A traceback or error at the end of `.e` | `1`, `2`, … | your program | fix it, test it (Part 5), submit again |
| Results missing, but the job reports success | `0` | your program, hidden by the last command | read `.e`, add `set -e` |
| `.e`: `=>> PBS: job killed: walltime … exceeded limit …` | `-29` | PBS, at the walltime | more walltime ([Lesson 6](lesson-6.md)), or split the work ([Lesson 8](lesson-8.md)) |
| `cgroup/OOM: Killed because of memory limit` | `137` | PBS, at the memory limit | more memory ([Lesson 6](lesson-6.md)) |
| Output just stops, `.e` is empty | `143` | someone ran `qdel` | nothing, if it was you |
| Back in `Q` by itself | `-20` | a failed node | nothing: it runs again |
| A refusal message | none: the job never ran | PBS, before it started | fix the request |
| Waiting in `Q` with a `comment` | none yet | nobody | wait; ask for less next time |

Other clusters, and older guides, may show different numbers for the same events, such as `271` for a walltime kill. The words in the logs are the more reliable guide.

---

## 🧭 Part 5: Fail in a minute, not after the queue (~3 min)

### Step 1: Why test first

Failures like the ones in Part 2 usually show up in a job's first minute: a missing file, a typo, a setting the program does not know. In a batch job, that minute comes after however long the job waited in the queue, which for a GPU job can be hours. Running the code once, small, before you submit, moves the failure to where it costs a minute.

### Step 2: Test it in an interactive GPU session

An interactive session from [Lesson 3](lesson-3.md) is the place to do it. The interactive GPU queue gives you a slice of a GPU rather than a whole card, enough to check that the code runs. On the login node, inside `tmux`:

```bash
qsub -I -l select=1:ncpus=6:ngpus=1:mem=32GB -l walltime=01:00:00 -P ABCDEF1234
```

When the prompt changes to a GPU node, run the program the way the job would, but small. For Lesson 4's job, that means fewer reviews and one epoch, written to its own files so the real results are not overwritten:

```bash
cd ~/hello-aqua
uv run python imdb_sentiment.py --limit 500 --epochs 1 --out test.json --model-dir test_model
```

If it fails, the error is on your screen: fix it and run it again. When it finishes cleanly, `exit` the session and `qsub` the real job script. Your own program works the same way with whatever setting makes it small.

!!! tip "Reproduce it by hand"
    When a batch job fails and the logs do not make the reason obvious, run the same command in an interactive session and watch it fail.

---

## 🎯 Key Takeaways

!!! success "You now know"

    📜 **Read the end of `.e`, then the summary at the end of `.o`** — together they say who stopped the job

    🗂️ **The `.o` summary lasts; `qstat -xf` forgets after four days**

    🧮 **A job's exit status is its last command's** — `set -e` makes an early failure count

    ⏱️ **PBS says so when it stops a job** — `job killed: walltime` and `cgroup/OOM` are PBS, not your program

    🚦 **Refused jobs never run; waiting jobs have not failed** — the `comment` line says why they wait

    🧪 **Test small in an interactive session before you queue long**

---

## 🔗 What's Next?

→ **[Lesson 6: Right-sizing Requests](lesson-6.md)** — how much walltime and memory to ask for, so the endings in Part 3 stop happening.

For work that cannot fit in one walltime at all, [Lesson 8](lesson-8.md) splits it across jobs.

!!! question "Stuck?"
    - **No `.o` file at all?** The logs appear in the directory you ran `qsub` from, and only once the job ends.
    - **`qstat: Unknown Job Id`?** PBS has forgotten the job; it keeps finished jobs for four days. The summary at the end of its `.o` file has the same record.
    - **`FileExistsError` or `File exists` when you run a job again?** An earlier attempt left its output behind. Move or remove it, or have the job write to a new directory.
    - **The error says to inspect another log?** The program ran another program, and the real error is in that program's log.
    - **Errors mentioning `$'\r'`?** The script was saved with Windows line endings. Convert it on Aqua with `sed -i 's/\r$//' my_job.pbs`, and set your editor to Unix (LF) line endings.
    - **`Disk quota exceeded`?** Your home directory is full, usually of environments and caches. [Lesson 2](lesson-2.md) covers where those belong.

---

## 📝 Quick Reference

=== "Where to look"
    ```bash
    tail my_job.e*                       # errors, and PBS's message if it stopped the job
    tail -n 30 my_job.o*                 # your output, then Aqua's summary
    grep Exit_status my_job.o*           # the verdict, for as long as you keep the file
    qstat -xf <job-id> | grep -E "Exit_status|resources_used"   # the same, for four days
    qstat -f <job-id> | grep comment     # why a queued job has not started
    ```

=== "Exit status on Aqua"
    ```text
    0      the script's last command succeeded (check .e anyway)
    1, 2   the script's last command failed: read the end of .e
    -29    PBS stopped it at the walltime
    137    PBS stopped it at the memory limit
    143    someone ran qdel
    -20    the node failed; PBS queued the job again
    ```

=== "Safer job script"
    ```bash
    #!/bin/bash
    #PBS -N my_job
    #PBS -l select=1:ncpus=4:mem=8GB
    #PBS -l walltime=01:00:00
    #PBS -P ABCDEF1234
    #PBS -m abe

    set -e
    cd "$PBS_O_WORKDIR"
    uv run python my_program.py
    ```

=== "Test first"
    ```bash
    qsub -I -l select=1:ncpus=6:ngpus=1:mem=32GB -l walltime=01:00:00 -P ABCDEF1234
    cd ~/hello-aqua
    uv run python my_program.py              # at its smallest setting; watch it run, fix, repeat
    exit
    qsub my_job.pbs
    ```

[^1]: Sheng Di, Hanqi Guo, Eric Pershey, Marc Snir, Franck Cappello, "[Characterizing and Understanding HPC Job Failures over the 2K-day Life of IBM BlueGene/Q System](https://snir.cs.illinois.edu/listed/C111.pdf)". 99.4% of the job failures studied were attributed to user behaviour.
[^2]: Rakesh Kumar, Saurabh Jha, et al., "[The Mystery of the Failing Jobs: Insights from Operational Data from Two University-Wide Computing Systems](https://saurabhjha.one/pubs/DSN20b/paper.pdf)", DSN 2020. Jobs killed at their walltime used 33% and 43% of all compute hours on the two systems studied.
