#!/usr/bin/env python3
"""Tell the IndexNow search engines (Bing, and through it ChatGPT search and Copilot;
Yandex, Seznam, Naver) which pages changed, so they recrawl at once instead of waiting
for the sitemap. Family guide 1.34, "Promotion plumbing"; copied in spirit from the
Vintage site's tools/indexnow.mjs (2026-11-14).

The key is the 32-hex name of the one public/<key>.txt file; that file holds the key.

  python3 tools/indexnow.py --since <git-ref>   pages whose built HTML changed since that commit
  python3 tools/indexnow.py --all               every page in public/sitemap.xml
  python3 tools/indexnow.py <url> [<url> ...]   those addresses
  add --dry to print the list without sending it

Run it after a push, once the deploy is live (about 90 s). The first submit can answer
403 "SiteVerificationNotCompleted" until the engines have fetched the key file; retry
until 200 or 202.
"""
import json, re, subprocess, sys, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
ORIGIN = "https://avenegtechnologies.com"

keys = [p for p in PUBLIC.glob("*.txt") if re.fullmatch(r"[0-9a-f]{32}", p.stem)]
if len(keys) != 1:
    sys.exit(f"indexnow: expected one public/<32-hex>.txt key file, found {len(keys)}")
key = keys[0].stem
if keys[0].read_text().strip() != key:
    sys.exit("indexnow: the key file must contain its own name")

def to_url(f: str):
    p = f.removeprefix("public/")
    if p in ("404.html",):
        return None
    if p == "index.html":
        return ORIGIN + "/"
    if p.endswith("/index.html"):
        return f"{ORIGIN}/{p[:-len('index.html')]}"
    return None

args = sys.argv[1:]
dry = "--dry" in args
if "--all" in args:
    urls = re.findall(r"<loc>([^<]+)</loc>", (PUBLIC / "sitemap.xml").read_text())
elif "--since" in args:
    ref = args[args.index("--since") + 1]
    changed = subprocess.run(["git", "diff", "--name-only", ref, "HEAD", "--", "public"],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    urls = [u for u in map(to_url, changed) if u]
    if urls:
        urls.append(f"{ORIGIN}/sitemap.xml")
else:
    urls = [a for a in args if a.startswith("http")]
urls = [u for u in dict.fromkeys(urls) if u.startswith(ORIGIN)]
if not urls:
    print("indexnow: nothing changed, nothing sent."); sys.exit(0)
if dry:
    print("\n".join(urls)); print(f"indexnow: {len(urls)} URLs (dry run, not sent)."); sys.exit(0)

body = json.dumps({"host": "avenegtechnologies.com", "key": key,
                   "keyLocation": f"{ORIGIN}/{key}.txt", "urlList": urls}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, method="POST",
                             headers={"Content-Type": "application/json; charset=utf-8"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        status, text = r.status, r.read().decode(errors="replace")
except urllib.error.HTTPError as e:
    status, text = e.code, e.read().decode(errors="replace")
# 200 OK and 202 Accepted both mean received; 403 means the key is not verified yet.
print(f"indexnow: {len(urls)} URLs -> HTTP {status}")
if status not in (200, 202):
    print(text, file=sys.stderr); sys.exit(1)
