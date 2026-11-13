#!/usr/bin/env python3
"""
Split the insert-ready set into PAST (publish now) and FUTURE (schedule),
based on a cutoff date, and write two manifests.

WP-CLI accepts a past date with post_status=publish and keeps it, and a
future date with post_status=future and schedules it. So we insert the WHOLE
set in ONE chronological pass, choosing the status per record by its date.
That keeps ID order == date order (the thing that mattered).

Outputs:
  wp-import/insert/INDEX.json          full ordered manifest with a status field
  wp-import/insert/SPLIT-REPORT.txt
"""
import json
import os
from datetime import datetime

INS = "/srv/kjv/wp-import/insert"
CUTOFF = datetime(2026, 9, 23, 21, 45, 0)   # now-ish; anything at/before = publish

index = json.load(open(os.path.join(INS, "INDEX.json")))
past = future = 0
for r in index:
    dt = datetime.fromisoformat(r["date"])
    if dt <= CUTOFF:
        r["status"] = "publish"
        past += 1
    else:
        r["status"] = "future"
        future += 1

json.dump(index, open(os.path.join(INS, "INDEX.json"), "w"), indent=2)

# verify the manifest itself is in date order
inv = sum(1 for i in range(1, len(index))
          if datetime.fromisoformat(index[i]["date"]) < datetime.fromisoformat(index[i-1]["date"]))

rep = []
rep.append("=== SPLIT REPORT ===")
rep.append(f"cutoff: {CUTOFF}")
rep.append(f"records: {len(index)}")
rep.append(f"  publish (at/before cutoff): {past}")
rep.append(f"  future  (after cutoff):     {future}")
rep.append(f"date inversions in manifest: {inv}")
rep.append("")
rep.append("--- last 3 to publish ---")
for r in [x for x in index if x["status"] == "publish"][-3:]:
    rep.append(f"  {r['order']:>5}  {r['date']}  {r['series']:<12} {r['title'][:50]}")
rep.append("")
rep.append("--- first 3 to schedule ---")
for r in [x for x in index if x["status"] == "future"][:3]:
    rep.append(f"  {r['order']:>5}  {r['date']}  {r['series']:<12} {r['title'][:50]}")
open(os.path.join(INS, "SPLIT-REPORT.txt"), "w").write("\n".join(rep))
print("\n".join(rep))
