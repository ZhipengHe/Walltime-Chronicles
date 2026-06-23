# Getting Started: HPC Crash Course

Welcome to the Crash Course Café! ☕ Pull up a chair and let's get you productive on QUT Aqua without the usual learning curve headaches.

!!! info "Course is mid-restructure (2026-06-23)"
    The Crash Course is migrating from a topic-driven 0–7 outline to a **workflow-driven 1–7 outline**, where each lesson ends with a tangible deliverable. The new outline is below.

    - **Lessons 1 and 2** show **pre-rewrite content** — accurate, but the upcoming rewrites will reshape the structure (Lesson 1 absorbs a hands-on SSH/interactive-job at the end; Lesson 2 focuses purely on tooling install).
    - **Lessons 3–7** are **stubs** with scope contracts and pointers to existing deeper guides.

    Per-lesson rewrites land as they're written.

---

## Course Overview

### What This Course Covers

This isn't your typical academic introduction to high-performance computing. This is a practical, no-nonsense guide to getting real work done on QUT's Aqua system. We'll focus on the essential skills you need to submit jobs, avoid common mistakes, and not look like a complete newbie in your first week.

### Who This Is For

- **New to HPC/PBS**: You've heard scary stories about command lines and job schedulers
- **New to QUT Aqua**: You've used other HPC systems but Aqua has its own quirks
- **Impatient learners**: You want to be productive today, not after reading 200 pages of documentation

### Course Philosophy

#### Quick Wins Over Comprehensive Theory

We'll teach you the 20% of knowledge that handles 80% of your daily tasks. Deep theory can wait until you actually need it.

#### Practical Solutions Over Academic Explanations

Every concept comes with copy-paste ready examples and real-world context from QUT Aqua.

#### QUT Aqua-Specific Focus

Generic PBS tutorials are everywhere. This course is tailored specifically to QUT's configuration, quirks, and common issues.

### What You'll Learn

By the end of this crash course, you'll be able to:

- **Connect to Aqua and run an interactive job** without breaking anything
- **Submit your first PBS batch job** — and find its output
- **Diagnose common failures** before panicking
- **Right-size resource requests** — cores, memory, walltime, GPU
- **Scale beyond a single job** — arrays for bulk work, dependencies for long pipelines
- **Know when to dig deeper** into the specialized guides

### What You Need

- **Basic command line familiarity**: You can navigate directories and edit files
- **QUT account access**: You can SSH into Aqua
- **A specific task in mind**: Having real work to do makes learning stick

### What You DON'T Need

- Deep understanding of parallel computing
- Experience with other job schedulers
- Perfect knowledge of every PBS directive

### Course Structure

#### Time Commitment

- **Total time**: ~2 hours across **7 focused lessons**
- **Lesson format**: 15–20 minutes each
- **Hands-on from Lesson 1**: First SSH connection and an interactive job within the opening lesson
- **Follow-up learning**: Each lesson connects to detailed guides for when you need more

#### How This Connects to Other Guides

This crash course is your launching pad. When you hit specific challenges, you'll know exactly which detailed guide to consult:

- **Remote development issues** → [Cmd+Opt+Remote](../remote-dev/index.md)
- **Walltime estimation** → [The Scheduler's Gambit](../scheduler/index.md)
- **PBS script patterns** → [PBS Cookbook](../pbs-scripts/index.md)

#### Next Steps After Completion

1. **Practice with your real work** — apply what you've learned immediately
2. **Bookmark the troubleshooting guides** — for when things inevitably go wrong
3. **Join the QUT HPC community** — share your own discoveries and pain points

---

## Prerequisites

**Required before starting the lessons:**

- [ ] **QUT HPC access**: Confirmed SSH access to Aqua
- [ ] **Essential Linux commands**: Comfortable with `cd`, `ls`, `pwd`, `mkdir`, `cp`, `mv`, `rm`, `chmod`
- [ ] **Linux file system**: Understanding absolute vs relative paths, directory structure, home directory (`~`), root (`/`), permissions
- [ ] **File transfer method**: SCP, rsync, or remote editing setup complete

*Need help with setup? See the [Prerequisites Checklist](prerequisites.md) for verification commands, then [Cmd+Opt+Remote](../remote-dev/index.md) for tooling options.*

---

## Course Outline

### Lesson 1: Welcome to Aqua (15 min)

> *"What is this magical compute cluster anyway?"*

- Cluster mental model — file systems, login vs compute nodes
- First SSH connection and a 5-minute interactive job
- Where to put your files (home / scratch / work / TMPDIR)

[→ Lesson 1](lesson-1.md) — *pre-rewrite content (was Lesson 0: HPC Fundamentals)*

### Lesson 2: Tooling Setup (15 min)

> *"Getting your Python tools ready"*

- Pick one: uv (default) or Miniforge / micromamba (for conda-forge packages)
- Install via upstream installers — no QUT module needed (~5 to ~30 seconds per tool)
- Create a test environment, verify it works

[→ Lesson 2](lesson-2.md) — *pre-rewrite content (was Lesson 1: Environment Setup & First Interactive Session)*

### Lesson 3: Your First Batch Job (15–20 min)

> *"Hello World, meet High Performance Computing"*

- PBS script anatomy
- Submit with `qsub`, monitor with `qstat -u $USER`
- Read `.o` / `.e` output, kill with `qdel`

[→ Lesson 3](lesson-3.md) — *stub with scope contract and pointers*

### Lesson 4: When Jobs Fail (15 min)

> *"Reading PBS tea leaves and error messages"*

- Queue states, the `.o` / `.e` split, `tracejob`
- The 5 failures you'll actually hit
- The "what now?" decision tree

[→ Lesson 4](lesson-4.md) — *stub with scope contract and pointers*

### Lesson 5: Right-sizing Requests (15–20 min)

> *"How much computer do I actually need?"*

- The request-then-tune loop
- Cores, memory, walltime, GPU — what to ask for and why
- One worked translation: laptop script → PBS request

[→ Lesson 5](lesson-5.md) — *stub with scope contract and pointers*

### Lesson 6: Job Arrays (15 min)

> *"When the same script runs 100 times"*

- `qsub -J 1-N`, `PBS_ARRAY_INDEX`
- Sub-job monitoring with `qstat -t`
- Recovering from partial failure

[→ Lesson 6](lesson-6.md) — *stub with scope contract and pointers*

### Lesson 7: Long Jobs — Dependencies & Checkpointing (15–20 min)

> *"When one walltime ceiling isn't enough"*

- The 48-hour-barrier problem
- Job dependencies with `afterok` (wrapper-script idiom)
- Checkpointing intuition

[→ Lesson 7](lesson-7.md) — *stub with scope contract and pointers*

---

Ready to dive in? Start with the [Prerequisites Checklist](prerequisites.md), then head to [Lesson 1](lesson-1.md) and get from zero to productive in record time! 🚀
