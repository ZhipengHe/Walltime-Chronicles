# Lesson 5: Right-sizing Requests

!!! warning "Lesson under construction"
    This lesson hasn't been written yet. The scope below is the planned contract; the linked guides in **Until this lesson lands** cover the underlying material today.

!!! quote "Mission Statement"
    *"How much computer do I actually need?"* ⚖️

## 📋 What You'll Accomplish (planned)

By the end of this 15–20 minute lesson, you'll have:

- [ ] **The request-then-tune loop** — run small, observe, scale (instead of guessing big)
- [ ] **Cores** — `ncpus=N`, plus the `OMP_NUM_THREADS=$NCPUS` one-liner that bites everyone
- [ ] **Memory** — `mem=NGB`, and what "OOM kill" actually means about your request
- [ ] **Walltime** — the 2× rule of thumb, and when to consult the deeper estimation theory
- [ ] **GPU** — `ngpus=1`, `CUDA_VISIBLE_DEVICES` set automatically; short and practical
- [ ] **One worked translation** — "12 GB Python script, ~3 hr on my laptop" → a real PBS request
- [ ] **When to go deeper** — explicit pointers, not duplication, into the scheduler section

## 🔗 Until this lesson lands

- **Walltime estimation theory** — the 2× rule, scaling laws, complexity classes: [Guess, Request, Regret: The Art of Walltime](../scheduler/The-Art-of-Walltime.md)
- **Hardware/queue field guide** — which queue backs which silicon, per-queue ceilings: [Know Your Nodes](../scheduler/Know-Your-Nodes.md)
- **8 worked PBS resource shapes** — copy-paste recipes for real Aqua scenarios: [Walltime by Recipe](../scheduler/Walltime-by-Recipe.md)
- **Post-hoc tuning** — see what your job actually used: [PBS Brew Inspector](../pbs-scripts/PBS-Brew-Inspector.md)

---

← **[Lesson 4: When Jobs Fail](lesson-4.md)** · **[Lesson 6: Job Arrays](lesson-6.md)** →
