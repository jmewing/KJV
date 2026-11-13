#!/usr/bin/env python3
"""
FINAL names pass v2 — fixes found by the integrity check:

  A. book-title collisions (Jeremiah, Job, Isaiah, John, Matthew...) inflated
     their verse counts because the counter included book headings and
     cross-references. Fix: count BODY TEXT only (strip "Book C:V " prefixes
     and any standalone book-name headings).
  B. remaining non-people that reappeared or survived: Christ, Tema, Zanoah,
     Peor, Purim, Eshtemoa, and any other place/title stragglers.
  C. minimum-occurrence cutoff re-applied AFTER correct counting.

Outputs: wp-import/names/LIST.json  +  LIST-report.txt   (the real final list)
"""
import json
import os
import random
import re

REPO = "/srv/kjv"
KJV = os.path.join(REPO, "kjv-texts", "kjv.txt")
NDIR = os.path.join(REPO, "wp-import", "names")
MIN_OCC = 5

# --- A. build BODY TEXT only --------------------------------------------
raw = open(KJV, encoding="utf-8").read()
# drop the "Genesis 1:1 " style verse prefixes so "Genesis"/book names in
# refs are not counted as occurrences of a person
body = re.sub(r"^[1-3]?\s?[A-Za-z]+(?:\s+of\s+[A-Za-z]+)?\s+\d+:\d+\s+", "", raw, flags=re.M)
print(f"body text: {len(body)} chars (from {len(raw)})")

# --- B. hard exclusions: titles, places, things that must never publish ---
NOT_PEOPLE = set("""
Christ Jesus Lord God Father Son Spirit Ghost Almighty Most High
Lamb Rock Redeemer Saviour Savior Mediator Comforter
Word Light Truth Way Life Bread Vine Door Shepherd Cornerstone
Amen Selah Hosanna Hallelujah Zion Sion
Tema Zanoah Peor Purim Eshtemoa Nob Bahurim Rephidim
Mizpeh Shushan Ramothgilead Tirzah Ziklag Joppa Riblah Hor
Olives Howl Art Gibeah
Babylon Egypt Assyria Persia Greece Rome Israel Judah Jerusalem Eden
Sinai Horeb Canaan Philistia Palestina Emmaus Galilee Samaria Bethlehem
""".split())

names = json.load(open(os.path.join(NDIR, "FINAL-names.json")))
print(f"in: {len(names)}")

out = []
for r in names:
    nm = r["name"]
    if nm in NOT_PEOPLE:
        continue
    # C. recount against BODY TEXT ONLY
    n = len(re.findall(r"\b" + re.escape(nm) + r"\b", body))
    if n < MIN_OCC:
        continue
    r = dict(r)
    r["verse_count"] = n
    out.append(r)

print(f"after exclusion + body-only recount: {len(out)}")

# --- ordering: uncommon first, common later; scrambled within bands -----
random.seed(20250101)
out.sort(key=lambda r: r["verse_count"])
bands = {}
for r in out:
    bands.setdefault(r["verse_count"] // 5, []).append(r)
ordered = []
for k in sorted(bands):
    chunk = bands[k][:]
    random.shuffle(chunk)
    ordered.extend(chunk)
for i, r in enumerate(ordered, 1):
    r["position"] = i

json.dump(ordered, open(os.path.join(NDIR, "LIST.json"), "w"), indent=2)

rep = []
rep.append("=== FINAL PEOPLE-NAMES LIST (v2, body-text counted) ===")
rep.append(f"count: {len(ordered)}")
rep.append("")
rep.append("--- book-name people, corrected counts (were inflated) ---")
for b in ["Jeremiah","Job","Isaiah","John","Matthew","Ezra","Nehemiah","Daniel","Esther","Ruth","Amos","Joel","Micah","Haggai","Zephaniah","Zechariah","Obadiah","Jonah","James","Titus"]:
    m = next((r for r in ordered if r["name"] == b), None)
    rep.append(f"  {b:<14} {m['verse_count'] if m else '-'}")
rep.append("")
rep.append("--- first 25 (obscure, early) ---")
for r in ordered[:25]:
    rep.append(f"  {r['position']:>3}  {r['verse_count']:>4}x  {r['name']}")
rep.append("")
rep.append("--- last 25 (common, late) ---")
for r in ordered[-25:]:
    rep.append(f"  {r['position']:>3}  {r['verse_count']:>4}x  {r['name']}")
rep.append("")
rep.append("--- titles that must be absent ---")
for w in ["Christ","Lord","God","Father","Almighty"]:
    rep.append(f"  {w:<12} {'PRESENT!' if any(r['name']==w for r in ordered) else 'absent OK'}")
open(os.path.join(NDIR, "LIST-report.txt"), "w").write("\n".join(rep))
print("\n".join(rep[:30]))
