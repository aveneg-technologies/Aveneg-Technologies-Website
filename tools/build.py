#!/usr/bin/env python3
"""Build avenegtechnologies.com from src/ into public/.

    python3 tools/build.py          write the pages, llms-full.txt and sitemap.xml
    python3 tools/build.py check    exit 1 if public/ is not what src/ builds

Why this exists. Every page used to carry its own copy of the header, the footer and
the stylesheet, and the seven copies drifted apart (different widths, line heights and
footers on different pages). Now the shared parts live once in src/partials/, the
styles once in public/styles/site.css, and each page in src/pages/ holds only its own
content. Cloudflare still deploys public/ as plain static files: nothing runs at deploy
time, so run this and commit public/ before pushing. `check` is the guard against
forgetting.

What it writes (and nothing else in public/ is touched):
    public/index.html, public/<page>/index.html, public/404.html
    public/llms-full.txt    the text of every page, generated from the same sources
    public/sitemap.xml      one entry per page, lastmod from each page's `modified`

A page source is an HTML fragment that starts with a comment of `key: value` lines:

    <!--
    path: /products/
    title: Products · Aveneg Technologies, LLC
    description: One or two sentences for search results.
    nav: products            (home | products | about | contact | none)
    modified: 2026-10-13     (the day the page's content last changed)
    robots: index, follow    (optional; default shown)
    sitemap: yes             (optional; `no` keeps it out of sitemap.xml and llms-full.txt)
    -->

Any <script type="application/ld+json"> block in the fragment is moved into <head>.
The rest becomes the page's <main>. `{{include:lockup-archive}}` in a page pulls in
src/partials/lockup-archive.html, so each product logo is written once. The masthead and
the colophon pull in lockup-house.html, the company's own logo, the same way.

Standard library only, and no syntax newer than Python 3.8: macOS's own python3 can run it.
"""
import html
import pathlib
import re
import sys
import tempfile
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT = ROOT / "public"
SITE = "https://avenegtechnologies.com"
NAV_KEYS = ("home", "products", "about", "contact")
JSONLD = re.compile(r'<script type="application/ld\+json">.*?</script>\s*', re.S)
INCLUDE = re.compile(r"\{\{include:([a-z-]+)\}\}")


def read(path):
    return path.read_text(encoding="utf-8")


def include(name, page):
    """{{include:name}} in a page pulls in src/partials/name.html (the product lockups)."""
    part = SRC / "partials" / (name + ".html")
    if not part.exists():
        raise SystemExit("%s includes %s, but src/partials/%s.html does not exist" % (page, name, name))
    return read(part).rstrip("\n")


def parse_page(path):
    """Split a page source into its front matter, its JSON-LD blocks and its body."""
    text = read(path)
    match = re.match(r"\s*<!--\n(.*?)\n-->\n?", text, re.S)
    if not match:
        raise SystemExit("%s: must start with a <!-- key: value --> comment" % path)
    meta = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise SystemExit("%s: front matter line needs `key: value`: %r" % (path, line))
        meta[key.strip()] = value.strip()
    for key in ("path", "title", "description", "nav", "modified"):
        if key not in meta:
            raise SystemExit("%s: front matter is missing `%s`" % (path, key))
    if meta["nav"] not in NAV_KEYS + ("none",):
        raise SystemExit("%s: nav must be one of %s or none" % (path, ", ".join(NAV_KEYS)))
    body = INCLUDE.sub(lambda m: include(m.group(1), path), text[match.end():])
    meta["jsonld"] = "".join(m.group(0).strip() + "\n" for m in JSONLD.finditer(body))
    meta["body"] = JSONLD.sub("", body).strip() + "\n"
    meta["source"] = path
    return meta


def out_path(meta, root):
    path = meta["path"]
    if path.endswith("/"):
        return root / path.strip("/") / "index.html" if path != "/" else root / "index.html"
    return root / path.lstrip("/")


def fill(template, values):
    """Replace {{name}} tokens. An unknown token is an error, not an empty string."""
    def sub(match):
        name = match.group(1)
        if name not in values:
            raise SystemExit("template uses {{%s}} but no value was given" % name)
        return values[name]
    return re.sub(r"\{\{([a-z_:]+)\}\}", sub, template)


