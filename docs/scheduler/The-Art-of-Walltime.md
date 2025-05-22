# Guess, Request, Regret: The Art of Walltime

## :material-timer-sand: The Great Walltime Dilemma

So, you're staring at the PBS script prompt, cursor blinking accusingly at `#PBS -l walltime=??:??:??`, and you're playing that familiar game: "How long will this actually take?" Welcome to **The Art of Walltime** — where every estimate is a guess, every request is a prayer, and every job termination is potential regret.

This guide is essentially a survival manual that:

* Helps you interpret your historical job data (like reading tea leaves, but with actual numbers).
* Shows you how to make walltime decisions that won't keep you up at night.
* Teaches you to balance between "too short and doomed to fail" and "so long you'll die of old age in the queue".
* Respects the sacred 48-hour limit (except for the mythical persistent queue).

**Result:** *Jobs that actually finish, queue priority that doesn't make you weep, and the sweet, sweet feeling of resource efficiency.*

---

## :material-scale-balance: The Walltime Calculation Ritual

### 1. Check Your Job History (Know Yourself)

!!! info "See `pbs_brew_inspector.sh` recipe from [PBS Brew Inspector: Tasting Notes from Your Job History](../pbs-scripts/PBS-Brew-Inspector.md)."

Before you guess, see what your past jobs tell you. Use the `pbs_brew_inspector.sh` script to get wisdom from the past:

```bash
./pbs_brew_inspector.sh -g  # For GPU jobs
./pbs_brew_inspector.sh -c  # For CPU jobs
```

What to look for:

* **True Runtime vs Requested Walltime** - How much of your requested time are you actually using?
* **Walltime Usage %** - If this is consistently low, you're being wasteful!
* **Job patterns** - Are similar jobs taking consistent time?

### 2. The Golden Ratio: The 2x Rule

Take your best guess at how long your job will run. Now double it. This isn't pessimism; it's realism with a safety cushion.

Why this works:

* Accounts for unexpected dataset quirks
* Covers random slowdowns from shared resources
* Gives you time to notice if something's gone horribly wrong

### 3. Queue Sensitivity Analysis (Know Your Environment)

#### Queue Walltime Limits

!!! info "See detailed queue limits in [QUT Aqua HPC Documentation](https://docs.eres.qut.edu.au/hpc-queue-limits)."

QUT Aqua HPC system has specific queue limits you should know intimately:

* **12:00:00 (12 hours)**
    * CPU Interactive Jobs (`cpu_inter_exec`)
    * GPU Interactive Jobs (`gpu_inter_exec`)

* **48:00:00 (2 days)**
    * CPU Batch Jobs (`cpu_batch_exec`)
    * GPU Batch Jobs (`gpu_batch_exec`)
    * CPU Batch Large Memory Jobs (`cpu_batch_exlm`)

* **368:00:00 (15 days)**
    * Interactive Persistent Jobs (`cpu_inter_pers`)

#### Critical distinction

* **Batch jobs** release resources as soon as they finish (even if they finish early).
* **Interactive jobs** hold their resources for the entire walltime (even if your task is done).

>  *The longer your walltime request, the longer you'll wait in the queue. It's not just policy; it's physics. Or politics. Or both.*

---

## :material-flask-outline: Practical Walltime Science

### The Walltime Estimation Formula

$$ T_{\text{estimated}} = T_{\text{baseline}} \times S + M $$

Where:

* **$T_{\text{baseline}}$**: From similar jobs or early testing (in hours)
* **$S$**: Scaling factor representing the ratio of computational workload between new and baseline jobs
* **$M$**: Safety margin (e.g., 1 hour for short jobs, 4+ hours for multi-day runs)

The scaling factor $S$ can be expressed as:

$$ S = \frac{\text{Computational workload of new job}}{\text{Computational workload of baseline job}} $$

This ratio depends on algorithm complexity, data size, model architecture, and hardware configuration, as detailed in the formulas below.

### Scaling Rules for Different Workloads

#### CPU-Based Workloads

* **$O(n)$ Linear Algorithms:**
    * $S \approx \frac{n_{\text{new}}}{n_{\text{baseline}}}$
    * Examples: data parsing, point-wise operations, streaming analytics
    * Doubling data size doubles runtime with constant resources

