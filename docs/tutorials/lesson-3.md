# Lesson 3: Working Interactively

!!! quote "Mission Statement"
    *"Interactive is where you develop. Batch is where you run."* 🧪

Lesson 1's interactive job was a round-trip with nothing in the middle. This lesson puts real work there: request a shell sized for it, run a training script on a compute node by hand, keep the session alive if your connection drops, and recognise when the work should become a batch job.

## 📋 What You'll Accomplish

By the end of this 15–20 minute lesson, you'll have:

- [ ] **Sized an interactive request** — cores, memory and walltime, inside the queue caps
- [ ] **Installed PyTorch and fetched `train_mnist.py`** with its data, on the login node
- [ ] **Run it by hand on a compute node** inside `qsub -I`
- [ ] **Kept a session alive across a dropped connection** with `tmux`
- [ ] **Known when to stop being interactive** and let Lesson 4 take over

!!! tip "You need Lesson 2's environment"
    Everything below assumes `~/hello-aqua/.venv` (uv) or the `hello-aqua` env (Miniforge / micromamba) from [Lesson 2](lesson-2.md) exists and works. If not, do the Test Drive there first; it takes two minutes.

---

## ⚖️ Part 1: Size the request (~3 min)

Lesson 1 asked for one core and one gigabyte because the point was to arrive somewhere. This time the point is to work, so the request has to fit the work, and it has to fit the queue.

PBS routes `qsub -I` to one of two interactive queues by whether you asked for a GPU:

| Queue | You get | Per job | Per user, all your interactive jobs | Walltime |
|---|---|---|---|---|
| `cpu_inter_exec` | a shell on `cpu1n001`, the single interactive CPU node | 1–8 cores, 1–34 GB | 8 cores, 34 GB | ≤ 12 h |
| `gpu_inter_exec` (`:ngpus=1`) | a shell plus **MIG slices**, ~10 GB of an H100 or ~20 GB of an A100 each, not whole cards | 1–12 cores, 1–68 GB, 1–2 slices | 12 cores, 68 GB, 2 slices | ≤ 12 h |

