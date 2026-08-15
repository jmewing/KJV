#!/usr/bin/env python3
"""Extract unique normalized tokens from target books to help expand lexicons."""
import os, re, unicodedata, json, collections

SRC = os.path.dirname(os.path.abspath(__file__))

def norm_heb(w):
    w = unicodedata.normalize('NFD', w)
    out = []
    for ch in w:
        cat = unicodedata.category(ch)
        if cat.startswith('P') or ch in '־':
            continue
        out.append(ch)
    return ''.join(out)

def norm_grc(w):
    w = w.lower()
    w = unicodedata.normalize('NFD', w)
    out = []
    for ch in w:
        if unicodedata.category(ch) == 'Mn':
            continue
        out.append(ch)
    w = ''.join(out)
    w = w.replace('ς', 'σ')
    w = re.sub(r'[^ἀ-῾a-z0-9]+$', '', w)
    return w

def norm_lat(w):
    w = w.lower()
    w = unicodedata.normalize('NFD', w)
    out = []
    for ch in w:
        if unicodedata.category(ch) == 'Mn':
            continue
        out.append(ch)
    w = ''.join(out)
    w = re.sub(r'[^a-z]+$', '', w)
    w = re.sub(r'^[^a-z]+', '', w)
    return w

configs = {
    'heb': ('wlc.txt', ['Gen','Exod','Ps'], norm_heb, r'[\s\u05be]+'),
    'grc': ('lxx.txt', ['Gen','Ps'], norm_grc, r'[\s,;:.!?]+'),
    'lat': ('vulg.txt', ['Gen','Ps','John'], norm_lat, r'[\s,;:.!?]+'),
    'tr': ('tr.txt', ['Matt','John','Rom'], norm_grc, r'[\s,;:.!?]+'),
}

for lang,(fn,books,norm,patt) in configs.items():
    path = os.path.join(SRC, fn)
    counts = collections.Counter()
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.match(r'^([A-Za-z0-9]+)\s+(\d+):(\d+)\s+(.+)$', line)
            if not m: continue
            b = m.group(1)
            if b not in books: continue
            text = m.group(4)
            if lang == 'heb':
                text = text.replace('פ', '').replace('ס', '').strip()
            for raw in re.split(patt, text):
                raw = raw.strip()
                if not raw: continue
                key = norm(raw)
                if not key: continue
                counts[key] += 1
    out = []
    for tok, n in counts.most_common(500):
        out.append(f"{tok}\t{n}")
    open(os.path.join(SRC, f'freq-{lang}.txt'), 'w', encoding='utf-8').write('\n'.join(out))
    print(f'{lang}: {len(counts)} unique tokens, wrote top 500')