* **$O(n\log n)$ Log-Linear Algorithms:**
    * $S \approx \frac{n_{\text{new}}}{n_{\text{baseline}}} \times \frac{\log n_{\text{new}}}{\log n_{\text{baseline}}}$
    * Examples: sorting, FFTs, divide and conquer algorithms, heap operations
    * Doubling data size slightly more than doubles runtime (2.1-2.3×)

* **$O(n^2)$ Quadratic Algorithms:**
    * $S \approx \frac{n_{\text{new}}^2}{n_{\text{baseline}}^2}$
    * Examples: pairwise distance matrices, naive string matching, simple nested loops
    * Doubling data size quadruples runtime (4×)

* **$O(n^3)$ Cubic Algorithms:**
    * $S \approx \frac{n_{\text{new}}^3}{n_{\text{baseline}}^3}$
    * Examples: 3D simulations, molecular dynamics, sparse matrix operations
    * Doubling data size increases runtime by 8× (rapidly becomes impractical)

* **$O(n^k)$ Polynomial Algorithms:**
    * $S \approx \frac{n_{\text{new}}^k}{n_{\text{baseline}}^k}, \text{where } k > 3$
    * Examples: k-clique finding, certain dynamic programming solutions, naive polynomial evaluation
    * Scaling becomes prohibitive for large datasets as $k$ increases

* **$O(2^n)$ Exponential Algorithms:**
    * $S \approx \frac{2^{n_{\text{new}}}}{2^{n_{\text{baseline}}}}$
    * Examples: traveling salesman via brute force, power set generation, exhaustive combinatorial search
    * Even small increases in problem size can cause astronomical runtime increases

* **$O(n!)$ Factorial Algorithms:**
    * $S \approx \frac{n_{\text{new}}!}{n_{\text{baseline}}!}$
    * Examples: exact combinatorial optimisation, brute-force search in NP-complete problems
    * Practical only for very small problem sizes (typically $n < 12$)


#### GPU-Based Workloads (Deep Learning)

* **Simplified Practical Formula** (when detailed architecture changes are unknown):
    * $S \approx \frac{b_{\text{new}} \times p_{\text{new}} \times s_{\text{new}} \times e_{\text{new}}}{b_{\text{baseline}} \times p_{\text{baseline}} \times s_{\text{baseline}} \times e_{\text{baseline}}}$ where $p=\text{parameters}$, $s=\text{input size}$, $e=\text{epochs}$

* **Data Size Scaling**: 
    * Linear models: $S \approx \frac{N_{\text{new}}}{N_{\text{baseline}}}$ where $N=\text{samples}$
    * Neural networks: $S \approx \left(\frac{N_{\text{new}}}{N_{\text{baseline}}}\right)^c$ where $c \approx 0.8\text{-}0.9$ due to:
        * Vectorisation benefits with larger datasets
        * GPU kernel efficiency at scale
        * Potential for convergence in fewer epochs with more diverse data

* **Batch Size Considerations**:
    * Theoretical throughput: $S \approx \frac{b_{\text{baseline}}}{b_{\text{new}}}$ where $b=\text{batch size}$
    * Reality (throughput): $S \approx \left(\frac{b_{\text{baseline}}}{b_{\text{new}}}\right)^c$ where $c \approx 0.8\text{-}0.9$ due to:
        * Memory bandwidth limitations
        * Kernel launch overhead
        * Diminishing efficiency gains at large batch sizes
    * Reality (convergence): Larger batches may require more epochs to reach the same accuracy, adding an additional factor of $\left(\frac{b_{\text{new}}}{b_{\text{history}}}\right)^{0.1\text{-}0.3}$

* **Model Size Effects**:
    * Parameter count scaling:
        * Dense models: $S \approx \frac{p_{\text{new}}}{p_{\text{baseline}}}$ where $p=\text{parameters}$
        * Sparse models: $S \approx \left(\frac{p_{\text{new}}}{p_{\text{baseline}}}\right)^c$ where $c < 1$
        * Very large models: $S \approx \left(\frac{p_{\text{new}}}{p_{\text{baseline}}}\right)^d$ where $d > 1$ due to cache effects and memory access patterns
        * Note: When model size exceeds GPU memory, performance drops dramatically due to gradient checkpointing or model parallelism

