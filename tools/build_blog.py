"""Render the latest blog posts and splice them into the README.

Reads the portfolio's RSS feed and writes, per theme, one header image
(blog_header_<theme>.svg) plus one row per post (blog_post_<n>_<theme>.svg).
Every row is its own image inside its own link, for the same reason as the
link buttons: nothing inside a README SVG is clickable.

The section lives between the BLOG markers in README.md and is rewritten on
every run. With no posts the markers are left empty and every blog image is
removed, so the profile shows nothing until the first post is published.
A feed that cannot be fetched or parsed leaves the README and images as they
were: a network hiccup must not wipe the section.

Usage:
    python tools/build_blog.py
    BLOG_FEED=path/to/feed.xml python tools/build_blog.py   # local test
"""

from __future__ import annotations

import datetime as dt
import html
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

from build_card import ADVANCE, LINE_MID, THEMES
from build_links import OUTLINE_MIX, PX, stepped
from build_pacman import CANVAS_W, mix

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
FEED = os.environ.get("BLOG_FEED", "https://lucianogiraudi.dev/feed.xml")
RAW = "https://raw.githubusercontent.com/Luagir94/Luagir94/main"

START = "<!-- BLOG:START -->"
END = "<!-- BLOG:END -->"

MAX_POSTS = 4
FONT = 16
ROW_H = 16 * PX
HEADER_H = 36
PAD = 18
COLS = int((CANVAS_W - 2 * PAD) / (FONT * ADVANCE))
READ = "READ >"


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def fetch_posts() -> list[dict] | None:
    """Return the newest posts, or None when the feed is unreachable or invalid."""
    try:
        if FEED.startswith(("http://", "https://")):
            req = urllib.request.Request(FEED, headers={"User-Agent": "profile-readme-builder"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
        else:
            raw = Path(FEED).read_bytes()
        channel = ET.fromstring(raw).find("channel")
        if channel is None:
            raise ValueError("no <channel> element")
    except Exception as exc:  # noqa: BLE001 -- any failure means "keep what we have"
        print(f"feed unavailable ({exc}); leaving the blog section untouched", file=sys.stderr)
        return None

    posts = []
    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if not title or not link.startswith("https://"):
            continue
        try:
            date = parsedate_to_datetime(item.findtext("pubDate") or "").date()
        except (TypeError, ValueError):
            date = None
        posts.append({"title": title, "link": link, "date": date})

    posts.sort(key=lambda p: p["date"] or dt.date.min, reverse=True)
    return posts[:MAX_POSTS]


def svg(width: float, height: float, theme: str, body: str) -> str:
    c = THEMES[theme]
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width:g}px" height="{height:g}px"
     viewBox="0 0 {width:g} {height:g}" font-family="ConsolasFallback,Consolas,Menlo,monospace">
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
.fg {{fill: {c['fg']};}}
</style>
{body}
</svg>
"""


def header(theme: str) -> str:
    y = HEADER_H / 2 + LINE_MID * FONT
    body = (f'<text x="{PX:g}" y="{y:.2f}" font-size="{FONT}px">'
            f'<tspan class="key">&gt; </tspan><tspan class="fg">tail ~/blog</tspan>'
            f'<tspan class="cc">  # latest posts</tspan></text>')
    return svg(CANVAS_W, HEADER_H, theme, body)


def row(theme: str, post: dict) -> str:
    c = THEMES[theme]
    date = post["date"].isoformat() if post["date"] else "----------"
    room = COLS - len(date) - 2 - len(READ) - 2
    title = post["title"]
    if len(title) > room:
        title = title[: room - 1].rstrip() + "…"
    dots = "." * (room - len(title))
    mid = (PX + ROW_H - 2 * PX) / 2 + LINE_MID * FONT
    body = (
        f'<g class="px">'
        f'<path d="{stepped(0, 0, CANVAS_W, ROW_H)}" fill="{mix(c["bg"], c["fg"], OUTLINE_MIX)}"/>'
        f'<path d="{stepped(PX, PX, CANVAS_W - 2 * PX, ROW_H - 2 * PX)}" fill="{c["bg"]}"/>'
        f'<rect x="{2 * PX}" y="{ROW_H - 2 * PX}" width="{CANVAS_W - 4 * PX}" height="{PX}" fill="{c["value"]}"/>'
        f'</g>'
        f'<text x="{PAD}" y="{mid:.2f}" font-size="{FONT}px">'
        f'<tspan class="key">{date}</tspan>  <tspan class="fg">{esc(title)}</tspan>'
        f'<tspan class="cc"> {dots} </tspan><tspan class="value">{esc(READ)}</tspan></text>'
    )
    return svg(CANVAS_W, ROW_H, theme, body)


def picture(name: str, alt: str) -> str:
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{RAW}/{name}_dark.svg">'
            f'<img alt="{html.escape(alt)}" width="100%" src="{RAW}/{name}_light.svg"></picture>')


def section(posts: list[dict]) -> str:
    if not posts:
        return ""
    lines = ["", f'<p align="left">{picture("blog_header", "Latest blog posts")}</p>', ""]
    for i, post in enumerate(posts):
        lines.append(f'<a href="{html.escape(post["link"])}">{picture(f"blog_post_{i}", post["title"])}</a>')
    return "\n".join(lines) + "\n"


def main() -> None:
    posts = fetch_posts()
    if posts is None:
        return

    for old in ROOT.glob("blog_*.svg"):
        old.unlink()
    for theme in THEMES:
        if posts:
            (ROOT / f"blog_header_{theme}.svg").write_text(header(theme), encoding="utf-8")
        for i, post in enumerate(posts):
            (ROOT / f"blog_post_{i}_{theme}.svg").write_text(row(theme, post), encoding="utf-8")

    readme = README.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        raise SystemExit(f"README.md is missing the {START} / {END} markers")
    head, rest = readme.split(START, 1)
    _, tail = rest.split(END, 1)
    README.write_text(head + START + section(posts) + END + tail, encoding="utf-8")
    print(f"blog     : {len(posts)} post(s) from {FEED}")


if __name__ == "__main__":
    main()
