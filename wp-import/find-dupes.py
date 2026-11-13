#!/usr/bin/env python3
"""
Find near-duplicate / same-sounding NAME groups in the cleaned list.

Two different problems, handled differently:

  (a) TRUE HOMONYMS — one name spelling, but it belongs to MORE THAN ONE
      person in scripture (e.g. Naamah, Pelatiah, Zechariah, Jonathan).
      => KEEP as one entry, but the post should note multiple bearers.

  (b) SPELLING VARIANTS — different spellings that are the SAME person
      (e.g. Ahaziah/Ahaziahu, Elias/Elijah, Uzziah/Azariah in places).
      => MERGE into one entry (canonical spelling wins).

  (c) LOOKALIKES — names that merely resemble each other but are unrelated
      people (Shelumiel vs Sheshan).  => LEAVE ALONE, no action.

Detection strategy:
  * group by a normalised phonetic key (metaphone-ish, simplified for KJV
    transliterations: strip vowels, collapse doubles, map ph->f, c->k, etc.)
  * for each group with >1 spelling, inspect the verses: if the spellings
    co-occur in the same genealogical chain / same verse, they are variants
    of ONE person -> merge.  Otherwise they are distinct names (homonyms or
    lookalikes) -> keep.

Outputs:
  wp-import/names/dup-groups.json   — grouped report for review
  wp-import/names/dup-report.txt
"""
import json
import os
import re
from collections import defaultdict

REPO = "/srv/kjv"
KJV = os.path.join(REPO, "kjv-texts", "kjv.txt")
NDIR = os.path.join(REPO, "wp-import", "names")

names = json.load(open(os.path.join(NDIR, "cleaned-names.json")))
print(f"names in: {len(names)}")

# --- verse index ---------------------------------------------------------
verses = []
for line in open(KJV, encoding="utf-8"):
    m = re.match(r"^(.+?)\s+(\d+):(\d+)\s+(.*)$", line.strip())
    if m:
        verses.append((m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)))


def phone_key(n: str) -> str:
    """Crude phonetic key tuned for KJV transliterations."""
    s = n.lower()
    s = s.replace("ph", "f").replace("ch", "k").replace("sh", "s")
    s = re.sub(r"[^a-z]", "", s)
    s = re.sub(r"c(?=[eiy])", "s", s)   # soft c
    s = s.replace("c", "k")
    s = s.replace("z", "s").replace("x", "ks")
    s = re.sub(r"[aeiouy]", "", s)      # drop vowels
    s = re.sub(r"(.)\1+", r"\1", s)     # collapse doubles
    return s


groups = defaultdict(list)
for r in names:
    groups[phone_key(r["name"])].append(r)

multi = {k: v for k, v in groups.items() if len(v) > 1}
print(f"phonetic groups with >1 spelling: {len(multi)}")

# --- inspect each group to classify -------------------------------------
report = []
merge_suggestions = []
homonym_groups = []
lookalikes = []

for key, members in sorted(multi.items(), key=lambda x: -max(m["verse_count"] for m in x[1])):
    spellings = [m["name"] for m in members]
    # do any two spellings appear in the SAME verse? -> same person/context
    same_verse = False
    for _b, _c, _v, text in verses:
        present = [s for s in spellings if re.search(r"\b" + re.escape(s) + r"\b", text)]
        if len(present) > 1:
            same_verse = True
            break

    entry = {
        "key": key,
        "spellings": spellings,
        "counts": {m["name"]: m["verse_count"] for m in members},
        "same_verse": same_verse,
    }
    if same_verse:
        merge_suggestions.append(entry)
    else:
        # are the spellings used in similar narrative roles? check first-occurrence
        # book/chapter context similarity as a weak signal
        firsts = {}
        for s in spellings:
            for b, c, v, text in verses:
                if re.search(r"\b" + re.escape(s) + r"\b", text):
                    firsts[s] = (b, c)
                    break
        entry["first_seen"] = firsts
        # same book+chapter => very likely same person, different spelling
        if len(set(firsts.values())) == 1 and len(firsts) == len(spellings):
            merge_suggestions.append(entry)
        else:
            homonym_groups.append(entry)

report.append("=== NEAR-DUPLICATE / SAME-SOUNDING NAME REPORT ===")
report.append(f"names: {len(names)}")
report.append(f"phonetic groups with >1 spelling: {len(multi)}")
report.append(f"  -> same-verse merges suggested: {len(merge_suggestions)}")
report.append(f"  -> homonym/lookalike groups (keep separate): {len(homonym_groups)}")
report.append("")
report.append("--- SAME-PERSON SPELLING VARIANTS (merge these) ---")
for e in merge_suggestions:
    report.append(f"  {e['spellings']}  counts={e['counts']}  same_verse={e['same_verse']}")
report.append("")
report.append("--- HOMONYM / LOOKALIKE GROUPS (distinct people, keep) ---")
for e in homonym_groups:
    report.append(f"  {e['spellings']}  counts={e['counts']}")
    if e.get("first_seen"):
        report.append(f"      first seen: {e['first_seen']}")

json.dump({"merge": merge_suggestions, "homonyms": homonym_groups},
          open(os.path.join(NDIR, "dup-groups.json"), "w"), indent=2)
open(os.path.join(NDIR, "dup-report.txt"), "w").write("\n".join(report))
print("\n".join(report[:12]))
print(f"\nfull report: {NDIR}/dup-report.txt")