* **Architecture-Specific Computation** (Forward + Backward Pass):
    * Feedforward NNs: $S \approx \frac{b_{\text{new}} \times N_{\text{new}} \times \sum_i (n_i \times n_{i+1})}{b_{\text{baseline}} \times N_{\text{baseline}} \times \sum_i (n_i \times n_{i+1})_{\text{baseline}}}$ where $b=\text{batch size}$, $N=\text{samples}$, $n_i=\text{neurons in layer i}$
    
    * CNNs: $S \approx \frac{b_{\text{new}} \times \sum_i (h_i \times w_i) \times \sum_j (k_j^2 \times c_{j,\text{in}} \times c_{j,\text{out}})}{b_{\text{baseline}} \times \sum_i (h_i \times w_i)_{\text{baseline}} \times \sum_j (k_j^2 \times c_{j,\text{in}} \times c_{j,\text{out}})_{\text{baseline}}}$ where $h,w=\text{height,width}$, $k=\text{kernel size}$, $c=\text{channels}$
    
    * RNNs: $S \approx \frac{b_{\text{new}} \times s_{\text{new}} \times h_{\text{new}}^2 \times l_{\text{new}} \times (1+d_{\text{new}})}{b_{\text{baseline}} \times s_{\text{baseline}} \times h_{\text{baseline}}^2 \times l_{\text{baseline}} \times (1+d_{\text{baseline}})}$ where $s=\text{sequence length}$, $h=\text{hidden dimension}$, $l=\text{layers}$, $d=\text{bidirectional (0/1)}$
    
    * Transformers: $S \approx \frac{b_{\text{new}} \times s_{\text{new}}^2 \times d_{\text{new}} \times l_{\text{new}}}{b_{\text{baseline}} \times s_{\text{baseline}}^2 \times d_{\text{baseline}} \times l_{\text{baseline}}}$ where $s=\text{sequence length}$, $d=\text{embedding dimension}$, $l=\text{layers}$, $b=\text{batch size}$

* **Convergence Variability**:
    * Stochastic factors can cause training to require 0.5-2× the expected number of epochs
    * Always include a buffer factor of at least 1.5× for convergence uncertainty

#### Hardware Scaling Effects (Optional)

> **Note:** The following scaling rules are based on the assumption that the hardware is the limiting factor for the new job and more resources are required. If the same resources are used for the new job, the scaling rules may not be applicable.

* **CPU Multi-Threading**:
    * Ideal scaling: $S \approx \frac{C_{\text{baseline}}}{C_{\text{new}}}$ where $C$ = number of cores
    * Typical reality: $S \approx \frac{C_{\text{baseline}}}{C_{\text{new}} \times e}$ where $e \approx 0.7-0.9$ is efficiency factor
    * Amdahl's Law: $S \approx \frac{1}{(1-p) + \frac{p \times C_{\text{baseline}}}{C_{\text{new}}}}$ where $p$ is parallelisable fraction
  
* **GPU Scaling**:
    * Multi-GPU data parallelism: $S \approx \frac{G_{\text{baseline}}}{G_{\text{new}} \times e}$ where $G$ = number of GPUs, $e \approx 0.7-0.9$
    * Model Parallelism: Generally worse efficiency than data parallelism
    * Multi-node penalty: $S_{\text{multi-node}} \approx S_{\text{single-node}} \times e_{\text{comm}}$ where $e_{\text{comm}} < 1$ is communication efficiency

    ??? warning "Consider the balance between walltime and GPUs"
        There's often a trade-off between walltime and resource requests (GPUs). A job that uses more resources may finish faster but wait longer in the queue and consume more of your allocation. Consider these alternatives:

        | Approach | Walltime | Resources | Queue Time | Total Time |
        |----------|----------|-----------|------------|------------|
        | High-resource | 12h | 4× H100 GPUs | 24h+ | 36h+ |
        | Balanced | 24h | 2× H100 GPUs | 8h | 32h |
        | Low-resource | 36h | 1× H100 GPU | 2h | 38h |

        **Key considerations:**

        * **Queue congestion**: More resources generally means longer queue wait times
        * **Allocation efficiency**: Using fewer resources over longer times is often more efficient
        * **Urgency factor**: If results are needed quickly, higher resource requests may be justified
        * **Scalability**: Not all workloads scale efficiently with more resources
        * **Checkpoint frequency**: Longer jobs should implement more frequent checkpoints

