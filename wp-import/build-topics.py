#!/usr/bin/env python3
"""
Build the TOPICS list for the Wednesday series, INTERLEAVED.

Why interleave: a thematically-grouped list would put 4 marriage topics in a
row. Readers want variety week to week, so topics are drawn round-robin from
themed buckets — consecutive Wednesdays come from different themes.

105 topics fill 2025-2026; the remainder carries into 2027.

Output: wp-import/topics/topics.json  (ordered, 105 used + overflow listed)
"""
import json
import os

OUTDIR = "/srv/kjv/wp-import/topics"
os.makedirs(OUTDIR, exist_ok=True)

BUCKETS = {
    "foundations": [
        "God", "Jesus", "the Holy Spirit", "the Trinity", "creation",
        "the Bible", "faith", "trusting God", "prayer", "hearing God",
        "heaven", "hell", "angels", "demons", "miracles",
        "sin", "forgiveness", "grace", "mercy", "repentance",
        "salvation", "being born again", "eternal life", "judgment",
    ],
    "feelings": [
        "worry and anxiety", "fear", "stress", "rest", "contentment",
        "grief and loss", "death", "suffering", "illness",
        "depression", "loneliness", "anger", "revenge",
        "jealousy", "pride", "humility", "guilt", "shame",
        "hope", "joy", "peace", "patience", "kindness",
        "self-control", "temptation", "addiction", "bad habits", "discipline",
    ],
    "relationships": [
        "marriage", "divorce", "husbands", "wives", "children",
        "parenting", "family", "friendship", "love", "sex",
        "dating", "singleness", "widows", "aging parents", "honoring parents",
        "lying", "gossip", "conflict", "reconciliation", "boundaries",
    ],
    "money_work": [
        "money", "wealth", "poverty", "giving", "tithing",
        "debt", "work", "laziness", "gambling",
        "stewardship", "generosity", "greed", "bribery", "honest business",
    ],
    "living": [
        "obedience", "worship", "the Sabbath", "the church", "baptism",
        "the Lord's Supper", "spiritual gifts", "serving others", "evangelism",
        "missions", "persecution", "being a good neighbor", "justice", "the poor",
        "immigrants and strangers", "war", "peacemaking", "government", "voting",
        "alcohol", "food and diet", "modesty",
    ],
    "hard_questions": [
        "why bad things happen", "predestination", "free will", "God's will",
        "answered prayer", "unanswered prayer", "doubt", "backsliding",
        "assurance of salvation", "the end times", "the antichrist", "the rapture",
        "the resurrection", "the afterlife", "ghosts", "astrology",
        "witchcraft", "idols", "other religions", "cursing and swearing",
        "suicide", "mental illness",
    ],
}

# --- interleave: round-robin across buckets, longest bucket first ---------
order = ["foundations", "feelings", "relationships", "money_work", "living", "hard_questions"]
queues = {k: list(BUCKETS[k]) for k in order}
interleaved = []
while any(queues.values()):
    for k in order:
        if queues[k]:
            interleaved.append(queues[k].pop(0))

# de-dup, preserve order
seen, topics = set(), []
for t in interleaved:
    if t.lower() not in seen:
        seen.add(t.lower())
        topics.append(t)

USED = 105
used, overflow = topics[:USED], topics[USED:]

json.dump({"used": used, "overflow_2027": overflow},
          open(os.path.join(OUTDIR, "topics.json"), "w"), indent=2)

print(f"total topics: {len(topics)}   used 2025-2026: {len(used)}   carry to 2027: {len(overflow)}")
print("\n--- first 21 Wednesdays (note the theme variety) ---")
for i, t in enumerate(used[:21], 1):
    print(f"  {i:>3}  What does the Bible say about {t}?")
print("\n--- last 8 ---")
for i, t in enumerate(used[-8:], len(used) - 7):
    print(f"  {i:>3}  What does the Bible say about {t}?")
