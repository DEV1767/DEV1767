#!/usr/bin/env python3
"""Fetch the public contribution calendar for a user into data/contributions.json.

Usage: python scripts/fetch_contributions.py [username]
No token needed: it reads the same public HTML fragment GitHub's profile page uses.
"""
import json, re, sys, urllib.request, pathlib

USER = sys.argv[1] if len(sys.argv) > 1 else "DEV1767"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "contributions.json"

req = urllib.request.Request(
    f"https://github.com/users/{USER}/contributions",
    headers={"User-Agent": "profile-card-renderer"},
)
html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")

cells = {}
for m in re.finditer(r"<td[^>]*?data-date=\"([\d-]+)\"[^>]*?id=\"([^\"]+)\"[^>]*?data-level=\"(\d)\"", html):
    cells[m.group(2)] = {"date": m.group(1), "level": int(m.group(3)), "count": 0}

for m in re.finditer(r"<tool-tip[^>]*?for=\"([^\"]+)\"[^>]*>([^<]*)</tool-tip>", html):
    cid, text = m.group(1), m.group(2)
    n = re.match(r"(\d+) contribution", text.strip())
    if cid in cells and n:
        cells[cid]["count"] = int(n.group(1))

days = sorted(cells.values(), key=lambda d: d["date"])
if not days:
    sys.exit("No contribution cells found; GitHub markup may have changed.")

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps({"user": USER, "days": days}, indent=1))
print(f"{USER}: {len(days)} days, {sum(d['count'] for d in days)} contributions -> {OUT}")
