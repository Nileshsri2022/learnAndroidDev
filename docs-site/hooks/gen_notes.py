"""
Generate the MkDocs site from the course notes and transcripts.

Invoked automatically by the mkdocs-gen-files plugin during `mkdocs serve` /
`mkdocs build`. Produces (as in-memory virtual files, nothing written to disk):

  index.md                     homepage with day-by-day tables
  days/<nn>/index.md           per-day overview + lecture index
  days/<nn>/<slug>.md          one page per lecture note
  transcripts/<nn>/<slug>.md   one page per raw transcript file
  SUMMARY.md                   explicit navigation for literate-nav
"""

from __future__ import annotations

import html
import re
from pathlib import Path

import mkdocs_gen_files

ROOT = Path(__file__).resolve().parent.parent          # docs-site/
REPO = ROOT.parent                                     # learnAndroidDev/
SRC = REPO / "DanisPanjuta"
TRANSCRIPTS = SRC / "transcripts"

COMPOSE_DAYS = range(1, 19)      # Day 1-18  -> Jetpack Compose track
XML_DAYS = range(19, 33)         # Day 19-32 -> Android 12 / XML track

NOTE_RE = re.compile(r"^(\d+)\s*[.\-]?\s*(.*)$")
DASHES_RE = re.compile(r"^-{5,}\s*$")
DAY_PREFIX_RE = re.compile(r"^Day\s*\d+\s*[-–]?\s*(.*)$")


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "page"


def clean_title(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" .-–")


