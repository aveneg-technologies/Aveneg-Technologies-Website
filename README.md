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
- Both products are in development, coming Early 2027. Neither is available.
- No personal names, no phone number, no price, no tip amounts.
- Trademark (Brad, 2026-10-23): the brand is "Watch Vault"; the TM goes after "Vault", never
  after the product name ("Watch Vault™ Archive"). In the lockups, a superscript TM after
  VAULT and nothing after ARCHIVE or TRACKER. In running text only the first prominent
  mention of each product on a page carries it. ™ only, never ®. No trademark sentence
  anywhere. Aveneg Technologies' own name and logo carry no mark.
- The legal text on Terms and Privacy is changed only on purpose, with its "Last updated" date.

## Pictures and ornament

- **The company logo** is the owner's own artwork (drawn 2026-10-13): a brass disc with the
  letter A cut out of it inside a ring, AVENEG over TECHNOLOGIES. Its shapes are never redrawn;
  to change the logo, replace the paths from new artwork. It lives in four places:
  - `src/partials/lockup-house.html`: the masthead and the colophon both include it. Its colours
    come from the stylesheet (`.house-ring`, `.house-brass`, `.house-name`, `.house-sub`), so it
    follows the site's tokens and prints dark on white paper.
  - `public/img/aveneg-technologies-lockup.svg`: the same lockup as a file, in the colours for a
    dark ground (name `#D6D5D3`, sub-line `#A8ABB2`, brass `#C6A15B`), matching how the product
    lockups are coloured. The share card uses it.
  - `public/img/aveneg-technologies-lockup-light.svg`: the colours the artwork was drawn in, for
    a white or light ground (documents, letterhead). No page uses it.
  - `public/mark.svg`: the mark alone, the browser-tab icon. `favicon-32.png`,
    `apple-touch-icon.png` and `icon-512.png` are rendered from it (the last two on the ink
    ground); `icon-512.png` is also the `logo` in the home page's JSON-LD.
- `public/img/dial.svg` is drawn by `tools/gen_dial.py public/img/dial.svg`.
- `public/og-image.png` is rendered from `tools/og-image.html` (the command is at the top of that file).
- `public/img/watch-vault-archive.webp` is the Archive's own published product image, unmodified.
  The Home page shows list rows four to six of it (see the note in section 4.7 of the stylesheet).
- `public/img/watch-vault-tracker.webp` is the Tracker site's hero phone (its Today screen),
  captured whole at 2x (680 x 1427) from that site's own build. Re-take it when their hero
  phone changes; its corner is 56px on a 340 x 713 phone, which is the `16.5% / 7.85%` radius
  in the stylesheet.
- `src/partials/lockup-tracker.html` is the Tracker's lockup artwork, copied from the Tracker
  site's own page (its TM included); its colours come from the stylesheet (`.lk-*`). Replace
  it from the Tracker's page when theirs changes; never redraw a shape.