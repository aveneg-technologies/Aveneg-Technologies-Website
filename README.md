# avenegtechnologies.com

The business website of Aveneg Technologies, LLC. Static HTML and one stylesheet, served by
Cloudflare from `public/`. No JavaScript, no web fonts, no build at deploy time.

## Changing the site

```
src/pages/        one file per page: its own content only
src/partials/     the parts every page shares: head, masthead, colophon, the product lockups
public/styles/site.css    the one stylesheet
public/img/       the hero dial, the product pictures, the Tracker lockup
tools/build.py    writes public/*.html, public/llms-full.txt and public/sitemap.xml from src/
```

1. Edit a page in `src/pages/` or a shared part in `src/partials/`. Change the page's `modified:`
   date when its content changes.
2. `python3 tools/build.py`
3. `python3 tools/build.py check` (exits 1 if `public/` is not what `src/` builds)
4. Commit `src/` and `public/` together. A push to `main` deploys.

Never edit `public/*.html`, `public/llms-full.txt` or `public/sitemap.xml` by hand: the next
build overwrites them. Everything else in `public/` (the stylesheet, images, `robots.txt`,
`llms.txt`, `AGENTS.md`, `_headers`) is edited in place.

When a fact about the company or a product changes, change it in the page **and** in
`public/llms.txt` and `public/AGENTS.md`, which state the same facts for AI assistants.

## Rules the copy follows

- The company is privacy first. "Encrypted" is said only of Watch Vault Archive.
- Both products are in development, coming Winter 2027. Neither is available.
- No personal names, no phone number, no price, no tip amounts.
- The legal text on Terms and Privacy is changed only on purpose, with its "Last updated" date.

## Pictures and ornament

- `public/img/dial.svg` is drawn by `tools/gen_dial.py public/img/dial.svg`.
- `public/og-image.png` is rendered from `tools/og-image.html` (the command is at the top of that file).
- `public/img/watch-vault-archive.webp` is the Archive's own published product image, unmodified.
  The Home page shows list rows four to six of it (see the note in section 4.7 of the stylesheet).
- `public/img/watch-vault-tracker.webp` is the Tracker site's phone illustration, captured at 2x.
- `public/img/watch-vault-tracker-lockup.svg` is the Tracker's lockup artwork: replace the file
  from the Tracker's own artwork, never redraw a shape.

## Security header

`public/_headers` sends a Content-Security-Policy that allows only this site's own stylesheet
and images, plus Cloudflare's Web Analytics script. Inline `style=""` attributes and `<style>`
blocks are blocked by it, so keep all styling in `site.css`.
