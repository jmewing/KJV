#!/usr/bin/env python3
"""
Build the final BIBLE NAMES publishing list.

Filter (Jeremy-confirmed 2026-09-23):
  * people names only (places/things/groups/titles excluded)
  * QUALIFY at >= 5 occurrences in the KJV  -> ~845 names
  * normalize possessives (David's -> David)
  * drop remaining non-people stragglers
  * weight: UNCOMMON names first (early 2025), common names later
  * scramble within bands so it is NOT alphabetical, but keeps the
    uncommon-first tendency Jeremy described

Output: wp-import/names/final-names.json  (ordered Tue/Thu publishing list)
        wp-import/names/final-report.txt
"""
import csv
import json
import os
import random
from collections import Counter

NAMES = "/srv/kjv/wp-import/names"
MIN_OCC = 5
SEED = 20250101  # deterministic scramble

random.seed(SEED)

# --- remaining non-people that survive the >=5 filter ---------------------
EXTRA_EXCLUDE = set("""
Almighty Art Gibeah
Selah Amen Hosanna Hallelujah
Zion Sion Goshen Rameses
Baal Ashtaroth Asherah Molech Chemosh Dagon Rimmon Tammuz
Bel Merodach Nebo Succothbenoth Milcom
""".split())

# --- tribal/patriarch names: keep, but they are people (sons of Jacob) ----
PATRIARCHS = {
    "Reuben", "Simeon", "Levi", "Judah", "Dan", "Naphtali", "Gad",
    "Asher", "Issachar", "Zebulun", "Joseph", "Benjamin",
    "Ephraim", "Manasseh",
}

# --- read the extracted candidates ----------------------------------------
rows = list(csv.DictReader(open(os.path.join(NAMES, "people-names.csv"))))

# normalize possessives and merge counts
merged = Counter()
for r in rows:
    nm = r["name"]
    n = int(r["verse_count"])
    base = nm[:-2] if nm.endswith("'s") else nm
    merged[base] += n

print(f"candidates after possessive-merge: {len(merged)}")

# --- apply the >=5 cutoff + exclusions ------------------------------------
final = {}
for nm, n in merged.items():
    if n < MIN_OCC:
        continue
    if nm in EXTRA_EXCLUDE:
        continue
    final[nm] = n

print(f"qualifying names (>= {MIN_OCC} occurrences): {len(final)}")

# --- weight: uncommon FIRST, common LATER ---------------------------------
# "Commonality today" is proxied by KJV frequency as a weak signal, but the
# real intent is: rare/obscure biblical names early, household names late.
# Rank by frequency ascending => least-mentioned (most obscure) go first.
ordered = sorted(final.items(), key=lambda x: x[1])  # ascending freq

# --- scramble within frequency bands to avoid an obviously alphabetical ----
# --- or strictly ascending list -------------------------------------------
bands = {}
for nm, n in ordered:
    key = n // 5  # band width of 5 occurrences
    bands.setdefault(key, []).append(nm)

scrambled = []
for key in sorted(bands.keys()):
    chunk = bands[key][:]
    random.shuffle(chunk)
    scrambled.extend(chunk)

# --- emit ----------------------------------------------------------------
out = []
for i, nm in enumerate(scrambled, 1):
    out.append({
        "position": i,
        "name": nm,
        "verse_count": final[nm],
        "is_patriarch": nm in PATRIARCHS,
    })

json.dump(out, open(os.path.join(NAMES, "final-names.json"), "w"), indent=2)

rep = []
rep.append("=== FINAL BIBLE NAMES LIST ===")
rep.append(f"qualifying: {len(out)} names (>= {MIN_OCC} occurrences, people only)")
rep.append(f"scramble seed: {SEED} (deterministic)")
rep.append("")
rep.append("--- FIRST 40 (most obscure, early 2025) ---")
for r in out[:40]:
    rep.append(f"  {r['position']:>3}  {r['verse_count']:>4}x  {r['name']}")
rep.append("")
rep.append("--- LAST 40 (most common, late in series) ---")
for r in out[-40:]:
    rep.append(f"  {r['position']:>3}  {r['verse_count']:>4}x  {r['name']}")
open(os.path.join(NAMES, "final-report.txt"), "w").write("\n".join(rep))
print("\n".join(rep))
