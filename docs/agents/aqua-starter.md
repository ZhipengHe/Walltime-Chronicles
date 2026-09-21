# Help an agent understand and use Aqua

[AGENTS.md](templates/aqua/AGENTS.md) is general guidance for understanding and using QUT Aqua. It explains the system, directs the agent to relevant documentation, and sets boundaries for hands-on work. Use it in a global agent configuration, alongside project instructions, or simply as a reference while learning. No project or cluster account is needed to begin.

Start with the [website knowledge index](../llms.txt), read the [formatted Aqua instructions](templates/aqua/AGENTS.md), or download the [plain-text instructions](aqua-guide.txt) and save them under the filename your agent supports. The text export is generated from the maintained Markdown file during the website build.

??? example "Copy the complete AGENTS.md"

    ```markdown
    --8<-- "docs/agents/templates/aqua/AGENTS.md"
    ```

## Choose how to use it

| Use | How to provide the guidance |
| :-- | :-- |
| Learn about Aqua | Attach the file or give its contents to the assistant and ask a question. No installation or remote access is necessary. |
| Give a global agent Aqua knowledge | Include or reference the guidance through the tool's supported global instruction mechanism. Its scope clause applies Aqua-specific rules only to Aqua-related tasks. |
| Work within a project | Include it alongside the project's instructions. Add local paths, environments, and scientific requirements there when relevant. |

Review existing instructions before merging; do not overwrite them blindly. This file lives in the documentation as a reusable resource and does not configure Walltime Chronicles itself. Verify the tool's supported instruction-loading mechanism. For Codex, consult the [AGENTS.md documentation](https://developers.openai.com/codex/guides/agents-md/); other agents may require a different filename or an explicit reference. Ask the agent to summarize the guidance it loaded.

For learning, an initial request can be:

> Use this Aqua guidance to explain how the system works and which documentation I should read first. Explain login nodes, compute allocations, PBS jobs, and storage. I am only learning; do not connect to the cluster or change anything.

For hands-on assistance:

> Use this Aqua guidance to help with the task I describe. Read the relevant documentation, establish only the context needed for the task, and prepare the requested commands or changes. Show consequential operations for review and wait for my specific queue approval before executing them.

Configure real permissions separately before enabling remote operations: limit access to the relevant files and commands, retain approval prompts, and use the institution's supported access controls. Do not enable unrestricted command execution just because the instructions contain safety rules.

## How llms.txt connects the pieces

