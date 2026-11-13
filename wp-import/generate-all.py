#!/usr/bin/env python3
"""
Generate REAL written content for every skeleton record, grounded in the KJV
text and the source data. Replaces the placeholder prose.

Series:
  devotional   -> LLM reflection from the day's scheduled passage
  names        -> LLM entry about the person + code-added verse list
  topics       -> LLM study from verses gathered ACROSS books + verse list
  prophecies   -> LLM study from a real prophecy/fulfilment reference pair
  discoveries  -> the existing written markdown posts (no LLM)

Design:
  * resume-safe: a record already generated (file + "generated": true) is skipped
  * per-record log + sentinel, safe to run detached for hours
  * parallel workers (default 4) against local ollama
  * NOTHING is written to WordPress here

Usage:  python3 generate-all.py [--workers N] [--limit N] [--only series]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

REPO = "/srv/kjv"
KJV = os.path.join(REPO, "kjv-texts", "kjv.txt")
SCHED = "/home/jmewing/.openclaw/workspace/kvj-reading-schedule.md"
SCHED = "/home/jmewing/.openclaw/workspace/kjv-reading-schedule.md"
SKEL = os.path.join(REPO, "wp-import", "skeleton", "skeleton.json")
OUT = os.path.join(REPO, "wp-import", "content")
LOG = os.path.join(REPO, "wp-import", "generate.log")
MODEL = "deepseek-v4.1-flash:cloud"
OLLAMA = "http://127.0.0.1:11434/api/generate"

os.makedirs(OUT, exist_ok=True)
_lock = threading.Lock()

BOOKS = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Joshua","Judges","Ruth",
"1 Samuel","2 Samuel","1 Kings","2 Kings","1 Chronicles","2 Chronicles","Ezra","Nehemiah",
"Esther","Job","Psalms","Proverbs","Ecclesiastes","Song of Solomon","Isaiah","Jeremiah",
"Lamentations","Ezekiel","Daniel","Hosea","Joel","Amos","Obadiah","Jonah","Micah","Nahum",
"Habakkuk","Zephaniah","Haggai","Zechariah","Malachi","Matthew","Mark","Luke","John","Acts",
"Romans","1 Corinthians","2 Corinthians","Galatians","Ephesians","Philippians","Colossians",
"1 Thessalonians","2 Thessalonians","1 Timothy","2 Timothy","Titus","Philemon","Hebrews",
"James","1 Peter","2 Peter","1 John","2 John","3 John","Jude","Revelation"]
BIDX = {b: i for i, b in enumerate(BOOKS)}
# longest-first so "1 Samuel" matches before "Samuel"
BOOK_RE = "|".join(sorted([re.escape(b) for b in BOOKS], key=len, reverse=True))

from collections import defaultdict
BY_BOOK = defaultdict(list)
ALLV = []
for line in open(KJV, encoding="utf-8"):
    m = re.match(r"^(.+?)\s+(\d+):(\d+)\s+(.*)$", line.strip())
    if m:
        b, c, v, t = m.group(1).strip(), int(m.group(2)), int(m.group(3)), m.group(4)
        BY_BOOK[b].append((c, v, t))
        ALLV.append((b, c, v, t))
print(f"verses loaded: {len(ALLV)}")

MON = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
schedule = {}
for line in open(SCHED, encoding="utf-8"):
    m = re.match(r"^\|\s*\w{3}\s+(\w{3})\s+(\d{2})\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", line)
    if m and MON.get(m.group(1)):
        schedule[(MON[m.group(1)], int(m.group(2)))] = (m.group(3), m.group(4))


def log(msg):
    with _lock:
        with open(LOG, "a") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')} {msg}\n")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def ref_str(b, c, v):
    return f"{b} {c}:{v}"


def parse_reading(s):
    """'Acts 1-2' -> ('Acts',1,2) ; no psalm/None -> None"""
    if not s or s.strip() in ("—", "-", ""):
        return None
    m = re.match(r"^(.+?)\s+(\d+)(?:\s*[-–]\s*(\d+))?$", s.strip())
    if not m:
        return None
    return (m.group(1).strip(), int(m.group(2)), int(m.group(3)) if m.group(3) else int(m.group(2)))


def passage_text(book, c1, c2, cap=14000):
    out = []
    for (c, v, t) in BY_BOOK.get(book, []):
        if c1 <= c <= c2:
            out.append(f"{c}:{v} {t}")
    s = "\n".join(out)
    return s[:cap]


def parse_refs(s):
    """Extract (book, chapter, v1, v2) tuples from 'Isaiah 53:4-6; Psalm 22:16-18, 37'."""
    out = []
    for part in re.split(r"[;,]", s):
        part = part.strip()
        if not part:
            continue
        m = re.match(rf"^({BOOK_RE})\s+(\d+):(\d+)(?:\s*[-–]\s*(\d+))?$", part)
        if m:
            out.append((m.group(1), int(m.group(2)), int(m.group(3)),
                        int(m.group(4)) if m.group(4) else int(m.group(3))))
    return out


def verses_for_refs(refs, cap=6000):
    chunks = []
    for (b, c, v1, v2) in refs:
        for (cc, vv, t) in BY_BOOK.get(b, []):
            if cc == c and v1 <= vv <= v2:
                chunks.append(f"{b} {cc}:{vv} {t}")
    s = "\n".join(chunks)
    return s[:cap]


def ollama(prompt, num_predict=1600, temp=0.7, tries=3):
    for attempt in range(tries):
        try:
            r = subprocess.run(
                ["curl", "-s", "--max-time", "600", OLLAMA, "-d", json.dumps({
                    "model": MODEL, "prompt": prompt, "stream": False, "think": False,
                    "options": {"temperature": temp, "num_predict": num_predict}})],
                capture_output=True, text=True, timeout=660)
            resp = json.loads(r.stdout).get("response", "").strip()
            if resp:
                return resp
            log(f"  empty response (attempt {attempt+1})")
        except Exception as e:
            log(f"  ollama error (attempt {attempt+1}): {e}")
        time.sleep(3)
    return ""


# ---------------- per-series prompt builders -----------------------------
def p_names(rec):
    name = rec["name"]
    pat = re.compile(r"\b" + re.escape(name) + r"\b")
    hits = sorted((BIDX.get(b, 999), c, v, b, t) for (b, c, v, t) in ALLV if pat.search(t))
    total = len(hits)
    show = hits[:12]
    vt = "\n".join(f"{b} {c}:{v} {t}" for (_i, c, v, b, t) in show)
    prompt = f"""You are writing a reference entry about a person named in the King James Bible.

