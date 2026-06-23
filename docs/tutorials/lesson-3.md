# Lesson 3: Your First Batch Job

!!! warning "Lesson under construction"
    This lesson hasn't been written yet. The scope below is the planned contract; the linked guides in **Until this lesson lands** cover the underlying material today.

!!! quote "Mission Statement"
    *"Hello World, meet High Performance Computing"* 👋

## 📋 What You'll Accomplish (planned)

By the end of this 15–20 minute lesson, you'll have:

- [ ] **PBS script anatomy** — shebang, `#PBS` directives, body, and the `cd $PBS_O_WORKDIR` discipline
- [ ] **A working Hello World script** — about 10 lines: echo, hostname, sleep 30, echo done
- [ ] **Submitted your first job with `qsub`** — captured the job ID and know what to do with it
- [ ] **Monitored a job with `qstat -u $USER`** — watched it move Q → R → C
- [ ] **Read your `.o` (stdout) and `.e` (stderr) files** — figured out where your job's prints actually go
- [ ] **Killed a stuck job with `qdel <job_id>`** — when something goes wrong

## 🔗 Until this lesson lands

- **Working PBS script templates** that run N experiments sequentially inside one job: [Batch-Cooking PBS Scripts with a Bash Pan](../pbs-scripts/Batch-Cooking-PBS-Scripts-with-a-Bash-Pan.md)
- **Production-grade PBS shapes** for 8 real Aqua scenarios: [Walltime by Recipe](../scheduler/Walltime-by-Recipe.md)
- **After your job finishes** — introspect what it actually used: [PBS Brew Inspector](../pbs-scripts/PBS-Brew-Inspector.md)

---

← **[Lesson 2: Environment Setup](lesson-2.md)** · **[Lesson 4: When Jobs Fail](lesson-4.md)** →
