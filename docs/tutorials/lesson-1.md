# Lesson 1: Environment Setup & First Interactive Session

!!! quote "Mission Statement"
    *"Getting your tools ready and taking the cluster for a test drive"* 🚗💨

Welcome to your first hands-on lesson! Think of this as setting up your workshop before building anything. We'll get your Python environment sorted, install some essential tools, and take QUT Aqua for a test drive with an interactive session.

## 📋 What You'll Accomplish

By the end of this 15-minute lesson, you'll have:

- [ ] **Python environment setup** - Miniconda or UV installed
- [ ] **First interactive session running** - Actually using compute resources
- [ ] **Clear understanding** of login vs compute nodes

!!! tip "Open Your Favourite Terminal Simulator!"
    Keep a terminal window open to QUT Aqua throughout this lesson. You'll be running commands as we go!

---

## :simple-python: Part 1: Python Environment Setup (8 minutes)

!!! tip "Choose Your Path"
    You can use either **Miniconda** OR **UV** for Python environment management. Both are excellent choices --
     pick the one that appeals to you! Learning one is perfectly sufficient for HPC work.

### 🐍 Installing Miniconda (5 minutes)

Miniconda is your Python environment lifesaver on HPC systems. No more "it works on my laptop" nightmares!

#### Why Miniconda on HPC?

!!! info "The Problem"
    HPC Python requires you to load modules before use, which can be cumbersome for development. Miniconda gives you:

    - **Full control** over Python versions
    - **Isolated environments** for different projects
    - **No permission headaches** when installing packages

#### Installation Steps

