# Lesson 3: Working Interactively

!!! quote "Mission Statement"
    *"Interactive is where you develop. Batch is where you run."* 🧪

Lesson 1's interactive job did nothing on purpose. Lesson 2 gave you a Python environment and never ran it on a compute node. This lesson closes the gap: you ask PBS for a shell sized for real work, run the course's one worked example on it by hand, and **measure** it. The two numbers you write down at the end, how long it ran and how much memory it peaked at, are what Lesson 4 submits with and what Lesson 6 sizes from. Along the way you learn what interactive jobs are actually for, and the moment to stop using them.

## 📋 What You'll Accomplish

By the end of this 15–20 minute lesson, you'll have:

- [ ] **Sized an interactive request on purpose** — cores, memory and walltime for a development session, inside the caps that bound it
- [ ] **Known which queue you land on** — `cpu_inter_exec` vs `gpu_inter_exec`, and why an interactive GPU is a slice, not a card
- [ ] **Installed PyTorch into your Lesson 2 environment** and fetched `train_mnist.py`, the script every later lesson reuses, plus its data
- [ ] **Run it by hand on a compute node** from inside `qsub -I`, and watched it learn to read digits
- [ ] **Measured it** — wall time with `time`, peak memory with `/usr/bin/time -v`
- [ ] **Kept a session alive across a dropped connection** with `tmux`
- [ ] **Known when to stop being interactive** and let Lesson 4 take over

!!! tip "You need Lesson 2's environment"
    Everything below assumes `~/hello-aqua/.venv` (uv) or the `hello-aqua` env (Miniforge / micromamba) from [Lesson 2](lesson-2.md) exists and works. If not, do the Test Drive there first; it takes two minutes.

---

## ⚖️ Part 1: Size the request (~3 min)

Lesson 1 asked for one core and one gigabyte because the point was to arrive somewhere. This time the point is to work, so the request has to fit the work. Two things bound it.

**The interactive queues have caps.** PBS routes `qsub -I` to one of two interactive queues by whether you asked for a GPU:

| Queue | You get | Per job | Per user, all your interactive jobs | Walltime |
|---|---|---|---|---|
| `cpu_inter_exec` | a shell on `cpu1n001`, the single interactive CPU node | 1–8 cores, 1–34 GB | 8 cores, 34 GB | ≤ 12 h |
| `gpu_inter_exec` | a shell plus **one MIG slice** (about 1/7 of an H100, ~10 GB VRAM) | 1–12 cores, 1–68 GB, `ngpus=1` | 12 cores, 68 GB, 2 slices | ≤ 12 h |

