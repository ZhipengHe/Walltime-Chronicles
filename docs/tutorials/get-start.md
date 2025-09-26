# Getting Started: HPC Crash Course

Welcome to the Crash Course Café! ☕ Pull up a chair and let's get you productive on QUT Aqua without the usual learning curve headaches.

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

- **Submit your first PBS job** without breaking anything
- **Estimate walltime** without wildly over- or under-requesting
- **Choose appropriate resources** (cores, memory, queues)
- **Troubleshoot common failures** before panicking
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

- **Total time**: ~105 minutes across 7 focused lessons
- **Lesson format**: 15 minutes each for maximum retention
- **Immediate productivity**: You'll get your environment set up and run interactive tasks in Lesson 1
- **Follow-up learning**: Each lesson connects to detailed guides for when you need more

#### How This Connects to Other Guides

This crash course is your launching pad. When you hit specific challenges, you'll know exactly which detailed guide to consult:

- **Remote development issues** → Cmd+Opt+Remote
- **Complex walltime estimation** → The Scheduler's Gambit
- **Advanced PBS scripting** → PBS Cookbook

#### Next Steps After Completion

1. **Practice with your real work** - Apply what you've learned immediately
2. **Bookmark the troubleshooting guides** - For when things inevitably go wrong
3. **Join the QUT HPC community** - Share your own discoveries and pain points

---

## Prerequisites

**Required before starting the lessons:**

- [x] **QUT HPC access**: Confirmed SSH access to Aqua
- [x] **Essential Linux commands**: Comfortable with `cd`, `ls`, `pwd`, `mkdir`, `cp`, `mv`, `rm`, `chmod`
- [x] **Linux file system**: Understanding absolute vs relative paths, directory structure, home directory (`~`), root (`/`), permissions
- [x] **File transfer method**: SCP, rsync, or remote editing setup complete

*Need help with setup? See our [Remote Development Guide](../remote-dev/) first.*

---

## Course Outline

> *Or it's just a list of lessons that I haven't written yet.*

### Lesson 0: HPC Fundamentals (15 min)

>*"What is this magical compute cluster anyway?"*

- [x] Understanding clusters, nodes, and cores (with QUT Aqua specifics)
- [x] QUT Aqua's file systems and storage locations
- [x] What PBS actually does for you (Interactive, Batch, Array jobs)
- [x] Why job scheduling exists (and why it's worth the hassle)

### Lesson 1: Environment Setup & First Interactive Session (15 min)

> *"Getting your tools ready and taking the cluster for a test drive"*

- [ ] Installing miniconda for Python environment management
- [ ] Setting up uv for fast Python package management
- [ ] Starting your first interactive session
- [ ] Running simple commands and exploring the environment
- [ ] Understanding the difference between login and compute nodes

### Lesson 2: Your First PBS Job (15 min)

> *"Hello World, meet High Performance Computing"*

- [ ] Anatomy of a PBS script
- [ ] Writing your first job script
- [ ] Submitting and monitoring jobs
- [ ] Understanding job output

### Lesson 3: Resource Requests Decoded (15 min)

> *"How much computer do I actually need?"*

- [ ] Cores vs memory: the eternal confusion solved
- [ ] Walltime estimation without crystal balls
- [ ] Node types and when to use them
- [ ] Queue selection strategy

### Lesson 4: When Jobs Fail (15 min)

> *"Reading PBS tea leaves and error messages"*

- [ ] Common failure patterns and their signatures
- [ ] PBS error codes that actually matter
- [ ] Quick diagnostic commands
- [ ] Emergency troubleshooting checklist

### Lesson 5: Resource Optimization (15 min)

> *"Making your jobs faster and more efficient"*

- [ ] Job monitoring and performance analysis
- [ ] Identifying bottlenecks
- [ ] Resource request tuning
- [ ] Parallel job basics

### Lesson 6: Advanced Workflows (15 min)

> *"Moving beyond single jobs"*

- [ ] Job arrays for bulk processing
- [ ] Job dependencies and chaining
- [ ] File management best practices
- [ ] When to graduate to complex workflows

### Lesson 7: Troubleshooting Like a Pro (15 min)

> *"Building your diagnostic toolkit"*

- [ ] Advanced monitoring tools
- [ ] Performance profiling basics
- [ ] Knowing when you've outgrown the basics
- [ ] Where to get help when you're stuck

---

Ready to dive in? Let's start with [Prerequisites Checklist](prerequisites.md) and get you from zero to productive in record time! 🚀
