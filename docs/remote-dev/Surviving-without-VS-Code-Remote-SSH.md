# Surviving without VS Code Remote SSH

> *"Or: "They took away my extension, but not my will to code.""*


!!! failure "VS Code Remote SSH is banned"
    QUT Aqua banned VS Code Remote SSH extension due to potential high workload on the node. Even you try to connect to Aqua through Remote SSH, it will be disconnected automatically after around 30 seconds.
    Check [this](https://docs.eres.qut.edu.au/hpc-vscode-usage#using-vs-code-to-edit-files-on-the-hpc) for more details.

So... you're trying to develop on QUT Aqua, but the server gods have other plans. Maybe you can't use VS Code Remote SSH. Maybe you're just feeling adventurous. But do not worry — you can still edit remote files and develop like a champ. Here's how I've kept my sanity while developing on remote HPC systems.

---

## :puzzle_piece: 1. Fake it with SSH-mounted folders 

### :cheese: Option A: Mount via Finder — the cheese board approach

> Here's a quick guide for macOS users. Please refer to the [official documentation](https://docs.eres.qut.edu.au/hpc-transferring-files-tofrom-hpc#using-file-explorer-or-finder-to-mount-a-drive-to-the-hpc) for other OS.

1. Open **Finder** → `Go` → `Connect to Server...`
2. Enter:

   ```
   smb://hpc-fs/home/
   ```
3. Mount it, then open the folder in VS Code like it's 1999.

:memo: *Note*: You can edit files, but **no shell**, **no Git**, and no terminal tantrums. It's like eating cake without the frosting.

#### But ... is this method elegant?

If you're a macOS user, you might have experienced the `.DS_Store` file issue. It's a hidden file that causes all sorts of trouble when you try to edit files on the HPC.

![DS_Store Meme](./images/DS_Store-meme.png) 

Check out [The .DS_Store Strikes Back: Finder Edition](./The-DS_Store-Strikes-Back.md) about why this is a problem and how to solve it (or not).

### :wrench: Option B: SSHFS — The slightly nerdier route

!!! warning "The below content is still under construction"

    I just started using SSHFS recently, so I'm not sure if this is a good idea. Need to test it out.

Mount your HPC home directory *directly* via SSH, no Finder fluff. It's like having your HPC filesystem in your pocket.

#### For macOS Users:
```bash
# Install the prerequisites
brew install macfuse
brew install --cask macfuse
brew install gromgit/fuse/sshfs-mac

# Mount your HPC home
mkdir ~/aqua
sshfs your-username@aqua.qut.edu.au:/home/your-username ~/aqua
```

#### For Linux Users (Ubuntu):
```bash
# Install SSHFS
sudo apt-get install sshfs

# Mount your HPC home
mkdir ~/aqua
sshfs your-username@aqua.qut.edu.au:/home/your-username ~/aqua
```

Then open it in VS Code:
```bash
code ~/aqua
```

✅ *Pro*: Looks local. Feels local.
✅ *Con*: Feels **too** local for large files. Might lag.

---

## 🔁 2. `rsync`, `scp` and `git`: Your old-school sync buddies

### Option A: `rsync` & `scp` — The Reliable Workhorse

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

### Option B: Git — The Version Control Way

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

💡 *Pro Tip*: Use `.gitignore` to avoid syncing unnecessary files

---

## 🖥️ 3. The Terminal-Only Approach

When all else fails, embrace the terminal:

```bash
ssh your-username@aqua.qut.edu.au
```

Then pick your weapon of choice:

* `vim` — For the brave
* `nano` — For the sane
* `neovim` — For the modern
* `emacs` — For the... unique

🎯 *Bonus*: Fast, keyboard-driven, and doesn't require GUI permission forms.

> *Note*: I will write another page about how to use `neovim` and its plugins to replace VS Code as a lightweight editor (with SSH).

---

## 🌐 4. The Web-Based Approach

### Option A: Jupyter Notebooks

!!! warning "The below content is still under construction"

    I'm not sure if this is a good idea. Need to test it out.

```bash
# On the HPC
module load anaconda3
jupyter notebook --no-browser --port=8888

# On your local machine
ssh -N -L 8888:localhost:8888 your-username@aqua.qut.edu.au
```

### Option B: VS Code in Browser

If your sysadmin hasn’t locked *everything* down:

1. Install [`code-server`](https://github.com/coder/code-server) on the cluster
2. Open it in your browser
3. Marvel as VS Code rises from the ashes — web-style

⚠️ *Warning*: This might require a sysadmin's blessing

---

## TL;DR — What Works Best?

| Method            | Edit in VS Code | Shell Access | File Sync | GUI Required |
| ----------------- | --------------- | ------------ | --------- | ------------ |
| SMB (Finder)      | ✅               | ❌            | ✅         | Yes          |
| SSHFS             | ✅               | ❌            | ✅         | No           |
| rsync / Git       | ✅ (local edit)  | ✅            | ✅         | No           |
| Terminal Editors  | ❌ (no GUI)      | ✅            | N/A       | No           |
| Jupyter           | ✅ (in browser)  | ✅            | ✅         | Yes          |
| code-server       | ✅ (in browser)  | ✅            | ✅         | Yes          |

---

## 🎯 Pro Tips for Remote Development

1. **Keep Your Sanity**
   ```bash
   # Add to your ~/.ssh/config
   Host aqua
       HostName aqua.qut.edu.au
       User your-username
       IdentityFile ~/.ssh/id_rsa_aqua # Add your SSH key here
       ServerAliveInterval 60
   ```

2. **Monitor Your Resources**
   ```bash
   # Check disk usage
   du -sh ~/aqua
   
   # Check sync status
   rsync -avzn ./local/ your-username@aqua.qut.edu.au:/remote/
   ```

3. **Backup Everything**
   ```bash
   # Regular backups
   rsync -avz --backup --backup-dir=../backups/$(date +%Y%m%d) ./project/ your-username@aqua.qut.edu.au:/remote/
   ```

---

## Final Words

Remote development on HPC doesn't have to be a pain. Pick your poison, set up your workflow, and remember: the best development environment is the one that doesn't make you want to throw your computer out the window.

Happy coding, and may your HPC connections be stable! 🚀
