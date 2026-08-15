#!/usr/bin/env python3
"""Convert midvash/bible-data JSON books into plain text files.
One file per version, with optional reference prefix.
"""
import json, glob, os, re, sys

osis_to_canonical = [
    "Gen","Exod","Lev","Num","Deut","Josh","Judg","Ruth","1Sam","2Sam","1Kgs","2Kgs",
    "1Chr","2Chr","Ezra","Neh","Esth","Job","Ps","Prov","Eccl","Song","Isa","Jer",
    "Lam","Ezek","Dan","Hos","Joel","Amos","Obad","Jonah","Mic","Nah","Hab","Zeph",
    "Hag","Zech","Mal","Matt","Mark","Luke","John","Acts","Rom","1Cor","2Cor",
    "Gal","Eph","Phil","Col","1Thess","2Thess","1Tim","2Tim","Titus","Phlm","Heb",
    "Jas","1Pet","2Pet","1John","2John","3John","Jude","Rev"
]

def book_sort_key(filename):
    base = os.path.basename(filename).replace('.json','')
    try:
        return osis_to_canonical.index(base)
    except ValueError:
        return 999

def convert(src_dir, out_path, include_refs=True, strip_sofy_pasuq=False):
    files = sorted(glob.glob(os.path.join(src_dir, 'books', '*.json')), key=book_sort_key)
    lines = []
    for f in files:
        data = json.load(open(f, encoding='utf-8'))
        book = data.get('book', os.path.basename(f).replace('.json',''))
        for ch in data.get('chapters', []):
            ch_num = ch.get('chapter')
            for v in ch.get('verses', []):
                text = v.get('text','')
                if strip_sofy_pasuq:
                    text = text.rstrip(' ׃').rstrip('׃').rstrip(' :').rstrip(':')
                if include_refs:
                    lines.append(f"{book} {ch_num}:{v.get('number')} {text}")
                else:
                    lines.append(text)
    with open(out_path, 'w', encoding='utf-8') as w:
        w.write('\n'.join(lines) + '\n')
    print(f"Wrote {len(lines)} verses to {out_path}")

if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else '/home/jmewing/.openclaw/workspace/kjv-wlc-texts'
    convert(os.path.join(base,'wlc'),  os.path.join(base,'wlc.txt'),  include_refs=True, strip_sofy_pasuq=False)
    convert(os.path.join(base,'tr'),   os.path.join(base,'tr.txt'),   include_refs=True, strip_sofy_pasuq=False)
    convert(os.path.join(base,'kjv'),  os.path.join(base,'kjv.txt'),  include_refs=True, strip_sofy_pasuq=False)
    convert(os.path.join(base,'vulg'), os.path.join(base,'vulg.txt'), include_refs=True, strip_sofy_pasuq=False)
    convert(os.path.join(base,'clem'), os.path.join(base,'clem.txt'), include_refs=True, strip_sofy_pasuq=False)
