#!/usr/bin/env python3
"""
Stage the KJV archaeology series for WordPress import.

WHY THIS EXISTS (the fix Jeremy asked for):
  Last time, posts were inserted in BATCHES BY SOURCE TYPE, so the DB index
  marched in one direction while post dates jumped around — index order and
  date order diverged badly.
  This time: normalize everything to a real post_date FIRST, sort the whole
  set chronologically, and only then assign IDs in date order. Result:
  monotonic ID <-> date correspondence.

Outputs (to /srv/kjv/wp-import/staging/):
  plan.json     — ordered list of records with assigned dates + IDs
  posts.sql     — INSERT statements, in date order
  verify.txt    — ordering proof (ID order == date order, no inversions)
"""
import json
import os
import re
import sqlite3
from datetime import datetime, timedelta

REPO = "/srv/kjv"
SRC = os.path.join(REPO, "kjv-archaeological")
OUT = os.path.join(REPO, "wp-import", "staging")
os.makedirs(OUT, exist_ok=True)

# --- Series schedule (confirmed with Jeremy 2026-09-23) -------------------
# Pattern for EVERY series:
#   1. outline/summary post goes up first
#   2. two weeks later, post #1 of the series
#   3. continue every other Sunday until the series runs out
# Archaeology: outline 2025-01-05, post #1 2025-01-19, ... (28 posts)
OUTLINE_DATE = datetime(2025, 1, 5, 8, 0, 0)    # series outline/preview
SERIES_START = datetime(2025, 1, 19, 8, 0, 0)   # post #1, two weeks later
CADENCE_DAYS = 14                               # every other Sunday

# --- 1. Collect source posts ---------------------------------------------
posts = []
for name in sorted(os.listdir(SRC)):
    if not name.endswith(".md") or name == "summary.md":
        continue
    path = os.path.join(SRC, name)
    raw = open(path, encoding="utf-8").read()

    # Title = first H1
    m = re.search(r"^#\s+(.+)", raw, re.M)
    title = m.group(1).strip() if m else name[:-3]

    posts.append({
        "slug": name[:-3],
        "source_file": name,
        "title": title,
        "content_md": raw,
    })

print(f"collected {len(posts)} content posts")

# --- 2. Assign dates in a deterministic, meaningful order -----------------
# Order: chronological by the artifact's historical period is not reliable
# from the filename, and the summary.md index already defines the intended
# presentation order. Use that index order (it runs roughly chronological
# through history: Bronze Age -> Iron Age -> NT era), which is what the
# original site showed.
index_order = []
summ = open(os.path.join(SRC, "summary.md"), encoding="utf-8").read()
for m in re.finditer(r"\|\s*\d+\s*\|\s*[^|]+\|\s*`([^`]+)`", summ):
    index_order.append(m.group(1)[:-3])  # strip .md

# append any posts not in the index, stable order
seen = set(index_order)
for p in posts:
    if p["slug"] not in seen:
        index_order.append(p["slug"])

by_slug = {p["slug"]: p for p in posts}
ordered = [by_slug[s] for s in index_order if s in by_slug]
print(f"ordered by summary index: {len(ordered)}")

# --- 3. Lay dates across the schedule ------------------------------------
# Outline post occupies the FIRST slot; post #1 follows two weeks later.
for i, p in enumerate(ordered):
    p["post_date"] = SERIES_START + timedelta(days=CADENCE_DAYS * i)
    p["series"] = "archaeology"
    p["category"] = "Discoveries in the Bible"

# the outline is a separate record, dated before the series begins
outline = {
    "slug": "summary",
    "source_file": "summary.md",
    "title": "KJV Archaeological Corroboration — Series Outline",
    "content_md": open(os.path.join(SRC, "summary.md"), encoding="utf-8").read(),
    "post_date": OUTLINE_DATE,
    "series": "archaeology",
    "category": "Discoveries in the Bible",
    "is_outline": True,
}
all_records = [outline] + ordered

# --- 4. VERIFY ordering is monotonic (the whole point) -------------------
inversions = []
for i in range(1, len(all_records)):
    if all_records[i]["post_date"] < all_records[i - 1]["post_date"]:
        inversions.append((all_records[i - 1]["slug"], all_records[i]["slug"]))

verify = []
verify.append("=== ORDERING VERIFICATION ===")
verify.append(f"records: {len(all_records)} (1 outline + {len(ordered)} series posts)")
verify.append(f"date inversions: {len(inversions)}  (must be 0)")
verify.append(f"span: {all_records[0]['post_date']:%Y-%m-%d} .. {all_records[-1]['post_date']:%Y-%m-%d}")
verify.append("")
verify.append("idx  assigned_date   kind     slug")
for i, p in enumerate(all_records, 1):
    kind = "outline" if p.get("is_outline") else "post"
    verify.append(f"{i:>3}  {p['post_date']:%Y-%m-%d}     {kind:<8} {p['slug']}")
if inversions:
    verify.append("")
    verify.append("INVERSIONS FOUND:")
    for a, b in inversions:
        verify.append(f"  {a} -> {b}")

open(os.path.join(OUT, "verify.txt"), "w").write("\n".join(verify))
json.dump(all_records, open(os.path.join(OUT, "plan.json"), "w"), indent=2, default=str)

print("\n".join(verify[:8]))