* **Memory**:
    * Memory bandwidth scaling: $S \approx \frac{M_{\text{new}}}{M_{\text{baseline}}} \times e$ where $e \approx 0.6-0.8$ for memory-bound tasks
    * Swapping penalty: If memory requirements exceed available RAM, expect 10-100× slowdown
    * Large memory jobs: Request just enough memory to avoid OOM errors, but not excessively more
    * Memory locality: Tasks with good cache locality scale better with cores than pure memory bandwidth
    * NUMA effects: Multiple CPU sockets can reduce scaling efficiency by 5-15% due to non-uniform memory access

    ??? info "Memory-bound vs Compute-bound Jobs"
        * **Memory-bound jobs** (e.g., large data processing) benefit more from increased memory bandwidth than additional CPU cores
        * **Compute-bound jobs** (e.g., numerical simulations) benefit more from additional CPU/GPU cores than memory
        * Identifying which category your job falls into helps make better resource requests

!!! example "Here provides some examples of how to use the scaling rules to estimate the walltime for different types of jobs. (TODO)"




---

## :material-alert-circle-outline: Warning Signs You're Doing It Wrong

### Walltime Sins and Their Punishments

* **The Miniaturist**: Requesting 1 hour for a 50-epoch training job. *Punishment: Endless cycle of failed jobs and lost progress.*

* **The Hoarder**: Requesting 7 days for a 4-hour job. *Punishment: Your job ages like fine wine in the queue while your deadline approaches like a freight train.*

* **The Queue Mismatched**: Putting a 24-hour job in a 12-hour interactive queue. *Punishment: Guaranteed failure halfway through, with bonus frustration.*

* **The Copy-Paster**: Using the same walltime for every job without thought. *Punishment: Developing a reputation with the HPC admins, who will tell stories about you at their holiday parties.*

* **The Optimist**: "It'll definitely be faster this time!" *Punishment: Explaining to your supervisor why you have no results for the meeting.*

* **The Resource Hog**: Running minor tasks in batch queues with max resources. *Punishment: Everyone in the Uni quietly resenting you.*

---

## :material-tools: Troubleshooting Your Walltime Woes

Even the best walltime artists occasionally create masterpieces of miscalculation. Here's how to recover:

### When Jobs Die Too Young

If your jobs keep hitting walltime limits:

* **Emergency Checkpoint**: Implement regular checkpoints in your code
* **Divide and Conquer**: Split work into smaller chunks with job dependencies
* **Post-mortem Analysis**: Review the last few output lines before termination
* **Run Time Estimation**: Add progress tracking with estimated completion time
* **Queue Migration**: Consider moving from interactive (12h limit) to batch (48h limit)

### When You're Stuck in Queue Purgatory

If your jobs never seem to start:

* **Queue Status Check**: Use `qstat -q` to see all queue loads
* **Right-sizing**: Consider if you can use a different queue with different limits
* **Time vs Resources Trade**: Sometimes less RAM/GPUs but longer walltime is the better choice
* **Memory Reality Check**: Are you requesting more than the queue's memory range allows?
* **Batch vs Interactive**: Remember batch jobs release resources early; interactive jobs don't

### The Interactive Job Conundrum

When using interactive queues, remember:

* They hold resources for the full walltime even if your code finishes early
* They have much shorter walltime limits (12h vs 48h)
* They typically have lower resource limits (e.g., 2 GPUs vs 8 GPUs)
* Use `cpu_inter_pers` only when you really need 7+ days of runtime

---

## :material-chef-hat: Walltime Recipes for Common Scenarios

### Recipe: The Quick Test Run

```
#PBS -l walltime=01:00:00
#PBS -q cpu_inter_exec  # or gpu_inter_exec if you need GPUs
```

