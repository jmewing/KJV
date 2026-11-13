#!/usr/bin/env python3
"""
Extract BIBLICAL PEOPLE NAMES from the KJV text.

Method (matches what Jeremy described we did before):
  1. read the whole KJV text
  2. find every capitalized proper-noun token (names are capitalized in KJV)
  3. filter out PLACES and THINGS (and common sentence-initial words)
  4. what remains is PEOPLE names
  5. weight by modern commonality: UNCOMMON names first, common names later
  6. shuffle so it is NOT alphabetical, but with the uncommon-first tendency kept

Outputs:
  wp-import/names/people-names.csv     — name, verse_count, commonality_rank
  wp-import/names/people-names.json    — ordered publishing list (Tue/Thu)
  wp-import/names/report.txt           — what was found / filtered, for review
"""
import csv
import json
import os
import re
from collections import Counter

REPO = "/srv/kjv"
KJV = os.path.join(REPO, "kjv-texts", "kjv.txt")
OUT = os.path.join(REPO, "wp-import", "names")
os.makedirs(OUT, exist_ok=True)

# --- Place / thing names to EXCLUDE (KJV proper nouns that are not people) ---
# Curated from the KJV corpus itself; these are the high-frequency ones.
PLACES = set("""
Eden Egypt Egyptian Egyptians Assyria Assyrian Assyrians Babylon Babylonian Babylonians
Israel Israelites Judah Jerusalem Zion Sinai Horeb Canaan Canaanite Canaanites Philistine
Philistines Moab Moabite Moabites Ammon Ammonite Ammonites Edom Edomite Edomites
Samaria Samaritans Galilee Galilean Judea Judaea Bethlehem Nazareth Capernaum
Damascus Syria Syrian Syrians Tyre Sidon Tarshish Nineveh Ninevites
Sodom Gomorrah Zeboim Admah Shechem Shiloh Bethel Gilgal Gibeon Hebron Beersheba
Gaza Ashkelon Ashdod Ekron Gath Ai Jericho Ramah Mizpah Gilboa Carmel Lebanon
Jordan Nile Euphrates Tigris Kishon Jabbok Arnon Kedron Kidron
Zion Sion Goshen Midian Midianites Amalek Amalekites Hivite Hivites Hittite Hittites
Jebusite Jebusites Amorite Amorites Girgashite Perizzite Kenite Kenites
Persia Persian Persians Greece Greek Greeks Rome Roman Romans Macedonia Macedonian
Corinth Corinthians Ephesus Ephesian Ephesians Philippi Philippians
Thessalonica Thessalonians Galatia Galatians Colosse Colossians Laodicea
Crete Cyprus Malta Patmos Antioch Iconium Lystra Derbe Troas Miletus
Smyrna Pergamos Thyatira Sardis Philadelphia Hierapolis
Bethany Bethsaida Cana Chorazin Emmaus Gethsemane Golgotha Calvary
Ararat Babel Shinar Babylon Ur Haran Padanaram
Zarephath Zorah Timnath Timnah Aijalon Arad Hormah Eglon Debir Libnah Lachish
Megiddo Jezreel Taanach Endor Aphek Ebenezer Mahanaim Penuel Succoth
Bashan Gilead Ammon Golan Heshbon Dibon Aroer Medeba
Ezion Geber Elath Eziongeber
Arabia Arabian Arabians Ethiopia Ethiopian Ethiopians Libya Cyrene
India Spain Illyricum Dalmatia Pontus Cappadocia Bithynia Asia Phrygia Pamphylia
Pisidia Lycia Cilicia Isauria Lycaonia
Tabor Hermon Nebo Pisgah Seir Paran Kadesh Kadeshbarnea
Sodom Zoar Admah Zeboiim
Egypt Goshen Rameses Pithom Succoth
""".split())

