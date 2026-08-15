#!/usr/bin/env python3
"""Build parallel verse-by-verse TSV from WLC, TR, KJV texts.
Lines only where a verse exists in at least one text.
"""
import csv, re, os

BASE = '/home/jmewing/.openclaw/workspace/kjv-wlc-texts'
OUT = os.path.join(BASE, 'parallel.tsv')

def parse_txt(path):
    refs = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            m = re.match(r'^(\S+)\s+(\d+):(\d+)\s+(.*)$', line)
            if not m:
                continue
            book, ch, vs, text = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
            refs[(book, ch, vs)] = text
    return refs

canonical_order = [
    "Gen","Exod","Lev","Num","Deut","Josh","Judg","Ruth","1Sam","2Sam","1Kgs","2Kgs",
    "1Chr","2Chr","Ezra","Neh","Esth","Job","Ps","Prov","Eccl","Song","Isa","Jer",
    "Lam","Ezek","Dan","Hos","Joel","Amos","Obad","Jonah","Mic","Nah","Hab","Zeph",
    "Hag","Zech","Mal","Matt","Mark","Luke","John","Acts","Rom","1Cor","2Cor",
    "Gal","Eph","Phil","Col","1Thess","2Thess","1Tim","2Tim","Titus","Phlm","Heb",
    "Jas","1Pet","2Pet","1John","2John","3John","Jude","Rev"
]
book_rank = {b: i for i, b in enumerate(canonical_order)}

def ref_key(ref):
    book, ch, vs = ref
    return (book_rank.get(book, 9999), ch, vs)

wlc  = parse_txt(os.path.join(BASE, 'wlc.txt'))
tr   = parse_txt(os.path.join(BASE, 'tr.txt'))
kjv  = parse_txt(os.path.join(BASE, 'kjv.txt'))
lxx  = parse_txt(os.path.join(BASE, 'lxx.txt'))
vulg = parse_txt(os.path.join(BASE, 'vulg.txt'))
clem = parse_txt(os.path.join(BASE, 'clem.txt'))

all_refs = sorted(set(wlc) | set(tr) | set(kjv) | set(lxx) | set(vulg) | set(clem), key=ref_key)

with open(OUT, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f, delimiter='\t')
    writer.writerow(['book', 'chapter', 'verse', 'wlc', 'lxx', 'vulg', 'clem', 'tr', 'kjv'])
    for ref in all_refs:
        writer.writerow([ref[0], ref[1], ref[2], wlc.get(ref, ''), lxx.get(ref, ''), vulg.get(ref, ''), clem.get(ref, ''), tr.get(ref, ''), kjv.get(ref, '')])

print(f"Wrote {len(all_refs)} rows to {OUT}")
