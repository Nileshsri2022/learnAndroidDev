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

## Build a static bundle (GitHub Pages etc.)

```bash
mkdocs build          # output in site/
```

Then deploy `site/` wherever you like, e.g.:

```bash
mkdocs gh-deploy      # pushes site/ to the gh-pages branch
```

## Structure

| Path | Purpose |
| --- | --- |
| `mkdocs.yml` | Site configuration (Material theme, search, dark mode) |
| `hooks/gen_notes.py` | Generates homepage, day pages, lecture pages, transcript pages and the nav |
| `docs/` | Reserved for handwritten pages (currently empty) |
| `site/` | Build output (git-ignored) |

What you get:

- **Home** with day-by-day tables for both course tracks
- One page per **lecture note** (439 pages), grouped into 32 days
- One page per **raw transcript** (520 pages), marked with 🗣 in the sidebar
- Full-text **search across everything**, dark mode, copy-buttons on code blocks