THINGS = set("""
Lord God LORD GOD Jesus Christ Jehovah Messiah Emmanuel Immanuel
Spirit Ghost Holy Angel Angels Cherubim Cherub Seraphim Seraph
Satan Devil Beelzebub Belial Antichrist
Scripture Scriptures Law Gospel Epistle Psalms Psalm Proverbs
Passover Pentecost Tabernacle Temple Ark Altar Mercyseat Candlestick
Sabbath Circumcision Unleavened
Israelite Hebrew Hebrews Jew Jews Gentile Gentiles
Adam Eve Noah Abraham Isaac Jacob Joseph Moses Aaron Joshua Caleb
""".split())  # NOTE: people names that are ALSO used as things/eras get re-checked below

# Sentence-initial or common capitalized words that are NOT names
COMMON_CAP = set("""
And But For Now Then So Thus Yet Therefore Wherefore Nevertheless Moreover Howbeit Whereupon Whereof Wherein Thereof Therein Hereby
Behold Lo Yea Nay If When Where What Who Whom Why How Which That This These Those
In On At By To Of From With Unto Upon Into Through After Before Afterward
He She It They We Ye You I Me Him Her Them Us My Thy Thine His Their Our Your
The A An All Every Some Any None No Not Neither Either Both
As Is Was Were Be Been Being Am Are Shall Will Would Should Could May Might Must
Do Did Done Doth Dost Hath Have Has Had Having Let Make Made
O Oh Amen Selah Hallelujah Hosanna
Thus Then There Here Hence Thither Hither Whither
Day Days Night Nights Morning Evening Week Weeks Month Months Year Years
King Kings Queen Queens Prince Princes Priest Priests Prophet Prophets
Father Mother Son Daughter Brother Sister Brethren Children Child Man Men Woman Women
Servant Servants Master Masters Lord Lords
God Gods Good Evil Right Righteous Wicked Holy
For Unto According Because Seeing Except Save
One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve
First Second Third Fourth Fifth Sixth Seventh Eighth Ninth Tenth
Now This So Go Come Came Saith Saying Spake Spoke
Hearken Hear See Look Behold Arise Rise Stand Sit Go Come
""".split())

# Archaic KJV verbs/adverbs/pronouns that get capitalized mid-clause.
# These are the big polluters (Take, Give, Also, Even, Surely, Verily...).
KJV_VERBS = set("""
Thou Thee Thy Thine Ye Yourself Himself Herself Myself Itself Themselves
Take Taken Took Give Given Gave Speak Spake Spoken Say Said Saith Saying
Also Even Surely Verily Yea Nay Woe Blessed Cursed Behold Lo
Fear Feared Fearing Rejoice Rejoiced Sing Sang Sung Praise Praised
Hear Heard Hearken Harken See Seen Saw Look Looked Behold
Come Came Coming Go Went Gone Depart Departed Return Returned
Arise Arose Rise Rose Stand Stood Sit Sat Dwell Dwelt Abide Abode
Bring Brought Carry Carried Lead Led Follow Followed
Know Knew Known Understand Understood Remember Remembered Forget Forgot
Write Wrote Written Read Call Called Cry Cried Weep Wept
Pray Prayed Bless Blessed Curse Cursed Swear Sware Eat Ate Drink Drank
Smite Smote Slay Slew Kill Killed Die Died Dead Live Lived
Build Built Destroy Destroyed Break Brake Broken Fight Fought
Send Sent Receive Received Ask Asked Answer Answered
Teach Taught Learn Learned Turn Turned Keep Kept
Therefore Wherefore Howbeit Yet Still Ever Never Always
Right Well Truly Indeed Peradventure Perhaps
Let Make Made Put Set Lay Laid
Whosoever Whatsoever Wheresoever Whencesoever Howsoever
Great Small Many Much Few Little More Most
Now Then Hence Away Hither Thither
Because Although Though Except Unless Whether

But Also And For Nor So Then Thus
Yea Nay Verily Surely Truly
Take Give Come Go See Hear Speak Say
Woe Lo Behold Amen
""".split())