NAME: {name}
SOURCE NOTE (who this was): {rec.get('description','')}
GENDER: {rec.get('gender','')}
TESTAMENT: {rec.get('testament','')}
TIMES THE NAME APPEARS IN THE KJV: {total}

SCRIPTURE REFERENCES (KJV, actual text):
{vt}

Write the entry with EXACTLY these headings:

## Who This Was
Two or three paragraphs (~250-350 words). Say who this person was, the setting in
which they appear, what they did, and what Scripture says of them. Stay strictly
within what the Bible text and the source note above state. Do not invent details.

## The Name
One paragraph. Hebrew/Greek names often carry meaning. If the meaning of THIS name
is well established, explain it. If it is not clearly recoverable, say so plainly.
Never invent a meaning for the sake of having one.

## A Closing Thought
One paragraph (~70-110 words) drawing a brief, honest lesson or observation from
this person's life. Warm and pastoral in tone.

Return ONLY the entry text, starting with the first heading."""
    body = ollama(prompt, num_predict=1400)
    parts = [f"<p><strong>{esc(name)}</strong> is a name found in the King James Bible"
             + (f", appearing {total} time{'s' if total != 1 else ''} in the text." if total else ".")
             + "</p>"]
    parts.append(md_sections_to_html(body))
    facts = []
    if rec.get("gender"):
        facts.append(f"<strong>Gender:</strong> {esc(rec['gender'].title())}")
    if rec.get("testament"):
        t = rec["testament"]
        facts.append("<strong>Testament:</strong> " + esc("Old and New Testaments" if t == "both" else t.title()))
    facts.append(f"<strong>Mentions in the KJV:</strong> {total}")
    parts.append("<h2>At a Glance</h2>")
    parts.append("<ul>" + "".join(f"<li>{f}</li>" for f in facts) + "</ul>")
    if show:
        parts.append("<h2>Where It Appears in Scripture</h2>")
        items = []
        for (_i, c, v, b, t) in show:
            snip = esc(t)
            if len(snip) > 260:
                snip = snip[:257] + "..."
            items.append(f"<li><strong>{esc(ref_str(b, c, v))}</strong> &mdash; {snip}</li>")
        parts.append("<ul>" + "".join(items) + "</ul>")
    return "\n".join(parts)


def p_topics(rec):
    topic = rec.get("topic") or rec["title"]
    t = topic.lower()
    if t.startswith("the "):
        t = t[4:]
    term = t.split(" and ")[0].split(",")[0].split("?")[0].strip()
    pat = re.compile(r"\b" + re.escape(term) + r"\b", re.I) if term else None
    picks = []
    if pat:
        for b in BOOKS:
            for (c, v, txt) in BY_BOOK.get(b, []):
                if pat.search(txt):
                    picks.append((b, c, v, txt))
                    break
            if len(picks) >= 14:
                break
    vt = "\n".join(f"{b} {c}:{v} {txt}" for (b, c, v, txt) in picks)
    prompt = f"""You are writing a Bible study on one subject.