!!! tip "Shortcut: use the QUT-provided Miniconda module instead"
    If you don't need a specific Miniconda version, QUT eResearch already ships one. You can skip the install-yourself steps below and just:

    ```bash
    module load Miniconda3/24.9.2-0
    conda init
    source ~/.bashrc
    ```

    Verify with `conda --version`. An `Anaconda3/2024.02-1` module is also available if you want the full Anaconda distribution. See [QUT eResearch — Conda package and environment manager](https://docs.eres.qut.edu.au/hpc-conda-package-and-environment-manager)[^1] for details.

!!! info "Want to install Miniconda yourself? Follow QUT's official steps"
    For the install-yourself path, see [Accessing available software — Install Conda](https://docs.eres.qut.edu.au/hpc-accessing-available-software#install-conda) from QUT eResearch[^1]. The steps below mirror that guide.

1. **Download the installer** (from your home directory):

    ```bash
    cd ~
    # create the directory if it doesn't exist
    mkdir -p ~/miniconda3
    # download the installer and rename it to miniconda.sh
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
    ```

2. **Run the installer**:

    ```bash
    # run the installer
    # batch mode "-b"
    # update "-u"
    # install to ~/miniconda3 "-p"
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
    # remove the installer
    rm ~/miniconda3/miniconda.sh
    ```

3. **Activate the Base Environment**:

    ```bash
    # activate the base environment
    source ~/miniconda3/bin/activate
    ```

    !!! example "Installation Prompts"
        ```text
        Do you accept the license terms? [yes|no] → yes
        Miniconda3 will now be installed into this location:
        /home/your-username/miniconda3 → Press ENTER
        Do you wish the installer to initialize Miniconda3? → yes
        ```

4. **Activate the installation**:

    ```bash
    source ~/.bashrc
    ```

5. **Verify it worked**:

    ```bash
    conda --version
    which python
    ```

    !!! success "Expected Output"
        ```text
        conda 25.x  # whatever the latest installer ships
        /home/your-username/miniconda3/bin/python
        ```

#### Quick Environment Test

Create a test environment to make sure everything works:

```bash
conda create -n test-env python=3.11 -y
conda activate test-env
python --version
conda deactivate
```

!!! warning "Troubleshooting"
    If `conda` command isn't found after installation:
    ```bash
    export PATH="/home/$USER/miniconda3/bin:$PATH"
    echo 'export PATH="/home/$USER/miniconda3/bin:$PATH"' >> ~/.bashrc
    ```

### ⚡ Installing UV (3 minutes)

UV is the new hotness in Python package management - it's blazingly fast and perfect for HPC environments where every second counts.

#### Why UV?

!!! abstract "Speed Comparison"
    | Tool | Time to install requests |
    |------|-------------------------|
    | pip  | ~15 seconds |
    | conda | ~30 seconds |
    | **uv** | **~2 seconds** ⚡ |

#### Installation

If you set up conda above, you can drop UV into the base env. If you skipped conda, UV has a one-line standalone installer that doesn't need it:

=== "Inside conda base"
    ```bash
    conda activate base
    pip install uv
    ```

=== "Standalone (no conda needed)"
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.bashrc
    ```

#### Verify Installation

```bash
uv --version
```

!!! success "Expected Output"
    ```text
    uv 0.5.x  # or newer
    ```

#### Quick Test Drive

Let's see UV in action:

```bash
# Create a temporary directory
mkdir ~/uv-test && cd ~/uv-test

# Create a virtual environment with UV (super fast!)
uv venv test-venv

# Activate it
source test-venv/bin/activate

# Install a package (watch the speed!)
uv pip install requests

# Test it works
python -c "import requests; print('UV works! 🎉')"

# Clean up
deactivate
cd ~ && rm -rf ~/uv-test
```

---

## 🖥️ Part 2: Your First Interactive Session (7 minutes)

Now for the fun part - let's actually use some compute resources! Interactive sessions are perfect for testing, debugging, and exploring.

### Understanding the Architecture

!!! info "HPC Node Types"
    ```mermaid
    graph TB
        A[Your Laptop] -->|SSH| B[Login Node]
        B -->|qsub -I| C[Compute Node]
        B -->|File Management| D[Storage]
        C -->|Heavy Computing| D

        style B fill:#e1f5fe
        style C fill:#fff3e0
        style D fill:#f3e5f5
    ```

=== "Login Nodes"
    - **Purpose**: File management, job submission, light editing
    - **Resources**: Shared with all users
    - **Rules**: NO heavy computation allowed
    - **Think of it as**: The reception desk

=== "Compute Nodes"
    - **Purpose**: Your actual work happens here
    - **Resources**: Dedicated to your job
    - **Rules**: This is where you run everything
    - **Think of it as**: Your private office

### Starting an Interactive Session

Time to request some compute resources:

```bash
qsub -I -l walltime=00:30:00 -l select=1:ncpus=2:mem=4GB
```

!!! example "Command Breakdown"
    - `qsub -I` → Request an **interactive** session
    - `-l walltime=00:30:00` → Maximum 30 minutes
    - `-l select=1:ncpus=2:mem=4GB` → 1 node, 2 cores, 4GB RAM

### What Happens Next

!!! note "The Waiting Game"
    You'll see something like:
    ```text
    qsub: waiting for job 12345.aqua-head to start
    qsub: job 12345.aqua-head ready
    ```

    Then your prompt changes to indicate you're on a compute node (Aqua names compute nodes by type: `cpu1n001`, `cpu1n002`, ..., `gpu1n001`, ..., `mem1n001`):
    ```text
    [your-username@cpu1n001 ~]$
    ```

### Testing Your New Environment

Once you're on a compute node, let's test our setup:

```bash
# Check where you are
hostname
echo "I'm on a compute node! 🎯"

# Test conda
conda --version

# Test UV
uv --version

# Check your resources
echo "CPU info:"
lscpu | grep "CPU(s):"
echo "Memory info:"
free -h
```

### Quick Python Environment Test

Let's create a project-specific environment and test it:

```bash
# Create a new conda environment for a hypothetical project
conda create -n hpc-project python=3.11 numpy pandas -y

# Activate it
conda activate hpc-project

# Use UV to add more packages quickly
uv pip install matplotlib seaborn

# Quick test
python -c "
import numpy as np
import pandas as pd
import matplotlib
print('All packages imported successfully! 📦✅')
print(f'NumPy version: {np.__version__}')
print(f'Pandas version: {pd.__version__}')
print(f'Matplotlib version: {matplotlib.__version__}')
"
```

### Understanding Resource Usage

!!! tip "Monitoring Your Usage"
    ```bash
    # Check your job details
    qstat -f $PBS_JOBID

    # Monitor resource usage
    htop  # If available, or use 'top'
    ```

### Ending Your Interactive Session

When you're done exploring:

```bash
# Deactivate your environment
conda deactivate

# Exit the interactive session
exit
```

You'll be back on the login node, and your compute resources are released.

---

## 🎯 Key Takeaways

!!! success "You've Successfully Learned"

    ✅ **Environment Management**: Miniconda gives you Python superpowers on HPC

    ✅ **Fast Package Installation**: UV makes package management lightning quick

    ✅ **Interactive Computing**: You can test and debug directly on compute nodes

    ✅ **Node Architecture**: Login nodes vs compute nodes - know the difference!

!!! warning "Important Rules to Remember"

    🚫 **Never run heavy computation on login nodes**

    ✅ **Always use interactive sessions or jobs for real work**

    💾 **Environments persist** - you only need to set them up once

    ⏰ **Interactive sessions have time limits** - plan accordingly

---

## 🔗 What's Next?

!!! info "Coming Up in Lesson 2"
    Now that your environment is set up, you're ready to write and submit your first PBS job script! We'll cover:

    - PBS script anatomy
    - Writing your first job
    - Submitting and monitoring
    - Understanding output files

!!! question "Need Help?"

    - **Environment issues?** Check [Surviving without VS Code Remote SSH](../../remote-dev/Surviving-without-VS-Code-Remote-SSH/)
    - **Package problems?** See [Surviving without VS Code Remote SSH](../../remote-dev/Surviving-without-VS-Code-Remote-SSH/)
    - **Interactive session not starting?** Review [Guess, Request, Regret: The Art of Walltime](../../scheduler/The-Art-of-Walltime/)

---

## 📝 Quick Reference

=== "Essential Commands"
    ```bash
    # Conda basics
    conda create -n myenv python=3.11
    conda activate myenv
    conda deactivate

    # UV basics
    uv pip install package-name
    uv pip install -r requirements.txt

    # Interactive session
    qsub -I -l walltime=00:30:00 -l select=1:ncpus=2:mem=4GB
    ```

=== "File Locations"
    ```bash
    # Miniconda installation
    ~/miniconda3/

    # Conda environments
    ~/miniconda3/envs/

    # UV cache
    ~/.cache/uv/
    ```

=== "Troubleshooting"
    ```bash
    # If conda isn't found
    source ~/.bashrc
    export PATH="~/miniconda3/bin:$PATH"

    # If UV isn't found
    conda activate base
    which uv
    ```

Up next: **Lesson 2 — Your First PBS Job** *(coming soon)*. You'll learn to write a batch script, submit it, and read the output once it's published.

[^1]: Access only in QUT network. Please use VPN to access the documentation when off-campus.