The [llms.txt proposal](https://llmstxt.org/) describes a concise website overview with annotated links that an agent follows as needed. For Walltime Chronicles, the file sits at the root of the project site, under `/Walltime-Chronicles/llms.txt`. It covers this documentation site; it does not configure the rest of the author's website.

| Resource | What it provides | When to read it |
| :-- | :-- | :-- |
| `llms.txt` | Site purpose, authority boundaries, and a curated route into the documentation | When first approaching the site or finding a topic |
| Aqua instructions | A system overview, operating rules, and a decision process for learning or acting | When establishing how the agent should assist with Aqua |
| Topic guides and official QUT documentation | Detailed procedures, examples, and current site requirements | When the user's question needs those details |
| User's task and any local instructions | Actual intent, authorized actions, paths, inputs, and success criteria | When preparing or performing a concrete operation |

For example, a question about a waiting job should lead the agent to the scheduler explanation and relevant state information. It should not load every tutorial, invent a new job request, or assume that reading the queue guide authorizes cancellation.

A newcomer can give a browsing-capable agent this prompt after the site is published:

```text
Start at https://zhipenghe.me/Walltime-Chronicles/llms.txt.
Read the linked Aqua guidance, then follow the documentation relevant
to my question. Explain what is documented, what is assumed, and what
would need checking on the live system. Apply the Aqua guidance when
assisting me with Aqua, subject to my instructions and site policy.
Do not install anything, connect to Aqua, or change jobs merely to learn.
My question is: [describe what you want to understand or accomplish].
```

The agent needs a way to retrieve the linked content. If browsing is unavailable, provide the instruction file and relevant documentation excerpts yourself. A URL in a prompt is not evidence that the agent read it. Ask for a brief explanation of the sources used and the next step appropriate to your question.

Loading the website is also separate from persistent configuration. To retain the guidance across sessions, deliberately add it through your agent's supported instruction mechanism. Review it first and retain its Aqua-only scope. Do not assume every assistant automatically discovers `llms.txt`, follows all its links, or treats fetched web content as installed instructions.

The index stays short; the detailed knowledge remains in maintained pages. The Aqua instructions are available as plain text, while the topic links lead to the readable website guides. There is no need to maintain a second giant document containing all tutorials just to get started.

## What good assistance looks like

The examples below are illustrative. They describe behavior and review boundaries, not evidence of jobs executed on Aqua.

### Learning before using the cluster

**User:** "I have never used Aqua. Do I need a GPU?"

**Useful response:** Explain that Aqua supports different workloads and that a GPU helps only when the software and task can use it. Ask about the program and workload if a recommendation depends on them. Point to the introductory and hardware guides. No account, repository, SSH connection, or sample allocation is needed to explain the choice.

This keeps onboarding useful for someone who is exploring HPC, rather than turning every conversation into a project-setup questionnaire.

### Preparing a job without submitting it

**User:** "Can you turn this analysis command into an Aqua batch job?"

**Useful response:** Inspect the supplied command and relevant documentation, establish the needed paths and environment, and prepare a PBS script. Explain the resource estimate and output locations. Show the proposed submission for review. If the script calls a workflow runner that can launch additional jobs, include those effects in the proposal.

A concise review can use this shape:

```text
Purpose: [what the job should accomplish]
Working directory and script: [reviewed paths]
Exact command: [the prepared invocation, not yet executed]
Resources: [queue, account/project, CPU, memory, GPU, walltime]
Extent: [job count, array range, dependencies, concurrency]
Inputs and outputs: [paths, including logs and checkpoints]
Checks: [what passed, what was not checked, remaining assumptions]
Completion: [what evidence will show that the task finished]
Approval requested: [the specific submission or finite group of jobs]
```

Approval should be easy to understand because the preparation is already concrete. It should not be an early request for broad permission to "do whatever is needed."

### Investigating a queued job

**User:** "This job has been waiting for hours. Can you check it?"

**Useful response:** With authorized remote inspection, read the particular job's state and scheduler explanation, then relate them to Aqua's scheduling guidance. A resource request that cannot currently fit differs from an invalid request or a failed job. Report the evidence and any proposed change. Do not cancel and resubmit merely because the job has waited.

Read-only permission can cover ordinary status queries without repeated prompts. It still does not authorize a queue change.

### Diagnosing missing software or an inaccessible file

**User:** "The command works in my terminal, but the agent says it cannot find it."

**Useful response:** Compare the relevant execution contexts and environment initialization. A remote non-interactive shell may differ from the user's login shell. Determine whether the problem is setup, path, or availability before proposing installation or startup-file edits.

For a file-access failure, start with the named file and directory. Do not turn a diagnostic request into recursive permission changes, storage recalls, or a scan of every shared directory. Explain the smallest justified repair and its effects before asking for any required approval.

### Checking whether work actually finished

**User:** "The dashboard says finished. Are the results complete?"

**Useful response:** Compare scheduler accounting, application logs, and the intended workload. For an array, check whether all expected members produced their outputs. For a simulation, check the requested end condition. For training, compare the resolved configuration with actual progress. A wrapper exiting successfully or a checkpoint existing is only part of the evidence.

If the connection drops or accounting is unavailable, say that the current state is unknown. If the job timed out, distinguish useful partial outputs from a completed result and propose any recovery as a separate action.

## What the file can and cannot do

The instructions tell the agent how to work. They do not enforce access restrictions, prevent every mistaken command, or grant technical permissions. Review what the agent can actually read, write, execute, and transmit. Protection around a local process does not automatically extend through SSH or into a batch job.

A mature personal workflow may later use bounded standing authorization. That requires a separate, explicit agreement specifying the account and task scope, allowed operations, resource and job-count limits, duration, stop conditions, and reporting. It must also comply with site policy and the agent tool's controls. Experience with another agent or task does not activate it here. The supplied guidance starts with explicit approval for specific queue actions.

The guidance leaves changing cluster facts in the official documentation and uses local runbooks when available. It does not prescribe a universal GPU model, walltime, queue, polling interval, or mandatory interactive preflight. Task-specific requirements are established when needed, not required before the agent can answer general questions.

## Adapt it to another HPC system

Replace the Aqua overview, documentation links, operating details, and scope clause with the other centre's equivalents. Review PBS wording, permitted agent placement and access methods, storage rules, and submission procedures throughout. The general principles of task scope, user approval, proportionate checking, and evidence-based reporting remain useful. Centre policies differ, particularly on whether an agent may run on a login node or use generic SSH access.

For website onboarding, this guidance can also be linked from an `llms.txt` reading index. It already includes an Aqua overview and a topic-based reading map, so it can be used independently. An index helps an agent discover documentation; the guidance explains how to apply that knowledge. Neither should promise that loading one file supplies all current system knowledge or enforces safe behavior.

## Lessons from published HPC-agent guidance

The Aqua instructions synthesize local operational experience and published centre guidance and Markdown examples. The short quotations below were checked against the linked primary sources on 21 September 2026. They explain the design; their institution-specific commands and permissions do not become Aqua policy.

### Put approval at the consequential action

> Require explicit user approval before submitting, cancelling, requeueing, or modifying a Slurm job or allocation.

[NERSC's agent template](https://github.com/NERSC/coding-agents/blob/main/claude/.claude/CLAUDE.md) names the operations that need approval. The Aqua guidance applies that principle to PBS and to indirect submissions through wrappers. This is more useful than a vague instruction to "be careful": the agent can prepare the work independently while knowing exactly where to stop.

### Keep the user accountable and informed

> You are accountable for everything your agent does under your account, exactly as if you had typed it yourself.

[Purdue's acceptable-use guidance](https://docs.rcac.purdue.edu/agentic-ai/acceptable_use/) makes the account owner's responsibility explicit. Our practical response is to make the intended command, affected resources, and evidence visible. An approval prompt is useful only when the user can understand what they are approving.

### Distinguish instructions from enforced restrictions

> A system prompt saying "only use read-only commands" is a request, not a control. It fails open.

The [Zhanyl-tech read-only Slurm MCP example](https://github.com/Zhanyl-tech/slurm-mcp) illustrates an allowlist enforced by a tool. Its own documentation limits that protection to that tool's surface. Giving the same agent unrestricted shell access would be a separate capability. This is an architectural lesson, not a recommendation to install a Slurm tool on Aqua.

[CSCS's guidance](https://docs.cscs.ch/guides/coding-agents/) adds two useful points: start with restrictive permissions while learning the agent's behavior, and do not assume that a sandbox around the agent propagates into submitted jobs. These support gradual, explicit authorization rather than importing an experienced user's personal autonomy settings into a newcomer setup.

### Verify the goal as well as the process

> Process state ≠ training completeness.

The [VisCy Markdown instructions](https://github.com/mehta-lab/VisCy/blob/4b62365c0df25929bffc7f01b3bb2d1c11d69cce/CLAUDE.md) use this distinction to motivate cross-checking application progress and scheduler evidence. The Aqua version generalizes it beyond training: a task is complete when its expected work and outputs are verified. Site-specific exit signatures and cancellation heuristics need their own validation.

## Markdown examples worth studying

These examples contributed specific patterns rather than whole files to copy. Repository examples describe their authors' environments and may permit actions that this newcomer guidance does not.

| Example | Useful pattern | How it is used here |
| :-- | :-- | :-- |
| [NERSC base instructions](https://github.com/NERSC/coding-agents/blob/main/claude/.claude/CLAUDE.md) | Short sections for software, storage, security, and local additions | Separate general Aqua rules from optional task context; keep searches bounded. |
| [Aalto's global and project rules](https://scicomp.aalto.fi/triton/usage/ai-agents/) | Global cluster guidance with links to details, supplemented by local conventions | Make the Aqua file useful globally and fetch topic detail only when needed. Aalto's hostnames, polling floor, and Git restrictions are not copied. |
| [Virginia Tech ARC instructions](https://github.com/AdvancedResearchComputing/examples/blob/c2130fe3651214a11b7b173a049db84b9cbf228a/LLM/claude-code/CLAUDE.md) | Explain the shared-system impact of parallelism, many small jobs, and filesystem activity | Bound processes and searches; plan job count and monitoring. Local login-node limits are not treated as Aqua limits. |
| [Aurora PBS instructions](https://github.com/globus-labs/exaserve/blob/b544361d44e405523f54da43c391f898d84ea25d/AGENTS.md) | Verify execution context, track remaining walltime, and preserve outputs | Verify the actual allocation before compute and report time-limit failures. Its mandatory interactive workflow is not made universal. |
| [Scoped monitoring instructions](https://github.com/rwchakra/claude-code-hpc/blob/72b5120df17588e55bc2c0614ad6c7a0a0a4f0d7/CLAUDE.md) | Read-only status and log inspection have an explicit scope | Monitoring authorization does not imply permission to cancel, retry, or change files. |
| [QUT CMR sandbox and broker instructions](https://github.com/centre-for-microbiome-research/hpc_scripts/blob/2c5e29e5761b473f284097cdec4cf006516993fe/CLAUDE.md) | Document writable paths, environment context, and restrictions inherited by jobs | Check the actual access path and workload boundary. This is a particular Aqua toolchain, not evidence that every Aqua account has those controls. |

Some links in the underlying survey could not be retrieved. They are not used here as verified authority. The survey's historical search gaps also do not establish that guidance or tools are absent today. Current QUT policy remains the authority for whether a proposed Aqua workflow is permitted.

## Maintaining the website entry point

The editable sources are `docs/llms.txt` and the Markdown Aqua instructions. The site build copies the index as a static file and generates `agents/aqua-guide.txt` from the instruction source. Edit the Markdown source once; the rendered page, copy block, and plain-text export use the same content.

When adding a substantial topic, update the index if it helps an agent find the right page. Keep live queue values and detailed procedures in their authoritative sources. Verify that the built index and linked guide are available after deployment before telling users to start from the public URL. Local build verification alone does not establish that a new page is online.
