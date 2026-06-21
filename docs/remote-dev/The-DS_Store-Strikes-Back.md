# The .DS_Store Strikes Back: Finder Edition

> *A long time ago, on a remote server far, far away...*

When working with remote servers from macOS, you'll inevitably encounter the dark side of the Force: hidden system files that follow your every move. These invisible menaces can break deployment scripts, bloat repositories, and generally cause chaos in your otherwise pristine remote environments.

!!! tip "Companion page"
    This is the macOS-only sidebar to [Surviving without VS Code Remote SSH](Surviving-without-VS-Code-Remote-SSH.md), which covers the broader workflow of editing and transferring files on Aqua. That page sends you here whenever you mount the HPC as a Finder share.

---

## :material-medical-bag: TL;DR Survival Kit

If you opened this page in a panic, here are the four commands that buy back peace and quiet.

```bash
# 1. Tell macOS to stop writing .DS_Store on network shares.
defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
killall Finder

# 2. Sweep what's already there (run from the offending folder; or remotely via SSH).
find . \( -name ".DS_Store" -o -name "._*" \) -delete

# 3. Strip AppleDouble metadata locally before you copy a folder to the HPC.
dot_clean ~/path/to/folder

# 4. Transfer from Terminal — Finder is the source of the problem, so don't use it.
rsync -avz --exclude='.DS_Store' --exclude='._*' ./project/ aqua:~/project/
```

Read on for the lore.

---

## :material-death-star-variant: Episode V: The .DS_Store Strikes Back

!!! warning "The Dark Side of macOS"
    Imperial `.DS_Store` files have driven Rebel developers from their remote server folders. These hidden files spread like the Dark Side across every folder you visit.

- **Darth `.DS_Store`**: "Your lack of `defaults write` is disturbing. My hidden files will spread across every folder you visit."

- **Luke:** "But I've tried `.gitignore`! It has no power here on remote connections!"

- **Yoda:** "Use the Terminal, Luke. Or the sacred command to disable .DS_Store on network volumes."

- **Han:** "I've been running from these hidden files for ten years. Not a remote server is safe in the galaxy!"

### :material-broom: Clean up the Dark Side

=== ":material-trash-can-outline: Sweep existing"

    ```bash
    # Run inside the affected directory, or remotely via SSH on the HPC.
    find . -name ".DS_Store" -delete
    ```

=== ":material-shield-outline: Prevent future"

    ```bash
    # Disable .DS_Store on *network* volumes (SMB / AFP / NFS).
    # Local drives are unaffected — those still get .DS_Store as normal.
    defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true

    # Restart Finder to pick up the change.
    killall Finder
    ```

    !!! info "Network volumes only"
        `DSDontWriteNetworkStores` does nothing for local APFS / HFS+ drives. That's intentional — the goal is to stop Finder polluting the HPC, not your laptop.

---

## :material-alien-outline: Episode VI: The Return of the Metadata (`._*`)

> *"The `._*` files are back, and they're more annoying than ever."*

!!! warning "The Hidden Menace"
    When you copy files to a remote server through Finder, macOS creates mysterious `._*` files. They're like the Ewoks of the file system — small, seemingly harmless, but they can cause big problems for Python imports, shell globs, and tarballs.

- **Darth Metadata**: "Your files are not complete without my metadata. I will follow them everywhere."

- **Luke**: "But these `._*` files are causing issues with my Python scripts!"

- **Yoda**: "Hidden they are, but dangerous they can be. Clean them you must."

### :material-trash-can-outline: Sweep existing `.DS_Store` *and* `._*` files

```bash
# Important: the parens are load-bearing. Without them, find's -o precedence
# makes -delete apply only to .DS_Store, and ._* files survive.
find . \( -name ".DS_Store" -o -name "._*" \) -delete
```

