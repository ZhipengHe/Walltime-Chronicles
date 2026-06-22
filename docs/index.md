# A PBS Survival Guide

> A guide nobody asked for, but everyone eventually needs.

Welcome to **Walltime Chronicles** — a personal documentation project capturing all the weird, confusing, and occasionally infuriating challenges I have faced while using **QUT's HPC systems** (powered by PBS).

If you have ever:

- Submitted a job that instantly failed for reasons only known to the cluster gods,
- Fought with `walltime` limits like you were disarming a bomb,
- Wondered why your script runs perfectly *except* when submitted through `qsub`,
- Or simply stared into the abyss of PBS logs…

Then this is the right place.

!!! tip "Crash Course Café — opinionated onboarding for newcomers"
    Lessons 0 and 1 of the [Crash Course Café](tutorials/index.md) are now shipped — prerequisites checklist, HPC fundamentals, and your first interactive session. More lessons land as I write them; no promises on completion dates.

---

## :material-compass-outline: Where to Start

Pick your entry point. Each card is one shipped page.

<!-- markdownlint-disable MD033 -->
<div class="grid cards" markdown>

- :material-school: **New to QUT Aqua?**

    ---

    Start with the prerequisites checklist, then walk through HPC fundamentals (L0) and your first interactive session (L1).

    [:octicons-arrow-right-24: Crash Course Café](tutorials/index.md)

- :material-server-network: **Picking hardware?**

    ---

    Three-tier field guide to every node on Aqua — H100s, A100 MIG slices, large-memory boxes, the watchdog queue. Tells you which queue backs which silicon.

    [:octicons-arrow-right-24: Know Your Nodes](scheduler/Know-Your-Nodes.md)

- :material-timer-sand: **Sizing walltime?**

    ---

    The 2× rule, queue ceilings, scaling rules by workload (CPU complexity classes, GPU architectures), and a worked ResNet finetune example.

    [:octicons-arrow-right-24: The Art of Walltime](scheduler/The-Art-of-Walltime.md)

- :material-chef-hat: **Writing batch scripts?**

    ---

    Copy-paste recipe that sequentially runs N experiments inside one PBS job — timestamped names, modules + venv, log banners, and `qsub`.

    [:octicons-arrow-right-24: Batch-Cooking PBS Scripts](pbs-scripts/Batch-Cooking-PBS-Scripts-with-a-Bash-Pan.md)

- :material-microscope: **Inspecting past jobs?**

    ---

    A user-friendly alternative to `qjobs -x` — walltime usage %, CPU saturation, GPU utilisation, memory footprint, all in one tasting-notes table.

    [:octicons-arrow-right-24: PBS Brew Inspector](pbs-scripts/PBS-Brew-Inspector.md)

- :material-apple: **macOS remote-dev pain?**

    ---

    Survival paths when VS Code Remote-SSH isn't an option, plus the standalone guide to taming `.DS_Store` and `._*` files when Finder mounts the HPC.

    [:octicons-arrow-right-24: Surviving without Remote-SSH](remote-dev/Surviving-without-VS-Code-Remote-SSH.md)

</div>
<!-- markdownlint-enable MD033 -->

---

## :material-clipboard-list-outline: What You'll Find Here

- :material-bug-outline: **Mystery errors & how I solved them** — real issues with real fixes (and real frustration).
- :material-lightbulb-on: **Tips, workarounds, and gotchas** — things that *should* have been in the official docs.
- :material-script-text-outline: **PBS scripts & snippets** — copy-paste-friendly templates with helpful comments.
- :material-flask-outline: **Experiments & mistakes** — because learning is messy.

## :material-cancel: What You'll Not Find Here

- :material-book-open-variant: **Basic Linux tutorials** — this isn't "Linux for Dummies". I assume you know your `ls` from your `rm -rf`.
- :material-school-outline: **PBS 101** — no "What is PBS?" here. If you don't know what `qsub` means, start with the [official docs](https://docs.eres.qut.edu.au/about-aqua)[^1].
- :material-format-list-checks: **Comprehensive tutorials** — this is a collection of "oh, *that's* why it failed!" moments, not a step-by-step path to HPC mastery.
- :material-cog-outline: **System administration** — I'm not your sysadmin. If you need to configure the cluster, that's above my pay grade.
- :material-bug: **Debugging your code** — your Python script is throwing errors? That's between you and your debugger. I'm here for PBS-related mysteries only.
- :material-rocket-launch: **Performance optimisation** — want to make your code run faster? I'll share some tricks that *might* work, but no promises. This isn't a magic wand for your algorithms, just PBS-specific tweaks that occasionally make things less slow.

---

## :material-shield-alert-outline: Disclaimer

!!! info "Before you start"
    Before you start using this guide, please read the [QUT HPC "Aqua" Official Documentation](https://docs.eres.qut.edu.au/about-aqua)[^1] and [Altair's PBS Pro Reference Guide](https://help.altair.com/2022.1.0/PBS%20Professional/PBSReferenceGuide2022.1.pdf) thoroughly.

This is not an official QUT HPC "Aqua" guide. It is just my (occasionally ranty) collection of notes, meant to help others avoid the black holes I fell into. Use at your own risk — and sanity.

Happy queueing, and may your jobs always run on the first try.

---

## :material-source-pull: Contributing

If you have any suggestions or corrections, please feel free to open an issue or a pull request on [GitHub](https://github.com/ZhipengHe/Walltime-Chronicles).

## :material-license: License

This project is licensed under the MIT License. See the [LICENSE](LICENSE.md) file for details.

[^1]: Access only in QUT network. Please use VPN to access the documentation when off-campus.
