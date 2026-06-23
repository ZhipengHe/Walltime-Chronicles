# Lesson 2: Tooling Setup

!!! quote "Mission Statement"
    *"Pick a Python tool, install it once, never fight with system Python again."* 🛠️

You'll spend more of your HPC life inside a Python environment than anywhere else. Aqua ships system Python for the sysadmin's sake, not yours — touching it for your own work is a recipe for permission errors, version conflicts, and "it worked yesterday." This lesson picks one isolated Python tool, installs it on Aqua, and proves it works. Fifteen minutes; one terminal; done.

## 📋 What You'll Accomplish

By the end of this 15-minute lesson, you'll have:

- [ ] **Picked one** Python tool — Miniconda or UV
- [ ] **Installed it on Aqua** (via the QUT module or a direct installer)
- [ ] **Created a test environment** with one package
- [ ] **Verified it works** — `python --version` + an import that doesn't crash

!!! tip "Pick one — don't install both your first time"
    Both are good choices. Learning one is plenty for the rest of this course. You can add the other later when you have a concrete reason. Your first interactive session (Lesson 1) used whichever Python Aqua gave you by default; from this lesson onward you control your own environment.

---

## Decide: Miniconda or UV?

The choice between them is mostly about what you'll *install* into the environment, not how you'll use it day-to-day. Both give you isolated environments. Both work fine on Aqua.

=== "Miniconda — for ML / data science / scientific stack"
    - **Why pick it:** Conda packages bundle their **binary / system dependencies** (CUDA runtime, MKL, glibc constraints). When you `conda install pytorch=2.2 cudatoolkit=12.1`, conda actually handles the CUDA side. pip can't do that.
    - **Speed:** Slower than UV when you're just adding pip packages. The trade-off is conda doing real work.
    - **Familiarity:** Industry default for HPC ML. Most QUT eResearch examples assume conda.

=== "UV — for pure-Python projects and speed"
    - **Why pick it:** Rust-based, **10–30× faster than pip** for installs and resolves. Wonderful when you're iterating on `requirements.txt` and not waiting on big binary packages.
    - **Limitation:** No equivalent of conda's binary-dependency handling. For CUDA-linked PyTorch you'll usually fall back to pip-installable wheels or pair UV with conda for the system bits.
    - **Familiarity:** Newer (Astral, late 2024), gaining ground fast. Drop-in for `pip` / `venv` workflows.

**Default if you can't decide:** Miniconda if your work involves PyTorch/TensorFlow/CUDA/scientific Python; UV otherwise.

---

## Install Miniconda