??? bug "Why the parens matter"
    `find` parses `-name "._*" -o -name ".DS_Store" -delete` as
    `( -type f -name "._*" ) -o ( -name ".DS_Store" -delete )`,
    so the `-delete` action only attaches to the second branch. The first branch silently falls back to the implicit `-print`. Result: `.DS_Store` gone, `._*` printed but very much still there. Wrap both `-name` clauses in `\( \)` to force the grouping.

### :material-information-outline: Why these files exist

macOS uses `._*` AppleDouble files to store data the destination filesystem can't natively hold:

- Resource forks
- Extended attributes (custom icons, tags, quarantine flags, code signatures…)
- Finder metadata

??? info "Filesystems that trigger AppleDouble creation"

    | Filesystem | Why `._*` appears |
    |---|---|
    | SMB shares (Linux Samba — including Aqua's `hpc-fs`) | No native xattr support |
    | FAT, exFAT, NTFS thumb drives | No native xattr support |
    | WebDAV mounts | Depends on server config |
    | APFS / HFS+ (local Mac drives) | **Doesn't happen** — xattrs are stored natively |

    The pattern: anything that isn't a native Mac filesystem becomes a source of `._*` litter.

### :material-shield-half-full: What you can't prevent — and what you can

There's no kill switch for `._*` files on non-extended-attribute filesystems. But you can keep the damage contained:

- **Mitigate at the source** — `dot_clean` locally before you copy (next section).
- **Sidestep entirely** — transfer from Terminal, never Finder (section after that).
- **Quarantine** — `.gitignore` so they don't leak into your repos (last section).

The previous version of this page joked that there was no solution. That was funny but unhelpful. The honest version: *creation* can't be fully prevented; *impact* can.

### :material-content-save-cog: `dot_clean` — Apple's built-in cleanup

`dot_clean(1)` ships with macOS and merges `._*` files back into their parents (preserving xattrs where the destination filesystem supports them) or strips them. Run it on the local copy *before* you transfer:

```bash
# Default: merge ._* back into the main file where possible, then remove.
dot_clean ~/path/to/folder

# Force-remove without trying to merge (use when you don't care about xattrs).
dot_clean -m ~/path/to/folder
```

After `dot_clean`, the folder is clean and any subsequent SCP / rsync transfer carries no AppleDouble residue.

### :material-rocket-launch: `rsync` to sidestep Finder entirely

Finder is the source of the mess. Terminal transfers (SCP, SFTP, rsync) don't create `._*` files at all because they don't go through the AppleDouble translation layer. The cleanest workflow is to never mount the HPC in Finder for the purpose of copying things — use this from Terminal instead:

```bash
# Push a local folder to Aqua, excluding macOS noise even if it sneaks in.
rsync -avz --exclude='.DS_Store' --exclude='._*' \
    ~/path/to/local/project/ \
    aqua:~/project/
```

For the broader SCP / SFTP / SSHFS comparison, see the [Surviving guide's transfer section](Surviving-without-VS-Code-Remote-SSH.md).

### :material-source-branch: For Git users

Add the patterns to your repo's `.gitignore` (and ideally your global gitignore at `~/.gitignore_global`):

```bash
# Write two distinct lines. `echo "._*\n.DS_Store"` writes a literal "\n" —
# .gitignore then matches neither pattern correctly.
printf '%s\n' '._*' '.DS_Store' >> .gitignore
```

This doesn't stop creation, but it stops the leakage into commits.

---

## :material-link-variant: See also

- [Surviving without VS Code Remote SSH](Surviving-without-VS-Code-Remote-SSH.md) — the parent page for the whole macOS-on-Aqua workflow (SMB, SSHFS, SFTP, Remote Tunnel).
- [`dot_clean(1)`](https://ss64.com/mac/dot_clean.html) — Apple's man page for the metadata-cleanup utility.
- [`defaults`](https://ss64.com/mac/defaults.html) — the macOS preferences-writing tool used to flip `DSDontWriteNetworkStores`.

---

## :material-star-four-points: Final Words

> *"The Force is strong with clean file systems."*

May your remote development be free of metadata files, and may the Force be with you. :rocket:
