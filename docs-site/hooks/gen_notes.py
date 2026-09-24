"""
Generate the MkDocs site from the course notes, transcripts and source code.

Design goals (UI simplicity):
  * Top tab bar: Home | App projects | Days 1-18 | Days 19-32
  * Sidebar shows ONLY the days (short titles) and, inside one day, only its
    lecture notes - everything else lives on the day page in collapsible
    <details> blocks.
  * Code projects live under their own "App projects" tab with a gallery page.
  * Long titles are shortened for the sidebar; full titles stay on the pages.

Produces (in-memory virtual files, nothing written to disk):
  index.md                      homepage
  apps/index.md                 gallery of all source projects
  days/<nn>/index.md            per-day overview (notes / code / slides / transcripts)
  days/<nn>/<slug>.md           one page per lecture note
  days/<nn>/transcript-*.md     one page per raw transcript (not in the sidebar)
  days/<nn>/code-<project>/     source browser (not in the day sidebar; in Apps tab)
  SUMMARY.md                    explicit navigation for literate-nav
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

JUNK_PARTS = {"__MACOSX", "build", ".gradle", ".idea", "out", ".kotlin", ".git"}

SOURCE_EXTS = {".kt", ".java", ".xml", ".kts", ".gradle", ".properties",
               ".pro", ".toml", ".cfg", ".json"}
GRADLE_NAMES = {"settings.gradle", "settings.gradle.kts",
                "build.gradle", "build.gradle.kts"}
LANG_MAP = {".kt": "kotlin", ".kts": "kotlin", ".java": "java", ".xml": "xml",
            ".gradle": "groovy", ".properties": "properties", ".pro": "properties",
            ".gitignore": "text", ".toml": "toml", ".json": "json", ".cfg": "ini"}
MAX_CODE_BYTES = 200_000

NAV_DAY_MAX = 30        # sidebar label length for day titles
NAV_LECTURE_MAX = 44    # sidebar label length for lecture titles


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "page"


def clean_title(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" .-–")


def short_title(text: str, maxlen: int = NAV_DAY_MAX) -> str:
    """Shorten a day/lecture title for sidebar use."""
    t = clean_title(text)
    if len(t) <= maxlen:
        return t
    # Drop trailing track markers like "- Android 12 - XML".
    t = re.sub(r"\s*[-–]\s*Android\s*1[02]\s*(Version)?\s*$", "", t).strip(" -–")
    if len(t) <= maxlen:
        return t
    parts = [p.strip() for p in t.split(" - ") if p.strip()]
    if len(parts) > 1:
        if len(parts[0]) <= maxlen:
            return parts[0]
        if len(parts[-1]) <= maxlen:
            return parts[-1]
    cut = t[:maxlen].rsplit(" ", 1)[0]
    return cut + "…"


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
    def __init__(self, name: str, root: Path, day: int):
        self.name = name
        self.root = root
        self.day = day
        self.files: list[Path] = []
        self.binaries: int = 0

    @property
    def rel_root(self) -> str:
        return self.root.relative_to(REPO).as_posix()


def discover_projects(day: int) -> list[Project]:
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
        proj = Project(root.name, root, day)
        for f in sorted(root.rglob("*")):
            if not f.is_file() or is_junk(f):
                continue
            if f.name in ("gradlew", "gradlew.bat") or "gradle-wrapper" in f.name:
                continue
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


def lang_breakdown(proj: Project) -> str:
    langs: dict[str, int] = {}
    for f in proj.files:
        ext = f.suffix.lower()
        key = LANG_MAP.get(ext, ext.strip(".") or "other")
        langs[key] = langs.get(key, 0) + 1
    return ", ".join(f"{v} {k}" for k, v in sorted(langs.items(), key=lambda x: -x[1]))


def project_file_page(proj: Project, f: Path) -> str:
    code = f.read_text(encoding="utf-8", errors="replace").rstrip()
    lang = LANG_MAP.get(f.suffix.lower(), "text")
    fence = "````" if "```" in code else "```"
    rel = f.relative_to(proj.root).as_posix()
    return (
        f"# {html.escape(f.name)}\n\n"
        f"`{html.escape(rel)}` · **[{html.escape(proj.name)}](index.md)** · "
        f"[Day {proj.day}](../index.md) · [GitHub]({github_url(f)}){{: .md-button }}\n\n"
        f"{fence}{lang}\n{code}\n{fence}\n"
    )


def project_overview_page(proj: Project,
                          links: list[tuple[str, str]]) -> str:
    """File list grouped by folder in collapsible blocks."""
    out = [
        f"# 📱 {html.escape(proj.name)}",
        "",
        f"Source code for **Day {proj.day}** · {len(proj.files)} files "
        f"({lang_breakdown(proj)}) · [GitHub]({github_url(proj.root)}){{: .md-button }}",
        "",
        "!!! tip \"How to browse\"",
        "    Open a folder below, or press <kbd>Ctrl</kbd>+<kbd>K</kbd> and type a",
        "    class name (e.g. *WishDao*) to jump straight to a file.",
        "",
    ]
    groups: dict[str, list[tuple[str, str]]] = {}
    for rel, href in links:
        parent = str(Path(rel).parent)
        groups.setdefault(parent, []).append((Path(rel).name, href))

    for i, (folder, files) in enumerate(
            sorted(groups.items(), key=lambda kv: (kv[0] != ".", kv[0]))):
        label = "." if folder == "." else folder
        open_attr = " open" if folder == "." else ""
        out += [f"<details{open_attr}><summary>"
                f"📁 <code>{html.escape(label)}</code> — {len(files)} file(s)</summary>",
                ""]
        out += [f"- [`{html.escape(name)}`]({href})" for name, href in files]
        out += ["", "</details>", ""]

    if proj.binaries:
        out += [f"*{proj.binaries} image/media files are not rendered — "
                f"see them [on GitHub]({github_url(proj.root)}).*", ""]
    return "\n".join(out)


def file_tree_links(proj: Project, href: dict[Path, str]) -> list[tuple[str, str]]:
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
apps_nav: list[str] = []                    # Apps tab children
tracks_nav: dict[int, list[str]] = {1: [], 2: []}
all_projects: list[tuple[Project, str]] = []   # (project, overview href)
day_rows = {1: [], 2: []}
totals = {"notes": 0, "transcripts": 0, "code": 0}

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
        write(f"{section}/{slug}.md",
              path.read_text(encoding="utf-8", errors="replace"))
        label = f"{num}. {title}" if num is not None else title
        toc.append((label, f"{slug}.md", slug))

    # ---- transcript pages (NOT in the sidebar) ----------------------------
    trans_links: list[tuple[str, str]] = []
    for stem, path in transcripts:
        t_title, body = transcript_body(path)
        slug = unique_slug(slugify(stem))
        write(f"{section}/transcript-{slug}.md",
              f"# {html.escape(t_title)}\n\n"
              f"> 🗣 Raw course transcript — what the instructor said, word for word.\n\n"
              f"{body}\n")
        trans_links.append((clean_title(t_title), f"transcript-{slug}.md"))

    # ---- source code pages (Apps tab only) --------------------------------
    day_code: list[tuple[str, str, int, Path]] = []
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
            write(f"{pdir}/{hrefs[f]}", project_file_page(proj, f))
        write(f"{pdir}/index.md",
              project_overview_page(proj, file_tree_links(proj, hrefs)))
        href = f"{pslug}/index.md"
        day_code.append((proj.name, href, len(proj.files), proj.root))
        all_projects.append((proj, f"{section}/{href}"))
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

    # ---- day overview page -------------------------------------------------
    overview = [f"# Day {day} — {html.escape(day_title)}", ""]
    track_name = "Jetpack Compose track" if track == 1 else "Android 12 / XML track"
    stats = f"**{track_name}** · **{len(notes)} notes**"
    if trans_links:
        stats += f" · **{len(trans_links)} transcripts**"
    if day_code:
        stats += f" · **{len(day_code)} app project(s)**"
    overview += [stats, ""]

    if notes:
        overview += ["## 📖 Lecture notes", ""]
        overview += [f"- [{html.escape(label)}]({link})" for label, link, _ in toc]
        overview.append("")
    if day_code:
        overview += ["## 📱 Source code", ""]
        overview += [f"- **[{html.escape(name)}]({href})** — {n} files · "
                     f"[GitHub]({github_url(root)})"
                     for name, href, n, root in day_code]
        overview.append("")
    if downloads:
        overview += ["## 📄 Slides & links", ""]
        overview += [f"- [{html.escape(t)}]({u})" for t, u in downloads]
        overview.append("")
    if trans_links:
        overview += ["## 🗣 Raw transcripts", ""]
        overview += ["<details><summary>Show the verbatim lecture transcripts "
                     f"({len(trans_links)})</summary>", ""]
        overview += [f"- [{html.escape(t)}]({link})" for t, link in trans_links]
        overview += ["", "</details>", ""]
    overview += ["", f"[← All app projects](../../apps/index.md)" if day_code else "", ""]
    write(f"{section}/index.md", "\n".join(overview))

    # ---- nav: days carry only their lecture notes ---------------------------
    day_index = f"{section}/index.md"
    nav_day = f"    - [Day {day} · {html.escape(short_title(day_title))}]({day_index})"
    tracks_nav[track].append(nav_day)
    for label, link, _ in toc:
        short = label if len(label) <= NAV_LECTURE_MAX else label[:NAV_LECTURE_MAX].rsplit(" ", 1)[0] + "…"
        tracks_nav[track].append(f"        - [{html.escape(short)}]({section}/{link})")

    totals["notes"] += len(notes)
    totals["transcripts"] += len(trans_links)
    day_rows[track].append(
        f"| [Day {day}]({day_index}) | {html.escape(day_title)} | {len(notes)} | "
        f"{len(projects) or '—'} |"
    )

# --------------------------------------------------------------------------
# Apps gallery (own tab)
# --------------------------------------------------------------------------

gallery = [
    "# 📱 App projects",
    "",
    f"All **{len(all_projects)} source projects** from the course — "
    f"{totals['code']} browsable files. Also searchable with <kbd>Ctrl</kbd>+<kbd>K</kbd>.",
    "",
    "| Project | Day | Files |",
    "| ------- | --- | ----- |",
]
for proj, href in sorted(all_projects, key=lambda x: x[0].day):
    gallery.append(f"| **[{html.escape(proj.name)}]({href})** | {proj.day} | "
                   f"{len(proj.files)} |")
gallery += [
    "",
    "!!! note",
    "    Images/layouts resources are linked to GitHub; Kotlin, XML and Gradle",
    "    files are fully rendered here with syntax highlighting.",
    "",
]
write("apps/index.md", "\n".join(gallery))

# --------------------------------------------------------------------------
# Homepage
# --------------------------------------------------------------------------

home = [
    "# Android Dev Masterclass — Study Notes",
    "",
    "Personal study notes, full course transcripts and browsable app source code",
    "for **Danis Panjuta's Android 14 & Kotlin Masterclass**.",
    "",
    f"- **{len(titles)} days · {totals['notes']} lecture notes · {totals['transcripts']} transcripts"
    f" · {len(all_projects)} app projects ({totals['code']} source files)**",
    "- Search everything with <kbd>Ctrl</kbd>+<kbd>K</kbd> — notes, transcripts, code.",
    "",
    "| | |",
    "| --- | --- |",
    "| 📖 **Learn** | Pick a day from the **Days 1–18** or **Days 19–32** tab above |",
    "| 📱 **Code** | Open the **App projects** tab — every project, one click |",
    "| 🗣 **Transcripts** | Collapsed at the bottom of each day page |",
    "",
    "## All days at a glance",
    "",
    "### Jetpack Compose track (Days 1–18)",
    "",
    "| Day | Focus | Notes | Apps |",
    "| --- | ----- | ----- | ---- |",
    *day_rows[1],
    "",
    "### Android 12 / XML track (Days 19–32)",
    "",
    "| Day | Focus | Notes | Apps |",
    "| --- | ----- | ----- | ---- |",
    *day_rows[2],
    "",
    "## The two tracks",
    "",
    "- **Days 1–18 (Compose):** Kotlin basics, Jetpack Compose, MVVM, Retrofit/REST,",
    "  navigation, location & Google Maps, Room, and a Firebase chat app.",
    "- **Days 19–32 (XML toolkit):** Kotlin fundamentals, then classic View-based apps —",
    "  calculator, quiz, drawing, 7-minute workout, Happy Places, weather, Trello clone.",
    "",
]
write("index.md", "\n".join(home))

# --------------------------------------------------------------------------
# SUMMARY.md — top tabs: Home | Apps | Compose | XML
# --------------------------------------------------------------------------

summary = [
    "# Table of contents",
    "",
    "- [Home](index.md)",
    "- [📱 App projects](apps/index.md)",
]
for proj, href in sorted(all_projects, key=lambda x: x[0].day):
    summary.append(f"    - [{html.escape(proj.name)} · Day {proj.day}]({href})")
summary.append("- Days 1–18 · Compose()")
summary += tracks_nav[1]
summary.append("- Days 19–32 · XML()")
summary += tracks_nav[2]
summary.append("")
write("SUMMARY.md", "\n".join(summary))