SUBJECT: {topic}

VERSES GATHERED FROM ACROSS SCRIPTURE (KJV, actual text):
{vt}

Write the study with EXACTLY these headings:

## What Scripture Says
Three or four paragraphs (~350-450 words) drawing on the verses above. Show the
breadth of the Bible's teaching on this subject, moving through different parts of
Scripture. Ground every claim in the verses given. Do not invent quotations.

## Living It Out
One or two paragraphs of plain, practical application for an ordinary reader.

## Reflection
1. <a searching question tied to this subject>
2. <a second such question>

Return ONLY the study text, starting with the first heading."""
    body = ollama(prompt, num_predict=1500)
    parts = [f"<p>The Bible has a great deal to say about <strong>{esc(topic)}</strong>. "
             f"This study gathers passages from across Scripture and sets them out for "
             f"reading and reflection.</p>"]
    parts.append(md_sections_to_html(body))
    if picks:
        parts.append("<h2>Verses to Consider</h2>")
        items = []
        for (b, c, v, txt) in picks:
            snip = esc(txt)
            if len(snip) > 300:
                snip = snip[:297] + "..."
            items.append(f"<li><strong>{esc(ref_str(b, c, v))}</strong> &mdash; {snip}</li>")
        parts.append("<ul>" + "".join(items) + "</ul>")
        parts.append("<h2>Where These Come From</h2>")
        parts.append("<p>These verses are drawn from different parts of the Bible on "
                     "purpose. A subject is rarely settled by a single line; the whole "
                     "counsel of Scripture gives the shape of it.</p>")
    return "\n".join(parts)


def p_devotional(rec):
    d = rec["date"]
    if isinstance(d, str):
        d = datetime.fromisoformat(d)
    primary, psalm = schedule.get((d.month, d.day), ("", "—"))
    pr = parse_reading(primary)
    text = passage_text(*pr) if pr else ""
    pp = parse_reading(psalm)
    pv = ""
    if pp:
        pvv = []
        for (c, v, t) in BY_BOOK.get(pp[0], []):
            if c == pp[1]:
                pvv.append(f"{c}:{v} {t}")
        pv = "\n".join(pvv)[:2500]
    angle = ("Open on the narrative — what is actually happening in this passage, and "
             "who the people are.") if d.year % 2 else (
             "Open on the application — what this passage asks of a reader today.")
    prompt = f"""You are writing a daily devotional for a King James Version Bible reading plan.

DATE: {d.strftime('%A, %B %-d, %Y')}
TODAY'S PASSAGE: {primary}
PSALM PORTION: {psalm}

PASSAGE TEXT (KJV):
{text}

{f'PSALM TEXT (KJV):{chr(10)}{pv}' if pv else ''}

Write the devotional with EXACTLY these headings:

