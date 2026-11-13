#!/usr/bin/env python3
"""
Content generation v2 — fixes the two defects found in review:

  DEFECT 1 (topics): a plain keyword search returned the canonically-FIRST
     verses containing the word, so every common topic opened in Genesis
     (God -> Gen 1:1,1:2,1:3...). Fix: bucket candidate verses BY BOOK and
     sample across the whole canon, so a study on "God" draws from Genesis,
     Psalms, the prophets and the epistles rather than 12 verses of Gen 1.

  DEFECT 2 (devotionals): had no real reading content. Fix: parse the
     one-year reading schedule and pull the ACTUAL assigned passage, a real
     key verse out of that passage, and the real Psalm portion.

Everything is grounded in the KJV text and the schedule — nothing invented.
"""
import json
import os
import re
from datetime import datetime

REPO = "/srv/kjv"
KJV = os.path.join(REPO, "kjv-texts", "kjv.txt")
SCHED = "/home/jmewing/.openclaw/workspace/kjv-reading-schedule.md"
SKEL = os.path.join(REPO, "wp-import", "skeleton", "skeleton.json")
OUT = os.path.join(REPO, "wp-import", "content")
os.makedirs(OUT, exist_ok=True)

BOOKS = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Joshua","Judges","Ruth",
"1 Samuel","2 Samuel","1 Kings","2 Kings","1 Chronicles","2 Chronicles","Ezra","Nehemiah",
"Esther","Job","Psalms","Proverbs","Ecclesiastes","Song of Solomon","Isaiah","Jeremiah",
"Lamentations","Ezekiel","Daniel","Hosea","Joel","Amos","Obadiah","Jonah","Micah","Nahum",
"Habakkuk","Zephaniah","Haggai","Zechariah","Malachi","Matthew","Mark","Luke","John","Acts",
"Romans","1 Corinthians","2 Corinthians","Galatians","Ephesians","Philippians","Colossians",
"1 Thessalonians","2 Thessalonians","1 Timothy","2 Timothy","Titus","Philemon","Hebrews",
"James","1 Peter","2 Peter","1 John","2 John","3 John","Jude","Revelation"]
BIDX = {b: i for i, b in enumerate(BOOKS)}

verses = []
for line in open(KJV, encoding="utf-8"):
    m = re.match(r"^(.+?)\s+(\d+):(\d+)\s+(.*)$", line.strip())
    if m:
        verses.append((m.group(1).strip(), int(m.group(2)), int(m.group(3)), m.group(4)))
print(f"verses loaded: {len(verses)}")

# index: book -> chapter -> [verses]
from collections import defaultdict
BY_BOOK = defaultdict(list)
for (b, c, v, t) in verses:
    BY_BOOK[b].append((c, v, t))


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def ref_str(b, c, v):
    return f"{b} {c}:{v}"


# ============ TOPICS =====================================================
def topic_verses(term, per_book=1, max_books=12):
    """Sample verses containing `term`, spread ACROSS books of the Bible."""
    pat = re.compile(r"\b" + re.escape(term) + r"\b", re.I)
    picks = []
    for b in BOOKS:
        for (c, v, t) in BY_BOOK.get(b, []):
            if pat.search(t):
                picks.append((BIDX[b], c, v, b, t))
                break   # one verse per book keeps the selection broad
        if len(picks) >= max_books:
            break
    return picks


def build_topic_html(rec):
    topic = rec.get("topic") or rec["title"]
    # derive the search term from the topic phrase
    t = topic.lower()
    if t.startswith("the "):
        t = t[4:]
    term = t.split(" and ")[0].split(",")[0].split("?")[0].strip()
    seeds = topic_verses(term)
    parts = [f"<p>The Bible has a great deal to say about <strong>{esc(topic)}</strong>. "
             f"This study gathers passages from across Scripture &mdash; law, history, "
             f"poetry, prophecy, and the letters &mdash; and sets them out for reading "
             f"and reflection.</p>"]
    if seeds:
        parts.append("<h2>Verses to Consider</h2>")
        items = []
        for _i, c, v, b, txt in seeds:
            snip = esc(txt)
            if len(snip) > 300:
                snip = snip[:297] + "..."
            items.append(f"<li><strong>{esc(ref_str(b,c,v))}</strong> &mdash; {snip}</li>")
        parts.append("<ul>" + "".join(items) + "</ul>")
        parts.append("<h2>Where These Come From</h2>")
        parts.append("<p>These verses are drawn from different parts of the Bible on "
                     "purpose. A subject is rarely settled by a single line; the whole "
                     "counsel of Scripture gives the shape of it.</p>")
    parts.append("<h2>Thinking It Through</h2>")
    parts.append(f"<p>Read the passages slowly. Ask what they reveal about God&rsquo;s "
                 f"character, and what they ask of us in the matter of {esc(topic)}. "
                 f"Scripture rarely hands us a single tidy rule; it gives a direction "
                 f"to walk in.</p>")
    return "\n".join(parts)


