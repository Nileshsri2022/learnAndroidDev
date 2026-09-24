#!/usr/bin/env python3
"""
Verify the built site: every internal link resolves, every page has content.

Usage:  python3 check_links.py [--site DIR]

Checks
  1. Every internal href/src on every page resolves to a real file
     (directory-style URLs -> <dir>/index.html).
  2. Every page has real content (word count of the <article> area) and
     code pages actually rendered a code block.
  3. Page counts per category (notes / transcripts / code / days).
  4. Sample of external links is reachable (HEAD, best-effort).

Exit code is non-zero if any internal link is broken.
"""

from __future__ import annotations

import argparse
import html.parser
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse


class LinkExtractor(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self.article_words = 0
        self._in_article = 0
        self._text: list[str] = []
        self.has_code = False

    def handle_starttag(self, tag, attrs):
        if tag in ("a", "img", "link", "script"):
            d = dict(attrs)
            url = d.get("href") or d.get("src")
            if url:
                self.hrefs.append(url)
        if tag == "article":
            self._in_article += 1
        if tag in ("pre", "code"):
            self.has_code = True

    def handle_endtag(self, tag):
        if tag == "article" and self._in_article:
            self._in_article -= 1

    def handle_data(self, data):
        if self._in_article:
            self._text.append(data)


def extract(path: Path) -> LinkExtractor:
    p = LinkExtractor()
    p.feed(path.read_text(encoding="utf-8", errors="replace"))
    p.article_words = len(" ".join(p._text).split())
    return p


def site_url_prefix() -> str:
    """Path prefix from mkdocs.yml `site_url`, e.g. "/learnAndroidDev"."""
    cfg = Path(__file__).resolve().parent / "mkdocs.yml"
    try:
        text = cfg.read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.search(r"^\s*site_url:\s*(\S+)", text, re.M)
    return urlparse(m.group(1)).path.rstrip("/") if m else ""


def resolve(page_html: Path, url: str, site: Path, prefix: str = "") -> Path | None:
    """Resolve an internal URL to a file under site/ (or None if missing).

    Root-relative URLs on 404.html carry the `site_url` path prefix (e.g.
    `/learnAndroidDev/apps/`), because that page can be served from any depth.
    Strip the prefix before resolving against site/, or every one of them would
    be reported broken.
    """
    target = unquote(urlparse(url).path)
    if target.startswith("/"):
        if prefix and (target == prefix or target.startswith(prefix + "/")):
            target = target[len(prefix):]
        candidate = site / target.lstrip("/")
    else:
        candidate = (page_html.parent / target).resolve()
        if not candidate.is_relative_to(site.resolve()):
            return None  # escapes the site root -> broken by construction
    if candidate.is_dir() or url.endswith("/"):
        candidate = candidate / "index.html"
    elif candidate.suffix == "" and not candidate.exists():
        candidate = candidate / "index.html"  # directory-style URL
    if candidate.exists():
        return candidate
    # mkdocs converts foo.md -> foo/ ; also tolerate foo.html
    if candidate.with_suffix(".html").exists():
        return candidate.with_suffix(".html")
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="site")
    ap.add_argument("--external-sample", type=int, default=25)
    args = ap.parse_args()

    site = Path(args.site).resolve()
    prefix = site_url_prefix()
    pages = sorted(site.rglob("*.html"))
    broken: list[tuple[str, str]] = []
    other_pages: list[str] = []
    thin: list[tuple[str, int]] = []
    no_code: list[str] = []
    external: Counter = Counter()
    checked_targets: set[Path] = set()
    cat = Counter()

    for page in pages:
        rel = page.relative_to(site).as_posix()
        # Code pages are nested: days/NN/code-<proj>/<file>/index.html — so the
        # `code-` segment is an ancestor, not necessarily the immediate parent.
        parts = rel.split("/")
        code_idx = next((i for i, p in enumerate(parts) if p.startswith("code-")), -1)
        is_code_page = code_idx >= 0
        # days/NN/code-<proj>/index.html -> the project overview page
        is_code_index = is_code_page and len(parts) == code_idx + 2
        if rel == "index.html":
            cat["home"] += 1
        elif rel == "apps/index.html":
            cat["apps-gallery"] += 1
        elif rel == "SUMMARY/index.html":
            cat["toc-page"] += 1
        elif re.match(r"days/\d{2}/index", rel):
            cat["day-overview"] += 1
        elif "transcript-" in rel:
            cat["transcript"] += 1
        elif is_code_index:
            cat["code-project-index"] += 1
        elif is_code_page:
            cat["code-file"] += 1
        elif re.match(r"days/\d{2}/", rel):
            cat["lecture-note"] += 1
        else:
            cat["other"] += 1
            other_pages.append(rel)

        info = extract(page)
        # Tiny .gitignore/etc. pages are fine: rendered code IS the content.
        if info.article_words < 15 and not info.has_code and rel != "404.html":
            thin.append((rel, info.article_words))
        if is_code_page and not is_code_index and not info.has_code:
            no_code.append(rel)

        for url in info.hrefs:
            scheme = urlparse(url).scheme
            if scheme in ("http", "https"):
                external[url] += 1
                continue
            if scheme or url.startswith(("mailto:", "javascript:", "#")):
                continue
            target = resolve(page, url, site, prefix)
            if target is None:
                broken.append((rel, url))
            else:
                checked_targets.add(target)

    print(f"pages crawled:        {len(pages)}")
    print(f"internal link checks: {len(checked_targets)} unique targets "
          f"(+fragments) — all resolved" if not broken else
          f"internal link checks: {len(checked_targets)} unique targets")
    print(f"page categories:      {dict(sorted(cat.items()))}")
    print(f"external unique URLs: {len(external)}")

    if thin:
        print(f"\nTHIN PAGES (<15 words of content): {len(thin)}")
        for rel, w in thin[:15]:
            print(f"  {rel}  ({w} words)")
    if no_code:
        print(f"\nCODE PAGES WITHOUT CODE BLOCK: {len(no_code)}")
        for rel in no_code[:15]:
            print(f"  {rel}")
    if broken:
        print(f"\nBROKEN INTERNAL LINKS: {len(broken)}")
        for src, url in broken[:40]:
            print(f"  {src}  ->  {url}")
        if len(broken) > 40:
            print(f"  ... and {len(broken) - 40} more")

    if args.external_sample and external:
        sample = [u for u, _ in external.most_common()]
        step = max(1, len(sample) // args.external_sample)
        picks = sample[::step][:args.external_sample]
        ok = fail = 0
        for u in picks:
            try:
                r = subprocess.run(
                    ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                     "-I", "-L", "--max-time", "8", u],
                    capture_output=True, text=True, timeout=15)
                code = r.stdout.strip()
                if code.startswith(("2", "3")) or code == "200":
                    ok += 1
                else:
                    fail += 1
                    print(f"  external {code or 'ERR'}: {u[:100]}")
            except Exception:
                fail += 1
                print(f"  external ERR: {u[:100]}")
        print(f"\nexternal sample: {ok} OK, {fail} failed "
              f"(of {len(picks)} sampled from {len(external)})")

    print()
    if broken or thin or no_code:
        print("RESULT: FAIL")
        return 1
    print("RESULT: ALL OK — every internal link resolves, all pages have content")
    return 0


if __name__ == "__main__":
    sys.exit(main())
