"""Publish the Aqua instructions as plain text alongside the rendered page."""

from pathlib import Path

from mkdocs.structure.files import File


def on_files(files, *, config):
    """Add a plain-text export of the maintained Aqua instructions to the site."""
    source = Path(config.docs_dir) / "agents/templates/aqua/AGENTS.md"
    files.append(
        File.generated(
            config,
            "agents/aqua-guide.txt",
            content=source.read_text(encoding="utf-8"),
        )
    )
    return files