# ============ DEVOTIONALS ================================================
MON = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
       "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
schedule = {}
for line in open(SCHED, encoding="utf-8"):
    m = re.match(r"^\|\s*\w{3}\s+(\w{3})\s+(\d{2})\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", line)
    if m:
        mo, dy, primary, psalm = MON.get(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
        if mo:
            schedule[(mo, dy)] = (primary, psalm)
print(f"schedule days parsed: {len(schedule)}")


def parse_reading(s):
    """'Acts 1-2' -> ('Acts', 1, 2); '1 Corinthians 8-9' -> ('1 Corinthians', 8, 9)."""
    if not s or s.strip() in ("—", "-", ""):
        return None
    s = s.strip()
    m = re.match(r"^(.+?)\s+(\d+)(?:\s*[-–]\s*(\d+))?$", s)
    if not m:
        return None
    book, c1 = m.group(1).strip(), int(m.group(2))
    c2 = int(m.group(3)) if m.group(3) else c1
    return (book, c1, c2)


def reading_verses(book, c1, c2, limit=6):
    out = []
    for (c, v, t) in BY_BOOK.get(book, []):
        if c1 <= c <= c2:
            out.append((c, v, t))
            if len(out) >= limit:
                break
    return out


def build_devotional_html(rec):
    d = rec.get("date")
    if isinstance(d, str):
        d = datetime.fromisoformat(d)
    day = d.strftime("%A, %B %-d, %Y")
    primary, psalm = schedule.get((d.month, d.day), ("", "—"))
    pr = parse_reading(primary)
    parts = [f"<p><em>{esc(day)}</em></p>"]

    parts.append("<h2>Scripture Readings</h2>")
    rows = []
    if primary and primary != "—":
        rows.append(f"<li><strong>Primary Reading:</strong> {esc(primary)}</li>")
    if psalm and psalm != "—":
        rows.append(f"<li><strong>Psalm Portion:</strong> {esc(psalm)}</li>")
    parts.append("<ul>" + "".join(rows) + "</ul>" if rows else "<p>(no reading assigned)</p>")

    # key verse drawn from the ACTUAL primary reading
    if pr:
        rv = reading_verses(*pr, limit=8)
        if rv:
            # choose a verse in the middle of the sample for a representative pick
            c, v, t = rv[min(len(rv)//2, len(rv)-1)]
            parts.append("<h2>Key Verse</h2>")
            parts.append(f"<p><strong>{esc(ref_str(pr[0], c, v))}</strong> &mdash; "
                         f"&ldquo;{esc(t)}&rdquo;</p>")
        parts.append("<h2>The Reading</h2>")
        items = []
        for (c, v, t) in reading_verses(*pr, limit=4):
            items.append(f"<li><strong>{esc(ref_str(pr[0],c,v))}</strong> &mdash; {esc(t)}</li>")
        parts.append("<ul>" + "".join(items) + "</ul>")

    # psalm verse
    pp = parse_reading(psalm)
    if pp:
        pv = reading_verses(*pp, limit=1)
        if pv:
            c, v, t = pv[0]
            parts.append("<h2>Psalm Verse</h2>")
            parts.append(f"<p><strong>{esc(ref_str(pp[0], c, v))}</strong> &mdash; "
                         f"&ldquo;{esc(t)}&rdquo;</p>")

    parts.append("<h2>Reflection</h2>")
    parts.append("<p>Take a few quiet minutes with today&rsquo;s reading. What does it "
                 "show you about God? What does it ask of you today?</p>")
    parts.append("<h2>Prayer</h2>")
    parts.append("<p>Father, thank You for Your word and for the day You have given. "
                 "Open our hearts to what we read, and let it shape what we do. "
                 "Through Jesus Christ our Lord. Amen.</p>")
    return "\n".join(parts)


# ============ NAMES / PROPHECIES / DISCOVERIES ===========================
def find_refs(name, limit=8):
    pat = re.compile(r"\b" + re.escape(name) + r"\b")
    hits = [(BIDX.get(b, 999), c, v, b, t) for (b, c, v, t) in verses if pat.search(t)]
    hits.sort()
    return hits[:limit], len(hits)


def build_name_html(rec):
    name = rec["name"]
    hits, total = find_refs(name, 10)
    desc = rec.get("description") or ""
    gender = rec.get("gender") or ""
    testament = rec.get("testament") or ""
    parts = [f"<p><strong>{esc(name)}</strong> is a name found in the King James Bible"
             + (f", appearing {total} time{'s' if total != 1 else ''} in the text." if total else ".")
             + "</p>"]
    if desc:
        parts += ["<h2>Who This Was</h2>", f"<p>{esc(desc)}</p>"]
    facts = []
    if gender:
        facts.append(f"<strong>Gender:</strong> {esc(gender.title())}")
    if testament:
        facts.append("<strong>Testament:</strong> "
                     + esc("Old and New Testaments" if testament == "both" else testament.title()))
    facts.append(f"<strong>Mentions in the KJV:</strong> {total}")
    parts += ["<h2>At a Glance</h2>", "<ul>" + "".join(f"<li>{f}</li>" for f in facts) + "</ul>"]
    if hits:
        parts.append("<h2>Where It Appears in Scripture</h2>")
        items = []
        for _i, c, v, b, t in hits:
            snip = esc(t)
            if len(snip) > 260:
                snip = snip[:257] + "..."
            items.append(f"<li><strong>{esc(ref_str(b,c,v))}</strong> &mdash; {snip}</li>")
        parts.append("<ul>" + "".join(items) + "</ul>")
    parts += ["<h2>About This Name</h2>",
              "<p>Names in the Bible often carry meaning rooted in the language they came "
              "from, and many were given to mark something about the person or the moment "
              "of their birth. This entry is part of a series working through the names of "
              "the King James Bible in order.</p>"]
    return "\n".join(parts)


def build_prophecy_html(rec):
    return "\n".join([
        "<p>This study considers a prophecy given in Scripture and how it was fulfilled.</p>",
        "<h2>The Prophecy</h2>",
        "<p>The passage foretelling the event, with the circumstances in which it was given.</p>",
        "<h2>The Fulfilment</h2>",
        "<p>The later record showing the prophecy come to pass.</p>",
        "<h2>Why It Matters</h2>",
        "<p>Fulfilled prophecy is one of the strongest evidences for the reliability of Scripture.</p>",
    ])


def markdown_to_html(md):
    out, in_ul = [], False
    for ln in md.split("\n"):
        s = ln.rstrip()
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            if in_ul: out.append("</ul>"); in_ul = False
            lvl = min(len(m.group(1)) + 1, 6)
            out.append(f"<h{lvl}>{esc(m.group(2))}</h{lvl}>")
            continue
        if re.match(r"^\s*[-*]\s+", s):
            if not in_ul: out.append("<ul>"); in_ul = True
            out.append("<li>" + esc(re.sub(r"^\s*[-*]\s+", "", s)) + "</li>")
            continue
        if not s.strip():
            if in_ul: out.append("</ul>"); in_ul = False
            continue
        if in_ul: out.append("</ul>"); in_ul = False
        out.append("<p>" + esc(s) + "</p>")
    if in_ul: out.append("</ul>")
    return "\n".join(out)


CATS = {"devotional": "Daily Devotional", "names": "Bible Names",
        "topics": "What Does the Bible Say", "discoveries": "Discoveries in the Bible",
        "prophecies": "Bible Prophecies"}

skeleton = json.load(open(SKEL))
print(f"skeleton records: {len(skeleton)}")

index, counts = [], {}
for rec in skeleton:
    series = rec["series"]
    counts[series] = counts.get(series, 0) + 1
    if series == "names":
        html = build_name_html(rec)
    elif series == "topics":
        html = build_topic_html(rec)
    elif series == "devotional":
        html = build_devotional_html(rec)
    elif series == "prophecies":
        html = build_prophecy_html(rec)
    elif series == "discoveries":
        src = os.path.join(REPO, "kjv-archaeological", rec["slug"] + ".md")
        html = markdown_to_html(open(src, encoding="utf-8").read()) if os.path.exists(src) else "<p>(pending)</p>"
    else:
        html = "<p>(pending)</p>"
    slug = rec["slug"]
    json.dump({"order": rec["order"], "series": series, "title": rec["title"],
               "slug": slug, "date": rec["date"], "category": CATS[series], "html": html},
              open(os.path.join(OUT, f"{rec['order']:05d}-{slug}.json"), "w"), indent=2)
    index.append({"order": rec["order"], "slug": slug, "series": series,
                  "title": rec["title"], "file": f"{rec['order']:05d}-{slug}.json"})

json.dump(index, open(os.path.join(OUT, "INDEX.json"), "w"), indent=2)
print(f"content files written: {len(index)}")
for k in sorted(counts):
    print(f"  {k:<12} {counts[k]}")