def first_h1(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return clean_title(line[2:])
    return None


# --------------------------------------------------------------------------
# Discover days
# --------------------------------------------------------------------------

def day_titles() -> dict[int, str]:
    """Section titles, derived from the transcript folder names."""
    titles: dict[int, str] = {}
    if not TRANSCRIPTS.is_dir():
        return titles
    for entry in sorted(TRANSCRIPTS.iterdir()):
        m = re.match(r"^(\d+)\s*-\s*(.+)$", entry.name)
        if entry.is_dir() and m:
            rest = m.group(2)
            dm = DAY_PREFIX_RE.match(rest)
            titles[int(m.group(1))] = clean_title(dm.group(1) if dm else rest)
    return titles


def lectures_for_day(day: int) -> list[tuple[int | None, str, Path]]:
    """(lecture_number, title, path) sorted by number; unnumbered notes last."""
    folder = SRC / f"Day {day}"
    if not folder.is_dir():
        return []
    items: list[tuple[int | None, str, Path]] = []
    for path in sorted(folder.glob("*.md")):
        stem = path.stem
        m = NOTE_RE.match(stem)
        num = int(m.group(1)) if m and m.group(1).isdigit() else None
        title = clean_title(m.group(2)) if m else clean_title(stem)
        h1 = first_h1(path.read_text(encoding="utf-8", errors="replace"))
        items.append((num, h1 or title or f"Lecture {num}", path))
    items.sort(key=lambda it: (it[0] is None, it[0] if it[0] is not None else it[1]))
    return items


def transcripts_for_day(day: int) -> list[tuple[str, Path]]:
    """(lecture_title, path) sorted by filename (NN- prefix)."""
    folder = TRANSCRIPTS / _transcript_dirname(day)
    if folder is None or not folder.is_dir():
        return []
    out = []
    for path in sorted(folder.glob("*.txt")):
        out.append((path.stem, path))
    return out


def _transcript_dirname(day: int) -> str | None:
    if not TRANSCRIPTS.is_dir():
        return None
    for entry in TRANSCRIPTS.iterdir():
        m = re.match(r"^(\d+)\s*-", entry.name)
        if entry.is_dir() and m and int(m.group(1)) == day:
            return entry.name
    return None


def transcript_body(path: Path) -> tuple[str, str]:
    """Strip the Course/Chapter/Lecture header block; return (title, body)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    title, body_start = path.stem, 0
    for i, line in enumerate(lines[:12]):
        if DASHES_RE.match(line.strip()):
            body_start = i + 1
            break
        lm = re.match(r"^Lecture:\s*(.+)$", line)
        if lm:
            title = clean_title(lm.group(1))
    body = "\n".join(lines[body_start:]).strip()
    return title, body


# --------------------------------------------------------------------------
# Track page names
# --------------------------------------------------------------------------

page_slugs: set[str] = set()


def unique_slug(base: str) -> str:
    slug, i = base, 2
    while slug in page_slugs:
        slug = f"{base}-{i}"
        i += 1
    page_slugs.add(slug)
    return slug


def write(vpath: str, content: str) -> None:
    with mkdocs_gen_files.open(vpath, "w") as f:
        f.write(content)


# --------------------------------------------------------------------------
# Build virtual files
# --------------------------------------------------------------------------

titles = day_titles()
nav_entries: list[str] = []
day_rows = {1: [], 2: []}   # track -> table rows

for day in sorted(titles):
    if day not in COMPOSE_DAYS and day not in XML_DAYS:
        continue
    track = 1 if day in COMPOSE_DAYS else 2
    day_title = titles.get(day, f"Day {day}")
    notes = lectures_for_day(day)
    transcripts = transcripts_for_day(day)

    nn = f"{day:02d}"
    section = f"days/{nn}"
    page_slugs = set()

    # ---- lecture pages ---------------------------------------------------
    toc: list[tuple[str, str, str]] = []   # (label, link, slug)
    for num, title, path in notes:
        base = f"{num}-{slugify(title)}" if num is not None else slugify(title)
        slug = unique_slug(base)
        vpath = f"{section}/{slug}.md"
        write(vpath, path.read_text(encoding="utf-8", errors="replace"))
        label = f"{num}. {title}" if num is not None else title
        toc.append((label, f"{slug}.md", slug))

    # ---- transcript pages ------------------------------------------------
    trans_links: list[tuple[str, str]] = []
    for stem, path in transcripts:
        t_title, body = transcript_body(path)
        slug = unique_slug(slugify(stem))
        vpath = f"{section}/transcript-{slug}.md"
        content = f"# {html.escape(t_title)}\n\n> Raw course transcript, verbatim.\n\n{body}\n"
        write(vpath, content)
        trans_links.append((clean_title(t_title), f"transcript-{slug}.md"))

    # ---- day overview ----------------------------------------------------
    overview = [f"# Day {day} — {html.escape(day_title)}", ""]
    track_name = "Jetpack Compose track" if track == 1 else "Android 12 / XML track"
    overview += [f"**{track_name}** · **{len(notes)} notes** · **{len(trans_links)} transcripts**", ""]

    if notes:
        overview += ["## Lecture notes", ""]
        for label, link, _ in toc:
            overview.append(f"- [{html.escape(label)}]({link})")
        overview.append("")

    if trans_links:
        overview += ["## Raw transcripts", ""]
        for t, link in trans_links:
            overview.append(f"- [{html.escape(t)}]({link})")
        overview.append("")

    write(f"{section}/index.md", "\n".join(overview))

    # ---- nav -------------------------------------------------------------
    day_index = f"{section}/index.md"
    if day == (1 if track == 1 else 19):
        track_label = "Jetpack Compose track" if track == 1 else "Android 12 / XML track"
        nav_entries.append(f"- {track_label}()")
    nav_entries.append(f"    - [Day {day} · {html.escape(day_title)}]({day_index})")
    for label, link, _ in toc:
        nav_entries.append(f"        - [{html.escape(label)}]({section}/{link})")
    for t, link in trans_links:
        nav_entries.append(f"        - [🗣 {html.escape(t)}]({section}/{link})")

    count = len(notes)
    day_rows[track].append(
        f"| [Day {day}]({day_index}) | {html.escape(day_title)} | {count} |"
    )

# --------------------------------------------------------------------------
# Homepage
# --------------------------------------------------------------------------

total_notes = sum(int(r.split("|")[-2]) for rows in day_rows.values() for r in rows)

home = [
    "# Android Dev Masterclass — Study Notes",
    "",
    "Personal study notes and full course transcripts for **Danis Panjuta's",
    "Android 14 & Kotlin Masterclass**, organised for browsing and full-text search.",
    "",
    f"- **{len(titles)} days · {total_notes} lecture notes · {len(list(TRANSCRIPTS.glob('*/*.txt')))} raw transcripts**",
    "- Press <kbd>Ctrl</kbd>+<kbd>K</kbd> (or click the magnifier) to search everything —",
    "  notes *and* transcripts.",
    "- Source material lives in the repo under [`DanisPanjuta/`](https://github.com/Nileshsri2022/learnAndroidDev).",
    "",
    "## Jetpack Compose track (Days 1–18)",
    "",
    "| Day | Focus | Notes |",
    "| --- | ----- | ----- |",
    *day_rows[1],
    "",
    "## Android 12 / XML track (Days 19–32)",
    "",
    "| Day | Focus | Notes |",
    "| --- | ----- | ----- |",
    *day_rows[2],
    "",
    "## About the two tracks",
    "",
    "- **Days 1–18 (Compose):** Kotlin basics, Jetpack Compose, MVVM, Retrofit/REST,",
    "  navigation, location & Google Maps, Room, and a Firebase chat app — built as",
    "  Unit Converter, Shopping List, Recipe, Wishlist, Music Player and Chat apps.",
    "- **Days 19–32 (XML toolkit):** Kotlin fundamentals, then classic View-based apps —",
    "  calculator, quiz, drawing (Canvas), 7-minute workout, Happy Places (maps + SQLite),",
    "  weather (Retrofit) and a Trello clone (Firebase Auth/Firestore/Storage/FCM).",
    "",
    "## Tips",
    "",
    "- The **🗣 entries** in the sidebar are the verbatim course transcripts, useful when",
    "  a note feels too condensed.",
    "- Toggle **dark mode** with the palette switch next to the search box.",
    "",
]
write("index.md", "\n".join(home))

# --------------------------------------------------------------------------
# SUMMARY.md (nav)
# --------------------------------------------------------------------------

summary = ["# Table of contents", "", "- [Home](index.md)", *nav_entries, ""]
write("SUMMARY.md", "\n".join(summary))
