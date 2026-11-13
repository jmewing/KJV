#!/usr/bin/env python3
"""
Clean the Bible names list: keep only REAL PEOPLE.

Method (context-based, not a growing blocklist):
  A real person name appears in PEOPLE contexts, e.g.
    - "children of X", "sons of X", "begat X", "X begat"
    - "X said / spake / did / went / came / dwelt"
    - genealogical / narrative framing
  A NON-person appears in other contexts:
    - as a verb   ("Howl ye", "Art thou")
    - as a place  ("the mount of Olives", "in Gibeah")
    - as a title  ("the Almighty God")

We score each candidate by the ratio of people-context hits to total hits.
Strong people signalling => keep. Verby/placey/titley => drop.

Outputs:
  wp-import/names/cleaned-names.json   (ordered, people only)
  wp-import/names/clean-report.txt     (kept / dropped with reasons)
"""
import json
import os
import re

REPO = "/srv/kjv"
KJV = os.path.join(REPO, "kjv-texts", "kjv.txt")
NDIR = os.path.join(REPO, "wp-import", "names")

SRC = os.path.join(NDIR, "final-names.json")
out = json.load(open(SRC))
print(f"input names: {len(out)}")

# --- load the KJV and build a verse index --------------------------------
verses = []
for line in open(KJV, encoding="utf-8"):
    m = re.match(r"^(.+?)\s+(\d+):(\d+)\s+(.*)$", line.strip())
    if m:
        verses.append((m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)))
print(f"verses: {len(verses)}")

# --- people-context patterns --------------------------------------------
PEOPLE_PAT = [
    r"\bchildren of {N}\b", r"\bsons? of {N}\b", r"\bdaughters? of {N}\b",
    r"\bbegat {N}\b", r"\b{N} begat\b", r"\b{N} was the son\b",
    r"\b{N} said\b", r"\b{N} spake\b", r"\b{N} answered\b",
    r"\b{N} went\b", r"\b{N} came\b", r"\b{N} took\b", r"\b{N} gave\b",
    r"\b{N} dwelt\b", r"\b{N} died\b", r"\b{N} arose\b", r"\b{N} did\b",
    r"\bunto {N}\b", r"\bwith {N}\b", r"\bof {N}\b",
    r"\b{N} and\b", r"\band {N}\b",
    r"\bthe son of {N}\b", r"\bthe father of {N}\b",
    r"\baccording to the house of {N}\b", r"\bhouse of {N}\b",
]

# --- NON-person signals: these strongly indicate verb / place / title ----
NONPERSON_PAT = [
    r"\bthe mount of {N}\b", r"\bmount {N}\b", r"\bin {N}\b", r"\bto {N}\b",
    r"\bthrough {N}\b", r"\bwilderness of {N}\b", r"\bcity of {N}\b",
    r"\bland of {N}\b", r"\bhill of {N}\b", r"\bvalley of {N}\b",
    r"\briver {N}\b", r"\bsea of {N}\b", r"\bgate of {N}\b",
    r"^{N}\s+(ye|thou|thee|thy|him|her|them|us|me)\b",   # verb: "Howl ye"
    r"\b{N} (thou|ye)\b",
    r"\billustrious\b", r"\bthe {N}\b", r"\bGod {N}\b", r"\bLord {N}\b",
]

# words that are known NOT to be persons even if context looks neutral
HARD_DROP = set("""
Howl Olives Art Gibeah Almighty Selah Amen Hosanna Hallelujah
Zion Sion Goshen Rameses Baal Ashtaroth Asherah Molech Chemosh Dagon
Rimmon Tammuz Bel Merodach Nebo Succothbenoth Milcom
Babylon Egypt Assyria Persia Greece Rome Israel Judah Jerusalem Eden
Sinai Horeb Canaan Philistia Palestina Emmaus Galilee Samaria Bethlehem
""".split())


def score(name):
    """Return (people_hits, nonperson_hits)."""
    ph = np = 0
    esc = re.escape(name)
    for _b, _c, _v, text in verses:
        if name not in text:
            continue
        for p in PEOPLE_PAT:
            if re.search(p.replace("{N}", esc), text):
                ph += 1
                break
        for p in NONPERSON_PAT:
            if re.search(p.replace("{N}", esc), text):
                np += 1
                break
    return ph, np


kept, dropped = [], []
for rec in out:
    nm = rec["name"]
    if nm in HARD_DROP:
        dropped.append((nm, rec["verse_count"], "hard-drop list"))
        continue
    ph, np = score(nm)
    # A person name is used in people contexts far more than place/verb ones.
    if ph == 0 and np > 0:
        dropped.append((nm, rec["verse_count"], f"non-person context (people=0, non={np})"))
    elif np > ph:
        dropped.append((nm, rec["verse_count"], f"mostly non-person (people={ph}, non={np})"))
    else:
        r = dict(rec)
        r["people_hits"] = ph
        r["nonperson_hits"] = np
        kept.append(r)

# renumber
for i, r in enumerate(kept, 1):
    r["position"] = i

json.dump(kept, open(os.path.join(NDIR, "cleaned-names.json"), "w"), indent=2)

rep = []
rep.append("=== NAME CLEANING REPORT ===")
rep.append(f"input:   {len(out)}")
rep.append(f"kept:    {len(kept)}   (real people)")
rep.append(f"dropped: {len(dropped)}")
rep.append("")
rep.append("--- DROPPED (all, with reason) ---")
for nm, vc, why in sorted(dropped, key=lambda x: -x[1]):
    rep.append(f"  {vc:>4}x  {nm:<20} {why}")
rep.append("")
rep.append("--- sample KEPT (first 40) ---")
for r in kept[:40]:
    rep.append(f"  {r['verse_count']:>4}x  {r['name']:<20} people={r['people_hits']} non={r['nonperson_hits']}")
open(os.path.join(NDIR, "clean-report.txt"), "w").write("\n".join(rep))
print("\n".join(rep[:10]))
print(f"\n... full report: {NDIR}/clean-report.txt")