## Devotional Thought
Three to five paragraphs (~380-480 words) of flowing prose reflecting on THIS passage.
Be concrete: name the actual people, places and events in the text. Connect it to
ordinary life and to the season of the year. Warm, literate, pastoral voice. No bullets.
{angle}

## Reflection
1. <a specific, searching question tied to this passage>
2. <a second such question>

## Prayer
One paragraph (~90-130 words) addressed to God, flowing directly from this passage.

Return ONLY the devotional text, starting with the first heading."""
    body = ollama(prompt, num_predict=2000)
    # code adds accurate readings + key verse
    parts = [f"<p><em>{esc(d.strftime('%A, %B %-d, %Y'))}</em></p>"]
    parts.append("<h2>Scripture Readings</h2>")
    rows = []
    if primary and primary != "—":
        rows.append(f"<li><strong>Primary Reading:</strong> {esc(primary)}</li>")
    if psalm and psalm != "—":
        rows.append(f"<li><strong>Secondary Reading:</strong> {esc(psalm)}</li>")
    parts.append("<ul>" + "".join(rows) + "</ul>")
    if pr:
        rv = [x for x in BY_BOOK.get(pr[0], []) if pr[1] <= x[0] <= pr[2]]
        if rv:
            c, v, txt = rv[min(len(rv) // 2, len(rv) - 1)]
            parts.append("<h2>Key Verse</h2>")
            parts.append(f"<p><strong>{esc(ref_str(pr[0], c, v))}</strong> &mdash; "
                         f"&ldquo;{esc(txt)}&rdquo;</p>")
    parts.append(md_sections_to_html(body))
    if pp:
        pvv = [(c, v, t) for (c, v, t) in BY_BOOK.get(pp[0], []) if c == pp[1]]
        if pvv:
            c, v, txt = pvv[0]
            parts.append(f"<h2>Psalm Verse</h2><p><strong>{esc(ref_str(pp[0], c, v))}</strong> "
                         f"&mdash; &ldquo;{esc(txt)}&rdquo;</p>")
    return "\n".join(parts)


def p_prophecies(rec):
    pr = parse_refs(rec.get("prophecy_ref", ""))
    fr = parse_refs(rec.get("fulfillment_ref", ""))
    pt = verses_for_refs(pr)
    ft = verses_for_refs(fr)
    prompt = f"""You are writing a Bible study on a prophecy and its fulfilment.

STUDY TITLE: {rec['title'].replace('Bible Prophecies — ','')}
THE PROPHECY: {rec.get('prophecy_ref','')}
THE FULFILMENT: {rec.get('fulfillment_ref','')}

PROPHECY TEXT (KJV):
{pt}

FULFILMENT TEXT (KJV):
{ft}

Write the study with EXACTLY these headings:

## The Prophecy
Two paragraphs (~200-260 words). Set out what was foretold, who spoke it, and the
circumstances in which it was given. Quote the actual text above.

## The Fulfilment
Two paragraphs (~200-260 words). Show how the record above reports the prophecy coming
to pass. Be precise about what the text does and does not claim.

## Why It Matters
One or two paragraphs (~120-180 words) on what fulfilled prophecy demonstrates about
the reliability of Scripture.

