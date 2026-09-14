# The Queue Is Not a Line: How Aqua Ranks Your Job

> *Or: first come, first served was never the deal.*

## :material-human-queue: Welcome to the Leaderboard

You submitted hours ago. Your job is still `Q`. A job that looks exactly like yours, submitted after yours, just started. Nothing is broken: the queue is a **leaderboard** that PBS rebuilds every scheduling cycle, and a job gets ahead of yours in one of two ways.

- :material-podium: **It outscores you.** The scoring rule is public. [The Formula on the Wall](#formula) below.
- :material-puzzle: **It fits a gap yours does not.** That is backfilling. [Backfill](#backfill) below.

---

## :material-function-variant: The Formula on the Wall {#formula}

Every cycle PBS evaluates the server attribute `job_sort_formula`[^2] for every queued job and tries the highest score first. Anyone can read it:

```bash
qmgr -c "print server" | grep -iE "job_sort_formula|eligible_time_enable|backfill_depth"
```

At the time of writing, Aqua's looked like this:

```text
set server job_sort_formula = "(48 * fairshare_factor) + ((6 * fairshare_factor) * ((mem/1048576/8) + ncpus + (ngpus*32))) + (0.000278 * eligible_time) + (4 * log(max(fairshare_factor, 1e-7)))"
set server eligible_time_enable = True
set server backfill_depth = 10
```

Writing $f$ for `fairshare_factor`:

$$
\text{score} = 48f \;+\; 6f \left( \frac{\text{mem}}{1048576 \cdot 8} + \text{ncpus} + 32\,\text{ngpus} \right) \;+\; \frac{\text{eligible\_time}}{3600} \;+\; 4 \ln \big( \max(f,\,10^{-7}) \big)
$$

!!! warning "Snapshot, not scripture"
    Sites tune this formula live, and there is no changelog. Run the `qmgr` line above before you quote a coefficient to anyone.

---

## :material-magnify: Reading It: What Each Part Means

| Variable | Comes from | Worth |
|---|---|---|
| `mem`, `ncpus`, `ngpus` | Your `select` line, as **requested**, not as used | 1 per 8 GB, 1 per core, 32 per GPU, then ×&nbsp;$6f$ |
| `eligible_time` | Seconds queued while blocked by a lack of resources | 1 per hour |
| `fairshare_factor` | Your recent usage against your share | A $48f$ bonus, the $6f$ multiplier, and a $4 \ln f$ penalty |
| walltime, `Priority` | — | Nothing. Walltime matters to [backfilling](#backfill) instead |

So the size price list is ==1 GPU = 32 cores = 256 GB==. [Recipe 4](Walltime-by-Recipe.md#recipe-4-single-h100-training)'s `ncpus=12:ngpus=1:mem=64gb` is 32 + 12 + 8 = **52** points of size, before the factor multiplies it.

### :material-scale-balance: `fairshare_factor`, the term that dominates

A number between 0 and 1, higher is better[^2][^3]:

$$f = 2^{-\,\text{usage}/\text{share}}$$

**Share**
:   Your slice of the cluster, set by the administrators. Nothing you submit changes it.

**Usage**
:   Your slice of everyone's recent consumption. It grows while your jobs run and fades when they stop.

Usage equal to share gives $f = 0.5$, twice your share gives $0.25$, almost nothing gives close to $1$. Two more rules:

- :material-account: **It belongs to you, not to a job.** All your queued jobs carry the same $f$, so among themselves they are ordered by size and waiting time.
- :material-server-network: **Each scheduler keeps its own records.** `qmgr -c "print sched"` shows a separate `sched_priv` for each, so CPU batch work does not lower your standing in the GPU batch queue.

!!! note "Where the page stops being precise"
    The usage unit, how fast it fades and the size of your share live in root-only scheduler configuration. Treat $f$ as a dial you influence but cannot read.

---

## :material-calculator: Putting It Together

<!-- markdownlint-disable MD033 -->
<div id="queue-score-explorer" class="qse"></div>
<!-- markdownlint-enable MD033 -->

!!! warning "You cannot out-wait a fair-share deficit"
    Every queued job earns the same point per hour, so two identical jobs submitted together keep the same score difference however long they wait. The difference closes only as your usage fades while you are not running.

---

## :material-puzzle: Backfill: How a Lower-Ranked Job Starts First {#backfill}

Starting jobs strictly by score would let one large job hold GPUs idle while it waits for a whole node. Backfilling uses those gaps[^2], much like a restaurant seating a walk-in couple at a table booked for 8 pm, as long as they will be gone by then. Each cycle PBS goes down the queue from the highest score, and backfilling needs two terms:

**Top job**
:   One of the `backfill_depth` highest-scoring jobs that cannot start yet. PBS books it a start time, and no other job may delay it.

**Filler**
:   A lower-ranked job that starts now anyway, because it fits an idle gap that ends before those bookings.

How many jobs get a booking depends on the queue:

| Scope | `backfill_depth` |
|---|---|
| `gpu_batch_exec` | **5** |
| `cpu_batch_exec` | 60 |
| server default, for queues without their own | 10 |

Suppose, in `gpu_batch_exec`, the four highest-ranked jobs cannot start and hold bookings, one of them on the only idle GPU from six hours from now. The jobs ranked 5th and 6th want that GPU:

| Job | Requests | Ends before the booking? | What happens |
|---|---|---|---|
| Ranked 5th | 24 hours | No | Cannot start, so it takes the fifth booking, for later |
| Ranked 6th | 4 hours | Yes | Starts now, before the 5th, and delays no booking |

Bookings go to the first five jobs that cannot start; walltime decides who fits a gap. PBS judges the fit from the walltime you **request**, so the same 6th-ranked job asking for 24 hours would wait too, and with all five bookings taken it would get none. Backfilling promises no start time: it only lets a job start now when its walltime fits a gap that exists now.

The animation plays two invented days on four of Aqua's H100 nodes, with Aqua's published scheduler settings: a cycle every 60 seconds and five bookings. Green bars are fillers, each ending before the booking on its GPU, and the dashed line in the queue marks where bookings stop. Fair-share factors are assumed, and only jobs that ask for `gpu_id=H100` are shown.

<!-- markdownlint-disable MD033 -->
<div id="backfill-animation" class="bfa"></div>
<!-- markdownlint-enable MD033 -->

- :material-eye-off: **`qstat -T` estimates a start only for top jobs**, and only for your own. Blank most likely means "not in the top five right now". An estimate can move earlier when running jobs finish before their walltime.
- :material-swap-vertical: **You can be next, and then not.** The list is rebuilt every cycle, and your running jobs keep lowering your $f$.

!!! note "Mechanism, not guarantee"
    The depths are public. The scheduler setting that switches bookings on is root-only, so this section describes how PBS backfills rather than proving Aqua does.

??? info "The comment `Not Running: Insufficient amount of resource: qlist`"
    On Aqua `qlist` tags each node with the queues allowed to use it. The comment means no node tagged for your queue had room that cycle. It says nothing about your fair share or your permissions.

---

## :material-chess-knight: What You Control

| Lever | Do | Why |
|---|---|---|
| :material-delete-forever: Waiting time | **Never delete and resubmit.** To shorten a queued job's walltime, use `qalter -l walltime=...`; users can only lower a request | `qdel` resets `eligible_time` to zero, and nothing gives those points back |
| :material-clock-check: Walltime | Request what the job needs plus a margin | A filler must end before the next booking, so padding closes gaps; too little and PBS kills the job |
| :material-arrow-collapse: Size | Trim for placement, not for points | Smaller requests fit more gaps but score lower, more so when $f$ is high |
| :material-link-variant: Chains | Use [Recipe 8](Walltime-by-Recipe.md#recipe-8-long-pipeline-with-chained-jobs)'s `afterok` links to fit gaps, not to bank waiting | Each link accrues nothing until the one before it ends |
| :material-sleep: $f$ | Stop running | Nothing else raises it |

??? info "When `eligible_time` accrues"
    Watch it with `qstat -f <jobid> | grep -E "eligible_time|comment"`. The rules[^2]:

    - :material-check: **Accrues** while the job is blocked by a lack of resources.
    - :material-close: **Does not accrue** while blocked by a run limit, a user hold, or a `qsub -a` start time. PBS does not show which state you are in.
    - :material-arrow-up-bold: **Only goes up** during the life of a job, and survives a requeue.

---

## :material-eye-off: What You Can See

| You want | Command | You get |
|---|---|---|
| The formula | `qmgr -c "print server" \| grep job_sort_formula` | All of it |
| Your job's score | nothing | Inside the scheduler process and its root-owned log |
| Your accrued wait | `qstat -f <jobid>` → `eligible_time` | Yes |
| Why you were skipped this cycle | `qstat -f <jobid>` → `comment` | Yes |
| Where you stand | `qstat -T` | A start estimate only for a top job |
| Your factor, your share, the decay | `pbsfs`, `sched_config` | Root only. Make friends with the HPC admin |
| Anyone else's job | `qstat -u <them>` | Empty. `query_other_jobs` is off |

Hiding scores and factors is standard PBS Professional, not an Aqua quirk[^4].

> **Remember:** A long wait is the scheduler doing arithmetic, not holding a grudge. The arithmetic is above. The grudge, if any, is yours.

---

## :material-arrow-right-circle: Where next

- :material-clock-outline: [Guess, Request, Regret: The Art of Walltime](The-Art-of-Walltime.md) — choosing a walltime that fits gaps.
- :material-chef-hat: [Walltime by Recipe](Walltime-by-Recipe.md) — copy-paste requests, including the single-GPU shape used on this page.
- :material-server-network: [Know Your Nodes](Know-Your-Nodes.md) — the hardware behind each queue.
- :material-school: QUT eResearch — [Queues and limits](https://docs.eres.qut.edu.au/hpc-queue-limits)[^1].

[^1]: Access only in QUT network. Please use VPN to access the documentation when off-campus.
[^2]: Altair, "[PBS Professional 2024.1 Administrator's Guide](https://help.altair.com/2024.1.0/PBS%20Professional/PBSAdminGuide2024.1.pdf)". Section 4.9.21 covers the job sorting formula, its terms and their units. Section 4.9.3 covers backfilling, top jobs and `backfill_depth`. Section 4.9.19 covers fair share, including how `fairshare_factor` is defined. Section 4.9.13 covers when eligible time accrues and when it does not.
[^3]: OpenPBS, "[Scheduler source code](https://github.com/openpbs/openpbs/tree/master/src/scheduler)". Where `fairshare_factor` is actually computed.
[^4]: MetaCentrum, "[Fairshare](https://docs.metacentrum.cz/en/docs/computing/resources/fairshare)". Tells users the fair-share value cannot be displayed directly.
