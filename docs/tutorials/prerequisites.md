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
    See the official QUT guide: [Getting Started with High Performance Computing](https://docs.eres.qut.edu.au/hpc-getting-started-with-high-performance-computin#accessing-the-hpc) (access only in QUT network. Please use VPN to access the documentation when off-campus.)

### 🐧 Essential Linux Commands & File Systems

Working on HPC systems means living in the Linux command line. You don't need to be a shell expert, but you should be comfortable with basic navigation, file operations, and understanding how the file system is organized.

!!! info "Need to learn Linux fundamentals?"
    QUT eResearch provides an excellent tutorial: [Introduction to the Unix Shell for HPC Users](https://docs.eres.qut.edu.au/sn-index) - covers essential commands, file systems, and more (access only in QUT network. Please use VPN to access the documentation when off-campus.)

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

!!! example "JupyterLab (Recommended for Data Science)"
    ```bash
    # On HPC
    jupyter lab --no-browser --port=8888

    # On your local machine
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

!!! info "Detailed Setup Instructions"
    Each method has specific setup requirements and trade-offs. See our comprehensive guide: [Surviving without VS Code Remote SSH](../../remote-dev/Surviving-without-VS-Code-Remote-SSH) for step-by-step instructions, troubleshooting, and performance tips.

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
