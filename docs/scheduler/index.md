# The Scheduler's Gambit

Walltime estimation, hardware selection, and PBS job sizing on Aqua. Four companion pages — the hardware menu, the math, the worked examples, and where your Python environments should live.

- :material-server-network: [Know Your Nodes](Know-Your-Nodes.md) — a field guide to Aqua's compute tiers (CPU batch, large-memory, H100 + A100 GPU, MIG slices, interactive). Read first.
- :material-clock-outline: [Guess, Request, Regret: The Art of Walltime](The-Art-of-Walltime.md) — queue caps, scaling factors, the 2× rule, recovery toolkit.
- :material-chef-hat: [Walltime by Recipe: Worked Examples for Aqua](Walltime-by-Recipe.md) — eight copy-paste PBS recipes from quick tests through chained jobs.
- :material-package-variant-closed: [uv on Aqua: Cache + Envs Placement](uv-on-aqua.md) — the same-filesystem rule, the bench numbers behind it, three placement patterns, and the `env.sh` idiom for team projects on `/work`.
