#!/usr/bin/env python3
"""
Build the BIBLE NAMES list from the authoritative BibleAsk KJV dataset.

Source: bibleask.org/wp-json/bibleask-labs/v1/names  (3,435 names, KJV)
  1,945 categorised 'person'  (matches Wikipedia's 1,940 individuals)
  each entry has: name, verseCount, gender, testament(s), description,
                  subtype, refs, aliasOf

Rules (Jeremy-confirmed):
  * PEOPLE ONLY (category contains 'person')
  * fold aliases via aliasOf into the canonical spelling
  * WEIGHT + SHUFFLE: least common first, most common last, banded so it is
    not alphabetical and not a rigid ascending list
  * use what fits 2025-2026; the remainder continues in 2027
"""
import json
import os
import random

REPO = "/srv/kjv"
NDIR = os.path.join(REPO, "wp-import", "names")
SRC = "/tmp/ba-names.json"

data = json.load(open(SRC))
all_names = data["names"]
people = [n for n in all_names if "person" in (n.get("categories") or [])]
print(f"source entries: {len(all_names)}")
print(f"people entries: {len(people)}")

# --- fold aliases ---------------------------------------------------------
by_name = {n["name"]: n for n in people}
canon, folded = [], []
for n in people:
    alias = n.get("aliasOf")
    if alias and alias in by_name and by_name[alias] is not n:
        folded.append((n["name"], alias))
        t = by_name[alias]
        t["verseCount"] = t.get("verseCount", 0) + n.get("verseCount", 0)
        t.setdefault("also_known_as", []).append(n["name"])
        continue
    canon.append(n)
print(f"aliases folded: {len(folded)}")
print(f"canonical people: {len(canon)}")

# --- WEIGHT + SHUFFLE ----------------------------------------------------
# least common -> earliest; most common -> latest; banded shuffle so it is
# not alphabetical and not a strict ascending list
canon.sort(key=lambda n: n.get("verseCount", 0))
random.seed(20250101)
bands = {}
for n in canon:
    vc = n.get("verseCount", 0)
    key = vc if vc <= 25 else (vc // 25) * 25
    bands.setdefault(key, []).append(n)
ordered = []
for k in sorted(bands):
    chunk = bands[k][:]
    random.shuffle(chunk)
    ordered.extend(chunk)
for i, n in enumerate(ordered, 1):
    n["position"] = i

json.dump(ordered, open(os.path.join(NDIR, "BIBLEASK-people.json"), "w"), indent=2)

rep = []
rep.append("=== BIBLEASK PEOPLE NAMES (authoritative KJV list) ===")
rep.append(f"source entries: {len(all_names)} | people: {len(people)} | aliases folded: {len(folded)} | final: {len(ordered)}")
rep.append("")
rep.append("--- first 30 (LEAST common -> earliest) ---")
for n in ordered[:30]:
    rep.append(f"  {n['position']:>4}  {n.get('verseCount',0):>4}x  {n['name']:<22} {n.get('gender','?'):<7} {n.get('description','')[:50]}")
rep.append("")
rep.append("--- last 30 (MOST common -> latest) ---")
for n in ordered[-30:]:
    rep.append(f"  {n['position']:>4}  {n.get('verseCount',0):>4}x  {n['name']:<22} {n.get('gender','?'):<7} {n.get('description','')[:50]}")
rep.append("")
rep.append("--- alias folds ---")
for a, b in sorted(folded):
    rep.append(f"  {a}  ->  {b}")
open(os.path.join(NDIR, "BIBLEASK-report.txt"), "w").write("\n".join(rep))

print("\n".join(rep[:6]))
print("...")
print(f"\nwrote BIBLEASK-people.json ({len(ordered)} names)")
