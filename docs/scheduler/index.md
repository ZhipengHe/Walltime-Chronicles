# The Scheduler's Gambit

Getting a job sized, placed and scheduled on Aqua: what the hardware offers, how long to ask for, and how the queue decides what runs next.

- :material-server-network: [Know Your Nodes](Know-Your-Nodes.md) — a field guide to Aqua's compute tiers (CPU batch, large-memory, H100 + A100 GPU, MIG slices, interactive). Read first.
- :material-clock-outline: [Guess, Request, Regret: The Art of Walltime](The-Art-of-Walltime.md) — queue caps, scaling factors, the 2× rule, recovery toolkit.
- :material-chef-hat: [Walltime by Recipe: Worked Examples for Aqua](Walltime-by-Recipe.md) — eight copy-paste PBS recipes from quick tests through chained jobs.
- :material-human-queue: [The Queue Is Not a Line: How Aqua Ranks Your Job](The-Queue-Is-Not-a-Line.md) — the `job_sort_formula`, what `fairshare_factor` is, how backfilling lets a lower-ranked job start first, and what you can and cannot see.
