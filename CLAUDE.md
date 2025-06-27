# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Walltime Chronicles is a MkDocs-based documentation site that provides a personal guide to PBS/HPC challenges on QUT's Aqua system. The project documents mysterious errors, PBS quirks, scripts, and workarounds for high-performance computing environments with a conversational, engaging writing style.

## Development Commands

### Documentation

```bash
# Install dependencies
pip install -r requirements.txt

# Build documentation
mkdocs build

# Serve documentation locally (default: http://127.0.0.1:8000)
mkdocs serve

# Deploy to GitHub Pages (if configured)
mkdocs gh-deploy
```

### Code Quality and Linting

```bash
# Run pre-commit on all files (formats markdown, checks YAML, fixes trailing whitespace)
pre-commit run --all-files

# Run pre-commit on staged files only
pre-commit run

# Install pre-commit hooks (run once after cloning)
pre-commit install
```

## Project Structure

- `docs/` - Main documentation content in Markdown
  - `index.md` - Homepage with project overview and disclaimers
  - `pbs-scripts/` - PBS job scripts and tools documentation
  - `scheduler/` - Walltime estimation and node selection guides
  - `remote-dev/` - Remote development setup and troubleshooting
  - `javascripts/` - KaTeX math rendering support
- `mkdocs.yml` - MkDocs configuration with Material theme
- `requirements.txt` - Python dependencies for MkDocs build
- `.pre-commit-config.yaml` - Pre-commit hooks for code quality

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

- `pbs_brew_inspector.sh` - PBS job history analysis tool for resource usage insights

## Important Notes

- **YAML configuration:** mkdocs.yml contains MkDocs-specific YAML tags that may not validate with standard YAML parsers
- **Mathematical content:** Several pages contain LaTeX formulas for walltime estimation calculations
- **Cross-references:** Pages frequently link to each other to build a comprehensive knowledge base
