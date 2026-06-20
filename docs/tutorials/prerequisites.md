# Before You Start: Prerequisites Checklist

Before diving into the HPC Crash Course lessons, make sure you're prepared with these essential foundations. Don't worry - we're not asking for expert-level knowledge, just enough familiarity to be productive.

## 📋 Prerequisites Checklist

**Required before starting the lessons:**

- [ ] 🖥️ **QUT HPC access**: Confirmed SSH access to Aqua
- [ ] 💻 **Essential Linux commands**: Comfortable with `cd`, `ls`, `pwd`, `mkdir`, `cp`, `mv`, `rm`, `chmod`
- [ ] 📁 **Linux file system**: Understanding absolute vs relative paths, directory structure, home directory (`~`), root (`/`), permissions
- [ ] 📤 **File transfer method**: SCP, rsync, or remote editing setup complete

---

## 🤔 Why These Prerequisites Matter

### 🖥️ QUT HPC Access

You'll obviously need to be able to connect to QUT's Aqua system. If you can SSH in and see a command prompt, you're good to go!

!!! info "Need to set up access?"
    See the official QUT guide: [Getting Started with High Performance Computing](https://docs.eres.qut.edu.au/hpc-getting-started-with-high-performance-computin#accessing-the-hpc)[^1].

### 🐧 Essential Linux Commands & File Systems

Working on HPC systems means living in the Linux command line. You don't need to be a shell expert, but you should be comfortable with basic navigation, file operations, and understanding how the file system is organized.

!!! info "Need to learn Linux fundamentals?"
    QUT eResearch provides an excellent tutorial: [Intro to the Shell](https://docs.eres.qut.edu.au/sn-index) - covers essential commands, file systems, and more[^1].

#### Core Commands You'll Use Daily

!!! example "Navigation & Information"
    ```bash
    pwd                      # Show current directory
    ls                       # List files in current directory
    ls -la                   # List all files with details
    cd /path/to/directory    # Change to specific directory
    cd ~                     # Go to home directory
    cd ..                    # Go up one directory level
    ```

!!! example "File & Directory Operations"
    ```bash
    mkdir project-name       # Create a new directory
    mkdir -p deep/nested/dirs # Create nested directories
    cp source.txt dest.txt   # Copy a file
    cp -r folder/ backup/    # Copy entire directory
    mv oldname.txt newname.txt # Rename/move file
    rm filename.txt          # Delete file
    rm -rf directory/        # Delete directory and contents
    ```

!!! example "File Permissions & Ownership"
    ```bash
    chmod +x script.sh       # Make file executable
    chmod 755 my-script      # Set read/write/execute permissions
    ls -l filename           # Check file permissions
    ```

#### Understanding the Linux File System

The Linux file system is hierarchical, starting from the root directory (`/`). Understanding paths is crucial for navigating HPC systems effectively.

!!! tip "Path Types"
    **Absolute Paths** - Start from root (`/`), always work regardless of current location
    ```bash
    /home/your-username/projects/analysis
    /scratch/your-username/large-data
    /usr/local/bin/python
    ```

    **Relative Paths** - Start from your current location, shorter but context-dependent
    ```bash
    ./script.sh              # File in current directory
    ../parent-folder/file    # File in parent directory
    data/results/output.txt  # File in subdirectory
    ```

!!! note "Special Directory Shortcuts"
    ```bash
    ~        # Your home directory (/home/username)
    /        # Root of entire file system
    .        # Current directory (where you are now)
    ..       # Parent directory (one level up)
    -        # Previous directory (where you just were)
    ```

#### Why This Matters for HPC

On HPC systems, you'll constantly be:

- **Navigating between directories** - home, scratch, project spaces
- **Managing files** - copying scripts, moving data, organizing results
- **Running executables** - making scripts executable, finding programs
- **Understanding paths** - referencing files in job scripts, setting up workflows

The better you are with these basics, the less time you'll spend fighting the system and more time doing actual work!

### 🌐 Remote Development in HPC

Working on HPC systems requires different strategies than local development. Choose the approach that best fits your project needs and comfort level.

!!! failure "Important: VS Code Remote SSH is NOT Available on QUT Aqua"
    VS Code Remote SSH extension is automatically disconnected after ~30 seconds due to server policies. Don't waste time trying to make it work!

    QUT eResearch's sanctioned replacement is **VSCode Remote Tunnel** running inside an interactive job — see Option 5 below.

#### Option 1: Develop Locally, Sync to HPC 💻➡️🖥️

Write and test code locally, then transfer to HPC for execution.

!!! tip "Best for:"
    - Small to medium codebases
    - Projects with simple dependencies
    - When you prefer familiar local tools
    - Quick script development and testing

**Transfer Methods:**

```bash
# rsync - Efficient directory syncing (recommended)
rsync -avz ./my-project/ username@aqua.qut.edu.au:~/projects/

# Git-based workflow (clean and version-controlled)
git push origin main    # Push to repository
# Then on HPC: git pull origin main

# SCP - Simple file copying
scp script.py username@aqua.qut.edu.au:~/
```

!!! info "Need more transfer options?"
    QUT eResearch has the full reference — Windows Map Drive (`\\hpc-fs\<username>`), Mac Finder (`smb://hpc-fs/<username>/`), WinSCP, and the dedicated SFTP endpoint at `eresdtn01.qut.edu.au`: [Transferring files to/from the HPC](https://docs.eres.qut.edu.au/hpc-transferring-files-tofrom-hpc)[^1]. Useful for Windows users and large datasets.

#### Option 2: Mount HPC as Local Drive 🗂️💻

Make HPC files appear as local folders for seamless editing.

!!! example "SSHFS Method (Recommended)"
    ```bash
    # macOS
    brew install macfuse gromgit/fuse/sshfs-mac
    mkdir ~/aqua
    sshfs <username@aqua.qut.edu.au>:/home/username ~/aqua

    # Linux
    sudo apt install sshfs
    sshfs username@aqua.qut.edu.au:/home/username ~/aqua

    # Then edit in VS Code as if files were local
    code ~/aqua
    ```

!!! warning "Limitations"
    - Can be slow for large files
    - Git operations may be unreliable
    - Connection drops freeze the filesystem

#### Option 3: Web-Based Development 🌐💻

Use browser-based development environments running on HPC.

!!! tip "QUT JupyterHub (Recommended for Data Science)"
    QUT eResearch runs a managed JupyterHub at [https://jupyterhub.eres.qut.edu.au](https://jupyterhub.eres.qut.edu.au)[^1] — log in with your QUT credentials, click *Start My Server*, and you get a backing PBS job (default `Aqua - 1 core, 8 GB, 8 hours`) without writing a single script. First connect can take up to ~10 minutes while your job queues.

    Full walkthrough: [How to use JupyterHub](https://docs.eres.qut.edu.au/how-to-use-jupyterhub)[^1].

!!! example "Manual JupyterLab (for custom environments)"
    Use this when JupyterHub's defaults don't fit — custom conda env, specific GPU, longer walltime, non-standard kernel. Start it inside an interactive PBS job and tunnel the port over SSH.

    ```bash
    # Inside an interactive job on HPC
    jupyter lab --no-browser --port=8888

    # On your local machine, in a new terminal
    ssh -N -L 8888:localhost:8888 username@aqua.qut.edu.au

    # Open: http://localhost:8888
    ```

#### Option 4: Terminal Development 💻

Embrace the command line with powerful terminal editors.

!!! tip "Editor Options"
    - **nano** - Simple and beginner-friendly
    - **vim/neovim** - Powerful and efficient (steep learning curve)
    - **emacs** - Highly customizable

    ```bash
    ssh username@aqua.qut.edu.au
    nano my-script.py  # or vim, emacs
    ```

#### Option 5: VSCode Remote Tunnel 🔌

Run a tunneled VS Code session from inside an interactive PBS job. This is the eResearch-sanctioned replacement for the blocked Remote-SSH extension.

!!! tip "Best for:"
    - You want the VS Code Remote-SSH experience without breaking eResearch policy
    - You're comfortable holding an interactive PBS job for the length of your session
    - You're already signed in with a Microsoft or GitHub account

!!! example "Sketch"
    ```bash
    # 1. Start an interactive job
    qsub -I -l walltime=02:00:00 -l select=1:ncpus=2:mem=4GB

    # 2. Inside the job, fetch the VS Code CLI (once per home dir)
    curl -Lk 'https://code.visualstudio.com/sha/download?build=stable&os=cli-alpine-x64' \
      --output vscode_cli.tar.gz
    mkdir -p ~/bin && tar -xf vscode_cli.tar.gz -C ~/bin/ && rm vscode_cli.tar.gz

    # 3. Start the tunnel and follow the device-code prompt
    ~/bin/code tunnel
    ```

    On your local machine: open VS Code, click the green Remote icon (bottom-left), **Connect to Tunnel**, and pick the HPC node from the list.

!!! warning "Trade-off"
    Your editor lives inside an interactive PBS job — when the job ends, the tunnel ends. Great for half-day sessions; not for "leave VS Code open all week" workflows.

!!! info "Detailed Walkthrough"
    QUT eResearch has the screenshot-by-screenshot version: [VS Code Usage — Option 2: VSCode Remote Tunnel](https://docs.eres.qut.edu.au/hpc-vscode-usage#option-2-vscode-remote-tunnel)[^1].

!!! info "Detailed Setup Instructions"
    Each method has specific setup requirements and trade-offs. See our comprehensive guide: [Surviving without VS Code Remote SSH](../remote-dev/Surviving-without-VS-Code-Remote-SSH.md) for step-by-step instructions, troubleshooting, and performance tips.

---

## 🧪 Quick Self-Assessment

!!! question "Test Yourself - Can you confidently:"

    **HPC Access & Connection:**

    - [ ] Connect to QUT Aqua via SSH?
    - [ ] Know where to get help if your access isn't working?

    **Linux Commands & File Systems:**

    - [ ] Navigate to your home directory from anywhere? (`cd ~`)
    - [ ] List all files including hidden ones? (`ls -la`)
    - [ ] Create directories and navigate between them?
    - [ ] Copy and move files using command line?
    - [ ] Explain the difference between `/home/you/file` and `~/file`?
    - [ ] Make a script executable with `chmod`?

    **Remote Development Workflow:**

    - [ ] Choose between local development vs remote development approaches?
    - [ ] Transfer or access files on the cluster (rsync/scp, mounted drives, or direct editing)?
    - [ ] Set up at least one development method (SSHFS, JupyterLab, or terminal editing)?

    If you answered "no" to any of these, spend some time practicing before starting the lessons!

---

## 🚀 Ready to Start?

Once you've checked off all the prerequisites, you're ready to begin with [Lesson 0: HPC Fundamentals](lesson-0.md)!

[^1]: Access only in QUT network. Please use VPN to access the documentation when off-campus.