**Best for:**

* Checking if your code runs at all
* Testing on small subsets of data
* Debugging startup issues
* When you'll be actively monitoring

### Recipe: The Standard Training Run

```
#PBS -l walltime=24:00:00
#PBS -q gpu_batch_exec  # For ML workloads
```

**Best for:**

* Most ML model training
* Medium-sized data processing
* Jobs with established completion patterns
* When you need those precious GPUs

### Recipe: The "I Have No Idea" Special

```
#PBS -l walltime=04:00:00
#PBS -q cpu_batch_exec
```

**Best for:**

* First runs of new code
* Exploratory analysis
* When you truly can't estimate (but don't want to clog the queue)
* When you know it needs more than interactive time

### Recipe: The Weekend Warrior

```
#PBS -l walltime=48:00:00  # The max for most queues
#PBS -q gpu_batch_exec  # Or cpu_batch_exec
```

**Best for:**

* Jobs submitted Friday that you want done by Monday
* Large-scale computations you've already tested
* When you won't be available to restart failures
* Hitting the maximum walltime and hoping for the best

### Recipe: The Pipeline Master

```
#PBS -l walltime=168:00:00  # 7 days
#PBS -q cpu_inter_pers
```

**Best for:**

* Workflow pipelines that need to persist
* Long-running services that coordinate other jobs
* Jobs where you truly need more than 48 hours
* When you're willing to sacrifice cores for time (only 1 core is needed)

---

## :material-lightbulb-on: Additional Tips From the Walltime Whisperers

* **Progress Bars are Your Friend**: Add `tqdm` or similar progress tracking to your scripts - they help you make better estimates next time.

* **Walltime Poetry**: Different queues, different rules. Learn the poetry of your specific HPC system.

* **The Batch Advantage**: Batch jobs release resources as soon as they finish. If your job might finish early, always use batch over interactive.

* **Two-Phase Approach**: Run a small version of your job first in an interactive queue to establish a baseline, then scale your walltime request accordingly for the batch queue.

* **Checkpoint Everything**: Your future self will thank you when that 47-hour job crashes at hour 46.

* **The "Kill Switch"**: Always have a way to gracefully terminate your job early if you realise you've made a horrible walltime mistake. Use `qhold <job_id>` to pause your job and `qdel <job_id>` to cancel it.

* **Analyse Your Usage**: Using `pbs_brew_inspector.sh`, track your average walltime efficiency. Aim for 75-85% usage of requested time.

---

## :material-flag-triangle: The Walltime Warrior's Creed

1. I shall not request more time than I need.
2. I shall not trust my first estimate.
3. I shall checkpoint regularly and defensively.
4. I shall learn from each job's runtime.
5. I shall remember interactive jobs hold resources until the bitter end.
6. I shall respect the 48-hour limit of most queues.
7. I shall curse quietly when my perfect estimate is still wrong.

---

## :material-rocket-launch: When All Else Fails: The Emergency Protocols

* **The HPC Whisperer**: Make friends with your HPC admin. They know secrets of the queues you can only dream of.

* **The Queue Switcher**: If your job won't fit in a 48-hour window, break it up or adapt it for the persistent queue.

* **The Late-Night Submission**: Some say submitting at 2 AM magically improves queue position. We can neither confirm nor deny.

* **The "Please Don't Die" Ritual**: This involves staring anxiously at your job's progress while muttering "just finish already" under your breath.

* **The 47:30 Panic Attack**: When you realize your 48-hour job might actually need 48:30, and you start frantically implementing checkpointing.

> **Remember:** Walltime isn't just a number – it's a relationship between you, your code, your data, the specific queue limits, and the cruel mistress of computational fate.

---

## :material-egg-easter: Coming Soon...

* A guide to interpreting cryptic error messages when your job dies with 5 seconds of walltime remaining.
* The psychological impact of watching your perfectly estimated job finish with exactly 00:00:01 remaining.
* Advanced negotiations with the queue scheduler: bargaining, pleading, and acceptance.
* Walltime support group: sharing stories of that time you asked for 48 hours and it took 48 hours and 3 minutes.

Remember, the perfect walltime doesn't exist. But the perfect walltime estimate does.
