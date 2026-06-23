# Before You Start: Prerequisites Checklist

Before diving into the HPC Crash Course lessons, make sure you're prepared with these essential foundations. Don't worry — we're not asking for expert-level knowledge, just enough familiarity to be productive.

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
    QUT eResearch provides an excellent tutorial: [Intro to the Shell](https://docs.eres.qut.edu.au/sn-index)[^1] — covers essential commands, file systems, and more.

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
    **Absolute Paths** — Start from root (`/`), always work regardless of current location
    ```bash
    /home/your-username/projects/analysis
    /scratch/your-username/large-data
    /usr/local/bin/python
    ```

    **Relative Paths** — Start from your current location, shorter but context-dependent
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

- **Navigating between directories** — home, scratch, project spaces
- **Managing files** — copying scripts, moving data, organizing results
- **Running executables** — making scripts executable, finding programs
- **Understanding paths** — referencing files in job scripts, setting up workflows

The better you are with these basics, the less time you'll spend fighting the system and more time doing actual work!

### 📤 File Transfer & Remote Development

You'll also need a way to get files on and off Aqua. Pick at least one approach before starting — `rsync` over SSH is the workhorse for most workflows, but `scp`, mounted drives (SSHFS), JupyterHub, or VS Code Remote Tunnel all work depending on your setup.

!!! tip "Full tooling walkthrough"
    The detailed guide — five options compared (local-sync, SSHFS mount, JupyterHub, terminal editors, VS Code Tunnel) with platform-specific setup — lives in **[Cmd+Opt+Remote → Surviving without VS Code Remote SSH](../remote-dev/Surviving-without-VS-Code-Remote-SSH.md)**. Pick one method that fits your workflow and you're set.

!!! failure "Important: VS Code Remote SSH is NOT available on QUT Aqua"
    The standard VS Code Remote SSH extension is disconnected by Aqua's policies after ~30 seconds. The sanctioned replacement is **VS Code Remote Tunnel** running inside an interactive PBS job — covered in the guide linked above. Don't waste time trying to make Remote SSH work.

---

## 🧪 Quick Self-Assessment

!!! question "Test Yourself — Can you confidently:"

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

    **File Transfer:**

    - [ ] Transfer or access files on Aqua via at least one method (rsync, scp, SSHFS mount, JupyterHub, or VS Code Tunnel)?

    If you answered "no" to any of these, spend some time practicing before starting the lessons!

---

## 🚀 Ready to Start?

Once you've checked off all the prerequisites, you're ready to begin with [Lesson 1: HPC Fundamentals](lesson-1.md)!

[^1]: Access only in QUT network. Please use VPN to access the documentation when off-campus.
