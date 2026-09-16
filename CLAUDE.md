# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Walltime Chronicles is a MkDocs-based documentation site that provides a personal guide to PBS/HPC challenges on QUT's Aqua system. The project documents mysterious errors, PBS quirks, scripts, and workarounds for high-performance computing environments with a conversational, engaging writing style.

## Development Commands

### Documentation

```bash
# Install dependencies (resolves from pyproject.toml + uv.lock)
uv sync

# Build documentation
uv run mkdocs build

# Serve documentation locally on a non-default port (avoid 8000 — it's often busy)
uv run mkdocs serve -a 127.0.0.1:8765

# Deploy to GitHub Pages (if configured)
uv run mkdocs gh-deploy
```

### Code Quality and Linting

```bash
# Run pre-commit on all files (formats markdown, checks YAML, fixes trailing whitespace)
pre-commit run --all-files

# Run pre-commit on staged files only
pre-commit run

# Install pre-commit hooks (run once after cloning)
pre-commit install

# Smoke-test the tutorial scripts (no PyTorch needed)
python -m unittest discover -s tests -v
```

## Project Structure

- `docs/` - Main documentation content in Markdown
    - `index.md` - Homepage with project overview and disclaimers
    - `tutorials/` - Crash Course Café: course index, prerequisites checklist, `lesson-1.md` … `lesson-9.md`; `scripts/` holds the task scripts the lessons run (see the table below)
    - `pbs-scripts/` - PBS job scripts and tools documentation
    - `scheduler/` - Walltime estimation, node selection, and uv cache/env placement guides
    - `remote-dev/` - Remote development setup, macOS metadata cleanup, `/work/<group>` permissions
    - `javascripts/` - KaTeX math rendering support
- `tests/` - Smoke tests for the tutorial scripts, plain `unittest`, no PyTorch needed (`python -m unittest discover -s tests`); CI runs them
- `benchmarks/uv-on-aqua/` - PBS-driven `uv sync` benchmark behind `docs/scheduler/uv-on-aqua.md`: `config.toml`, `scripts/` (run harness, sanitizer, analysis stubs), `workloads/` (locked `cpu-ml` / `gpu-ml` projects), `results-archive/` (redacted per-run bundles + summaries)
- `mkdocs.yml` - MkDocs configuration with Material theme
- `pyproject.toml` - Python project metadata and dependencies for MkDocs build
- `uv.lock` - Pinned dependency versions (managed by `uv sync` / `uv lock`)
- `.pre-commit-config.yaml` - Pre-commit hooks for code quality

### Tutorial scripts

Each lesson picks its own task; a script is not carried from one lesson to the next. Scripts are embedded into their lesson with a `--8<--` snippet and are downloadable, so the page and the file are the same source. Any data is downloaded by the script, never committed.

| Script | Used in | Task | Needs |
|---|---|---|---|
| `docs/tutorials/scripts/train_mnist.py` | Lesson 3 | MNIST digit classifier | PyTorch only |
| `docs/tutorials/scripts/imdb_sentiment.py` | Lessons 4 and 6 | IMDb review sentiment, fine-tuning DistilBERT (Hugging Face's text-classification guide, GPU) | PyTorch (CUDA build), transformers, datasets, evaluate, accelerate, scikit-learn |
| `docs/tutorials/scripts/radon_chains.py` | Lesson 7 | One MCMC chain of PyMC's multilevel radon model (PyMC's multilevel modelling primer, CPU); one chain per array subjob | pymc, arviz, netcdf4 |

## Writing Style and Content Guidelines

The documentation has a specific tone and style:

- **Conversational and engaging** - Uses humor and personality while remaining informative
- **Problem-focused** - Documents real frustrations and practical solutions
- **Copy-paste friendly** - Provides working code examples and scripts
- **QUT Aqua specific** - Tailored to QUT's HPC environment and PBS configuration

**Content focus:**

- PBS/HPC-specific challenges and solutions
- Real-world troubleshooting experiences
- Script templates with explanations
- Resource optimization guidance

**Content excludes:** Basic Linux tutorials, PBS fundamentals, general programming help

## Technical Architecture

- **MkDocs Material theme** with custom navigation structure
- **KaTeX support** for mathematical expressions (especially in walltime estimation)
- **Git integration** - Revision dates and contributor tracking enabled
- **Emoji support** via pymdownx extensions for engaging visual elements
- **Code highlighting** with line numbers and copy functionality
- **Pre-commit hooks** for automatic formatting and linting

## Key Scripts and Tools

The project includes practical HPC tools in `docs/pbs-scripts/scripts/`:

- `pbs_batch_cook.sh` - Generates and submits one timestamped PBS script that runs several experiment scripts sequentially
- `pbs_brew_inspector.sh` - PBS job history analysis tool for resource usage insights

Both are embedded into their doc pages with `--8<--` snippets, so the page and the downloadable file are the same source.

## Important Notes

- **YAML configuration:** mkdocs.yml contains MkDocs-specific YAML tags that may not validate with standard YAML parsers
- **Mathematical content:** Several pages contain LaTeX formulas for walltime estimation calculations
- **Cross-references:** Pages frequently link to each other to build a comprehensive knowledge base
