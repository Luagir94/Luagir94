"""Render the featured-project cards that sit under the link buttons.

Writes project_<slug>_<theme>.svg for every entry in PROJECTS, in both themes,
and rewrites the PROJECTS section of README.md to match. PROJECTS is the only
place to edit: add, remove or reorder entries there and the cards, their links
and the README all follow.

Like the link buttons, every card is its own image inside its own link,
because GitHub shows README SVGs through <img> and nothing inside one is
clickable. Two cards share a row: each image is half the card's width and the
gap between them is drawn inside the images, so the outer edges line up with
the profile card above.

Usage:
    python tools/build_projects.py
"""

from __future__ import annotations

import html
import textwrap
from pathlib import Path

from build_card import ADVANCE, THEMES
from build_links import OUTLINE_MIX, PX, stepped
from build_pacman import CANVAS_W, mix
from readme import picture, splice

ROOT = Path(__file__).resolve().parent.parent

# (slug, name, description, tech, link)
PROJECTS = (
    ("resume_builder", "Resume Builder",
     "Client-side resume builder that exports ATS-friendly PDFs right in the "
     "browser. No backend, no sign-up: your data never leaves your device.",
     ("React", "Tailwind CSS", "Vercel"),
     "https://application-resume-builder.vercel.app/"),
    ("globojs", "GloboJS",
     "Open-source library of reusable, typed React hooks, documented with "
     "Storybook.",
     ("Next.js", "React", "Tailwind CSS"),
     "https://github.com/Luagir94/globojs"),
)

PER_ROW = 2
GAP = 14
SLOT_W = CANVAS_W / PER_ROW
CARD_W = (CANVAS_W - (PER_ROW - 1) * GAP) / PER_ROW
PAD = 21                       # inner padding, a whole number of PX
TITLE_FONT = 18
BODY_FONT = 15
LINE = 20
DESC_LINES = 3
HEIGHT = 2 * PAD + TITLE_FONT + 8 + DESC_LINES * LINE + 8 + LINE + PX

BODY_COLS = int((CARD_W - 2 * PAD) / (BODY_FONT * ADVANCE))


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def wrap(text: str) -> list[str]:
    lines = textwrap.wrap(text, BODY_COLS)
    if len(lines) > DESC_LINES:
        raise SystemExit(f"description needs {len(lines)} lines, max {DESC_LINES}: {text!r}")
    return lines


def build(theme: str, index: int) -> str:
    c = THEMES[theme]
    _, name, desc, tech, _ = PROJECTS[index]
    x = (index % PER_ROW) * GAP / PER_ROW
    left = x + PAD

    y = PAD + TITLE_FONT * 0.8
    title = (f'<text x="{left:g}" y="{y:.2f}" font-size="{TITLE_FONT}px" font-weight="bold">'
             f'<tspan class="cc">~/</tspan><tspan class="key">{esc(name)}</tspan></text>')
    arrow = (f'<text x="{x + CARD_W - PAD:g}" y="{y:.2f}" font-size="{TITLE_FONT}px" '
             f'text-anchor="end" class="value">&gt;</text>')

    y += 8
    body = []
    for line in wrap(desc):
        y += LINE
        body.append(f'<tspan x="{left:g}" y="{y:.2f}">{esc(line)}</tspan>')

    y = HEIGHT - PAD - PX
    tags = "<tspan class=\"cc\"> · </tspan>".join(
        f'<tspan class="value">{esc(t)}</tspan>' for t in tech)

    return f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" width="{SLOT_W:g}px" height="{HEIGHT}px"
     viewBox="0 0 {SLOT_W:g} {HEIGHT}" font-family="ConsolasFallback,Consolas,Menlo,monospace">
<style>
@font-face {{
  src: local('Consolas'), local('Consolas Bold');
  font-family: 'ConsolasFallback';
  font-display: swap;
  size-adjust: 109%;
}}
text, tspan {{white-space: pre;}}
.px {{shape-rendering: crispEdges;}}
.key {{fill: {c['key']};}}
.value {{fill: {c['value']};}}
.cc {{fill: {c['dots']};}}
</style>
<g class="px">
<path d="{stepped(x, 0, CARD_W, HEIGHT)}" fill="{mix(c['bg'], c['fg'], OUTLINE_MIX)}"/>
<path d="{stepped(x + PX, PX, CARD_W - 2 * PX, HEIGHT - 2 * PX)}" fill="{c['bg']}"/>
<rect x="{x + 2 * PX:g}" y="{HEIGHT - 2 * PX}" width="{CARD_W - 4 * PX:g}" height="{PX}" fill="{c['key']}"/>
</g>
{title}
{arrow}
<text fill="{c['fg']}" font-size="{BODY_FONT}px">
{chr(10).join(body)}
</text>
<text x="{left:g}" y="{y:.2f}" font-size="{BODY_FONT}px">{tags}</text>
</svg>
"""


def section() -> str:
    rows = []
    for r in range(0, len(PROJECTS), PER_ROW):
        cells = "".join(
            f'<a href="{html.escape(link)}">{picture(f"project_{slug}", name, f"{100 / PER_ROW:g}%")}</a>'
            for slug, name, _, _, link in PROJECTS[r:r + PER_ROW])
        rows.append(f'<p align="left">{cells}</p>')
    return "".join(rows)


def main() -> None:
    print(f"row      : {CANVAS_W}px = {PER_ROW} x {CARD_W:g}px cards, {BODY_COLS} cols of body text")
    slugs = [slug for slug, *_ in PROJECTS]
    if len(set(slugs)) != len(slugs):
        raise SystemExit(f"duplicate project slugs: {slugs}")
    # Render everything first, so a description that does not fit stops the run
    # before any existing card is deleted.
    cards = {f"project_{slug}_{theme}.svg": build(theme, i)
             for theme in THEMES for i, (slug, *_) in enumerate(PROJECTS)}
    for old in ROOT.glob("project_*.svg"):
        old.unlink()
    for name, svg in cards.items():
        out = ROOT / name
        out.write_text(svg, encoding="utf-8")
        print(f"wrote {out.name} ({out.stat().st_size:,} bytes)")
    splice("PROJECTS", section())
    print(f"readme   : {len(PROJECTS)} project(s) in the PROJECTS section")


if __name__ == "__main__":
    main()
