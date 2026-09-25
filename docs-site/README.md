# Documentation site

A searchable, browsable website for the course notes and transcripts, built with
[MkDocs Material](https://squidfunk.github.io/mkdocs-material/).

The pages are **generated in memory** from `../DanisPanjuta/` at build time by
[`hooks/gen_notes.py`](hooks/gen_notes.py) (via the `mkdocs-gen-files` plugin) —
nothing is duplicated on disk, so editing a note in `DanisPanjuta/` and saving
automatically rebuilds the live site.

## Run locally

```bash
pip install -r requirements.txt
mkdocs serve          # http://localhost:8000
```

## Build a static bundle

```bash
mkdocs build          # output in site/
```

## Deploy to GitHub Pages (automatic)

Deployment is automated with [`.github/workflows/deploy-docs.yml`](../.github/workflows/deploy-docs.yml):
every push to `main` that touches `DanisPanjuta/` or `docs-site/` rebuilds the
site and publishes it to
**https://nileshsri2022.github.io/learnAndroidDev/**

One-time setup (already done if the site is live): repository **Settings →
Pages → Build and deployment → Source: GitHub Actions**. You can also redeploy
manually from the **Actions** tab → *Deploy docs to GitHub Pages* → **Run workflow**.

Prefer pushing by hand instead? `mkdocs gh-deploy` still works — it builds and
force-pushes `site/` to the `gh-pages` branch.

## Verify the site

After `mkdocs build`, run the checker — it crawls every page, verifies every
internal link resolves, and confirms every page has real content:

```bash
python3 check_links.py
```

## Structure

| Path | Purpose |
| --- | --- |
| `mkdocs.yml` | Site configuration (Material theme, search, dark mode) |
| `hooks/gen_notes.py` | Generates homepage, day pages, lecture pages, transcript pages and the nav |
| `docs/` | Reserved for handwritten pages (currently empty) |
| `site/` | Build output (git-ignored) |

What you get:

- **Top tab bar** — Home · App projects · ⚡ Cheat Sheets · 📚 Concept Index · Days 1–18 · Days 19–32 — with collapsed day sections and clean navigation
- **Bidirectional Switcher** — Every lecture note has a one-click badge linking to its verbatim transcript; transcripts link directly back to structured notes & code
- **In-page navigation** — Next and Previous lecture buttons at the bottom of every lecture note
- **Dedicated Cheat Sheets Hub** — Ready-to-copy code snippets covering Kotlin, Jetpack Compose, MVVM, Room, Retrofit, Permissions, and Compose vs XML
- **Concept Index & Glossary** — Alphabetical A–Z index mapping 50+ core Android concepts directly to lessons
- One page per **lecture note** (501 pages), grouped into 32 days
- One page per **raw transcript** (519 pages)
- A **source code browser** — 17 app projects (Unit Converter, Shopping List, Recipe,
  Wishlist, Music App, Chat Room, Age in Minutes, Calculator, Happy Places, Weather,
  Trello clone…) with every Kotlin/XML/Gradle file rendered syntax-highlighted
- Full-text **search across everything**, dark mode, copy-buttons on code blocks, select-all code, and tooltips
