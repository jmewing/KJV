#!/usr/bin/env python3
"""Split parallel.tsv into OT.tsv, NT.tsv, Apocrypha.tsv based on book membership.
"""
import csv, os

BASE = '/home/jmewing/.openclaw/workspace/kjv-wlc-texts'
OUT_DIR = os.path.join(BASE, 'parallel-by-testament')
os.makedirs(OUT_DIR, exist_ok=True)

ot = {
    'Gen','Exod','Lev','Num','Deut','Josh','Judg','Ruth','1Sam','2Sam','1Kgs','2Kgs',
    '1Chr','2Chr','Ezra','Neh','Esth','Job','Ps','Prov','Eccl','Song','Isa','Jer',
    'Lam','Ezek','Dan','Hos','Joel','Amos','Obad','Jonah','Mic','Nah','Hab','Zeph',
    'Hag','Zech','Mal'
}
nt = {
    'Matt','Mark','Luke','John','Acts','Rom','1Cor','2Cor','Gal','Eph','Phil','Col',
    '1Thess','2Thess','1Tim','2Tim','Titus','Phlm','Heb','Jas','1Pet','2Pet','1John',
    '2John','3John','Jude','Rev'
}
# Deuterocanon / apocrypha books present in LXX/Vulgate but not in Hebrew or Protestant canon.
apoc = {
    'Jdt','Tob','Wis','Sir','Bar','EpJer','1Macc','2Macc','3Macc','4Macc','PsSol',
    'Odae','SusOG','SusTh','DanOG','DanTh','BelOG','BelTh'
}

header = ['book', 'chapter', 'verse', 'wlc', 'lxx', 'vulg', 'clem', 'tr', 'kjv']
groups = {'OT': [], 'NT': [], 'Apocrypha': []}

with open(os.path.join(BASE, 'parallel.tsv'), encoding='utf-8', newline='') as f:
    reader = csv.reader(f, delimiter='\t')
    next(reader)
    for row in reader:
        if len(row) < 9:
            continue
        book = row[0]
        if book in nt:
            groups['NT'].append(row)
        elif book in apoc:
            groups['Apocrypha'].append(row)
        else:
            groups['OT'].append(row)

for name, rows in groups.items():
    path = os.path.join(OUT_DIR, f"{name}.tsv")
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(header)
        writer.writerows(rows)
    print(f"{name}: {len(rows):6d} verses → {path}")

print(f"\nWrote {len(groups)} files to {OUT_DIR}")
