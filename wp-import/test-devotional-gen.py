#!/usr/bin/env python3
"""Test LLM devotional generation: quality + timing on a small sample."""
import json
import os
import re
import subprocess
import sys
import time

REPO = "/srv/kjv"
KJV = os.path.join(REPO, "kjv-texts", "kjv.txt")
SCHED = "/home/jmewing/.openclaw/workspace/kjv-reading-schedule.md"
MODEL = sys.argv[1] if len(sys.argv) > 1 else "deepseek-v4.1-flash:cloud"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 2

BOOKS = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Joshua","Judges","Ruth",
"1 Samuel","2 Samuel","1 Kings","2 Kings","1 Chronicles","2 Chronicles","Ezra","Nehemiah",
"Esther","Job","Psalms","Proverbs","Ecclesiastes","Song of Solomon","Isaiah","Jeremiah",
"Lamentations","Ezekiel","Daniel","Hosea","Joel","Amos","Obadiah","Jonah","Micah","Nahum",
"Habakkuk","Zephaniah","Haggai","Zechariah","Malachi","Matthew","Mark","Luke","John","Acts",
"Romans","1 Corinthians","2 Corinthians","Galatians","Ephesians","Philippians","Colossians",
"1 Thessalonians","2 Thessalonians","1 Timothy","2 Timothy","Titus","Philemon","Hebrews",
"James","1 Peter","2 Peter","1 John","2 John","3 John","Jude","Revelation"]

from collections import defaultdict
BY_BOOK = defaultdict(list)
for line in open(KJV, encoding="utf-8"):
    m = re.match(r"^(.+?)\s+(\d+):(\d+)\s+(.*)$", line.strip())
    if m:
        BY_BOOK[m.group(1).strip()].append((int(m.group(2)), int(m.group(3)), m.group(4)))

MON = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
schedule = {}
for line in open(SCHED, encoding="utf-8"):
    m = re.match(r"^\|\s*\w{3}\s+(\w{3})\s+(\d{2})\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", line)
    if m and MON.get(m.group(1)):
        schedule[(MON[m.group(1)], int(m.group(2)))] = (m.group(3), m.group(4))


def parse_reading(s):
    if not s or s.strip() in ("—", "-", ""):
        return None
    m = re.match(r"^(.+?)\s+(\d+)(?:\s*[-–]\s*(\d+))?$", s.strip())
    if not m:
        return None
    return (m.group(1).strip(), int(m.group(2)), int(m.group(3)) if m.group(3) else int(m.group(2)))


def passage_text(book, c1, c2):
    out = []
    for (c, v, t) in BY_BOOK.get(book, []):
        if c1 <= c <= c2:
            out.append(f"{c}:{v} {t}")
    return "\n".join(out)


PROMPT = """You are writing a daily devotional for a King James Version Bible reading plan.

TODAY'S PASSAGE: {reading}
DATE: {date}

PASSAGE TEXT (KJV):
{text}

Write a devotional in EXACTLY this structure. Be specific to THIS passage — name the
actual people, places, and events in it. Never write generic filler that could apply to
any passage.

## Devotional Thought
<3-5 paragraphs of flowing prose (~350-450 words) that reflect on what this passage
teaches. Connect it to ordinary life and the season of the year. Write in a warm,
literate, pastoral voice. Do not use bullet points.>

## Reflection
1. <a specific, searching question tied to this passage>
2. <a second such question>

## Prayer
<one paragraph, ~80-120 words, addressed to God, flowing from the passage.>

Return ONLY the devotional text with those three headings."""


def gen(day, month):
    primary, psalm = schedule.get((month, day), ("", "—"))
    pr = parse_reading(primary)
    text = passage_text(*pr)[:9000] if pr else ""
    prompt = PROMPT.format(reading=primary, date=f"{month}/{day}", text=text)
    t0 = time.time()
    r = subprocess.run(
        ["curl", "-s", "--max-time", "600", "http://127.0.0.1:11434/api/generate",
         "-d", json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                           "think": False,
                           "options": {"temperature": 0.7, "num_predict": 1600}})],
        capture_output=True, text=True)
    dt = time.time() - t0
    try:
        resp = json.loads(r.stdout)
        out = resp.get("response", "")
    except Exception as e:
        out = f"ERR {e}: {r.stdout[:300]}"
    return primary, psalm, out, dt


for i, (d, mo) in enumerate([(1, 1), (2, 3), (3, 6)][:N]):
    primary, psalm, out, dt = gen(d, mo)
    print(f"\n{'='*70}\n{d}/{mo}  {primary}  (psalm {psalm})   [{dt:.1f}s]\n{'='*70}")
    print(out[:1800])
