#!/usr/bin/env python3
"""Split parallel.tsv into one TSV per book.
Outputs to parallel-by-book/ as <book>.tsv.
"""
import csv, os

BASE = '/home/jmewing/.openclaw/workspace/kjv-wlc-texts'
OUT_DIR = os.path.join(BASE, 'parallel-by-book')
os.makedirs(OUT_DIR, exist_ok=True)

header = ['book', 'chapter', 'verse', 'wlc', 'lxx', 'vulg', 'clem', 'tr', 'kjv']
rows_by_book = {}

with open(os.path.join(BASE, 'parallel.tsv'), encoding='utf-8', newline='') as f:
    reader = csv.reader(f, delimiter='\t')
    header_in = next(reader)
    for row in reader:
        if len(row) < 9:
            continue
        book = row[0]
        rows_by_book.setdefault(book, []).append(row)

for book, rows in rows_by_book.items():
    path = os.path.join(OUT_DIR, f"{book}.tsv")
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(header)
        writer.writerows(rows)
    print(f"{book}: {len(rows):5d} verses → {path}")

print(f"\nWrote {len(rows_by_book)} files to {OUT_DIR}")