Return ONLY the study text, starting with the first heading."""
    body = ollama(prompt, num_predict=1600)
    parts = [f"<p>This study considers a prophecy given in Scripture and the record of "
             f"its fulfilment. The prophets spoke long before the events they described, "
             f"and the account of fulfilment is part of why the text commands attention.</p>"]
    parts.append(md_sections_to_html(body))
    if pr or fr:
        rows = []
        if rec.get("prophecy_ref"):
            rows.append(f"<li><strong>The prophecy:</strong> {esc(rec['prophecy_ref'])}</li>")
        if rec.get("fulfillment_ref"):
            rows.append(f"<li><strong>The fulfilment:</strong> {esc(rec['fulfillment_ref'])}</li>")
        parts.append("<h2>Passages</h2><ul>" + "".join(rows) + "</ul>")
    return "\n".join(parts)


# ---------------- markdown -> html --------------------------------------
def md_sections_to_html(md):
    # Normalise heading depth: the shallowest heading in the document becomes
    # h2 (the post title is h1), deeper ones follow in order.
    depths = [len(m.group(1)) for m in re.finditer(r"^(#{1,6})\s+", md, re.M)]
    base = min(depths) if depths else 2
    out, in_ul, in_ol = [], False, False
    for ln in md.split("\n"):
        s = ln.rstrip()
        if not s.strip():
            if in_ul: out.append("</ul>"); in_ul = False
            if in_ol: out.append("</ol>"); in_ol = False
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            if in_ul: out.append("</ul>"); in_ul = False
            if in_ol: out.append("</ol>"); in_ol = False
            lvl = min(len(m.group(1)) - base + 2, 6)
            out.append(f"<h{lvl}>{esc(m.group(2))}</h{lvl}>")
            continue
        if re.match(r"^\s*\d+[.)]\s+", s):
            if in_ul: out.append("</ul>"); in_ul = False
            if not in_ol: out.append("<ol>"); in_ol = True
            out.append("<li>" + esc(re.sub(r"^\s*\d+[.)]\s+", "", s)) + "</li>")
            continue
        if re.match(r"^\s*[-*]\s+", s):
            if in_ol: out.append("</ol>"); in_ol = False
            if not in_ul: out.append("<ul>"); in_ul = True
            out.append("<li>" + esc(re.sub(r"^\s*[-*]\s+", "", s)) + "</li>")
            continue
        if in_ul: out.append("</ul>"); in_ul = False
        if in_ol: out.append("</ol>"); in_ol = False
        out.append("<p>" + esc(s) + "</p>")
    if in_ul: out.append("</ul>")
    if in_ol: out.append("</ol>")
    return "\n".join(out)


def markdown_to_html(md):
    return md_sections_to_html(md)


CATS = {"devotional": "Daily Devotional", "names": "Bible Names",
        "topics": "What Does the Bible Say", "discoveries": "Discoveries in the Bible",
        "prophecies": "Bible Prophecies"}
BUILDERS = {"names": p_names, "topics": p_topics, "devotional": p_devotional,
            "prophecies": p_prophecies}


def target_path(rec):
    return os.path.join(OUT, f"{rec['order']:05d}-{rec['slug']}.json")


def process(rec):
    path = target_path(rec)
    if os.path.exists(path):
        try:
            if json.load(open(path)).get("generated"):
                return ("skip", rec["order"])
        except Exception:
            pass
    series = rec["series"]
    if series == "discoveries":
        src = os.path.join(REPO, "kjv-archaeological", rec["slug"] + ".md")
        html = markdown_to_html(open(src, encoding="utf-8").read()) if os.path.exists(src) else "<p>(pending)</p>"
    else:
        html = BUILDERS[series](rec)
    if not html or len(html) < 200:
        log(f"  WEAK/EMPTY {series} {rec['slug']} ({len(html)} bytes)")
        return ("weak", rec["order"])
    json.dump({"order": rec["order"], "series": series, "title": rec["title"],
               "slug": rec["slug"], "date": rec["date"], "category": CATS[series],
               "html": html, "generated": True},
              open(path, "w"), indent=2)
    return ("ok", rec["order"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    skel = json.load(open(SKEL))
    if args.only:
        skel = [r for r in skel if r["series"] == args.only]
    if args.limit:
        skel = skel[:args.limit]
    log(f"=== START workers={args.workers} records={len(skel)} only={args.only or 'all'} ===")

    ok = sk = weak = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(process, r): r for r in skel}
        done = 0
        for f in as_completed(futs):
            r = futs[f]
            try:
                status, order = f.result()
            except Exception as e:
                log(f"  ERROR {r['slug']}: {e}")
                status = "err"
            done += 1
            if status == "ok": ok += 1
            elif status == "skip": sk += 1
            elif status == "weak": weak += 1
            if done % 10 == 0 or done == len(skel):
                el = time.time() - t0
                log(f"  progress {done}/{len(skel)}  ok={ok} skip={sk} weak={weak}  {el:.0f}s")
    log(f"=== DONE ok={ok} skip={sk} weak={weak} total={len(skel)} in {time.time()-t0:.0f}s ===")


if __name__ == "__main__":
    main()
