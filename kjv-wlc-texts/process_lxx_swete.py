#!/usr/bin/env python3
"""Convert lxx-swete per-word files into a single verse-ref-keyed TSV line.
Output: lxx.txt lines like '<book> <chapter>:<verse> <greek verse text>'
"""
import os, re, glob

BASE = '/home/jmewing/.openclaw/workspace/kjv-wlc-texts/lxx-swete-master/data'
OUT = '/home/jmewing/.openclaw/workspace/kjv-wlc-texts/lxx.txt'

# Map filenames to OSIS book codes.
latin_to_osis = {
    '01.Genesis': 'Gen', '02.Exodus': 'Exod', '03.Leviticus': 'Lev', '04.Numeri': 'Num',
    '05.Deuteronomium': 'Deut', '06.Josue': 'Josh', '08.Judices': 'Judg', '10.Ruth': 'Ruth',
    '11.Regnorum_I': '1Sam', '12.Regnorum_II': '2Sam', '13.Regnorum_III': '1Kgs', '14.Regnorum_IV': '2Kgs',
    '15.Paralipomenon_I': '1Chr', '16.Paralipomenon_II': '2Chr', '17.Esdras_A': 'Ezra', '18.Esdras_B': 'Neh',
    '19.Esther': 'Esth', '20.Judith': 'Jdt', '21.Tobias': 'Tob',
    '23.Machabaeorum_i': '1Macc', '24.Machabaeorum_ii': '2Macc', '25.Machabaeorum_iii': '3Macc', '26.Machabaeorum_iv': '4Macc',
    '27.Psalmi': 'Ps', '28.Odae': 'Odae', '29.Proverbia': 'Prov', '31.Canticum': 'Song',
    '32.Job': 'Job', '33.Sapientia_Salomonis': 'Wis', '34.Ecclesiasticus': 'Sir',
    '35.Psalmi_Salomonis': 'PsSol',
    '36.Osee': 'Hos', '37.Amos': 'Amos', '38.Michaeas': 'Mic', '39.Joel': 'Joel',
    '40.Abdias': 'Obad', '41.Jonas': 'Jonah', '42.Nahum': 'Nah', '43.Habacuc': 'Hab',
    '44.Sophonias': 'Zeph', '45.Aggaeus': 'Hag', '46.Zacharias': 'Zech', '47.Malachias': 'Mal',
    '48.Isaias': 'Isa', '49.Jeremias': 'Jer', '50.Baruch': 'Bar', '51.Threni_seu_Lamentationes': 'Lam',
    '52.Epistula_Jeremiae': 'EpJer', '53.Ezechiel': 'Ezek',
    '54.Susanna_translatio_Graeca': 'SusOG', '55.Susanna_Theodotionis_versio': 'SusTh',
    '56.Daniel_translatio_Graeca': 'DanOG', '57.Daniel_Theodotionis_versio': 'DanTh',
    '58.Bel_et_Draco_translatio_Graeca': 'BelOG', '59.Bel_et_Draco_Theodotionis_versio': 'BelTh',
}

verses = {}
for path in sorted(glob.glob(os.path.join(BASE, '*.txt'))):
    base = os.path.basename(path).replace('.txt','')
    if base in ('07.null', '09.null', '22.null', '30.null'):
        continue
    osis = latin_to_osis.get(base)
    if not osis:
        print(f"Skipping unmapped: {base}")
        continue
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = re.match(r'^\d+\.(\d+)\.(\d+)\s+(.*)$', line)
            if not m:
                continue
            ch, vs, word = int(m.group(1)), int(m.group(2)), m.group(3).strip()
            key = (osis, ch, vs)
            verses.setdefault(key, []).append(word)

with open(OUT, 'w', encoding='utf-8') as f:
    for key in sorted(verses):
        text = ' '.join(verses[key])
        f.write(f"{key[0]} {key[1]}:{key[2]} {text}\n")

print(f"Wrote {len(verses)} verses to {OUT}")
