# A PBS Survival Guide

> A guide nobody asked for, but everyone eventually needs.

Welcome to **Walltime Chronicles** — a personal documentation project capturing all the weird, confusing, and occasionally infuriating challenges I have faced while using **QUT's HPC systems** (powered by PBS).

If you have ever:

- Submitted a job that instantly failed for reasons only known to the cluster gods,
- Fought with `walltime` limits like you were disarming a bomb,
- Wondered why your script runs perfectly *except* when submitted through `qsub`,
- Or simply stared into the abyss of PBS logs...

Then this is the right place.

---

## What You'll Find Here

- :thread: **Mystery Errors & How I Solved Them**  
  Real issues with real fixes (and real frustration).

- :brain: **Tips, Workarounds, and Gotchas**  
  Things that *should* have been in the official docs.

- :hammer_pick: **PBS Scripts & Snippets**  
  Copy-paste-friendly templates with helpful comments.

- :test_tube: **Experiments & Mistakes**  
  Because learning is messy.

## What You'll Not Find Here

- :book: **Basic Linux Tutorials**  
  This isn't "Linux for Dummies". I assume you know your `ls` from your `rm -rf`.

- :scroll: **PBS 101**  
  No "What is PBS?" here. If you don't know what `qsub` means, start with the [official docs](https://docs.eres.qut.edu.au/about-aqua).

- :mortar_board: **Comprehensive Tutorials**  
  This is a collection of "Oh, that's why it failed!" moments, not a step-by-step guide to HPC mastery.

- :gear: **System Administration**  
  I'm not your sysadmin. If you need to configure the cluster, that's above my pay grade.

- :mag: **Debugging Your Code**  
  Your Python script is throwing errors? That's between you and your debugger. I'm here for PBS-related mysteries only.

- :rocket: **Performance Optimisation**  
  Want to make your code run faster? I'll share some tricks that *might* work, but no promises. This isn't a magic wand for your algorithms, just some PBS-specific tweaks that occasionally make things less slow.

---

## Disclaimer

!!! info "Before you start"
    Before you start using this guide, please read the [QUT HPC "Aqua" Official Documentation](https://docs.eres.qut.edu.au/about-aqua)[^1] and [Altair's PBS Pro Documentation](https://help.altair.com/2022.1.0/PBS%20Professional/PBSReferenceGuide2022.1.pdf) thoroughly.

[^1]: Access only in QUT network. Please use VPN to access the documentation when off-campus.

This is not an official QUT HPC "Aqua" guide. It is just my (occasionally ranty) collection of notes, meant to help others avoid the black holes I fell into. Use at your own risk — and sanity.

Happy queueing, and may your jobs always run on the first try.

---

## Contributing

If you have any suggestions or corrections, please feel free to open an issue or a pull request on [GitHub](https://github.com/ZhipengHe/Walltime-Chronicles).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE.md) file for details.


