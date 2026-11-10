"""Helpers for the README sections that generators rewrite between markers."""

from __future__ import annotations

import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
RAW = "https://raw.githubusercontent.com/Luagir94/Luagir94/main"


def picture(name: str, alt: str, width: str) -> str:
    """A theme-aware image: <name>_dark.svg in dark mode, <name>_light.svg otherwise."""
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{RAW}/{name}_dark.svg">'
            f'<img alt="{html.escape(alt)}" width="{width}" src="{RAW}/{name}_light.svg"></picture>')


def splice(section: str, content: str) -> None:
    """Replace whatever sits between the <section> markers in README.md."""
    start, end = f"<!-- {section}:START -->", f"<!-- {section}:END -->"
    text = README.read_text(encoding="utf-8")
    if start not in text or end not in text:
        raise SystemExit(f"README.md is missing the {start} / {end} markers")
    head, rest = text.split(start, 1)
    _, tail = rest.split(end, 1)
    README.write_text(head + start + content + end + tail, encoding="utf-8")
