# Lesson 6: Job Arrays

!!! warning "Lesson under construction"
    This lesson hasn't been written yet. The scope below is the planned contract; the linked guides in **Until this lesson lands** cover the underlying material today.

!!! quote "Mission Statement"
    *"When the same script runs 100 times"* 🔁

## 📋 What You'll Accomplish (planned)

By the end of this 15-minute lesson, you'll have:

- [ ] **When to use arrays** — parameter sweeps, file batch processing, Monte Carlo runs
- [ ] **Array submission** — `qsub -J 1-N script.pbs`
- [ ] **`PBS_ARRAY_INDEX`** — how to map it to inputs (table-lookup pattern, list-index pattern)
- [ ] **Sub-job monitoring** — `qstat -t <array_job_id>` without flooding the survey view
- [ ] **Output file naming** — the bracketed-index `.o` files
- [ ] **Recovering from partial failure** — re-run only the indices that failed

## 🔗 Until this lesson lands

- **Alternative pattern: sequential single-job runner** when arrays are overkill: [Batch-Cooking PBS Scripts with a Bash Pan](../pbs-scripts/Batch-Cooking-PBS-Scripts-with-a-Bash-Pan.md)

---

← **[Lesson 5: Right-sizing Requests](lesson-5.md)** · **[Lesson 7: Long Jobs](lesson-7.md)** →
