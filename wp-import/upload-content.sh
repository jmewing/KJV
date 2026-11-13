#!/bin/bash
# Package the insert-ready content and copy it to the VPS.
# Then (separately) run the dry-run. Does NOT insert.
set -euo pipefail

VPS="jmewing@129.121.127.233"
KEY="$HOME/.ssh/id_ed25519"
SRC="/srv/kjv/wp-import/insert"
TAR="/tmp/kjv-content.tgz"
DEST="/root/kjv-content"

[[ -f "$SRC/INDEX.json" ]] || { echo "missing $SRC/INDEX.json — run merge-verify.py first" >&2; exit 1; }

N=$(python3 -c "import json;print(len(json.load(open('$SRC/INDEX.json'))))")
echo "records in manifest: $N"
EXPECT=$(ls "$SRC"/[0-9]*-*.json | wc -l)
echo "content files present: $EXPECT"
[[ "$N" == "$EXPECT" ]] || { echo "MISMATCH: manifest says $N, files say $EXPECT" >&2; exit 1; }

tar -czf "$TAR" -C "$SRC" .
echo "archive: $(du -h "$TAR" | cut -f1)"

ssh -o ConnectTimeout=20 -i "$KEY" "$VPS" "sudo mkdir -p $DEST && sudo rm -f $DEST/*.json"
scp -o ConnectTimeout=20 -i "$KEY" "$TAR" "$VPS:/tmp/kjv-content.tgz"
ssh -o ConnectTimeout=20 -i "$KEY" "$VPS" "sudo tar -xzf /tmp/kjv-content.tgz -C $DEST && echo extracted: \$(ls $DEST | wc -l) files"

echo
echo "=== verify on VPS ==="
ssh -o ConnectTimeout=20 -i "$KEY" "$VPS" "ls $DEST | wc -l; python3 -c \"import json;print('manifest:',len(json.load(open('$DEST/INDEX.json'))))\""
