# Surviving without VS Code Remote SSH

> *"Or: "They took away my extension, but not my will to code.""*

!!! failure "VS Code Remote SSH is banned"
    QUT Aqua banned VS Code Remote SSH extension due to potential high workload on the node. Even you try to connect to Aqua through Remote SSH, it will be disconnected automatically after around 30 seconds.
    Check [this](https://docs.eres.qut.edu.au/hpc-vscode-usage#using-vs-code-to-edit-files-on-the-hpc) for more details.

So... you're trying to develop on QUT Aqua, but the server gods have other plans. Maybe you can't use VS Code Remote SSH. Maybe you're just feeling adventurous. But do not worry — you can still edit remote files and develop like a champ. Here's how I've kept my sanity while developing on remote HPC systems.

---

??? tip "Before you start: Recommend to add a shortcut to `~/.ssh/config`"
    If you are using SSH keys to connect to the HPC, you can add a shortcut to `~/.ssh/config` to make your life easier. QUT Aqua documentation provides a [guide](https://docs.eres.qut.edu.au/hpc-getting-started-with-high-performance-computin#how-you-log-into-aqua-depends-on-the-operating-system-of-your-computer) on how to set up SSH keys for passwordless login.

    ```bash
    # Add to your ~/.ssh/config
    Host aqua
        HostName aqua.qut.edu.au
        User your-username
        IdentityFile ~/.ssh/id_rsa_aqua # Add your SSH key here
        ServerAliveInterval 60
    ```
    Then, you can connect to the HPC by running `ssh aqua`. Also, you can use `aqua` to replace `your-username@aqua.qut.edu.au` in the following commands.

## :puzzle_piece: 1. Fake it with SSH-mounted folders

### :cheese: Option A: Mount via Finder

> Here's a quick guide for macOS users. Please refer to the [official documentation](https://docs.eres.qut.edu.au/hpc-transferring-files-tofrom-hpc#using-file-explorer-or-finder-to-mount-a-drive-to-the-hpc) for other OS.

1. Open **Finder** → `Go` → `Connect to Server...`
2. Enter:

    ```text
    smb://hpc-fs/home/
    ```

3. Mount it, then open the folder in VS Code like it's 1999.

:memo: *Note*: You can edit files, but **no shell**, **no Git**, and no terminal tantrums. It's like eating cake without the frosting.

#### But ... is this method elegant?

You've mounted an SMB share to your Finder. Congratulations! You've just volunteered for the following comedy of errors:

1. **Git Limitations** - Your version control system becomes severely limited over SMB. Git operations that work fine locally will fail or behave unpredictably through the mounted share.
2. **VS Code Terminal Issues** - The integrated terminal in VS Code won't work properly with mounted SMB shares. You'll get `Command not found` errors for most terminal operations.
3. **Connection Stability** - SMB connections can drop unexpectedly, especially during longer work sessions or when the network is unstable.
4. **HPC Dependency** - Since all your files live on the server, any HPC maintenance or downtime makes your work completely inaccessible.
5. **The .DS_Store Problem (macOS)** - Your Mac will create `.DS_Store` files in every folder you visit through Finder. These desktop service files clutter the HPC filesystem and serve no purpose on the server.

??? tip "For macOS users only: How to fix the .DS_Store and ._* files issue"
    ![DS_Store Meme](./images/DS_Store-meme.png)

    Check out [The .DS_Store Strikes Back: Finder Edition](./The-DS_Store-Strikes-Back.md) about why this is a problem and how to solve it (or not).

### :wrench: Option B: SSHFS — Mount through SSH Wizardry

Mount your HPC home directory *directly* via SSH, no Finder fluff. It's like having your HPC filesystem in your pocket.

#### For macOS Users

```bash
# Install the prerequisites (because your Mac doesn't come with everything, despite what Apple claims)
brew install macfuse
brew install gromgit/fuse/sshfs-mac

# Mount your HPC home (1)
mkdir ~/aqua
sshfs your-username@aqua.qut.edu.au:/home/your-username ~/aqua #(2)

# When you're done pretending these files are local
umount ~/aqua
# Or if that fails spectacularly (as technology loves to do)
diskutil unmount ~/aqua
```

1. When you're running `sshfs` first time, you will be asked to go to "System Preferences" → "Security & Privacy" → "Security" → click "Allow" for running the app. Then you also need to restart your Mac.
2. You can use `aqua` to replace `your-username@aqua.qut.edu.au` if you have added a shortcut to `~/.ssh/config`.

#### For Linux Users (Ubuntu)

```bash
# Install SSHFS (because of course Linux makes you work for everything)
sudo apt install sshfs

# Mount your HPC home, telling the laws of physics to take a break
mkdir -p ~/aqua
sshfs your-username@aqua.qut.edu.au:/home/your-username ~/aqua -o follow_symlinks

# To send these files back to their natural habitat
fusermount -u ~/aqua
```

#### For Windows Users

Install [WinFSP](https://github.com/winfsp/winfsp/releases) and [SSHFS-Win](https://github.com/winfsp/sshfs-win/releases), because Windows needs two separate things to do what other systems accomplish with one. Then use Windows Explorer (which Microsoft keeps renaming as if that will make us forget its bugs) to map a network drive:

```text
\\sshfs\your-username@aqua.qut.edu.au
```

Then open it in VS Code like you've just performed a miracle:

```bash
code ~/aqua
```

:check_mark: *Pro*:

- Looks local. Feels local.
- Git operations work... until they mysteriously don't

:x: *Con*:

- Feels **too** local for large files. Might lag.
- If the connection drops, your filesystem freezes like it's seen a ghost

??? tip "Performance Tips That Might Help (No Promises)"
    - Use `-o cache=yes` to create the illusion of performance (side effects may include file synchronization existential crises)
    - Add `-o compression=yes` to squeeze your data through the internet tubes more efficiently
    - If everything hangs, adjust your `ServerAlive` settings, which is like giving your connection a gentle nudge every few minutes to check if it's still breathing

??? info "Working with Git Over SSHFS: A Tragicomedy"
    When using Git over SSHFS, you're essentially asking Git to perform a synchronized swimming routine while blindfolded. For anything more complex than a simple commit, consider SSH-ing directly into the server and running Git commands there. Your future self will thank you for not testing the limits of your patience.

??? tip "For macOS users only: Still cannot get rid of the .DS_Store and ._* files?"
    ![DS_Store Meme](./images/DS_Store-meme.png)

    Check out [The .DS_Store Strikes Back: Finder Edition](./The-DS_Store-Strikes-Back.md) about why this is a problem and how to solve it (or not).

---

## :repeat: 2. `rsync`, `scp` and `git`: Your old-school sync buddies

### :gear: Option A: `rsync` & `scp` — The Reliable Workhorse

```bash
# Sync your local code to HPC
rsync -avz ./my-project/ your-username@aqua.qut.edu.au:/home/your-username/projects/

# Sync back from HPC
rsync -avz your-username@aqua.qut.edu.au:/home/your-username/projects/ ./my-project/
```

Or for a quick one-file fling:

```bash
scp script.py your-username@aqua.qut.edu.au:/home/your-username/projects/
```

It's not fancy, but it works — like duct tape.

### :simple-git: Option B: Git — The Version Control Way

If you are version-controlling your life (as you should), Git is a clean and reliable method.

```bash
# On your local machine
git init
git add .
git commit -m "Initial commit"
git remote add aqua your-username@aqua.qut.edu.au:/path/to/repo
git push aqua main

# On the HPC
git clone your-username@aqua.qut.edu.au:/path/to/repo
```

:check_mark: *Pro*: Clean history, branch control, reproducibility

:x: *Con*: Needs initial setup and your SSH keys must behave

---

## :desktop_computer: 3. The Terminal-Only Approach

When all else fails, embrace the terminal:

```bash
ssh your-username@aqua.qut.edu.au
```

Then pick your weapon of choice:

- `vim` — For the brave
- `nano` — For the sane
- `neovim` — For the modern
- `emacs` — For the... unique

:direct_hit: *Bonus*: Fast, keyboard-driven, and doesn't require GUI permission forms.

> *Note*: I will write another page about how to use `neovim` and its plugins to replace VS Code as a lightweight editor (with SSH).

---

## :globe_with_meridians: 4. The Web-Based Approach

### :simple-jupyter: Option A: Jupyter Notebooks

!!! info "Install Jupyter Lab in HPC before you start"
    The official Aqua documentation provides a [guide](https://docs.eres.qut.edu.au/hpc-accessing-available-software#install-conda) on how to install Miniconda in HPC.

```bash
# On the HPC
# I prefer to use Jupyter Lab instead of Jupyter Notebook
jupyter lab --no-browser --port=8888 # (1)

# On your local machine, forward the port 8888 to your local machine
# local_port:localhost:remote_port (2)
ssh -N -L 8888:localhost:8888 your-username@aqua.qut.edu.au
```

1. If port 8888 is already in use, you can try another port, e.g. 8889.
2. `-N` means no command to run on the remote machine. `-L` means forward the local port to the remote port. Both local and remote ports are 8888 in this case.

### :material-microsoft-visual-studio-code: Option B: VS Code in Browser

:warning: *Warning*: This might require a sysadmin's blessing! Fortunately, the server gods haven't locked *everything* down:

1. Install [`code-server`](https://github.com/coder/code-server) on the HPC.

    ```bash
    # On HPC server
    # Install code-server to your home directory
    curl -fsSL https://code-server.dev/install.sh | sh -s -- --method standalone --prefix=$HOME
    # code-server will be installed to $HOME/bin/code-server

    # check if code-server is installed
    code-server --version

    # Start code-server
    code-server  --bind-addr 127.0.0.1:8080 --disable-telemetry --disable-update-check --auth none

    # On your local machine
    # Forward the port 8080 to your local machine
    ssh -N -L 8080:127.0.0.1:8080 your-username@aqua.qut.edu.au
    ```

2. Open it in your browser

    ```text
    # Open the web page in your browser
    http://localhost:8080
    ```

3. Marvel as VS Code rises from the ashes — web-style

??? tip "Sync VS Code settings to code-server"
    You can import your VS Code settings to code-server by importing the profile from VS Code. Check out [this page](https://code.visualstudio.com/docs/configure/profiles#_share-profiles) for more details about how to export and import profiles. However, this's not the perfect solution. Not all VS Code extensions are available for code-server, some extensions are restricted for Microsoft VS Code. Only the extensions that are available for code-server are listed in [Open VSX Registry](https://open-vsx.org/).

??? tip "Run code-server in the background with `tmux`"
    You can run code-server in the background with `tmux` to avoid the session being killed after you disconnect from the HPC.

    ```bash
    # Start a new tmux session
    tmux new -s code

    # Run code-server in the background
    code-server --bind-addr 127.0.0.1:8080 --disable-telemetry --disable-update-check --auth none

    # Detach from the tmux session: `Ctrl+b`, then `d`

    # Reattach to the tmux session
    tmux attach -t code

    # Kill the tmux session
    tmux kill-session -t code

    # If you forget the session name, you can list all sessions
    tmux ls
    ```

??? failure "Known issue on Integrated Terminal and Extension Host"
    I found that the terminal and the extension host are not stable when using code-server. The issue seems to revolve around the **ptyHost**, **File Watcher**, and **Extension Host**, and it's being **repeatedly killed by SIGTERM**.

    :brain: **What Is Happening?**

    ```log
    [12:18:01] ptyHost terminated unexpectedly with code null
    [12:18:01] [File Watcher (universal)] restarting watcher after unexpected error: terminated by itself with code null, signal: SIGTERM (ETERM)
    [12:18:01] [127.0.0.1][d0f383fd][ExtensionHostConnection] <3126357> Extension Host Process exited with code: null, signal: SIGTERM.
    [12:18:02] [127.0.0.1][d0f383fd][ExtensionHostConnection] Unknown reconnection token (seen before).
    [12:18:02] [127.0.0.1][368c67ad][ExtensionHostConnection] New connection established.
    [12:18:02] [127.0.0.1][368c67ad][ExtensionHostConnection] <3132486> Launched Extension Host Process.
    ```

    From the logs:

    * :collision: The `ptyHost` process (responsible for terminal sessions) crashed or was killed — possibly due to system resource limits or policy.
    * :card_file_box: File watcher was forcefully killed (SIGTERM) — system or job policy likely did this.
    * :puzzle_piece: Extension host was also killed — same reason, likely tied to HPC rules.
    * :arrows_counterclockwise: code-server tried to reconnect to the crashed extension host but failed.
    * :new: code-server restarted the extension host process automatically.

---

## TL;DR — What Works (and What Requires Sacrifice)

| :hammer_and_wrench: Method | :woman_technologist: Edit in VS Code | :desktop_computer: Terminal Access | :file_folder: Where Files Live            | :frame_photo: GUI Needed | :zap: Vibe Check                       |
| ---------------------------- | ------------------------------------- | ----------------------------------- | ------------------------------------------ | ---------------------------- | -------------------------------------- |
| **SMB (Finder)**             | :white_check_mark: Yes, like it's local                | :x: Nope, just files                  | :file_cabinet: Remote (mounted)           | :white_check_mark: Yes                        | :cheese: "Cheesy but it works"         |
| **SSHFS**                    | :white_check_mark: Yes (mostly)                        | :x: Not really                        | :file_cabinet: Remote (mounted)           | :x: Nope                       | :turtle: "Kinda slow, kinda cool"      |
| **rsync / Git**              | :white_check_mark: Edit local, sync later              | :white_check_mark: Full control                      | :house: Local (then synced)                | :x: Nope                       | :toolbox: "Old school, solid"          |
| **Terminal Editors**         | :x: No GUI, no problem                  | :white_check_mark: Born in the terminal              | :file_cabinet: Remote (SSH only)          | :x: Nope                       | :crossed_swords: "For shell warriors" |
| **Jupyter**                  | :white_check_mark: Yes, via browser                    | :white_check_mark: If allowed                        | :file_cabinet: Remote (Jupyter workspace) | :white_check_mark: Yes                        | :test_tube: "Science with style"      |
| **code-server**              | :white_check_mark: Yes, but web-based                  | :question: Unstable                    | :file_cabinet: Remote (in browser)        | :white_check_mark: Yes                        | :genie: "Feels like cheating"          |

---

## Final Words

Remote development on HPC doesn't have to be a pain. Pick your poison, set up your workflow, and remember: the best development environment is the one that doesn't make you want to throw your computer out the window.

Happy coding, and may your HPC connections be stable! 🚀
