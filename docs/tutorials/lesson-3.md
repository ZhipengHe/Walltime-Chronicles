# Lesson 3: Working Interactively

!!! warning "Lesson under construction"
    This lesson hasn't been written yet. The scope below is the planned contract; the linked guides in **Until this lesson lands** cover the underlying material today.

!!! quote "Mission Statement"
    *"Interactive is where you develop. Batch is where you run."* 🧪

## 📋 What You'll Accomplish (planned)

By the end of this 15–20 minute lesson, you'll have:

- [ ] **Sized an interactive request on purpose** — cores, memory and walltime for a development session, and the caps that bound it (CPU: 8 cores / 34 GB / 12 h per job and per user; GPU: 12 cores / 64 GB / one MIG slice / 12 h)
- [ ] **Known which queue you land on** — `cpu_inter_exec` vs `gpu_inter_exec`, and why an interactive `ngpus=1` is a MIG slice, not a whole card
- [ ] **Run your Lesson 2 script on a compute node by hand** — `source .venv/bin/activate && python hello.py` from inside `qsub -I`
- [ ] **Measured it** — `time` for the runtime, `/usr/bin/time -v` for peak memory: the two numbers Lesson 6 will size your batch request from
- [ ] **Kept the session alive across disconnects** — `tmux` on the login node, so a dropped Wi-Fi doesn't take your job with it
- [ ] **Known when to stop being interactive** — resources are held for the full walltime whether you use them or not; anything that runs unattended is a batch job (Lesson 4)

## 🔗 Until this lesson lands

- **A ready-made interactive CPU request** — Recipe 1 in [Walltime by Recipe](../scheduler/Walltime-by-Recipe.md#recipe-1-quick-cpu-test-cpu_inter_exec)
- **Interactive queue caps, the single interactive CPU node, and MIG slices** — [Know Your Nodes](../scheduler/Know-Your-Nodes.md)
- **Probing with a small interactive job before sizing a big one** — [Guess, Request, Regret: The Art of Walltime](../scheduler/The-Art-of-Walltime.md)
- **VS Code Tunnel and Jupyter Lab inside an interactive job** — [Surviving without VS Code Remote SSH](../remote-dev/Surviving-without-VS-Code-Remote-SSH.md)

---

← **[Lesson 2: Tooling Setup](lesson-2.md)** · **[Lesson 4: Your First Batch Job](lesson-4.md)** →
