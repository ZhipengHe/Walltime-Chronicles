# Lesson 7: Long Jobs — Dependencies & Checkpointing

!!! warning "Lesson under construction"
    This lesson hasn't been written yet. The scope below is the planned contract; the linked guides in **Until this lesson lands** cover the underlying material today.

!!! quote "Mission Statement"
    *"When one walltime ceiling isn't enough"* ⏰

## 📋 What You'll Accomplish (planned)

By the end of this 15–20 minute lesson, you'll have:

- [ ] **The 48-hour-barrier problem** — walltime ceilings and queue limits on Aqua
- [ ] **Job dependencies with `afterok`** — `qsub -W depend=afterok:$JOB1 stage2.pbs`
- [ ] **The wrapper-script idiom** — chaining stages at submit time
- [ ] **Checkpointing intuition** — signal handlers for SIGTERM at walltime-end
- [ ] **When to checkpoint vs when to chain** — the rule of thumb

## 🔗 Until this lesson lands

- **Recipe 8 (long pipeline with chained jobs)** — production-grade `afterok` wrapper pattern with a full PBS script: [Walltime by Recipe](../scheduler/Walltime-by-Recipe.md)
- **Walltime estimation for long jobs**: [Guess, Request, Regret: The Art of Walltime](../scheduler/The-Art-of-Walltime.md)

---

← **[Lesson 6: Job Arrays](lesson-6.md)** · You've reached the end of the Crash Course! Back to the **[course outline](index.md)** for next steps.