The caps come from the queues themselves (`qstat -Qf cpu_inter_exec`); the [eResearch queue page](https://docs.eres.qut.edu.au/hpc-queue-limits)[^1] rounds them to 32 and 64 GB. Ask for more than the cap and the job is rejected at submit time, not queued.

**Interactive jobs hold everything they asked for, for the whole walltime.** A batch job releases its node the moment the script ends. An interactive job releases it when you `exit`, or when the walltime runs out, whichever comes first, and until then nobody else gets those cores. Every user on Aqua shares one interactive CPU node, so an oversized request is not a rounding error, it is someone else's afternoon. Two rules follow:

- **Cores and memory:** what the thing you are about to poke at needs, plus a little. Not the maximum.
- **Walltime:** how long you will actually sit at the keyboard, plus a buffer. One or two hours, not twelve.

For this lesson, four cores, eight gigabytes and one hour is plenty:

```bash
qsub -I -l select=1:ncpus=4:mem=8GB -l walltime=01:00:00
```

!!! info "When you'd pick the GPU queue instead"
    Add `:ngpus=1` and PBS sends you to `gpu_inter_exec`. The slice you get is for checking that a model loads and a CUDA build works, not for training. The queue lets one job hold two slices, but a single program cannot span two MIG instances without specialised code, so a second slice only helps if you have two independent things to run. For this lesson, one. Recipe 7 in [Walltime by Recipe](../scheduler/Walltime-by-Recipe.md#recipe-7-mig-slice-sanity-check) is the ready-made line, and [Know Your Nodes](../scheduler/Know-Your-Nodes.md) explains MIG. This lesson stays on CPU: `train_mnist.py` runs happily there and the CPU queue starts faster.

---

## 📦 Part 2: Get the script, its dependency, and its data (~4 min)

The course's worked example is `train_mnist.py`. It trains a small two-layer network to recognise handwritten digits from **MNIST**, the 70,000-image dataset every machine-learning course starts with. It is not a hard problem, and that is the point: the script costs real CPU, real memory and real time, every knob on it maps to something PBS charges you for, and at the end you get a number a human can judge: how many digits it read correctly. Lesson 3 runs it. Lesson 4 submits it. Lesson 5 breaks it. Lesson 6 sizes it. Lessons 7 and 8 multiply and chain it.

It needs only PyTorch. Install that into your Lesson 2 environment, download the script, and let the script fetch its data (12 MB, once). All of this is network and disk work, not compute, so the login node is the right place for it:

=== "uv"
    ```bash
    cd ~/hello-aqua
    source .venv/bin/activate

    # CPU build of PyTorch (about 800 MB installed; the CUDA build is gigabytes and needs a GPU node).
    # numpy is not required, but without it torch prints a warning on every import.
    uv pip install --index https://download.pytorch.org/whl/cpu torch numpy

    # The script, straight from this site's repository
    wget https://raw.githubusercontent.com/ZhipengHe/Walltime-Chronicles/main/docs/tutorials/scripts/train_mnist.py

    # Fetch the data now, so the compute node never has to. --epochs 0 downloads and exits.
    python train_mnist.py --epochs 0
    ```

    !!! note "Same-filesystem rule"
        If you followed Lesson 2's tip and moved `UV_CACHE_DIR` to `/scratch`, this venv on `/home` is now on a different filesystem from the cache, and uv will warn `Failed to hardlink files; falling back to full copy`. It still works, just slower. The fix is to keep cache and venv together: [uv on Aqua](../scheduler/uv-on-aqua.md).

=== "Miniforge"
    ```bash
    mkdir -p ~/hello-aqua && cd ~/hello-aqua
    conda activate hello-aqua
    conda install -c conda-forge pytorch-cpu numpy -y

    wget https://raw.githubusercontent.com/ZhipengHe/Walltime-Chronicles/main/docs/tutorials/scripts/train_mnist.py
    python train_mnist.py --epochs 0
    ```

=== "micromamba"
    ```bash
    mkdir -p ~/hello-aqua && cd ~/hello-aqua
    micromamba activate hello-aqua
    micromamba install -c conda-forge pytorch-cpu numpy -y

    wget https://raw.githubusercontent.com/ZhipengHe/Walltime-Chronicles/main/docs/tutorials/scripts/train_mnist.py
    python train_mnist.py --epochs 0
    ```

!!! example "Expected output of the data fetch"
    ```text
    host      aquarius01
    device    cpu  threads 1  seed 0
    download  https://ossci-datasets.s3.amazonaws.com/mnist/train-images-idx3-ubyte.gz
    download  https://ossci-datasets.s3.amazonaws.com/mnist/train-labels-idx1-ubyte.gz
    download  https://ossci-datasets.s3.amazonaws.com/mnist/t10k-images-idx3-ubyte.gz
    download  https://ossci-datasets.s3.amazonaws.com/mnist/t10k-labels-idx1-ubyte.gz
    data      60,000 training images, 10,000 test  (188 MB)
    done      test accuracy None  in 19.8s  -> results.json
    ```

    Four files land in `~/hello-aqua/data/mnist/`. The `None` is honest: zero epochs, no model to score. Delete `results.json` if it bothers you; the next run overwrites it.

You can also read the script here or [download it](scripts/train_mnist.py) directly. Skim the docstring at the top: it lists the knobs, and the rest of the course is a tour of them.

??? note "The script, in full (`train_mnist.py`)"

    ```python title="train_mnist.py"
    --8<-- "docs/tutorials/scripts/train_mnist.py"
    ```

---

## 🛠️ Part 3: Run it by hand on a compute node (~5 min)

Now the round-trip from Lesson 1, with work in the middle.

```bash
qsub -I -l select=1:ncpus=4:mem=8GB -l walltime=01:00:00
```

Wait for the prompt to change to `cpu1n001`. Then:

```bash
cd ~/hello-aqua
source .venv/bin/activate     # or: conda activate hello-aqua / micromamba activate hello-aqua

echo $NCPUS                   # → 4
python train_mnist.py
```

Two things to notice before the output even appears. Your home directory, script and data are all here unchanged, because `/home` is mounted on every node (Lesson 1). And `$NCPUS` is set: PBS tells every job how many cores it was given, and `train_mnist.py` reads it to decide how many threads to use. Lesson 6 is largely about programs that *don't* do that.

!!! example "What you should see"
    ```text
    host      cpu1n001
    device    cpu  threads 4  seed 0
    data      60,000 training images, 10,000 test  (188 MB)
    epoch   1/8  loss 0.0939  test accuracy 0.9613    5.3s
    epoch   2/8  loss 0.0546  test accuracy 0.9738    1.8s
    epoch   3/8  loss 0.0304  test accuracy 0.9749    1.8s
    epoch   4/8  loss 0.0272  test accuracy 0.9799    1.7s
    epoch   5/8  loss 0.0762  test accuracy 0.9787    1.7s
    epoch   6/8  loss 0.0680  test accuracy 0.9790    1.7s
    epoch   7/8  loss 0.0098  test accuracy 0.9789    1.7s
    epoch   8/8  loss 0.0136  test accuracy 0.9820    1.7s
    done      test accuracy 0.982  in 25.2s  -> results.json
    ```

    Eight passes over 60,000 digits and it reads 98 % of the 10,000 it has never seen. The accuracies will match to a few decimals (the seed is fixed); the times will wobble with whoever else is on `cpu1n001`, and the first epoch is slower than the rest while PyTorch warms up. The *shape* is what matters: a banner saying where it ran and with what, one line per epoch, a summary written to `results.json`.

Look at `results.json`. The script records its own runtime and peak memory:

```bash
cat results.json
```

```json
{
  "seed": 0,
  "samples": 60000,
  "width": 1024,
  "epochs": 8,
  "device": "cpu",
  "threads": 4,
  "test_accuracy": 0.982,
  "elapsed_s": 25.2,
  "peak_rss_mb": 494,
  "job_id": "25187891.aqua"
}
```

That `job_id` came from `$PBS_JOBID`, another variable PBS sets inside every job. A program that writes down what it used, and which job it ran in, is a habit worth forming now: it is how you will size Lesson 6's request, and later in the course it is how you will know what an unattended job did.

---

## 📏 Part 4: Measure it (~4 min)

`results.json` is the script's own account of itself. Now measure from outside, the way you would measure a program that keeps no records. Two tools, both already on the node.

**Wall time, with the shell's `time`:**

```bash
time python train_mnist.py
```

```text
real    0m16.3s
user    0m54.8s
sys     0m1.0s
```

`real` is what walltime meters (a second run is quicker than the first: the data is already in the page cache). `user` larger than `real` means more than one core was busy: about 55 seconds of CPU time in 16 seconds of wall time is roughly 3.4 cores' worth, out of the 4 you asked for. That ratio is the number PBS reports as `cpupercent` after a batch job, and the [PBS Brew Inspector](../pbs-scripts/PBS-Brew-Inspector.md) turns into a table.

**Peak memory, with GNU `time`:**

```bash
/usr/bin/time -v python train_mnist.py 2>&1 | grep -E "Elapsed|Maximum resident"
```

```text
        Elapsed (wall clock) time (h:mm:ss or m:ss): 0:18.34
        Maximum resident set size (kbytes): 513544
```

`Maximum resident set size` is the peak, in kilobytes; here about 500 MB, of which 188 MB is the digits themselves as floats and most of the rest is PyTorch. It agrees with the `peak_rss_mb` the script wrote for itself, which is the point of measuring twice. That is the number `mem=` has to cover with room to spare. You asked for 8 GB and used half a gigabyte, which is fine for a development session and exactly the kind of gap Lesson 6 teaches you to close for batch.

**Now turn a knob.** The whole point of having a compute node to yourself is that experiments are cheap:

```bash
time python train_mnist.py --threads 1 --out results-1thread.json
```

```text
epoch   8/8  loss 0.0136  test accuracy 0.9820    3.0s
done      test accuracy 0.982  in 25.0s  -> r1t.json

real    0m26.7s
user    0m25.6s
sys     0m0.9s
```

Same accuracy, `user` now equal to `real` (one core busy, as ordered), and the run takes about 1.7 times as long as it did on four threads: 3.0 s an epoch against 1.7 s. Not four times. Some of each step is bookkeeping that no amount of cores speeds up, and the fourth core buys less than the second. Write both numbers down. Lesson 6 starts from exactly this comparison, and the general shape of it, *more cores helps until it doesn't*, is most of what right-sizing is.

!!! tip "Write down your two numbers"
    Wall time at 4 threads, and peak memory. Put them in a note, or just keep `results.json`. Lesson 4 submits this script unattended with a walltime based on the first, and Lesson 6 sets `mem=` from the second.

---

## 🔌 Part 5: Survive a dropped connection (~3 min)

An interactive job's shell is your SSH session. Close the laptop, lose the Wi-Fi, and the shell dies, PBS ends the job, and anything running in it dies too. The cure is a terminal multiplexer on the **login node**, so the thing holding your job is not your Wi-Fi.

```bash
# On the login node, before you ask PBS for anything:
tmux new -s dev

# Inside tmux, as usual:
qsub -I -l select=1:ncpus=4:mem=8GB -l walltime=01:00:00
```

Detach with ++ctrl+b++ then ++d++; the job keeps running. Reconnect later and reattach:

```bash
tmux attach -t dev
```

Two things to know:

- **Aqua has more than one login node** (`aquarius01`, `aquarius02`, …), and `ssh aqua.qut.edu.au` lands you on one of them. A tmux session lives on the node where you started it, so `tmux ls` on the other node shows nothing. Run `hostname` when you start the session and, if you come back and it seems gone, check which node you are on before assuming the worst.
- The session does not survive a login-node reboot. Maintenance is the third Wednesday of each month; `time_until_outage.sh` tells you how far away it is.

`tmux` itself is fine on the login node: it uses no CPU to speak of. What runs *inside* it still has to obey the rule from Lesson 1: editing, `git`, `qsub` and friends yes; the training run itself no, that goes through `qsub -I` as above.

---

## 🛑 Part 6: Know when to stop (~1 min)

You have a compute node, an environment, a script, and a feel for how much it costs. This is the moment most people start running things, and the moment to stop and ask one question: **am I waiting on the machine, or is the machine waiting on me?**

- If you are typing, reading output, changing a parameter and running again, this is interactive work. Stay.
- If you have set something going and are watching it, or would like to walk away, or intend to run it more than once with different inputs, it is a batch job. That is Lesson 4, and it is one short file away.

When you are done, leave:

```bash
exit                 # ends the interactive job
qstat -u $USER       # nothing left running? good
```

Your node goes back into the pool. Twelve hours booked and abandoned would have kept it out of the pool for twelve hours.

---

## 🎯 Key Takeaways

!!! success "You now know"

    ⚖️ **Interactive requests are sized for the session, not the maximum** — the caps are 8 cores / 34 GB (CPU) and 12 cores / 68 GB / one MIG slice (GPU), 12 h, and everything you ask for is held until you leave

    📦 **The course's script** — `train_mnist.py` learns to read handwritten digits; its knobs are the rest of the course

    🛠️ **PBS tells your job what it got** — `$NCPUS`, `$PBS_JOBID`; programs that read them behave

    📏 **Two measurements** — `time` for wall time (and whether more than one core was used), `/usr/bin/time -v` for peak memory

    🔌 **`tmux` on the login node** keeps an interactive job alive across a dropped connection

    🛑 **Interactive is for developing; batch is for running** — the question is who is waiting on whom

---

## 🔗 What's Next?

→ **[Lesson 4: Your First Batch Job](lesson-4.md)** — the same script, submitted unattended, with the numbers you just measured.

!!! question "Stuck?"
    - **`qsub -I` sits at "waiting for job to start"?** There is one interactive CPU node and it may be full. Try fewer cores (`ncpus=2:mem=4GB`), or check `pbsnodeinfo | grep cpu1n001` to see how busy it is.
    - **`command not found: python` after the prompt changes?** You haven't activated the environment on the compute node. `source ~/hello-aqua/.venv/bin/activate` (or the conda equivalent) is per shell.
    - **The script tries to download on the compute node?** You skipped the `--epochs 0` fetch in Part 2, or ran from a different directory. It will still work (compute nodes can reach the internet), but fetch once on the login node and keep `data/mnist/` next to the script.
    - **PyTorch install is slow or warns about hardlinks?** Cache and venv are on different filesystems. [uv on Aqua](../scheduler/uv-on-aqua.md) has the three placements that avoid it.
    - **Want VS Code or Jupyter inside the interactive job instead of a bare shell?** [Surviving without VS Code Remote SSH](../remote-dev/Surviving-without-VS-Code-Remote-SSH.md) covers the tunnel and the port-forwarded Jupyter Lab, both of which run inside exactly the `qsub -I` you just used.
    - **Curious what the interactive node actually is?** [Know Your Nodes](../scheduler/Know-Your-Nodes.md), "CPU Interactive — the appetiser".

---

## 📝 Quick Reference

=== "Interactive requests"
    ```bash
    qsub -I -l select=1:ncpus=4:mem=8GB -l walltime=01:00:00            # CPU, this lesson
    qsub -I -l select=1:ncpus=6:ngpus=1:mem=32GB -l walltime=02:00:00   # one MIG slice
    echo $NCPUS $PBS_JOBID                                              # what PBS gave you
    exit                                                                # give it back
    ```

=== "Measuring"
    ```bash
    time python train_mnist.py                             # real = wall time; user > real = multi-core
    /usr/bin/time -v python train_mnist.py 2>&1 | grep -E "Elapsed|Maximum resident"
    python train_mnist.py --threads 1 --out results-1thread.json   # compare
    cat results.json                                       # the script's own account
    ```

=== "tmux"
    ```bash
    tmux new -s dev          # start (on the login node)
    # Ctrl-b then d          # detach
    tmux ls                  # list sessions on this login node
    tmux attach -t dev       # reattach
    tmux kill-session -t dev # done with it
    ```

=== "train_mnist.py knobs"
    ```bash
    python train_mnist.py --epochs 0                # fetch the data and exit
    python train_mnist.py --epochs 30               # longer (Lesson 4, 5)
    python train_mnist.py --width 8192              # more memory and compute (Lesson 5, 6)
    python train_mnist.py --threads 8               # more cores (Lesson 6)
    python train_mnist.py --device cuda             # the GPU PBS gave you (Lesson 6)
    python train_mnist.py --seed 7 --out run7.json  # one result per seed (Lesson 7)
    python train_mnist.py --checkpoint ckpt.pt      # resume if the file exists (Lesson 8)
    ```

[^1]: Access only in QUT network. Please use VPN to access the documentation when off-campus.
