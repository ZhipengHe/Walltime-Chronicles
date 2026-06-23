# Lesson 4: When Jobs Fail

!!! warning "Lesson under construction"
    This lesson hasn't been written yet. The scope below is the planned contract; the linked guides in **Until this lesson lands** cover the underlying material today.

!!! quote "Mission Statement"
    *"Reading PBS tea leaves and error messages"* 🔍

## 📋 What You'll Accomplish (planned)

By the end of this 15-minute lesson, you'll have:

- [ ] **The `.o` / `.e` file split** — where errors actually appear vs where stdout lands
- [ ] **PBS queue states** — Q (queued), R (running), H (held), E (exiting), F (finished)
- [ ] **`tracejob` for post-mortem** — the event log when a job has gone sideways
- [ ] **The 5 failures you'll actually hit:**
    1. Walltime exceeded (exit code 271 / "job killed: walltime exceeded")
    2. OOM kill (exit code 137 / signal 9)
    3. Module not loaded (`command: not found`)
    4. Wrong working directory (missing `cd $PBS_O_WORKDIR`)
    5. Job stuck in Q forever (resource shape rejected, or queue just busy)
- [ ] **The "what now?" decision tree** — when to retry, when to resize, when to ask

## 🔗 Until this lesson lands

- **Why your queue choice was rejected** — per-queue ceilings and node-type field guide: [Know Your Nodes](../scheduler/Know-Your-Nodes.md)
- **Right-sizing the next attempt after a walltime kill**: [Guess, Request, Regret: The Art of Walltime](../scheduler/The-Art-of-Walltime.md)
- **Post-hoc resource introspection** — what your job actually used: [PBS Brew Inspector](../pbs-scripts/PBS-Brew-Inspector.md)

---

← **[Lesson 3: Your First Batch Job](lesson-3.md)** · **[Lesson 5: Right-sizing Requests](lesson-5.md)** →
