# Getting Started: HPC Crash Course

Welcome to the Crash Course Café! ☕ Pull up a chair and let's get you productive on QUT Aqua without the usual learning curve headaches.

!!! info "Course status (2026-09-13)"
    Nine lessons, each ending with something you can do that you could not do before. This table is the one place the course's status is kept.

    | Lesson | Status |
    |---|---|
    | [1. Welcome to Aqua](lesson-1.md) | Written |
    | [2. Tooling Setup](lesson-2.md) | Written |
    | [3. Working Interactively](lesson-3.md) | Written |
    | [4. Your First Batch Job](lesson-4.md) | Written |
    | [5. When Jobs Fail](lesson-5.md) | Stub |
    | [6. Right-sizing Requests](lesson-6.md) | Stub |
    | [7. Job Arrays](lesson-7.md) | Stub |
    | [8. Long Jobs: Dependencies & Checkpointing](lesson-8.md) | Stub |
    | [9. Working with an AI Agent on Aqua](lesson-9.md) | Stub |

    A stub states the lesson's scope and points to the guides that cover the material today.

---

## Course Overview

### What This Course Covers

This isn't your typical academic introduction to high-performance computing. This is a practical, no-nonsense guide to getting real work done on QUT's Aqua system. We'll focus on the essential skills you need to submit jobs, avoid common mistakes, and have real work running in your first week.

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
- **Develop and measure on a compute node interactively** — before you submit anything unattended
- **Submit your first PBS batch job** — and find its output
- **Diagnose common failures** before panicking
- **Right-size resource requests** — cores, memory, walltime, GPU
- **Scale beyond a single job** — arrays for bulk work, dependencies for long pipelines
- **Work with an AI coding agent on Aqua** — without handing it the `qsub` button
- **Know when to dig deeper** into the specialized guides

### What You Need

- **Basic command line familiarity**: You can navigate directories and edit files
- **QUT account access**: You can SSH into Aqua
- **A specific task in mind**: Having real work to do makes learning stick

### What You DON'T Need

- Deep understanding of parallel computing
- Experience with other job schedulers
- Perfect knowledge of every PBS directive
- Python, strictly speaking. The examples are Python because that is what most readers run, but PBS does not care what is inside a job: every mechanic taught here applies to any command

### Course Structure

#### Time Commitment

- **Total time**: 2 to 3 hours across **9 focused lessons**
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

**Phase 1, the core loop (Lessons 1 to 4).** Connect, set up Python, run work by hand on a compute node, then hand that same loop to a script.

### Lesson 1: Welcome to Aqua (15 min)

> *"What is this magical compute cluster anyway?"*

- Cluster mental model — file systems, login vs compute nodes
- First SSH connection and a 5-minute interactive job
- Where to put your files (home / scratch / work / TMPDIR)

[→ Lesson 1](lesson-1.md)

### Lesson 2: Tooling Setup (15–20 min)

> *"Getting your Python tools ready"*

- Install uv with one command, no QUT module needed
- Create a project: `pyproject.toml` for what you asked for, `uv.lock` for what you got, then rebuild the environment from them
- The one filesystem rule for environments on Aqua; conda as a branch for non-PyPI packages

[→ Lesson 2](lesson-2.md)

### Lesson 3: Working Interactively (15–20 min)

> *"Interactive is where you develop. Batch is where you run."*

- Size an interactive request — CPU vs GPU interactive queues and their caps
- Run a small training script on a compute node by hand
- `tmux` for surviving disconnects; when a session should become a batch job

[→ Lesson 3](lesson-3.md)

### Lesson 4: Your First Batch Job (15–20 min)

> *"Write down what you want, hand it to PBS, and go do something else."*

- A job script: `#PBS` lines for the request, shell for the work, and what a job's shell starts with
- Fine-tune a language model to judge film reviews, on a GPU with nobody watching; results in files, logs beside them
- Find jobs with `qstat`, take one back with `qdel`

[→ Lesson 4](lesson-4.md)

**Phase 2, reliable operation (Lessons 5 and 6).** Read a failure before panicking, then size requests from measurements instead of guesses.

### Lesson 5: When Jobs Fail (15 min)

> *"Reading PBS tea leaves and error messages"*

- Queue states, the `.o` / `.e` split, `tracejob`
- The 5 failures you'll actually hit
- The "what now?" decision tree

[→ Lesson 5](lesson-5.md)

### Lesson 6: Right-sizing Requests (15–20 min)

> *"How much computer do I actually need?"*

- The measure-then-request loop
- Cores, memory, walltime, GPU — what to ask for and why
- One worked translation: a measured run → PBS request

[→ Lesson 6](lesson-6.md)

**Phase 3, scaling (Lessons 7 and 8).** Many jobs from one script, and work that outlives a single walltime.

### Lesson 7: Job Arrays (15 min)

> *"When the same script runs 100 times"*

- `qsub -J 1-N`, `PBS_ARRAY_INDEX`
- Sub-job monitoring with `qstat -t`
- Recovering from partial failure

[→ Lesson 7](lesson-7.md)

### Lesson 8: Long Jobs — Dependencies & Checkpointing (15–20 min)

> *"When one walltime ceiling isn't enough"*

- The 48-hour-barrier problem
- Job dependencies with `afterok` (wrapper-script idiom)
- Checkpointing intuition

[→ Lesson 8](lesson-8.md)

**Phase 4, the capstone (Lesson 9).** Put an AI agent inside the loop without handing it the `qsub` button.

### Lesson 9: Working with an AI Agent on Aqua (15–20 min)

> *"Delegate the typing, never the `qsub`."*

- Where the agent runs, and how it reaches Aqua
- Rules for the agent: `AGENTS.md` / `CLAUDE.md` for an HPC repo
- What to delegate, and what stays yours

[→ Lesson 9](lesson-9.md)

---

Ready to dive in? Start with the [Prerequisites Checklist](prerequisites.md), then head to [Lesson 1](lesson-1.md) and get from zero to productive in record time! 🚀