def render(meta, partials):
    values = {
        "title": html.escape(meta["title"], quote=True),
        "description": html.escape(meta["description"], quote=True),
        "robots": meta.get("robots", "index, follow"),
        "canonical": SITE + meta["path"],
        "jsonld": meta["jsonld"],
    }
    for key in NAV_KEYS:
        values["current:" + key] = ' aria-current="page"' if meta["nav"] == key else ""
    # A page that should not be indexed gets no canonical, Open Graph or Twitter tags.
    head = partials["head-noindex" if "noindex" in values["robots"] else "head"]
    page = (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        + fill(head, values)
        + "</head>\n<body>\n"
        + fill(partials["masthead"], values)
        + '\n<main id="main">\n'
        + meta["body"]
        + "</main>\n\n"
        + fill(partials["colophon"], values)
        + "\n</body>\n</html>\n"
    )
    return page


# ---------------------------------------------------------------------------
# llms-full.txt: the same pages as plain, quotable text
# ---------------------------------------------------------------------------

VOID = {"img", "br", "hr", "meta", "link", "input", "source", "col", "wbr"}
SKIP = {"script", "style", "svg"}
BLOCKS = {"p", "div", "section", "article", "address", "figure", "figcaption", "ul", "ol",
          "blockquote", "caption", "dl", "thead", "tbody", "main"}
LABEL_CLASSES = {"label", "eyebrow", "status"}
BREAK = "\u0000"


class PageText(HTMLParser):
    """Turn a page body into Markdown-flavoured text an assistant can quote."""

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.blocks = []
        self.buf = []
        self.skipping = 0
        self.links = []
        self.prefix = ""
        self.emphasis = False
        self.rows = None
        self.row = None
        self.term = None

    def text(self):
        raw = "".join(self.buf)
        self.buf = []
        parts = [re.sub(r"\s+", " ", p).strip() for p in raw.split(BREAK)]
        return "  \n".join(p for p in parts if p)

    def flush(self):
        text = self.text()
        if text:
            if self.emphasis:
                text = "_%s_" % text
            self.blocks.append(self.prefix + text)
        self.prefix = ""
        self.emphasis = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.skipping:
            if tag not in VOID:
                self.skipping += 1
            return
        if tag in SKIP or attrs.get("aria-hidden") == "true":
            if tag not in VOID:
                self.skipping = 1
            return
        classes = set((attrs.get("class") or "").split())
        if tag in ("h1", "h2", "h3", "h4"):
            self.flush()
            self.prefix = "#" * int(tag[1]) + " "
        elif tag in BLOCKS:
            self.flush()
            self.emphasis = tag == "p" and bool(classes & LABEL_CLASSES)
        elif tag == "li":
            self.flush()
            self.prefix = "- "
        elif tag == "br":
            self.buf.append(BREAK)
        elif tag == "a":
            self.links.append((len(self.buf), attrs.get("href", "")))
        elif tag == "img":
            if attrs.get("alt"):
                self.buf.append(attrs["alt"])
        elif tag == "table":
            self.flush()
            self.rows = []
        elif tag == "tr":
            self.row = []
        elif tag in ("th", "td", "dt", "dd"):
            self.buf = []

    def handle_endtag(self, tag):
        if self.skipping:
            self.skipping -= 1
            return
        if tag == "a" and self.links:
            start, href = self.links.pop()
            label = re.sub(r"\s+", " ", "".join(self.buf[start:])).strip()
            del self.buf[start:]
            if href.startswith("/"):
                href = SITE + href
            self.buf.append("[%s](%s)" % (label, href) if href and label else label)
        elif tag in ("h1", "h2", "h3", "h4", "li") or tag in BLOCKS:
            self.flush()
        elif tag in ("th", "td") and self.row is not None:
            self.row.append(self.text().replace("  \n", " ") or " ")
        elif tag == "tr" and self.rows is not None and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        elif tag == "table" and self.rows is not None:
            if self.rows:
                head, rest = self.rows[0], self.rows[1:]
                lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
                lines += ["| " + " | ".join(r) + " |" for r in rest]
                self.blocks.append("\n".join(lines))
            self.rows = None
        elif tag == "dt":
            self.term = self.text()
        elif tag == "dd":
            value = self.text()
            if value:
                self.blocks.append("- %s: %s" % (self.term, value) if self.term else "- " + value)
            self.term = None

    def handle_data(self, data):
        if not self.skipping:
            self.buf.append(data)


