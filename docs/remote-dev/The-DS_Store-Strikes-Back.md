# The .DS_Store Strikes Back: Finder Edition

> *A long time ago, on a remote server far, far away...*

## EPISODE V: THE .DS_STORE STRIKES BACK

!!! warning "The Dark Side of macOS"
    Imperial .DS_Store files have driven Rebel developers from their remote server folders. These hidden files spread like the Dark Side across every folder you visit.


- **Darth `.DS_Store`**: "Your lack of `defaults write` is disturbing. My hidden files will spread across every folder you visit."

- **Luke:** "But I've tried `.gitignore`! It has no power here on remote connections!"

- **Yoda:** "Use the Terminal, Luke. Or the sacred command to disable .DS_Store on network volumes."

- **Han:** "I've been running from these hidden files for ten years. Not a remote server is safe in the galaxy!"

### The Solution: Clean Up the Dark Side
1. **Remove Existing .DS_Store Files**
   ```bash
   # Clean up all .DS_Store files
   find . -name ".DS_Store" -delete
   ```

2. **Prevent Future .DS_Store Creation**
   ```bash
   # Disable .DS_Store on network volumes
   defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool TRUE
   
   # Restart Finder to apply changes
   killall Finder
   ```
---

## EPISODE VI: THE RETURN OF THE METADATA

> *"The ._ files are back, and they're more annoying than ever."*

!!! warning "The Hidden Menace"
    When you copy files to a remote server, macOS creates mysterious `._` files. They're like the Ewoks of the file system - small, seemingly harmless, but they can cause big problems.

- **Darth Metadata**: "Your files are not complete without my metadata. I will follow them everywhere."

- **Luke**: "But these `._` files are causing issues with my Python scripts!"

- **Yoda**: "Hidden they are, but dangerous they can be. Clean them you must."

### The Solution: Defeat the Metadata Menace

1. **Remove Existing Metadata Files**
   ```bash
   # Remove all ._ files
   find . -name "._*" -delete
   
   # Or clean both .DS_Store and ._ files
   find . -type f -name "._*" -o -name ".DS_Store" -delete
   ```

2. **Understanding the ._* Files - The Unstoppable Force**

    On macOS, preventing the creation of ._* files (AppleDouble metadata) entirely is not officially supported—especially on non-HFS+ or non-APFS volumes.

    **Why ._* files are created:**
    macOS uses ._* AppleDouble files to store:

        - Resource forks
        - Extended attributes (e.g., custom icons, tags)
        - Finder metadata

        These are automatically created when copying files to filesystems that don't support extended attributes, such as:
        - SMB shares (Linux Samba servers)
        - FAT, exFAT, NTFS drives
        - Some WebDAV volumes

3. **Best Available Solutions :question:**

    ***Just kidding, there are no best available solutions for this problem.*** That's why I said mount the remote server as a local drive by Finder is not a


4. **For Git Users**

    Add the following to your .gitignore file:
    ```bash
    # Add to your .gitignore (won't prevent creation, but prevents tracking)
    echo "._*\n.DS_Store" >> .gitignore
    ```

---

## Final Words

> *"The Force is strong with clean file systems."*

May your remote development be free of metadata files, and may the Force be with you! 🚀 