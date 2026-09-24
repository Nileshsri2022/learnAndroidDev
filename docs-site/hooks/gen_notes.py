"""
Generate the MkDocs site from the course notes, transcripts and source code.

Invoked automatically by the mkdocs-gen-files plugin during `mkdocs serve` /
`mkdocs build`. Produces (as in-memory virtual files, nothing written to disk):

  index.md                     homepage with day-by-day tables
  days/<nn>/index.md           per-day overview + lecture index
  days/<nn>/<slug>.md          one page per lecture note
  days/<nn>/transcript-*.md    one page per raw transcript file
  days/<nn>/code-<project>/    source browser: project page + one page per file
  SUMMARY.md                   explicit navigation for literate-nav

PDFs, images and other binaries are not copied into the site; day pages link
to them on GitHub instead.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import quote

import mkdocs_gen_files

ROOT = Path(__file__).resolve().parent.parent          # docs-site/
REPO = ROOT.parent                                     # learnAndroidDev/
SRC = REPO / "DanisPanjuta"
TRANSCRIPTS = SRC / "transcripts"
GITHUB_BASE = "https://github.com/Nileshsri2022/learnAndroidDev/blob/main/"

COMPOSE_DAYS = range(1, 19)      # Day 1-18  -> Jetpack Compose track
XML_DAYS = range(19, 33)         # Day 19-32 -> Android 12 / XML track

NOTE_RE = re.compile(r"^(\d+)\s*[.\-]?\s*(.*)$")
DASHES_RE = re.compile(r"^-{5,}\s*$")
DAY_PREFIX_RE = re.compile(r"^Day\s*\d+\s*[-–]?\s*(.*)$")

# Directory parts that never belong on the site (IDE/Gradle/zip junk).
JUNK_PARTS = {"__MACOSX", "build", ".gradle", ".idea", "out", ".kotlin", ".git"}

# Source files rendered as code pages.
SOURCE_EXTS = {".kt", ".java", ".xml", ".kts", ".gradle", ".properties",
               ".pro", ".toml", ".cfg", ".json"}
GRADLE_NAMES = {"settings.gradle", "settings.gradle.kts",
                "build.gradle", "build.gradle.kts"}
LANG_MAP = {".kt": "kotlin", ".kts": "kotlin", ".java": "java", ".xml": "xml",
            ".gradle": "groovy", ".properties": "properties", ".pro": "properties",
            ".gitignore": "text", ".toml": "toml", ".json": "json", ".cfg": "ini"}
MAX_CODE_BYTES = 200_000


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


def is_junk(path: Path) -> bool:
    return any(part in JUNK_PARTS for part in path.parts)


def github_url(path: Path) -> str:
    rel = path.relative_to(REPO).as_posix()
    return GITHUB_BASE + quote(rel)


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
    return [(p.stem, p) for p in sorted(folder.glob("*.txt"))]


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
# Source project discovery
# --------------------------------------------------------------------------

class Project:
    def __init__(self, name: str, root: Path):
        self.name = name
        self.root = root
        self.files: list[Path] = []      # text source files, sorted
        self.binaries: int = 0           # images/media (linked to GitHub)

    @property
    def rel_root(self) -> str:
        return self.root.relative_to(REPO).as_posix()


def discover_projects(day: int) -> list[Project]:
    """Find Gradle project roots under a Day folder (junk dirs skipped).

    A directory is a project root when it contains settings.gradle(.kts) or
    build.gradle(.kts), provided it is not nested inside an already-accepted
    root (so ``app/`` is not counted as its own project).
    """
    folder = SRC / f"Day {day}"
    if not folder.is_dir():
        return []

    candidates: list[Path] = []
    for path in sorted(folder.rglob("*")):
        if not path.is_dir() or is_junk(path):
            continue
        if any((path / g).is_file() for g in GRADLE_NAMES):
            candidates.append(path)

    roots: list[Path] = []
    for cand in sorted(candidates, key=lambda p: (len(p.parts), str(p))):
        if not any(cand != r and cand.is_relative_to(r) for r in roots):
            roots.append(cand)

    projects: list[Project] = []
    for root in roots:
        proj = Project(root.name, root)
        for f in sorted(root.rglob("*")):
            if not f.is_file() or is_junk(f):
                continue
            if f.name in ("gradlew", "gradlew.bat") or "gradle-wrapper" in f.name:
                continue
            # Machine-specific / credential-ish files: never render, link only.
            if f.name.lower() in ("local.properties", "google-services.json"):
                continue
            if f.suffix.lower() in SOURCE_EXTS or f.name == ".gitignore":
                if f.stat().st_size <= MAX_CODE_BYTES:
                    proj.files.append(f)
            elif f.suffix.lower() in {".png", ".webp", ".jpg", ".jpeg", ".gif",
                                      ".pdf", ".jar", ".ttf"}:
                proj.binaries += 1
        if proj.files:
            projects.append(proj)
    return projects


def project_file_page(day: int, proj: Project, f: Path) -> str:
    code = f.read_text(encoding="utf-8", errors="replace").rstrip()
    lang = LANG_MAP.get(f.suffix.lower(), "text")
    fence = "````" if "```" in code else "```"
    rel = f.relative_to(proj.root).as_posix()
    return (
        f"# {html.escape(f.name)}\n\n"
        f"`{html.escape(rel)}` · **[{html.escape(proj.name)}](index.md)** · Day {day} "
        f"· [GitHub]({github_url(f)}){{: .md-button }}\n\n"
        f"{fence}{lang}\n{code}\n{fence}\n"
    )


def project_overview_page(day: int, proj: Project,
                          links: list[tuple[str, str]]) -> str:
    langs: dict[str, int] = {}
    for f in proj.files:
        ext = f.suffix.lower()
        key = LANG_MAP.get(ext, ext.strip(".") or "other")
        langs[key] = langs.get(key, 0) + 1
    lang_str = ", ".join(f"{v} {k}" for k, v in sorted(langs.items(), key=lambda x: -x[1]))

    out = [
        f"# 📱 {html.escape(proj.name)}",
        "",
        f"Source code for **Day {day}** · {len(proj.files)} source files ({lang_str}) "
        f"· [Browse on GitHub]({github_url(proj.root)}){{: .md-button }}",
        "",
        "## Files",
        "",
    ]
    out += [f"- `{html.escape(label)}` — [view]({href})" for label, href in links]
    if proj.binaries:
        out += ["", f"*{proj.binaries} image/media files are not rendered here — "
                    f"see them [on GitHub]({github_url(proj.root)}).*"]
    return "\n".join(out) + "\n"


def file_tree_links(proj: Project, href: dict[Path, str]) -> list[tuple[str, str]]:
    """(relative_path_label, href) lines, sorted by path."""
    return [(f.relative_to(proj.root).as_posix(), href[f]) for f in proj.files]


# --------------------------------------------------------------------------
# Slugs / output helper
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
totals = {"notes": 0, "transcripts": 0, "projects": 0, "code": 0}

for day in sorted(titles):
    if day not in COMPOSE_DAYS and day not in XML_DAYS:
        continue
    track = 1 if day in COMPOSE_DAYS else 2
    day_title = titles.get(day, f"Day {day}")
    notes = lectures_for_day(day)
    transcripts = transcripts_for_day(day)
    projects = discover_projects(day)

    nn = f"{day:02d}"
    section = f"days/{nn}"
    page_slugs = set()

    # ---- lecture pages ---------------------------------------------------
    toc: list[tuple[str, str, str]] = []
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
        write(vpath, f"# {html.escape(t_title)}\n\n> Raw course transcript, verbatim.\n\n{body}\n")
        trans_links.append((clean_title(t_title), f"transcript-{slug}.md"))

    # ---- source code pages ----------------------------------------------
    code_links: list[tuple[str, str, int, Path]] = []
    for proj in projects:
        pslug = unique_slug("code-" + slugify(proj.name))
        pdir = f"{section}/{pslug}"
        hrefs: dict[Path, str] = {}
        seen: dict[str, int] = {}
        for f in proj.files:
            rel_slug = slugify(f.relative_to(proj.root).as_posix())[:110] or "file"
            base = rel_slug + ".md"
            if base in seen:
                seen[base] += 1
                base = rel_slug + f"-{seen[base]}.md"
            else:
                seen[base] = 1
            hrefs[f] = base
        for f in proj.files:
            write(f"{pdir}/{hrefs[f]}", project_file_page(day, proj, f))
        write(f"{pdir}/index.md",
              project_overview_page(day, proj, file_tree_links(proj, hrefs)))
        code_links.append((proj.name, f"{pslug}/index.md", len(proj.files), proj.root))
        totals["projects"] += 1
        totals["code"] += len(proj.files)

    # ---- downloads (PDFs, links, loose images) ----------------------------
    downloads: list[tuple[str, str]] = []
    folder = SRC / f"Day {day}"
    if folder.is_dir():
        for pdf in sorted(folder.glob("*.pdf")):
            downloads.append((f"📄 {pdf.stem.replace('+', ' ')}", github_url(pdf)))
        for link in sorted(folder.glob("link.txt")):
            url = link.read_text(encoding="utf-8", errors="replace").strip()
            if url.startswith("http"):
                downloads.append((f"🔗 {url}", url))
        for img in sorted(folder.glob("*.png")):
            downloads.append((f"🖼 {img.stem.replace('+', ' ')}", github_url(img)))

    # ---- day overview ------------------------------------------------------
    overview = [f"# Day {day} — {html.escape(day_title)}", ""]
    track_name = "Jetpack Compose track" if track == 1 else "Android 12 / XML track"
    stats = f"**{track_name}** · **{len(notes)} notes** · **{len(trans_links)} transcripts**"
    if projects:
        stats += f" · **{len(projects)} source project(s)**"
    overview += [stats, ""]

    if notes:
        overview += ["## Lecture notes", ""]
        overview += [f"- [{html.escape(label)}]({link})" for label, link, _ in toc]
        overview.append("")
    if code_links:
        overview += ["## Source code", ""]
        overview += [f"- 📱 [{html.escape(name)}]({href}) — {n} files · "
                     f"[GitHub]({github_url(root)})"
                     for name, href, n, root in code_links]
        overview.append("")
    if downloads:
        overview += ["## Downloads & links", ""]
        overview += [f"- [{html.escape(t)}]({u})" for t, u in downloads]
        overview.append("")
    if trans_links:
        overview += ["## Raw transcripts", ""]
        overview += [f"- [{html.escape(t)}]({link})" for t, link in trans_links]
        overview.append("")

    write(f"{section}/index.md", "\n".join(overview))

    # ---- nav ---------------------------------------------------------------
    day_index = f"{section}/index.md"
    if day == (1 if track == 1 else 19):
        track_label = "Jetpack Compose track" if track == 1 else "Android 12 / XML track"
        nav_entries.append(f"- {track_label}()")
    nav_entries.append(f"    - [Day {day} · {html.escape(day_title)}]({day_index})")
    for label, link, _ in toc:
        nav_entries.append(f"        - [{html.escape(label)}]({section}/{link})")
    for name, href, _, _ in code_links:
        nav_entries.append(f"        - [📱 {html.escape(name)}]({section}/{href})")
    for t, link in trans_links:
        nav_entries.append(f"        - [🗣 {html.escape(t)}]({section}/{link})")

    totals["notes"] += len(notes)
    totals["transcripts"] += len(trans_links)
    day_rows[track].append(
        f"| [Day {day}]({day_index}) | {html.escape(day_title)} | {len(notes)} | "
        f"{len(projects) or '—'} |"
    )

# --------------------------------------------------------------------------
# Homepage
# --------------------------------------------------------------------------

home = [
    "# Android Dev Masterclass — Study Notes & Source Code",
    "",
    "Personal study notes, full course transcripts and **browsable app source code**",
    "for **Danis Panjuta's Android 14 & Kotlin Masterclass**, organised for browsing",
    "and full-text search.",
    "",
    f"- **{len(titles)} days · {totals['notes']} lecture notes · {totals['transcripts']} transcripts"
    f" · {totals['projects']} app projects ({totals['code']} source files)**",
    "- Press <kbd>Ctrl</kbd>+<kbd>K</kbd> (or click the magnifier) to search everything —",
    "  notes, transcripts *and* source code.",
    "- Source material lives in the repo under [`DanisPanjuta/`](https://github.com/Nileshsri2022/learnAndroidDev).",
    "",
    "## Jetpack Compose track (Days 1–18)",
    "",
    "| Day | Focus | Notes | Apps |",
    "| --- | ----- | ----- | ---- |",
    *day_rows[1],
    "",
    "## Android 12 / XML track (Days 19–32)",
    "",
    "| Day | Focus | Notes | Apps |",
    "| --- | ----- | ----- | ---- |",
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
    "- **📱 entries** in the sidebar are browsable app source code (Kotlin, layouts, Gradle).",
    "- **🗣 entries** are the verbatim course transcripts, useful when a note feels too condensed.",
    "- **📄 links** on day pages point to the original slide PDFs on GitHub.",
    "- Toggle **dark mode** with the palette switch next to the search box.",
    "",
]
write("index.md", "\n".join(home))

# --------------------------------------------------------------------------
# SUMMARY.md (nav)
# --------------------------------------------------------------------------

summary = ["# Table of contents", "", "- [Home](index.md)", *nav_entries, ""]
write("SUMMARY.md", "\n".join(summary))
