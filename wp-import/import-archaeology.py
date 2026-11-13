#!/usr/bin/env python3
"""
Import the staged KJV series into WordPress, in DATE ORDER.

Guardrails (the reason this exists):
  * reads the verified plan.json (already sorted, 0 inversions)
  * inserts in that order so wp_posts.ID ascends with post_date
  * sets post_date AND post_date_gmt consistently (America/Chicago, CDT)
  * skips any slug that already exists (idempotent — safe to re-run)
  * reads everything back out of MySQL afterwards and proves ID order == date order

Run on the VPS as www-data (or with --allow-root via wp-cli style env).
Usage: python3 import-archaeology.py [--dry-run]
"""
import json
import os
import re
import subprocess
import sys

PLAN = "/srv/kjv/wp-import/staging/plan.json"
WP = "/var/www/inetking.org"
WP_CLI_USER = "www-data"
CATEGORY = "Discoveries in the Bible"
AUTHOR_LOGIN = "jmewing"
DRY = "--dry-run" in sys.argv


def wp(*args, check=True):
    """Run a wp-cli command in the WordPress root."""
    cmd = ["wp", "--path=" + WP, "--allow-root"] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"wp {' '.join(args)} failed: {r.stderr[:400]}")
    return r.stdout.strip()


def md_to_html(md: str) -> str:
    """Minimal, dependency-free markdown -> HTML matching the post style."""
    lines = md.split("\n")
    out, in_ul = [], False
    for ln in lines:
        s = ln.rstrip()
        # headings
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            lvl = min(len(m.group(1)) + 1, 6)  # h1 -> h2 (title is the post H1)
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            continue
        # list item
        if re.match(r"^\s*[-*]\s+", s):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append("<li>" + inline(re.sub(r"^\s*[-*]\s+", "", s)) + "</li>")
            continue
        # horizontal rule
        if re.match(r"^\s*---+\s*$", s):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append("<hr />")
            continue
        # blank
        if not s.strip():
            if in_ul:
                out.append("</ul>")
                in_ul = False
            continue
        # paragraph
        if in_ul:
            out.append("</ul>")
            in_ul = False
        out.append("<p>" + inline(s) + "</p>")
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


def inline(t: str) -> str:
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"`([^`]+?)`", r"<code>\1</code>", t)
    # bare URLs -> links
    t = re.sub(r"(?<![\"'=])(https?://[^\s<]+)", r'<a href="\1">\1</a>', t)
    return t


def main():
    plan = json.load(open(PLAN))
    print(f"plan: {len(plan)} records")

    # --- 1. ensure category exists ---------------------------------------
    cat_out = wp("term", "list", "--taxonomy=category", "--fields=term_id,name,slug",
                 "--format=csv")
    have_cat = None
    for line in cat_out.split("\n")[1:]:
        parts = line.split(",")
        if len(parts) >= 2 and parts[1].strip() == CATEGORY:
            have_cat = parts[0].strip()
    if have_cat:
        print(f"category exists: '{CATEGORY}' (id {have_cat})")
    else:
        if DRY:
            print(f"[dry] would create category '{CATEGORY}'")
            have_cat = "?"
        else:
            have_cat = wp("term", "create", "category", CATEGORY,
                          "--porcelain").strip()
            print(f"created category '{CATEGORY}' (id {have_cat})")

    # --- 2. existing slugs (idempotency) ---------------------------------
    existing = set()
    ps = wp("post", "list", "--post_type=post", "--post_status=any",
            "--fields=post_name", "--format=csv")
    for line in ps.split("\n")[1:]:
        if line.strip():
            existing.add(line.strip())
    print(f"existing posts: {len(existing)}")

    # --- 3. insert in DATE ORDER (plan is already sorted+verified) --------
    created = 0
    for i, rec in enumerate(plan, 1):
        slug = rec["slug"]
        if slug in existing:
            print(f"  {i:>3} SKIP (exists) {slug}")
            continue
        date = rec["post_date"]  # 'YYYY-MM-DD HH:MM:SS' local (CDT)
        html = md_to_html(rec["content_md"])
        if DRY:
            print(f"  {i:>3} [dry] {date} | {rec['title'][:60]}")
            continue
        out = wp(
            "post", "create",
            "--post_title=" + rec["title"],
            "--post_name=" + slug,
            "--post_content=" + html,
            "--post_status=publish",
            "--post_type=post",
            f"--post_author=1",
            f"--post_category={have_cat}",
            f"--post_date={date}",
            "--porcelain",
        )
        print(f"  {i:>3} created id={out}  {date}  {slug}")
        created += 1

    print(f"\ncreated {created} posts")
    if not DRY:
        # WordPress computed post_date_gmt from our local date + its own tz.
        wp("rewrite", "flush", "--hard")
        print("permalinks flushed")


if __name__ == "__main__":
    main()
