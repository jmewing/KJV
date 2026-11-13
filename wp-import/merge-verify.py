#!/usr/bin/env python3
"""
Merge all generated content into ONE insert-ready set and verify it.

This is the gate before WordPress. It:
  1. loads every generated content file
  2. sorts the WHOLE set by date (the original bug was batch-by-series inserts)
  3. verifies ZERO date inversions
  4. verifies every record has real content (no placeholders)
  5. writes INDEX.json (the insert order) + a human report

Run:  python3 wp-import/merge-verify.py
"""
import glob
import json
import os
from datetime import datetime

REPO = "/srv/kjv"
OUT = os.path.join(REPO, "wp-import", "content")
REPORT = os.path.join(REPO, "wp-import", "MERGE-REPORT.txt")

recs = []
missing = []
for f in sorted(glob.glob(os.path.join(OUT, "[0-9]*-*.json"))):
    if f.endswith("INDEX.json"):
        continue
    try:
        d = json.load(open(f))
        recs.append(d)
    except Exception as e:
        missing.append((f, str(e)))

print(f"content files: {len(recs)}  unreadable: {len(missing)}")

# --- sort the WHOLE set by date, then by series for ties ----------------
for r in recs:
    r["_dt"] = datetime.fromisoformat(r["date"])
recs.sort(key=lambda r: (r["_dt"], r["series"]))

# --- verify zero inversions --------------------------------------------
inversions = []
for i in range(1, len(recs)):
    if recs[i]["_dt"] < recs[i - 1]["_dt"]:
        inversions.append(i)

# --- verify content is real --------------------------------------------
PLACEHOLDERS = ("(pending)", "<p>(content pending)</p>")
ph = []
for r in recs:
    h = r.get("html") or ""
    if not h or len(h) < 200 or any(p in h for p in PLACEHOLDERS):
        ph.append((r["order"], r["slug"], len(h)))

# --- rewrite INDEX.json in final order ---------------------------------
index = []
for i, r in enumerate(recs, 1):
    r["order"] = i
    fn = f"{i:05d}-{r['slug']}.json"
    r["_file"] = fn
    index.append({"order": i, "slug": r["slug"], "series": r["series"],
                  "title": r["title"], "date": r["date"],
                  "category": r["category"], "file": fn})

# --- write the merged set under insert/ ---------------------------------
INS = os.path.join(REPO, "wp-import", "insert")
os.makedirs(INS, exist_ok=True)
for r in recs:
    payload = {k: v for k, v in r.items() if not k.startswith("_")}
    json.dump(payload, open(os.path.join(INS, r["_file"]), "w"), indent=2)
# keep the raw content dir in sync too
for r in recs:
    payload = {k: v for k, v in r.items() if not k.startswith("_")}
    json.dump(payload, open(os.path.join(OUT, r["_file"]), "w"), indent=2)
json.dump(index, open(os.path.join(INS, "INDEX.json"), "w"), indent=2)

from collections import Counter
counts = Counter(r["series"] for r in recs)
lines = []
lines.append("=== MERGE REPORT — insert-ready set ===")
lines.append(f"records: {len(recs)}")
lines.append(f"DATE INVERSIONS: {len(inversions)}   (must be 0)")
lines.append(f"placeholders/short: {len(ph)}")
lines.append("")
lines.append("--- per series ---")
for k, v in sorted(counts.items()):
    szs = sorted(len(r["html"]) for r in recs if r["series"] == k)
    lines.append(f"  {k:<12} {v:>5}   median_html={szs[len(szs)//2]:>6}  min={szs[0]:>5}  max={szs[-1]}")
lines.append("")
lines.append(f"first: {recs[0]['date']}  {recs[0]['series']:<12} {recs[0]['title']}")
lines.append(f"last:  {recs[-1]['date']}  {recs[-1]['series']:<12} {recs[-1]['title']}")
if inversions[:5]:
    lines.append("")
    lines.append("--- first inversions ---")
    for i in inversions[:5]:
        lines.append(f"  idx {i}: {recs[i-1]['date']} {recs[i-1]['slug']}  ->  {recs[i]['date']} {recs[i]['slug']}")
if ph[:10]:
    lines.append("")
    lines.append("--- placeholder/short records ---")
    for o, s, n in ph[:10]:
        lines.append(f"  {o} {s} ({n} bytes)")

open(REPORT, "w").write("\n".join(lines))
print("\n".join(lines))