This lesson stays on CPU. For the GPU queue, [Know Your Nodes](../scheduler/Know-Your-Nodes.md) explains the slices and Recipe 7 in [Walltime by Recipe](../scheduler/Walltime-by-Recipe.md#recipe-7-mig-slice-sanity-check) has the ready-made line.

The caps come from the queues themselves (`qstat -Qf cpu_inter_exec`); the [eResearch queue page](https://docs.eres.qut.edu.au/hpc-queue-limits)[^1] rounds them to 32 and 64 GB. Ask for more than the cap and the job is rejected at submit time.

!!! warning "Interactive jobs hold what they asked for until you leave"
    A batch job frees its node when the script ends. An interactive job frees it when you `exit` or the walltime runs out, and every user on Aqua shares the one interactive CPU node. Request what the session needs, not the cap, and one or two hours of walltime, not twelve.

!!! example "This lesson's request"
    ```bash
    qsub -I -l select=1:ncpus=4:mem=8GB -l walltime=01:00:00
    ```

    - `ncpus=4` → the script reads `$NCPUS` and uses every core PBS gives it
    - `mem=8GB` → memory for the whole job, all processes together; enough for the script with room to turn the knobs up
    - `walltime=01:00:00` → an hour at the keyboard, not the 12 h cap

    You submit this in Part 3. Part 2 comes first, because installing and downloading belongs on the login node.

---

## 📦 Part 2: Get the script, its dependency, and its data (~4 min)

`train_mnist.py` trains a small network to recognise handwritten digits from **MNIST**, the 70,000-image dataset every machine-learning course starts with. It finishes in under a minute on a few cores, reads `$NCPUS` for its thread count, and writes its runtime and peak memory to `results.json`.

It needs only PyTorch. Install that into your Lesson 2 environment, download the script, and let the script fetch its data (12 MB, once). All of this is network and disk work, not compute, so the login node is the right place for it:

=== "uv"
    ```bash
    cd ~/hello-aqua
    source .venv/bin/activate

    # CPU build of PyTorch (about 800 MB installed; the CUDA build is gigabytes and only useful on a GPU node).
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
    host      aquarius02
    device    cpu  threads 1  seed 0
    download  https://ossci-datasets.s3.amazonaws.com/mnist/train-images-idx3-ubyte.gz
    download  https://ossci-datasets.s3.amazonaws.com/mnist/train-labels-idx1-ubyte.gz
    download  https://ossci-datasets.s3.amazonaws.com/mnist/t10k-images-idx3-ubyte.gz
    download  https://ossci-datasets.s3.amazonaws.com/mnist/t10k-labels-idx1-ubyte.gz
    data      60,000 training images, 10,000 test  (188 MB)
    done      test accuracy None  in 19.8s  -> results.json
    ```

    Four files land in `~/hello-aqua/data/mnist/`. Accuracy is `None` because nothing was trained.

[Download the script](scripts/train_mnist.py), or read it here:

??? note "`train_mnist.py`"

    ```python title="train_mnist.py"
    --8<-- "docs/tutorials/scripts/train_mnist.py"
    ```

---

## 🛠️ Part 3: Run it by hand on a compute node (~5 min)

Now the round-trip from Lesson 1, with work in the middle.

### Step 1: Request the node

```bash
qsub -I -l select=1:ncpus=4:mem=8GB -l walltime=01:00:00
```

Wait for the prompt to change to `cpu1n001`.

### Step 2: Activate and run

```bash
cd ~/hello-aqua
source .venv/bin/activate     # or: conda activate hello-aqua / micromamba activate hello-aqua

echo $NCPUS                   # → 4
python train_mnist.py
```

`$NCPUS` is set by PBS inside every job; the script reads it for its thread count.

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

    Eight passes over 60,000 digits and it reads 98% of the 10,000 it has never seen. The accuracies will match to a few decimals (the seed is fixed). The times will vary with whoever else is on `cpu1n001`, and the first epoch is slower while PyTorch warms up.

### Step 3: Read the summary

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
  "job_id": "12345678.aqua"
}
```

`job_id` is `$PBS_JOBID`, also set by PBS. `elapsed_s` and `peak_rss_mb` are what you carry to Lesson 4: about 25 s and 500 MB, against a request of 1 h and 8 GB.

---

## 🔌 Part 4: Survive a dropped connection (~3 min)

An interactive job's shell is your SSH session. Lose the connection and PBS ends the job, along with anything running in it. The cure is `tmux` on the **login node**, so the thing holding your job is not your Wi-Fi. You are still inside the job from Part 3, so leave it first:

```bash
exit                          # back on the login node
tmux new -s dev               # a session that outlives your connection

# Inside tmux, the same request as before:
qsub -I -l select=1:ncpus=4:mem=8GB -l walltime=01:00:00
```

Detach with ++ctrl+b++ then ++d++; the job keeps running. Reconnect later and reattach:

```bash
tmux attach -t dev
```

Those two keys and two commands are all this lesson needs; the [tmux cheat sheet](https://tmuxcheatsheet.com/) has the rest (windows, panes, scrolling).

!!! note "If your session seems to have vanished"
    - **Aqua has more than one login node** (`aquarius01`, `aquarius02`, …), and `ssh aqua.qut.edu.au` lands you on one of them. A tmux session lives on the node where you started it, so `tmux ls` on the other node shows nothing. Run `hostname` when you start the session, and check it again before assuming the session is gone.
    - **Sessions do not survive a login-node reboot.** Maintenance is the third Wednesday of each month; `time_until_outage.sh` tells you how far away it is.

`tmux` costs the login node nothing. What runs inside it still follows Lesson 1's rule: editing, `git` and `qsub` yes, the training run no.

!!! tip "Interactive or batch?"
    Before you start running things in an interactive job, ask: **am I waiting on the machine, or is it waiting on me?**

    - If you are typing, reading output, changing a parameter and running again, this is interactive work. Stay.
    - If you have set something going and are watching it, or would like to walk away, or intend to run it more than once with different inputs, it is a batch job. That is Lesson 4.

---

## 🎯 Key Takeaways

!!! success "You now know"

    ⚖️ **Interactive requests are sized for the session, not the maximum** — the caps are 8 cores / 34 GB (CPU) and 12 cores / 68 GB / 2 MIG slices (GPU), 12 h, and everything you ask for is held until you leave

    🛠️ **PBS tells your job what it got** — `$NCPUS` for the thread count, `$PBS_JOBID` for the record

    🔌 **`tmux` on the login node** keeps an interactive job alive across a dropped connection

    🛑 **Interactive is for developing; batch is for running** — the question is who is waiting on whom

---

## 🔗 What's Next?

→ **[Lesson 4: Your First Batch Job](lesson-4.md)** — the same script, submitted unattended.

!!! question "Stuck?"
    - **`qsub -I` sits at "waiting for job to start"?** There is one interactive CPU node and it may be full. Try fewer cores (`ncpus=2:mem=4GB`), or check `pbsnodeinfo | grep cpu1n001` to see how busy it is.
    - **`command not found: python` after the prompt changes?** You haven't activated the environment on the compute node. `source ~/hello-aqua/.venv/bin/activate` (or the conda equivalent) is per shell.
    - **The script tries to download on the compute node?** You skipped the `--epochs 0` fetch in Part 2, or ran from a different directory. Fetch once on the login node and keep `data/mnist/` next to the script.
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
    python train_mnist.py --epochs 30               # longer run
    python train_mnist.py --width 8192              # more memory and compute
    python train_mnist.py --threads 8               # more cores
    python train_mnist.py --device cuda             # the GPU PBS gave you
    python train_mnist.py --seed 7 --out run7.json  # one result per seed
    python train_mnist.py --checkpoint ckpt.pt      # resume if the file exists
    ```

[^1]: Access only in QUT network. Please use VPN to access the documentation when off-campus.