=== "Via QUT module (recommended)"
    Fastest path — QUT eResearch already ships Miniconda as a module. No download, no installer flags.

    ```bash
    module load Miniconda3/24.9.2-0   # or whatever's current — see note below
    conda init
    source ~/.bashrc
    ```

    Verify:

    ```bash
    conda --version
    ```

    !!! example "Expected output"
        ```text
        conda 24.9.2
        ```

    !!! note "Available Miniconda versions on Aqua"
        Run `module avail Miniconda3` to see what's currently shipped. There's also an `Anaconda3/2024.02-1` module if you want the full Anaconda distribution. Reference: [QUT eResearch — Conda package and environment manager](https://docs.eres.qut.edu.au/hpc-conda-package-and-environment-manager)[^1].

=== "Direct installer (if you need a specific version)"
    Only do this if the QUT module versions don't match what you need. Mirrors [QUT's official install-Conda guide](https://docs.eres.qut.edu.au/hpc-accessing-available-software#install-conda)[^1].

    ```bash
    # Download the installer into ~/miniconda3/
    cd ~ && mkdir -p ~/miniconda3
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
         -O ~/miniconda3/miniconda.sh

    # Run in batch mode (-b), update (-u), install to ~/miniconda3 (-p)
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
    rm ~/miniconda3/miniconda.sh

    # Activate base + persist for future shells
    source ~/miniconda3/bin/activate
    source ~/.bashrc
    ```

    Verify:

    ```bash
    conda --version
    which python
    ```

    !!! example "Expected output"
        ```text
        conda 25.x
        /home/your-username/miniconda3/bin/python
        ```

!!! warning "If `conda` isn't found after you log back in"
    Your `~/.bashrc` change may not have stuck for new shells. Re-source it, or add the PATH export explicitly:

    ```bash
    source ~/.bashrc
    # or, persistently:
    echo 'export PATH="/home/$USER/miniconda3/bin:$PATH"' >> ~/.bashrc
    ```

---

## Install UV

Astral's one-line installer — no Python prerequisite, ~5 seconds:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

Verify:

```bash
uv --version
```

!!! example "Expected output"
    ```text
    uv 0.11.x or newer
    ```

---

## Test Drive: Create a Project Environment

Now prove it works. Pick the tab matching what you just installed, run the four commands, and you're done.

=== "Miniconda"
    ```bash
    # Create an isolated environment with Python 3.11 and one package
    conda create -n hello-aqua python=3.11 requests -y

    # Activate it — your prompt should now show (hello-aqua) at the front
    conda activate hello-aqua

    # Prove Python and the package both work
    python -c "import requests, sys; print('Python', sys.version.split()[0], '/ requests', requests.__version__)"

    # Drop back out when done (the env still exists for next time)
    conda deactivate
    ```

    !!! example "Expected output"
        ```text
        Python 3.11.10 / requests 2.32.x
        ```

=== "UV"
    ```bash
    # Make a project folder + a venv inside it (with an explicit Python version)
    mkdir -p ~/hello-aqua && cd ~/hello-aqua
    uv venv .venv --python 3.13

    # Activate it — your prompt should now show (.venv) at the front
    source .venv/bin/activate

    # Install a package (watch how fast)
    uv pip install requests

    # Prove Python and the package both work
    python -c "import requests, sys; print('Python', sys.version.split()[0], '/ requests', requests.__version__)"

    # Drop back out when done (the venv lives in ~/hello-aqua/.venv)
    deactivate
    ```

    !!! note "First-run Python download"
        The first time you ask UV for a specific Python version (here, 3.13), it downloads a standalone CPython build (~33 MiB) into `~/.local/share/uv/python/`. Subsequent `uv venv --python 3.13` calls reuse it instantly. Without `--python`, UV picks whatever Python is on your PATH (on Aqua that's the system Python 3.9.x).

    !!! example "Expected output"
        ```text
        Python 3.13.x / requests 2.34.x or newer
        ```

!!! tip "Where to put environments"
    For tooling like this, `/home/$USER` is fine — environments are typically MB-to-low-GB, easy to back up, and Lustre handles them OK if you don't end up with hundreds of envs each carrying thousands of files. If you'll have a *huge* conda env (multi-GB PyTorch + CUDA + scientific libs), consider creating it on `/scratch/$USER/envs/` and symlinking — see [Know Your Nodes — File systems](../scheduler/Know-Your-Nodes.md) for the trade-off.

---

## 🎯 Key Takeaways

!!! success "You now have"

    🐍 **An isolated Python** that won't conflict with the system Python or other users

    🧪 **A working test environment** with at least one package installed

    🛠️ **A reproducible setup** — `conda create` or `uv venv` will reproduce the same shape next time

    📦 **Two tools you know exist** — even if you picked one, you know what the other is good for

---

## 🔗 What's Next?

→ **[Lesson 3: Your First Batch Job](lesson-3.md)** — now that you have Python ready, time to wrap a job script around it and submit to PBS for real.

!!! question "Stuck?"
    - **Conda or UV not found after install?** Re-source `~/.bashrc` or check `PATH` (see the warnings above).
    - **Want the official QUT reference?** [QUT eResearch — Conda package and environment manager](https://docs.eres.qut.edu.au/hpc-conda-package-and-environment-manager)[^1].
    - **Need a different tool entirely?** Aqua also has system Python via `module load Python/3.x` — but you'll be sharing it with everyone else. Stick with isolated envs.

---

## 📝 Quick Reference

=== "Conda basics"
    ```bash
    conda create -n <name> python=3.11    # new env
    conda activate <name>                  # enter env
    conda deactivate                       # leave env
    conda env list                         # see all envs
    conda env remove -n <name>             # delete env
    ```

=== "UV basics"
    ```bash
    uv venv .venv                          # new venv (uses system Python)
    uv venv .venv --python 3.13            # ...or pin a Python version (auto-downloads)
    source .venv/bin/activate              # enter venv
    uv pip install <pkg>                   # add a package (fast)
    uv pip install -r requirements.txt     # install from requirements
    deactivate                             # leave venv
    ```

=== "File locations"
    ```bash
    ~/miniconda3/                  # Miniconda install (if direct-installed)
    ~/miniconda3/envs/             # Conda environments
    ~/.local/bin/uv                # UV binary (standalone install)
    ~/.local/share/uv/python/      # UV-managed Python versions (one dir per version)
    ~/.cache/uv/                   # UV's package cache
    ```

[^1]: Access only in QUT network. Please use VPN to access the documentation when off-campus.
