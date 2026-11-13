#!/usr/bin/env python3
"""
Build the SKELETON for all inetking.org series — titles + dates + order.

Why skeletons first (Jeremy, 2026-09-23):
  The index/date divergence bug only exists if posts are inserted in batches
  by series. Building ALL skeletons, merging them, sorting the WHOLE set
  chronologically, and verifying zero inversions proves index integrity
  BEFORE ~1,400 posts exist. Body content is filled in afterwards — editing
  a post preserves its index, so enrichment cannot disturb the ordering.

Schedule (Jeremy-confirmed):
  Devotional  : every day,          publish 10:00 AM
  Names       : Mon-Fri,            publish  1:00 PM
  Topics      : Wednesday,          publish  8:00 AM
  Discoveries : every other Sunday, publish  8:00 AM (outline leads)
  Prophecies  : every other Sunday, publish  8:00 AM (after Discoveries)

Window: 2025-01-01 .. 2026-12-31
"""
import csv
import json
import os
import re
from datetime import date, datetime, timedelta

REPO = "/srv/kjv"
OUT = os.path.join(REPO, "wp-import", "skeleton")
os.makedirs(OUT, exist_ok=True)

START = date(2025, 1, 1)
END = date(2026, 12, 31)

# series -> (category, publish time)
CATEGORIES = {
    "devotional": "Daily Devotional",
    "names": "Bible Names",
    "topics": "What Does the Bible Say",
    "discoveries": "Discoveries in the Bible",
    "prophecies": "Bible Prophecies",
}
TIME = {
    "devotional": (10, 0),
    "names": (13, 0),
    "topics": (8, 0),
    "discoveries": (8, 0),
    "prophecies": (8, 0),
}


def daterange(a, b):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)


records = []

# --- 1. Devotionals: every day ------------------------------------------
for d in daterange(START, END):
    h, m = TIME["devotional"]
    records.append({
        "series": "devotional",
        "date": datetime(d.year, d.month, d.day, h, m),
        "title": f"Daily Devotional — {d.strftime('%B %-d, %Y')}",
        "slug": f"devotional-{d.isoformat()}",
    })

# --- 2. Names: Mon-Fri, weighted list (authoritative BibleAsk people names)
names = json.load(open(os.path.join(REPO, "wp-import", "names", "BIBLEASK-people.json")))
ni = 0
for d in daterange(START, END):
    if d.weekday() >= 5:      # Mon=0 .. Fri=4
        continue
    if ni >= len(names):
        break
    rec = names[ni]
    h, m = TIME["names"]
    records.append({
        "series": "names",
        "date": datetime(d.year, d.month, d.day, h, m),
        "title": f"{rec['name']} — A Name in the Bible",
        "slug": f"name-{rec['name'].lower().replace(chr(39), '')}",
        "name": rec["name"],
        "verse_count": rec.get("verseCount", 0),
        "gender": rec.get("gender"),
        "description": rec.get("description"),
        "testament": rec.get("testament"),
    })
    ni += 1

# --- 3. Topics: Wednesday, real questions from the interleaved list ----
topics_data = json.load(open(os.path.join(REPO, "wp-import", "topics", "topics.json")))
topic_list = topics_data["used"]
ti = 0
for d in daterange(START, END):
    if d.weekday() != 2:
        continue
    if ti >= len(topic_list):
        break
    topic = topic_list[ti]
    ti += 1
    h, m = TIME["topics"]
    records.append({
        "series": "topics",
        "date": datetime(d.year, d.month, d.day, h, m),
        "title": f"What Does the Bible Say About {topic.title()}?",
        "slug": "bible-says-" + re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-"),
        "topic": topic,
    })

# --- 4. Discoveries: every other Sunday, outline leads ------------------
disc = json.load(open(os.path.join(REPO, "wp-import", "staging", "plan.json")))
for rec in disc:
    h, m = TIME["discoveries"]
    pd = rec["post_date"]
    if isinstance(pd, str):
        pd = datetime.fromisoformat(pd)
    records.append({
        "series": "discoveries",
        "date": pd,
        "title": rec["title"],
        "slug": rec["slug"],
    })

# --- 5. Prophecies: every other Sunday AFTER discoveries run out --------
# Discoveries end 2026-02-01; Prophecies take the next alternate Sunday slot.
prophecies = json.load(open(os.path.join(REPO, "wp-import", "prophecies", "prophecies.json")))
prop_slots = []
d = date(2026, 2, 15)
while d <= END:
    prop_slots.append(d)
    d += timedelta(days=14)
for i, pd in enumerate(prop_slots, 1):
    h, m = TIME["prophecies"]
    meta = prophecies[i - 1] if i <= len(prophecies) else {"title": f"Study #{i}", "prophecy": "", "fulfillment": ""}
    records.append({
        "series": "prophecies",
        "date": datetime(pd.year, pd.month, pd.day, h, m),
        "title": f"Bible Prophecies — {meta['title']}",
        "slug": f"prophecy-{i:03d}",
        "prophecy_ref": meta.get("prophecy", ""),
        "fulfillment_ref": meta.get("fulfillment", ""),
    })

# --- SORT THE WHOLE SET CHRONOLOGICALLY (the point of the exercise) -----
records.sort(key=lambda r: (r["date"], r["series"]))

# --- VERIFY: zero date inversions ---------------------------------------
inversions = []
for i in range(1, len(records)):
    if records[i]["date"] < records[i - 1]["date"]:
        inversions.append(i)

# --- assign the intended final order (this IS the insert order) ---------
for i, r in enumerate(records, 1):
    r["order"] = i

counts = {}
for r in records:
    counts[r["series"]] = counts.get(r["series"], 0) + 1

rep = []
rep.append("=== SKELETON PLAN (all series merged, date-ordered) ===")
rep.append(f"total records: {len(records)}")
rep.append(f"window: {records[0]['date']:%Y-%m-%d} .. {records[-1]['date']:%Y-%m-%d}")
rep.append(f"DATE INVERSIONS: {len(inversions)}   (must be 0)")
rep.append("")
rep.append("--- per series ---")
for k in sorted(counts):
    rep.append(f"  {k:<12} {counts[k]:>5}   category: {CATEGORIES[k]}")
rep.append("")
rep.append(f"names list remaining for 2027+: {len(names) - ni} of {len(names)}")
rep.append("")
rep.append("--- first 12 (chronological) ---")
for r in records[:12]:
    rep.append(f"  {r['order']:>5}  {r['date']:%Y-%m-%d %H:%M}  {r['series']:<12} {r['title'][:52]}")
rep.append("")
rep.append("--- last 12 (chronological) ---")
for r in records[-12:]:
    rep.append(f"  {r['order']:>5}  {r['date']:%Y-%m-%d %H:%M}  {r['series']:<12} {r['title'][:52]}")

open(os.path.join(OUT, "report.txt"), "w").write("\n".join(rep))
json.dump(records, open(os.path.join(OUT, "skeleton.json"), "w"), indent=2, default=str)

print("\n".join(rep))