def page_text(body):
    parser = PageText()
    parser.feed(body)
    parser.close()
    parser.flush()
    # Consecutive list items and definition rows read as one list, not as spaced paragraphs.
    out = []
    for block in parser.blocks:
        if out and block.startswith("- ") and out[-1].split("\n")[-1].startswith("- "):
            out[-1] += "\n" + block
        else:
            out.append(block)
    return "\n\n".join(out)


def llms_full(pages):
    newest = max(p["modified"] for p in pages)
    parts = [
        "# Aveneg Technologies, LLC — full text of avenegtechnologies.com\n\n"
        "> The main content of every page on %s (the repeated header and footer are "
        "omitted), generated from the pages themselves; content last changed %s. If this "
        "file and a page disagree, the page wins. Short index: %s/llms.txt. Fact sheet: "
        "%s/AGENTS.md." % (SITE, newest, SITE, SITE)
    ]
    for meta in pages:
        parts.append("---\n\nSource: %s%s\n\n%s" % (SITE, meta["path"], page_text(meta["body"])))
    return "\n\n".join(parts) + "\n"


def sitemap(pages):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for meta in pages:
        lines += ["  <url>", "    <loc>%s%s</loc>" % (SITE, meta["path"]),
                  "    <lastmod>%s</lastmod>" % meta["modified"], "  </url>"]
    return "\n".join(lines + ["</urlset>"]) + "\n"


# ---------------------------------------------------------------------------

ORDER = ["/", "/products/", "/about/", "/contact/", "/terms/", "/privacy/"]


def build(root):
    """Return {output path: text} for everything this script owns."""
    partials = {p.stem: read(p) for p in sorted((SRC / "partials").glob("*.html"))}
    for name in ("head", "head-noindex", "masthead", "colophon"):
        if name not in partials:
            raise SystemExit("src/partials/%s.html is missing" % name)
    for name in ("masthead", "colophon"):
        # The house lockup is written once (lockup-house.html) and used in both.
        partials[name] = INCLUDE.sub(
            lambda m, name=name: include(m.group(1), "src/partials/%s.html" % name), partials[name])
    pages = [parse_page(p) for p in sorted((SRC / "pages").glob("*.html"))]
    seen = {}
    for meta in pages:
        if meta["path"] in seen:
            raise SystemExit("%s and %s both claim %s" % (seen[meta["path"]], meta["source"], meta["path"]))
        seen[meta["path"]] = meta["source"]
    listed = [m for m in pages if m.get("sitemap", "yes") != "no"]
    listed.sort(key=lambda m: ORDER.index(m["path"]) if m["path"] in ORDER else len(ORDER))
    files = {out_path(meta, root): render(meta, partials) for meta in pages}
    files[root / "llms-full.txt"] = llms_full(listed)
    files[root / "sitemap.xml"] = sitemap(listed)
    return files


def main(argv):
    mode = argv[1] if len(argv) > 1 else "build"
    if mode == "build":
        files = build(OUT)
        for path, text in sorted(files.items()):
            path.parent.mkdir(parents=True, exist_ok=True)
            changed = not path.exists() or read(path) != text
            if changed:
                path.write_text(text, encoding="utf-8")
            print("%s %s" % ("wrote " if changed else "same  ", path.relative_to(ROOT)))
        return 0
    if mode == "check":
        with tempfile.TemporaryDirectory() as tmp:
            files = build(pathlib.Path(tmp))
            stale = []
            for path, text in sorted(files.items()):
                live = OUT / path.relative_to(tmp)
                if not live.exists() or read(live) != text:
                    stale.append(str(live.relative_to(ROOT)))
        if stale:
            print("public/ is out of date. Run `python3 tools/build.py`, then commit:")
            for name in stale:
                print("  " + name)
            return 1
        print("public/ matches src/ (%d files)" % len(files))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