# Tribes, clans, groups of people (not individuals)
GROUPS = set("""
Levites Levite Pharisees Pharisee Sadducees Sadducee Essenes Zealots
Israelites Hebrews Jews Gentiles Christians Disciples Apostles Prophets
Nephilim Rephaim Anakim Emim Zamzummim Gibeonites Nethinim
Chaldeans Chaldees Magi
Amorites Hittites Hivites Jebusites Perizzites Girgashites Canaanites
Philistines Moabites Ammonites Edomites Babylonians Assyrians Egyptians
Arameans Syrians Persians Greeks Romans Macedonians
Amalekites Midianites Kenites Kenizzites Kadmonites
Scribes Elders Rulers Officers Soldiers Centurions Publicans Pharisees
Brethren Kinsmen Neighbours Friends Enemies
""".split())

# Titles / offices (not personal names)
TITLES = set("""
Pharaoh Pharaohs Pharaoh's Caesar Caesars Herod Herods Tetrarch
Governor King Queen Prince Princess Priest Prophet Apostle Evangelist
High Priest Highpriest Captain Chief Chiefest Elder Deacon Bishop
Judge Judges Ruler Rulers Officer Officers Magistrate Magistrates
Centurion Centurions Soldier Soldiers Publican Publicans
Nebuchadnezzar's Pharaoh's Caesar's
Baal Baalim Ashtoreth Asherah Asheroth Molech Moloch Chemosh Dagon
Bel Merodach Rimmon Nebo Tammuz Succothbenoth Milcom
Antichrist Messiah Emmanuel Immanuel
""".split())

# --- read the KJV -----------------------------------------------------------
text = open(KJV, encoding="utf-8").read()
# strip the "Book C:V " prefixes so chapter refs don't pollute
body = re.sub(r"^[A-Za-z0-9 ]+\s+\d+:\d+\s+", "", text, flags=re.M)

# tokens: capitalized words (allow possessives, hyphens)
tokens = re.findall(r"\b([A-Z][a-z]{2,}(?:['-][A-Z]?[a-z]+)?)\b", body)
counts = Counter(tokens)

print(f"total capitalized tokens: {len(counts)}")

# --- classify ---------------------------------------------------------------
people, filtered_places, filtered_things, filtered_common = {}, {}, {}, {}
for word, n in counts.items():
    if word in COMMON_CAP or word in KJV_VERBS or word in GROUPS or word in TITLES:
        filtered_common[word] = n
    elif word in PLACES:
        filtered_places[word] = n
    elif word in THINGS:
        filtered_things[word] = n
    else:
        people[word] = n

print(f"people candidates: {len(people)}")
print(f"filtered places:   {len(filtered_places)}")
print(f"filtered things:   {len(filtered_things)}")
print(f"filtered common:   {len(filtered_common)}")

# --- report ----------------------------------------------------------------
rep = []
rep.append("=== BIBLE NAMES EXTRACTION REPORT ===")
rep.append(f"source: {KJV}")
rep.append(f"capitalized tokens found: {len(counts)}")
rep.append(f"people candidates: {len(people)}")
rep.append("")
rep.append("--- TOP 60 PEOPLE CANDIDATES (by verse count) ---")
for w, n in sorted(people.items(), key=lambda x: -x[1])[:60]:
    rep.append(f"  {n:>5}  {w}")
rep.append("")
rep.append("--- filtered as PLACES (top 30) ---")
for w, n in sorted(filtered_places.items(), key=lambda x: -x[1])[:30]:
    rep.append(f"  {n:>5}  {w}")
rep.append("")
rep.append("--- filtered as THINGS/titles (top 20) ---")
for w, n in sorted(filtered_things.items(), key=lambda x: -x[1])[:20]:
    rep.append(f"  {n:>5}  {w}")
open(os.path.join(OUT, "report.txt"), "w").write("\n".join(rep))
print("\n".join(rep[:12]))

# --- write raw candidate list ----------------------------------------------
with open(os.path.join(OUT, "people-names.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["name", "verse_count"])
    for name, n in sorted(people.items(), key=lambda x: -x[1]):
        w.writerow([name, n])

print(f"\nwrote {OUT}/people-names.csv")
