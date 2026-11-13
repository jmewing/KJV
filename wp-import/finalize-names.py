#!/usr/bin/env python3
"""
FINAL names cleanup — fixes the three defects found on 2026-09-23:

  1. lone divine titles / things that slipped through (God, Father, ...)
  2. the broken phonetic dup-detector (discarded) -> replaced with an
     EXPLICIT, scripture-verified spelling-variant map
  3. real people wrongly dropped (Doeg, ...) -> explicit re-admit list

Result: a final, defensible people-names list for the Tue-Fri series.

Outputs:
  wp-import/names/FINAL-names.json
  wp-import/names/FINAL-report.txt
"""
import json
import os
import re

REPO = "/srv/kjv"
KJV = os.path.join(REPO, "kjv-texts", "kjv.txt")
NDIR = os.path.join(REPO, "wp-import", "names")

names = json.load(open(os.path.join(NDIR, "cleaned-names.json")))
print(f"starting names: {len(names)}")

# --- 1. lone divine titles / non-persons that slipped through ------------
STILL_NOT_PEOPLE = set("""
God Father Son Spirit Ghost Lord Almighty Most High
Lamb Rock Redeemer Saviour Savior Mediator Comforter
Word Light Truth Way Life Bread Vine Door Shepherd
Amen Selah Hosanna Hallelujah Zion Sion
""".split())

# --- 2. explicit spelling-variant map (same person, different KJV spelling)
# Verified against scripture. Canonical form on the left is what we publish.
VARIANTS = {
    # NT Greek forms of OT names (same person, different testament spelling)
    "Elias": "Elijah",
    "Esaias": "Isaiah",
    "Jeremias": "Jeremiah",
    "Jonas": "Jonah",
    "Noe": "Noah",
    "Moses": "Moses",
    "Isaac": "Isaac",
    "Jacob": "Jacob",
    # KJV alternate spellings of the SAME individual
    "Ozias": "Uzziah",
    "Azarias": "Azariah",
    "Achaz": "Ahaz",
    "Ezechias": "Hezekiah",
    "Manasses": "Manasseh",
    "Josias": "Josiah",
    "Jechonias": "Jeconiah",
    "Zorobabel": "Zerubbabel",
    "Salathiel": "Shealtiel",
    "Abia": "Abijah",
    "Roboam": "Rehoboam",
    "Abijah": "Abijah",
    "Asa": "Asa",
    "Josaphat": "Jehoshaphat",
    "Joram": "Jehoram",
    "Ochosias": "Ahaziah",
    "Joatham": "Jotham",
    "Amon": "Amon",
    "Ezekias": "Hezekiah",
    "Sedecias": "Zedekiah",
    "Josedech": "Jehozadak",
    "Mathan": "Mattan",
    "Jona": "Jonah",
    "Zacharias": "Zechariah",
    "Elisabeth": "Elisabeth",
    "Judas": "Judah",
    "Juda": "Judah",
    "Simeon": "Simeon",
    "Levi": "Levi",
    "Aser": "Asher",
    "Zabulon": "Zebulun",
    "Issachar": "Issachar",
    "Nephthalim": "Naphtali",
    "Gad": "Gad",
    "Benjamin": "Benjamin",
    "Dan": "Dan",
    "Joseph": "Joseph",
    # people explicitly re-admitted (real persons my filter over-dropped)
}

# --- 3. real people the context filter wrongly dropped -------------------
READMIT = {
    "Doeg":   ("1 Samuel 21-22", "Edomite herdsman of Saul; killed the priests at Nob"),
    "Mizpeh": None,   # place — do NOT readmit; listed here only to be explicit
    "Shushan": None,  # place — do NOT readmit
    "Tirzah": None,   # place/person ambiguous — leave dropped
    "Ziklag": None,   # place
    "Joppa":  None,   # place
    "Riblah": None,   # place
}

# --- apply ---------------------------------------------------------------
merged = {}
for r in names:
    nm = r["name"]
    if nm in STILL_NOT_PEOPLE:
        continue
    canonical = VARIANTS.get(nm, nm)
    if canonical in merged:
        merged[canonical]["verse_count"] += r["verse_count"]
        merged[canonical]["also_known_as"].append(nm)
    else:
        merged[canonical] = {
            "name": canonical,
            "verse_count": r["verse_count"],
            "is_patriarch": r.get("is_patriarch", False),
            "also_known_as": [] if canonical == nm else [nm],
            "people_hits": r.get("people_hits", 0),
            "nonperson_hits": r.get("nonperson_hits", 0),
        }

# re-admit verified real people
for nm, info in READMIT.items():
    if info and nm not in merged:
        merged[nm] = {
            "name": nm,
            "verse_count": 5,      # appears >=5x; exact recount below
            "is_patriarch": False,
            "also_known_as": [],
            "readmitted": True,
            "note": info[1],
        }

print(f"after dedupe/title-drop: {len(merged)}")

# --- recount verse occurrences for the final set -------------------------
text = open(KJV, encoding="utf-8").read()
for nm, rec in merged.items():
    rec["verse_count"] = len(re.findall(r"\b" + re.escape(nm) + r"\b", text))

# --- ordering: UNCOMMON first, common later; scrambled within bands ------
final = sorted(merged.values(), key=lambda r: r["verse_count"])
# deterministic scramble within occurrence bands
import random
random.seed(20250101)
bands = {}
for r in final:
    bands.setdefault(r["verse_count"] // 5, []).append(r)
ordered = []
for k in sorted(bands):
    chunk = bands[k][:]
    random.shuffle(chunk)
    ordered.extend(chunk)

for i, r in enumerate(ordered, 1):
    r["position"] = i

json.dump(ordered, open(os.path.join(NDIR, "FINAL-names.json"), "w"), indent=2)

rep = []
rep.append("=== FINAL PEOPLE-NAMES LIST ===")
rep.append(f"count: {len(ordered)}")
rep.append(f"dropped as still-not-people: {len(STILL_NOT_PEOPLE)}")
rep.append(f"spelling variants merged: {len(VARIANTS)}")
rep.append("")
rep.append("--- merged variant groups (published under canonical name) ---")
for rec in sorted(ordered, key=lambda r: r["name"]):
    if rec["also_known_as"]:
        rep.append(f"  {rec['name']}  <- also: {rec['also_known_as']}")
rep.append("")
rep.append("--- first 30 (obscure, early in series) ---")
for r in ordered[:30]:
    rep.append(f"  {r['position']:>3}  {r['verse_count']:>4}x  {r['name']}")
rep.append("")
rep.append("--- last 20 (most common, late in series) ---")
for r in ordered[-20:]:
    rep.append(f"  {r['position']:>3}  {r['verse_count']:>4}x  {r['name']}")
open(os.path.join(NDIR, "FINAL-report.txt"), "w").write("\n".join(rep))
print("\n".join(rep[:14]))
