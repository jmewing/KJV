#!/usr/bin/env python3
"""
Rough machine-generated English glosses for biblical source texts.
Reads plain-text files and emits one glossed line per verse in the style:
  '<Book> <chapter>:<verse> <glossed English>'
Supplied words/grammar are bracketed, e.g., [the], [and], [he], [was], [to].

This is explicitly a rough, machine-generated gloss for personal reference only,
not an authoritative translation.
"""

import os, re, unicodedata

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SRC_DIR, "glossed-en")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Comprehensive rough lexicons for the target sample books.
# These are intentionally literal; supplied words are bracketed.
# ---------------------------------------------------------------------------

HEB_LEX = {
    # Articles / particles
    "הַ": "the", "הָ": "the", "הֶ": "the", "הֵ": "the", "הַ֣": "the",
    "וְ": "and", "וַ": "and [so]", "וָ": "and", "וּ": "and",
    "בְּ": "in", "בָּ": "in the", "בַּ": "in the", "בֹ": "in", "ב": "in",
    "לְ": "to/for", "לָ": "to the", "לַ": "to the", "לֹ": "to", "ל": "to",
    "מִ": "from", "מֵ": "from", "מִן": "from", "מֵעַל": "from upon",
    "אֶת": "[with]", "אֵת": "[acc]", "אֹתוֹ": "him", "אֹתָם": "them",
    "אֹתָהּ": "her", "אֹתָךְ": "you [f]", "אֹתְכֶם": "you [pl]", "אֹתִי": "me",
    "אֶל": "to/toward", "עַל": "upon", "עַד": "until", "עִם": "with",
    "כִּי": "for/because/that", "כֵּן": "so", "כָּל": "all", "כֹּל": "all",
    "כַּאֲשֶׁר": "as/which", "אֲשֶׁר": "which/who/that", "אִם": "if",
    "לֹא": "not", "אַל": "not [imperative]", "אֵין": "[there is] no",
    "גַּם": "also", "רַק": "only", "עוֹד": "still/yet", "עַתָּה": "now",
    "פֹּה": "here", "שָׁם": "there", "הִנֵּה": "behold", "נָא": "please",
    "אַיֵּה": "where", "מַה": "what", "מִי": "who",

    # Pronouns
    "הוּא": "he", "הִיא": "she", "הֵם": "they", "הֵמָּה": "they",
    "אֲנִי": "I", "אָנֹכִי": "I", "אַתָּה": "you [m]", "אַתְּ": "you [f]",
    "לוֹ": "to him", "לָהּ": "to her", "לָכֶם": "to you [pl]", "לָנוּ": "to us",
    "לִי": "to me", "לְךָ": "to you", "לָהֶם": "to them",
    "בּוֹ": "in him", "בָּהּ": "in her", "בָּם": "in them", "בִּי": "in me",
    "אֵלָיו": "to him", "אֵלֶיךָ": "to you", "אֵלַי": "to me", "אֵלֶיהָ": "to her",
    "אֵלֵיהֶם": "to them",
    "עָלָיו": "upon him", "עָלֶיךָ": "upon you", "עָלַי": "upon me", "עֲלֵיהֶם": "upon them",

    # Common verbs (Qal perfect/imperfect as literal forms)
    "אָמַר": "[he] said", "וַיֹּאמֶר": "and [he] said", "וַיֹּאמְרוּ": "and they said",
    "אֹמֵר": "saying", "לֵאמֹר": "to say",
    "הָיָה": "[he] was", "הָיְתָה": "[she] was", "וַיְהִי": "and there was",
    "יִהְיֶה": "he will be", "יִהְיוּ": "they will be", "הָיוּ": "they were",
    "וְהָיָה": "and he shall be", "וַתִּהְיֶה": "and she became",
    "עָשָׂה": "[he] made/did", "וַיַּעַשׂ": "and [he] did", "וַיַּעֲשׂוּ": "and they did",
    "תַּעֲשֶׂה": "you will do", "עָשִׂיתָ": "you did", "לַעֲשׂוֹת": "to do",
    "רָאָה": "[he] saw", "וַיַּרְא": "and [he] saw", "וַיִּרְאוּ": "and they saw",
    "הָלַךְ": "[he] walked", "וַיֵּלֶךְ": "and [he] went", "הֹלֵךְ": "walking",
    "בָּא": "[he] came", "וַיָּבֹא": "and [he] came", "וַיָּבֹאוּ": "and they came",
    "יָצָא": "[he] went out", "וַיֵּצֵא": "and [he] went out", "יוֹצְאֵי": "those going out of",
    "נָתַן": "[he] gave", "וַיִּתֵּן": "and [he] gave", "תִּתֵּן": "you will give",
    "לָקַח": "[he] took", "וַיִּקַּח": "and [he] took", "קָח": "take",
    "יָלַד": "[he] begat", "וַיּוֹלֶד": "and [he] begat", "וַתֵּלֶד": "and she bore",
    "קָרָא": "[he] called", "וַיִּקְרָא": "and [he] called", "קְרָא": "call",
    "שָׂם": "[he] put", "וַיָּשֶׂם": "and [he] put", "שִׁית": "to put",
    "דִּבֶּר": "[he] spoke", "וַיְדַבֵּר": "and [he] spoke", "דְּבַר": "word/speak",
    "שָׁמַע": "[he] heard", "שְׁמַע": "hear", "וַיִּשְׁמַע": "and [he] heard",
    "יָדַע": "[he] knew", "יָדַעְתִּי": "I know", "וַיֵּדַע": "and [he] knew",
    "חָיָה": "[he] lived", "וַיְחִי": "and [he] lived", "חַי": "alive",
    "מָת": "[he] died", "וַיָּמָת": "and [he] died", "מֵת": "dead",
    "עָלָה": "[he] went up", "עָשָׂה": "[he] made", "בָּנָה": "[he] built",
    "שָׁחַט": "[he] slaughtered", "עָבַר": "[he] passed over",
    "פָּתַח": "[he] opened", "סָגַר": "[he] closed", "מָלֵא": "[he] was full",
    "יָצַר": "[he] formed", "בָּרָא": "[he] created", "בָּרָאֲךָ": "created you",

    # Genesis core
    "בְּרֵאשִׁית": "in [the] beginning", "אֱלֹהִים": "God", "אֱלֹהֵי": "God of",
    "שָׁמַיִם": "heavens", "הַשָּׁמַיִם": "the heavens", "אָרֶץ": "earth", "הָאָרֶץ": "the earth",
    "תֹהוּ": "formlessness", "בֹהוּ": "void", "וָבֹהוּ": "and void",
    "חֹשֶׁךְ": "darkness", "הַחֹשֶׁךְ": "the darkness", "אוֹר": "light", "הָאוֹר": "the light",
    "פְּנֵי": "[the] face of", "עַל־פְּנֵי": "upon [the] face of", "תְהוֹם": "[the] deep",
    "רוּחַ": "spirit/wind", "מְרַחֶפֶת": "hovering", "מַיִם": "water(s)", "הַמַּיִם": "the waters",
    "יוֹם": "day", "יְמוֹם": "by day", "לַיְלָה": "night", "עֶרֶב": "evening", "בֹקֶר": "morning",
    "אֶחָד": "one", "שֵׁנִי": "second", "שְׁלִישִׁי": "third", "רְבִיעִי": "fourth",
    "חֲמִישִׁי": "fifth", "שִׁשִּׁי": "sixth", "שְׁבִיעִי": "seventh",
    "בֵּין": "between", "וּבֵין": "and between",
    "טוֹב": "good", "רַע": "evil/bad",
    "זָכָר": "male", "נְקֵבָה": "female", "פְּרוּ": "be fruitful", "רְבוּ": "multiply",
    "וַיִּשְׁרְצוּ": "and they swarmed", "וַיִּרְבּוּ": "and they multiplied",
    "וַיַּעַצְמוּ": "and they grew strong", "בִּמְאֹד": "very much", "מְאֹד": "very",
    "שֶׁמֶשׁ": "sun", "יָרֵחַ": "moon", "כּוֹכָבִים": "stars",
    "דָּגִים": "fish", "עוֹף": "birds", "בְּהֵמָה": "cattle", "חַיָּה": "living thing",
    "אָדָם": "man/mankind", "הָאָדָם": "the man", "אֲדָמָה": "ground", "מִן־הָאֲדָמָה": "from the ground",
    "צַלְמוֹ": "his image", "דְּמוּת": "likeness", "בְּרָאם": "he created them",
    "גַּן־עֵדֶן": "garden of Eden", "עֵדֶן": "Eden", "עֵץ": "tree", "עֲצֵי": "trees of",
    "נָהָר": "river", "פִּישׁוֹן": "Pishon", "גִּיחוֹן": "Gihon", "חִדֶּקֶל": "Hiddekel", "פְּרָת": "Euphrates",
    "חַוָּה": "Eve", "קַיִן": "Cain", "הֶבֶל": "Abel", "שֵׁת": "Seth", "אֱנוֹשׁ": "Enosh",
    "נֹחַ": "Noah", "הַמַּבּוּל": "the flood", "תֵּבָה": "ark",
    "אַבְרָם": "Abram", "אַבְרָהָם": "Abraham", "שָׂרָי": "Sarai", "שָׂרָה": "Sarah",
    "יִצְחָק": "Isaac", "רִבְקָה": "Rebekah", "יַעֲקֹב": "Jacob", "עֵשָׂו": "Esau",
    "לֵאָה": "Leah", "רָחֵל": "Rachel", "לָבָן": "Laban",
    "יוֹסֵף": "Joseph", "בִּנְיָמִן": "Benjamin", "יְהוּדָה": "Judah",
    "רְאוּבֵן": "Reuben", "שִׁמְעוֹן": "Simeon", "לֵוִי": "Levi",
    "יִשָּׂשכָר": "Issachar", "זְבוּלוּן": "Zebulun", "דָּן": "Dan",
    "נַפְתָּלִי": "Naphtali", "גָּד": "Gad", "אָשֵׁר": "Asher",
    "בְּנֵי": "sons of", "בֵּן": "son", "בַּת": "daughter", "בָּנִים": "sons",
    "אָב": "father", "אֵם": "mother", "אָח": "brother", "אָחוֹת": "sister",
    "אִישׁ": "man", "אִשָּׁה": "woman", "אֲנָשִׁים": "men", "נָשִׁים": "women",
    "מֶלֶךְ": "king", "מַמְלָכָה": "kingdom", "גּוֹי": "nation", "גּוֹיִם": "nations",
    "פַּרְעֹה": "Pharaoh", "מִצְרַיִם": "Egypt", "כְּנַעַן": "Canaan",
    "שָׁנָה": "year", "שָׁנִים": "years",
    "אֶרֶץ": "land", "בְּאֶרֶץ": "in [the] land", "בָּאָרֶץ": "in the land",
    "מֵאֶרֶץ": "from [the] land", "אֶל־הָאָרֶץ": "to the land",
    "מַיִם": "waters", "יָם": "sea", "הַיָּם": "the sea",
    "שָׁמַיִם": "heavens", "הַשָּׁמַיִם": "the heavens",
    "אֹהֶל": "tent", "מִשְׁכָּן": "tabernacle", "מִזְבֵּחַ": "altar",
    "קֹדֶשׁ": "holy", "קְדֹשִׁים": "holy ones", "טָהוֹר": "pure", "טָמֵא": "impure",

    # Exodus core
    "שְׁמוֹת": "names", "וְאֵלֶּה": "and these", "אֵלֶּה": "these",
    "בָּאוּ": "they came", "הַבָּאִים": "the ones coming",
    "בֵּית": "house of", "בָּנָיו": "his sons", "מִשְׁפְּחֹת": "families",
    "שִׁבְעִים": "seventy", "נֶפֶשׁ": "soul/life", "נְפָשׁוֹת": "souls/lives",
    "כָּל־הַנֶּפֶשׁ": "all the soul/life", "הַדּוֹר": "the generation",
    "מֹשֶׁה": "Moses", "אַהֲרֹן": "Aaron",
    "עֶבֶד": "servant", "עֲבָדִים": "servants", "עֲבוֹדָה": "service/work",
    "פֶּסַח": "Passover", "מַצּוֹת": "unleavened bread",
    "סֵפֶר": "book", "דְּבָרִים": "words/things", "הַדְּבָרִים": "the words/things",
    "חָצֵר": "court", "הֶחָצֵר": "the court",
    "מִדְבָּר": "wilderness", "בַּמִּדְבָּר": "in the wilderness",
    "שְׁבָטִים": "tribes", "שִׁבְטֵי": "tribes of",

    # Psalms core
    "מִזְמוֹר": "psalm", "לַמְנַצֵּחַ": "to the choir-master",
    "אַשְׁרֵי": "happy/blessed [is]", "הָאִישׁ": "the man",
    "רְשָׁעִים": "wicked ones", "חַטָּאִים": "sinners", "לֵצִים": "scorners",
    "תּוֹרַת": "law of", "תּוֹרָתוֹ": "his law", "חֶפְצוֹ": "his delight",
    "יֶהְגֶּה": "he meditates", "דֶּרֶךְ": "way of", "אֲרָחוֹת": "paths",
    "עֵץ": "tree", "שָׁתוּל": "planted", "פַּלְגֵי": "channels of",
    "פִּרְיוֹ": "its fruit", "בְּעִתּוֹ": "in its season", "עָלֵהוּ": "its leaf",
    "יִבּוֹל": "it withers", "יַצְלִיחַ": "prospers", "יִתֵּן": "it gives",
    "כַּמֹּץ": "like chaff", "תִּדְּפֶנּוּ": "drives it", "רוּחַ": "wind/spirit",
    "עַל־כֵּן": "therefore", "יָקוּמוּ": "they will stand/rise",
    "מִשְׁפָּט": "judgment", "עֲדַת": "congregation of", "צַדִּיקִים": "righteous ones",
    "צַדִּיק": "righteous one", "רָשָׁע": "wicked one",
    "יוֹדֵעַ": "[he] knows", "תֹּאבֵד": "she will perish",
    "יְהוָה": "YHWH/[the] LORD", "יָהּ": "Yah", "לַיהוָה": "to YHWH",
    "לֵב": "heart", "לִבִּי": "my heart", "נֶפֶשׁ": "soul",
    "שִׁיר": "song", "זִמְרָה": "song", "תְּהִלָּה": "praise",
    "הַלְלוּ": "praise [ye]", "הַלְלוּיָהּ": "hallelujah/praise Yah",
    "צוּר": "rock", "מָגֵן": "shield", "מִשְׂגַּב": "stronghold",
    "חֶסֶד": "loyal-love/mercy", "אֱמֶת": "truth", "צֶדֶק": "righteousness",
    "מִשְׁפָּט": "justice/judgment",

    # Numbers/nouns
    "אֶחָד": "one", "שְׁנַיִם": "two", "שָׁלֹשׁ": "three", "אַרְבַּע": "four",
    "חָמֵשׁ": "five", "שֵׁשׁ": "six", "שִׁבְעַת": "seven", "שְׁמוֹנָה": "eight",
    "תֵּשַׁע": "nine", "עֲשָׂרָה": "ten", "עֶשְׂרֵה": "fifteen", "עֶשְׂרִים": "twenty",
    "שְׁלֹשִׁים": "thirty", "אַרְבָּעִים": "forty", "חֲמִשִּׁים": "fifty",
    "מֵאוֹת": "hundreds", "אֶלֶף": "thousand",
    "אַחַת": "one [f]", "שְׁנֵי": "two of", "שְׁתֵּי": "two [f]",
    "שְׁלֹשָׁה": "three [m]", "אַרְבָּעָה": "four [m]", "חֲמֵשֶׁת": "five of",
    "שִׁבְעָה": "seven [m]", "עֲשָׂרָה": "ten [m]", "שִׁבְעִים": "seventy",
    "שְׁמוֹנִים": "eighty", "תְּשָׁעִים": "ninety", "מֵאָה": "hundred",
    "אֲלָפִים": "thousands", "רְבָבָה": "myriad/ten-thousand",
    "מִלְיוֹן": "thousand", "מִלְיוֹנֵי": "thousands of",

    # Adjectives
    "גָּדוֹל": "great", "קָטֹן": "small", "רַב": "many/much", "רַבִּים": "many",
    "טוֹב": "good", "רַע": "bad", "יָשָׁר": "straight/just",
    "חָכָם": "wise", "חָסִיד": "pious/loyal", "עָנִי": "poor", "אֶבְיוֹן": "needy",
    "גִּבּוֹר": "mighty", "קָדוֹשׁ": "holy",

    # Prepositions / adverbs
    "בְּתוֹךְ": "in the midst of", "תּוֹךְ": "midst of", "בֵּין": "between",
    "תַּחַת": "under", "מֵעַל": "from upon", "מִתַּחַת": "from under",
    "לִפְנֵי": "before", "מִפְּנֵי": "from before", "אַחֲרֵי": "after",
    "לְמַעַן": "for the sake of", "בַּעֲבוּר": "for the sake of", "עֵקֶב": "because of",
    "אַךְ": "only/however", "כֹּה": "thus", "פֹּה": "here",
    "לְעוֹלָם": "forever", "עוֹלָם": "eternity/forever",

    # Divine / names
    "אֱלֹהֵינוּ": "our God", "אֱלֹהֵי": "God of", "לֵאלֹהִים": "to God",
    "אֲדֹנָי": "my Lord", "אֲדֹנָי־יְהוִה": "Lord YHWH",
    "צְבָאוֹת": "of hosts", "עֶלְיוֹן": "Most High", "עוֹשֵׂה": "maker of",

    # Additional frequent tokens seen in freq list
    "הַזֶּה": "this", "זֶה": "this", "הַזֹּאת": "this", "זֹאת": "this",
    "הַהוּא": "that", "הִוא": "she", "הוּא": "he",
    "הַיּוֹם": "today", "בַּיּוֹם": "in the day", "בְּיוֹם": "in [the] day",
    "הָעָם": "the people", "עַם": "people", "עַמִּי": "my people", "עַמִּים": "peoples",
    "שֵׁם": "name", "שְׁמִי": "my name", "שִׁמְךָ": "your name",
    "יָד": "hand", "יָדוֹ": "his hand", "יָדְךָ": "your hand", "מִיַּד": "from hand of",
    "קוֹל": "voice", "רֹאשׁ": "head", "בֵּית": "house of", "בַּיִת": "house",
    "שָׂדֶה": "field", "הַשָּׂדֶה": "the field", "צֹאן": "flock", "הַצֹּאן": "the flock",
    "לֶחֶם": "bread", "זָהָב": "gold", "כֶּסֶף": "silver", "נְחֹשֶׁת": "bronze/copper",
    "שִׁטִּים": "acacia", "מוֹעֵד": "appointed time/tent of meeting",
    "כָּבוֹד": "glory/honor", "חֵן": "grace", "שָׁלוֹם": "peace",
    "אֶמֶת": "truth", "צֶדֶק": "righteousness", "מִשְׁפָּט": "justice",
    "חָסִיד": "loyal/pious", "חַסְדְּךָ": "your lovingkindness",
    "פָּנִים": "face", "פָּנֶיךָ": "your face",
    "נַפְשִׁי": "my soul", "נַפְשׁוֹ": "his soul", "לְנַפְשֵׁנוּ": "for our soul",

    # Proper nouns in Psalms / Genesis / Exodus
    "דָּוִד": "David", "לְדָוִד": "to/for David",
    "שְׁלֹמֹה": "Solomon", "מֹשֶׁה": "Moses", "אַהֲרֹן": "Aaron",
    "אֲבִיגַיִל": "Abigail", "מְרִיָם": "Miriam",

    # Batch 2 additions (Leviticus, Numbers, Deuteronomy)
    "אֲשֶׁר": "which/who/that", "כַּאֲשֶׁר": "as/which", "כָּל": "all", "כֹל": "all",
    "וְאֶת": "and [with/acc]", "וְאֵת": "and [with/acc]", "וְכָל": "and all",
    "וְכֹל": "and all", "וְלֹא": "and not", "וְאִם": "and if", "וְעַל": "and upon",
    "וְאֶל": "and to", "וְאָמַרְתָּ": "and you shall say", "וְכִי": "and if/when",
    "וְהִנֵּה": "and behold", "וְנָתַן": "and he will give", "וְהָיוּ": "and they shall be",
    "וְעַד": "and until", "וְכִפֶּר": "and he shall atone", "וְלָקַח": "and he shall take",
    "וְאַהֲרֹן": "and Aaron", "וַיֹּאמֶר": "and [he] said", "וַיְדַבֵּר": "and [he] spoke",
    "וַיִּסְעוּ": "and they journeyed", "וַיַּחֲנוּ": "and they encamped",
    "וַיִּקַּח": "and [he] took", "וַיַּעַל": "and [he] went up",
    "וַתִּהְיֶה": "and she/it was", "אוֹ": "or", "פֶּן": "lest",
    "אַתָּה": "you [m]", "אַתֶּם": "you [pl]", "לָךְ": "to you [f]",
    "אֶתְכֶם": "you [pl]", "אֱלֹהֶיךָ": "your God", "אֱלֹהֵיכֶם": "your God [pl]",
    "אֹתָם": "them", "אֲלֵהֶם": "to them", "לִבְנֵי": "to/for sons of", "לְכָל": "to all",
    "מֵאֵת": "from with", "מִכָּל": "from all", "מִתּוֹךְ": "from the midst of",
    "מִמֶּנּוּ": "from him/it", "מִבֶּן": "from a son", "בְּכָל": "in all",
    "בְּיוֹם": "in [the] day", "בַּיּוֹם": "in the day", "בְּאֹהֶל": "in [the] tent",
    "בְּאֶרֶץ": "in [the] land", "בַּמִּדְבָּר": "in the wilderness", "בְּלוּלָה": "mixed",
    "הַזֶּה": "this", "הַזֹּאת": "this", "הָאֵלֶּה": "these", "הָעֵדָה": "the congregation",
    "הַכֹּהֵן": "the priest", "הַלְוִיִּם": "the Levites", "הַקֹּדֶשׁ": "the holy [place/thing]",
    "הַמִּזְבֵּחַ": "the altar", "הַמִּזְבֵּחָה": "to the altar", "הַמִּשְׁכָּן": "the tabernacle",
    "הַנֶּגַע": "the plague/stroke", "הָעֹלָה": "the burnt offering", "הַחַטָּאת": "the sin offering",
    "הַשְּׁלָמִים": "the peace offerings", "הָעֶרֶב": "the evening", "הַדָּם": "the blood",
    "הַדָּבָר": "the word/thing", "הָאֶחָד": "the one", "הָאֲדָמָה": "the ground",
    "הָאֵשׁ": "the fire", "הַמָּקוֹם": "the place", "הַיַּרְדֵּן": "the Jordan",
    "הַהִוא": "that", "הַתּוֹרָה": "the law", "חֲמִשָּׁה": "five",
    "שִׁבְעַת": "seven [construct]", "שְׁנַיִם": "two", "עֶשְׂרִים": "twenty",
    "שְׁלֹשִׁים": "thirty", "אַחַת": "one [f]", "עָשָׂר": "ten [m]", "שְׁנֵי": "two of",
    "מִשְׁפַּחַת": "family of", "מִשְׁפְּחֹת": "families of", "לְמִשְׁפְּחֹתָם": "to their families",
    "צִוָּה": "[he] commanded", "נֹתֵן": "giving", "נָתַתִּי": "I have given",
    "דִּבֶּר": "[he] spoke", "דַּבֵּר": "speak!", "תִּהְיֶה": "she/you will be",
    "תַּעֲשׂוּ": "you [pl] shall do", "תַּעֲשֶׂה": "you shall do",
    "יַקְרִיב": "he will offer", "תַּקְרִיבוּ": "you [pl] shall offer",
    "יִטְמָא": "he will become impure", "יָבֹא": "he will come",
    "קָרְבָּנוֹ": "his offering", "לְרִשְׁתָּהּ": "to possess it",
    "לְעֹלָה": "for a burnt offering", "לְחַטָּאת": "for a sin offering",
    "לְמַטֵּה": "to/for tribe of", "לֵּאמֹר": "to say", "לְבֵית": "to/for house of",
    "לַמַּחֲנֶה": "to the camp", "בֶּן": "son of", "בְנֵי": "sons of",
    "בָּקָר": "cattle/oxen", "צֹאן": "flock", "עִזִּים": "goats", "כְּבָשִׂים": "lambs",
    "סֹלֶת": "fine flour", "נִיחֹחַ": "soothing aroma", "מִנְחָה": "grain offering",
    "מוֹאָב": "Moab", "בִּלְעָם": "Balaam", "בָּלָק": "Balak", "אֶלְעָזָר": "Eleazar",
    "כֶּסֶף": "silver", "זָהָב": "gold", "נְחֹשֶׁת": "bronze/copper",
    "פֶּתַח": "door/opening", "פִּי": "mouth of", "שָׁמָּה": "there",
    "מִחוּץ": "from outside", "עָלֶיהָ": "upon her/it", "בָּהּ": "in her/it", "בוֹ": "in him/it",
    "אֲבֹתָם": "their fathers", "וְאִישׁ": "and a man", "בְּגָדָיו": "his garments",
    "אִשֶּׁה": "fire offering", "אִשָּׁה": "woman/wife", "עוֹלָה": "burnt offering",
    "פַּר": "bull", "מַטֵּה": "tribe/staff", "חַטָּאת": "sin offering", "קָרְבָּן": "offering",
    "מוֹעֵד": "appointed time/tent of meeting", "נָחַל": "inheritance",
    "יְרִשְׁתֶּם": "you shall possess them", "נַחֲלָה": "inheritance",
    "גְּבוּל": "border", "עָרִים": "cities", "מִדְבָּר": "wilderness", "מַחֲנֶה": "camp",
    "יְהוֹשֻׁעַ": "Joshua", "כָּלֵב": "Caleb", "שָׁלוֹם": "peace", "מִלְחָמָה": "war",
    "עָנָן": "cloud", "נָסַע": "[he] journeyed", "חָנָה": "[he] encamped", "נָטָה": "[he] stretched",
    "הֵנִיחַ": "[he] caused to rest", "הִקְרִיב": "[he] offered", "הִקְטִיר": "[he] burned incense",
    "זָרַק": "[he] threw", "לָבַשׁ": "[he] clothed", "הִתְיַצֵּב": "stand [yourself]!",
    "הַרְאֵשׁ": "show!",
}

GRC_LEX = {
    # Articles
    "ο": "the [nom m]", "η": "the [nom f]", "το": "the [nom/acc n]",
    "του": "of the [gen]", "τησ": "of the [gen f]", "τω": "to the [dat]",
    "τη": "to the [dat f]", "τον": "the [acc m]", "την": "the [acc f]",
    "τοι": "the [nom pl m]", "ται": "the [nom pl f]", "τα": "the [nom/acc pl n]",
    "των": "of the [gen pl]", "τοισ": "to the [dat pl m]", "ταισ": "to the [dat pl f]",
    "τουσ": "the [acc pl m]", "τασ": "the [acc pl f]",

    # Conjunctions / particles
    "και": "and", "δε": "but/and", "γαρ": "for", "ουν": "therefore",
    "ει": "if", "εαν": "if", "ινα": "so that", "οτι": "that/because",
    "ωσ": "as", "καθωσ": "just as", "ωσει": "as/like",
    "οπου": "where", "οτε": "when", "εωσ": "until",
    "αλλα": "but", "αλλ": "but", "μη": "not", "ου": "not", "ουκ": "not",
    "ουχ": "not", "μεν": "indeed", "δε": "but", "τε": "and/both",
    "η": "or", "ειτε": "whether", "ουτε": "neither", "μητε": "neither",
    "γε": "indeed", "τοι": "surely", "περ": "indeed",

    # Prepositions
    "εν": "in", "εισ": "into/for", "εκ": "from/out of", "εξ": "from/out of",
    "απο": "from", "προσ": "toward", "επι": "upon", "υπερ": "for/over",
    "υπο": "by/under", "δια": "through/for", "μετα": "with/after",
    "κατα": "according to/down", "ανα": "up", "περι": "around/concerning",
    "παρα": "from/beside", "χωρισ": "apart from", "αντι": "instead of",
    "εναντιον": "before", "μεθ": "with",
    "επ": "upon", "παρ": "beside", "κατ": "according to", "δι": "through",
    "απ": "from", "ανθ": "instead of", "υφ": "under",

    # Pronouns
    "αυτου": "of him/his", "αυτων": "of them/their", "αυτω": "to him",
    "αυτον": "him", "αυτοισ": "to them", "αυτουσ": "them",
    "αυτησ": "of her/her", "αυτη": "she/her", "αυτην": "her",
    "αυτο": "it", "αυτος": "he", "αυτοι": "they",
    "σου": "of you/your", "σοι": "to you", "σε": "you",
    "μου": "of me/my", "μοι": "to me", "με": "me",
    "ημων": "of us/our", "ημιν": "to us", "ημασ": "us",
    "υμων": "of you/your [pl]", "υμιν": "to you [pl]", "υμασ": "you [pl]",
    "εμου": "of me", "εμε": "me", "εσυ": "you",
    "τισ": "who?", "τι": "what?", "ουτοσ": "this one", "εκεινοσ": "that one",
    "οσ": "whoever/which", "οσοι": "as many as", "οσα": "as many things",
    "αλληλων": "of one another",

    # Common verbs
    "εστιν": "[he/she/it] is", "ειμι": "I am", "ει": "you are", "εστε": "you are [pl]",
    "εισιν": "they are", "ην": "was", "ησαν": "they were", "εσονται": "they will be",
    "γινομαι": "I become", "γινεται": "it becomes", "εγενετο": "it came to be",
    "εγεννησεν": "he begat", "γεννα": "he begets", "εγεννήθησαν": "they were begotten",
    "εγεννηθη": "was begotten", "γενομενου": "having come to be",
    "εποιησεν": "he made", "ποιεω": "I do/make", "εποιησαν": "they made",
    "ειπεν": "he said", "λεγω": "I say", "λεγει": "he says", "λεγοντοσ": "saying",
    "ειπα": "I said", "ερεω": "I will say",
    "ορω": "I see", "ειδεν": "he saw", "οψεται": "he will see",
    "ακουω": "I hear", "ηκουσεν": "he heard", "ακουσατε": "hear [pl]",
    "πορευομαι": "I go", "επορευθη": "he went", "πορευου": "go",
    "ερχομαι": "I come", "ηλθεν": "he came", "ελθειν": "to come",
    "λαμβανω": "I take", "ελαβεν": "he took", "ελαβομεν": "we received",
    "λαβε": "take", "παραλαβειν": "to take",
    "διδωμι": "I give", "εδωκεν": "he gave", "εδωκαν": "they gave",
    "δωσει": "he will give", "διδωσιν": "he gives",
    "γινωσκω": "I know", "εγνω": "he knew", "γινωσκει": "he knows",
    "πιστευω": "I believe", "πιστευσωσιν": "they might believe", "πιστευοντι": "believing",
    "πιστευουσιν": "they believe",
    "αποστελλω": "I send", "απεσταλμενοσ": "sent",
    "αποθνησκω": "I die", "απεθανεν": "he died",
    "ζαω": "I live", "ζη": "he lives", "ζωη": "life",
    "θελω": "I want", "ηθελησεν": "he wanted",
    "δυναμαι": "I am able", "ηδυνατο": "he was able",
    "εχω": "I have", "ειχεν": "he had", "εχει": "he has",
    "ευρισκω": "I find", "ευρεθη": "was found",
    "ποιεω": "I do", "εποιησεν": "he did", "ποιησωσιν": "they might do",
    "κατευοδομαι": "I prosper", "κατευοδωθησεται": "will prosper",
    "διχαζω": "I separate", "διεχωρισεν": "he separated",
    "καλεω": "I call", "εκαλεσεν": "he called", "εκαλεσαν": "they called",
    "καλεσεισ": "you shall call", "καλεσουσιν": "they shall call",
    "απερχομαι": "I go away", "απηλθεν": "he went away",
    "σωζω": "I save", "σωσει": "he will save", "σωτηριαν": "salvation",
    "αγαπαω": "I love", "ηγαπησεν": "he loved", "αγαπη": "love",
    "δοξαζω": "I glorify", "δοξαν": "glory", "δοξα": "glory",
    "αμαρτανω": "I sin", "αμαρτια": "sin", "αμαρτιων": "of sins",
    "αφιημι": "I forgive/leave", "αφες": "forgive/leave",
    "κρινω": "I judge", "κρισισ": "judgment",
    "βαπτιζω": "I baptize", "βαπτιζειν": "to baptize",
    "διδασκω": "I teach", "εδιδασκεν": "he was teaching",
    "θεραπευω": "I heal", "εθεραπευσεν": "he healed",
    "πειραζω": "I tempt/test", "επειρασεν": "he tested",
    "προσευχομαι": "I pray", "προσευχη": "prayer",
    "νικαω": "I conquer", "νικη": "victory",

    # Divine / nouns
    "θεοσ": "God", "θεου": "of God", "θεῳ": "to God", "θεον": "God [acc]",
    "κυριοσ": "Lord", "κυριου": "of [the] Lord", "κυριε": "O Lord",
    "κυριον": "[the] Lord [acc]", "κυριω": "to [the] Lord",
    "πνευμα": "spirit/wind", "πνευματοσ": "of spirit", "πνευματι": "in spirit",
    "αγιοσ": "holy", "αγιου": "of holy", "αγιων": "of holy ones",
    "αγιωσυνησ": "of holiness",
    "χριστοσ": "Christ", "χριστου": "of Christ", "χριστω": "to Christ",
    "ιησουσ": "Jesus", "ιησου": "of Jesus", "ιησουν": "Jesus [acc]",
    "λογοσ": "word", "λογου": "of word", "λογον": "word [acc]",
    "φωσ": "light", "φωτοσ": "of light", "σκοτια": "darkness",
    "σκοτοσ": "darkness",
    "κοσμοσ": "world", "κοσμου": "of world", "κοσμον": "world [acc]",
    "ουρανοσ": "heaven", "ουρανον": "heaven [acc]", "ουρανων": "of heavens",
    "γη": "earth", "γησ": "of earth", "γην": "earth [acc]",
    "υδωρ": "water", "υδατοσ": "of water", "υδατα": "waters",
    "ημερα": "day", "ημερασ": "of day", "ημεραι": "days",
    "νυξ": "night", "εσπερα": "evening", "πρωι": "morning",
    "αβυσσοσ": "abyss", "αβυσσου": "of abyss",
    "ανθρωποσ": "man", "ανθρωπου": "of man", "ανθρωπον": "man [acc]",
    "ανθρωποι": "men", "ανθρωπων": "of men",

    # People / names (Greek forms)
    "αδαμ": "Adam", "σηθ": "Seth", "ενωσ": "Enosh", "καιναν": "Kenan",
    "μαλελεηλ": "Mahalaleel", "ιαρεδ": "Jared", "ενωχ": "Enoch",
    "μαθθουσαλα": "Methuselah", "λαμεχ": "Lamech", "νωε": "Noah",
    "σημ": "Shem", "χαμ": "Ham", "ιαφεθ": "Japheth",
    "αβρααμ": "Abraham", "ισαακ": "Isaac", "ιακωβ": "Jacob", "ιουδασ": "Judah",
    "δαβιδ": "David", "δαυειδ": "David",
    "ιωσηφ": "Joseph", "μαριαμ": "Mary", "μαριασ": "of Mary",
    "ιωαννησ": "John", "παυλοσ": "Paul", "πετροσ": "Peter",
    "παρεσ": "Perez", "ζαρα": "Zerah", "εσρωμ": "Hezron", "αραμ": "Aram",
    "αμιναδαβ": "Amminadab", "ναασσων": "Nahshon", "σαλμων": "Salmon",
    "βοοζ": "Boaz", "ωβηδ": "Obed", "ιεσσαι": "Jesse",
    "σολομων": "Solomon", "ουριασ": "Uriah", "ροβοαμ": "Rehoboam",
    "αβια": "Abijah", "ασα": "Asa", "ιωσαφατ": "Jehoshaphat", "ιωραμ": "Joram",
    "οζιασ": "Uzziah", "ιωαθαμ": "Jotham", "αχαζ": "Ahaz", "εζεκιασ": "Hezekiah",
    "μανασσησ": "Manasseh", "αμωσ": "Amon", "ιωσιασ": "Josiah",
    "ιεχονιασ": "Jeconiah", "σαλαθιηλ": "Shealtiel", "ζοροβαβελ": "Zerubbabel",
    "αβιουδ": "Abiud", "ελιακιμ": "Eliakim", "αζωρ": "Azor", "σαδωκ": "Zadok",
    "αχιμ": "Achim", "ελιουδ": "Eliud", "ελεαζαρ": "Eleazar", "ματθαν": "Matthan",
    "ιωσηφ": "Joseph",
    "ραχαβ": "Rahab", "ρουθ": "Ruth", "θαμαρ": "Tamar",
    "φαραω": "Pharaoh", "ισραηλ": "Israel",

    # Family nouns
    "υιοσ": "son", "υιου": "of son", "υιον": "son [acc]", "υιοι": "sons",
    "θυγατηρ": "daughter", "πατηρ": "father", "μητηρ": "mother",
    "αδελφοσ": "brother", "αδελφοι": "brothers", "αδελφων": "of brothers",
    "γυνη": "woman/wife", "γυναικα": "woman/wife [acc]",
    "τεκνον": "child", "τεκνα": "children",

    # Gospel of John / Romans
    "βιβλοσ": "book", "γενεσεωσ": "of genealogy/origin",
    "αρχη": "beginning", "εν": "in", "προσ": "toward", "αληθινοσ": "true",
    "αληθεια": "truth", "χαρισ": "grace/gift", "χαριτοσ": "of grace",
    "χαριν": "grace", "χαρισμα": "gift",
    "εξουσια": "authority", "εξουσιαν": "authority [acc]",
    "δοξαν": "glory",
    "μονογενησ": "only-begotten", "μονογενουσ": "of [the] only-begotten",
    "πατηρ": "father", "πατροσ": "of father", "πατρι": "to father",
    "σαρξ": "flesh", "σαρκοσ": "of flesh", "σαρκα": "flesh [acc]",
    "αιμα": "blood", "αιματων": "of bloods", "σπερματοσ": "of seed",
    "ανδροσ": "of man", "βουληματοσ": "of will", "θεληματοσ": "of will",
    "δουλοσ": "slave/servant", "κλητοσ": "called", "αποστολοσ": "apostle",
    "αφωρισμενοσ": "set apart", "ευαγγελιον": "gospel",
    "προεπηγγειλατο": "he promised beforehand", "προφητων": "of prophets",
    "γραφων": "of scriptures", "αγιων": "of holy ones",
    "ορισθεντοσ": "having been marked out", "δυναμει": "in power",
    "αναστασεωσ": "of resurrection", "νεκρων": "of dead ones",
    "χαριν": "grace", "αποστολην": "apostleship", "υπακοην": "obedience",
    "πιστεωσ": "of faith", "εθνεσιν": "to nations", "ονοματοσ": "of name",
    "ρώμη": "Rome", "αγαπητοισ": "beloved", "αγιοισ": "holy ones",
    "ειρηνη": "peace", "πατροσ": "of father", "ημων": "our",
    "ευχαριστω": "I thank", "δι": "through", "παντων": "of all",
    "πιστισ": "faith", "καταγγελλεται": "is proclaimed",
    "ολω": "whole", "μαρτυσ": "witness", "λατρευω": "I serve",
    "μνειαν": "remembrance", "ποιουμαι": "I make", "παντοτε": "always",
    "προσευχαισ": "prayers", "δεομενοσ": "beseeching", "πωσ": "somehow",
    "ηδη": "already", "ποτε": "at last", "ευοδοθησομαι": "I shall succeed",
    "θεληματι": "will", "επιποθω": "I long", "ιδειν": "to see",
    "μεταδω": "I might impart", "πνευματικον": "spiritual",
    "στηριχθηναι": "to be established", "συμπαρακληθηναι": "to be encouraged together",
    "αλληλοισ": "one another", "θελω": "I want", "αγνοειν": "to be ignorant",
    "αδελφοι": "brothers", "πολλακισ": "many times", "προεθεμην": "I purposed",
    "εκωλυθην": "I was hindered", "αχρι": "until", "δευρο": "now",
    "καρπον": "fruit", "σχω": "I might have", "λοιποισ": "remaining",
    "ελλησιν": "to Greeks", "βαρβαροισ": "to barbarians", "σοφοισ": "to wise",
    "ανοητοισ": "to foolish", "οφειλετησ": "debtor", "ειμι": "I am",
    "ουτωσ": "so", "προθυμον": "ready/eager", "ευαγγελισασθαι": "to preach the gospel",
    "επαισχυνομαι": "I am ashamed of", "δυναμισ": "power",
    "σωτηριαν": "salvation", "παντι": "to every", "ιουδαιω": "to [the] Jew",
    "ελληνι": "to [the] Greek", "δικαιοσυνη": "righteousness",
    "αποκαλυπτεται": "is revealed", "γεγραπται": "it has been written",
    "δικαιοσ": "righteous one", "ζησεται": "will live",
}

EXTRA_GRC = {
    "αιων": "age/eternity", "αιωνα": "age/eternity [acc]", "αιωνοσ": "of age/eternity",
    "αιωνιον": "eternal", "αιωνιοσ": "eternal",
    "εγω": "I", "συ": "you", "υμεισ": "you [pl]", "ημεισ": "we",
    "αμην": "amen", "ιδου": "behold", "νυν": "now", "ουν": "therefore",
    "παλιν": "again", "ευθεωσ": "immediately", "εξω": "outside",
    "εδεν": "he bound", "δεν": "he bound [?]", "εδοξεν": "it seemed",
    "ειπον": "they said", "ελεγον": "they were saying", "λεγοντεσ": "saying [pl]",
    "απεκριθη": "he answered", "αποκριθεισ": "having answered",
    "ερχεται": "he comes", "ηλθον": "they came", "εισηλθεν": "he entered",
    "εξηλθεν": "he went out", "εξαπεστειλεν": "he sent out",
    "ελθων": "having come", "εληλυθεν": "he has come",
    "τεκεν": "she bore", "εγεννησα": "I begat", "γεννησαι": "to beget",
    "γενε": "race/family", "γενοσ": "race", "γενεα": "generation",
    "γενηθη": "let there be", "γενησεται": "it will become",
    "γεγονεν": "has happened", "γενοντο": "they became",
    "μαθηται": "disciples", "μαθηταισ": "to disciples", "μαθητων": "of disciples",
    "προβατα": "sheep", "προβατων": "of sheep", "κτηνων": "of cattle",
    "ποδασ": "feet", "χειρασ": "hands", "χειρων": "of hands",
    "χειρα": "hand [acc]", "στομα": "mouth", "οφθαλμουσ": "eyes",
    "οφθαλμο": "eye", "οφθαλμοισ": "to eyes",
    "ουρανο": "heaven", "ουρανοισ": "in heavens", "ουρανοι": "heavens",
    "χανααν": "Canaan", "αιγυπτου": "of Egypt", "αιγυπτον": "Egypt [acc]",
    "αιγυπτ": "Egypt", "λαβαν": "Laban", "λωτ": "Lot", "σαρρα": "Sarah",
    "χειροσ": "of hand", "εμπροσθεν": "before", "νωπιον": "before",
    "προσωπον": "face", "προσωπου": "of face", "προσωπο": "face",
    "πολιν": "city [acc]", "πολει": "in city", "πολεωσ": "of city",
    "βασιλεια": "kingdom", "βασιλευσ": "king", "βασιλεωσ": "of king",
    "βασιλεισ": "kings", "βασιλευσιν": "to kings",
    "θαλασσησ": "of sea", "πυρ": "fire", "πυροσ": "of fire",
    "σπερμα": "seed", "σπερματοσ": "of seed",
    "ονομα": "name", "ονοματι": "in name", "ονοματοσ": "of name",
    "νομου": "of law", "νομον": "law [acc]", "νομω": "in law",
    "πατερα": "father [acc]", "πατρι": "to father",
    "υιων": "of sons", "θυγατερασ": "daughters [acc]", "θυγατερεσ": "daughters",
    "φωνησ": "of voice", "φωνην": "voice [acc]", "φων": "voice",
    "οικου": "of house", "οικον": "house [acc]", "οικοσ": "house",
    "τοπον": "place [acc]", "τοπου": "of place", "τοπω": "in place",
    "εδωκα": "I gave", "δωσω": "I will give", "δουναι": "to give",
    "ποιησασ": "having done", "ποιησαι": "to do", "ποιω": "I do",
    "ποιει": "[he] does", "ποιουντεσ": "doing", "ποιησον": "do",
    "ποιησωσιν": "they might do",
    "δυναται": "he is able", "δυνασαι": "you are able", "δυνατον": "possible",
    "εδει": "it was necessary", "δει": "it is necessary",
    "εαυτοισ": "to themselves", "αλληλουσ": "one another", "αλληλων": "of one another",
    "αλληλουια": "hallelujah", "καγω": "and I", "πλην": "but/however",
    "πρωτον": "first", "δευτερον": "second", "τριτον": "third",
    "ουδεισ": "no one", "ουδεν": "nothing", "ουχι": "not indeed",
    "εσται": "it will be", "εσομαι": "I will be", "εσεσθε": "you will be",
    "εστε": "you are [pl]", "ειναι": "to be",
    "καθ": "according to", "θε": "O God", "κε": "O Lord",
    "δο": "give", "δοξα": "glory", "δοξαν": "glory [acc]",
    "θεω": "to God", "λαλει": "[he] speaks", "ελαλησεν": "[he] spoke",
    "σφοδρα": "very much", "καλον": "good [n]", "κακον": "evil [n]",
    "τροφον": "food", "ποτον": "drink", "σημερον": "today",
    "που": "where", "πωσ": "how", "οταν": "whenever",
    "οπωσ": "so that", "οστισ": "whoever",
    "τινα": "someone", "τινοσ": "of someone", "ποιον": "which?",
    "ειδαμεν": "we saw", "οιδαμεν": "we know", "οιδατε": "you know [pl]",
    "οιδα": "I know", "ιδε": "see/behold", "ιδου": "behold",
    "πληρωθη": "it might be fulfilled", "προφητου": "of prophet",
    "κρισιν": "judgment [acc]", "δικαιωματα": "ordinances", "εντολασ": "commandments",
    "προσταγματα": "statutes", "διαθηκην": "covenant [acc]",
    "χθρων": "of enemies", "χθροι": "enemies", "εχθροσ": "enemy",
    "χειρα": "hand", "χθες": "yesterday",
    "μεροσ": "part", "μερων": "of parts", "μεσον": "midst",
    "μελλει": "he is about to", "καλεσει": "he will call",
    "μονον": "only", "αρτι": "now", "αρχιερεισ": "chief priests",
    "φαρισαιοι": "Pharisees", "ιουδαιοι": "Jews", "σιμων": "Simon",
    "πιλατοσ": "Pilate", "σωμα": "body", "σωματοσ": "of body",
    "πασ": "all/every", "πασι": "to all", "παντοσ": "of all/every",
    "εκει": "there", "εκεινη": "that one [f]", "εκεινο": "that one [n]",
    "εκεινου": "of that one", "εκεινοι": "those ones",
    "αυτα": "them/it [f/n pl]", "εαυτον": "himself", "σαυτον": "yourself",
    "δωδεκα": "twelve", "τριακοντα": "thirty", "χιλιαδεσ": "thousands",
    "επτα": "seven", "δεκα": "ten",

    # Batch 2 additions (LXX Exodus/Leviticus; TR Mark/Luke/Acts)
    "οι": "the [nom pl m]", "αι": "the [nom pl f]", "παν": "all/every [n]",
    "παντα": "all things", "παντες": "all [m pl]", "πασαν": "all/every [f acc]",
    "πασα": "all/every [f nom]", "παση": "all/every [f dat]", "παντος": "of all/every",
    "παντας": "all [acc pl m]", "πασι": "to all", "πασιν": "to all",
    "ταυτα": "these things", "τουτο": "this [n]", "ταυτην": "this [f acc]",
    "τουτω": "to this", "τουτων": "of these", "τουτου": "of this",
    "ταυτης": "of this [f]", "ταυτη": "to this [f]", "τινες": "some/certain [pl]",
    "τινι": "to someone", "τισι": "to some", "τινα": "someone/anyone",
    "τινος": "of someone", "οιτινες": "whoever/which [pl]", "ων": "of whom/which",
    "ω": "to whom/which", "μετ": "with [enclitic]", "εφ": "upon [enclitic]",
    "υπ": "under [enclitic]", "αν": "[modal particle]", "ενα": "one",
    "δυο": "two", "τρεις": "three", "τεσσαρες": "four", "πεντε": "five",
    "εξ": "six", "επτα": "seven", "εικοσι": "twenty", "τριακοντα": "thirty",
    "τεσσαρακοντα": "forty", "εκατον": "hundred", "πεντηκοντα": "fifty",
    "οιδα": "I know", "ειδον": "I saw", "ιδοντες": "having seen", "ιδων": "having seen",
    "ειπων": "having said", "ακουσας": "having heard", "ακουσαντες": "having heard",
    "ακουσαι": "to hear", "ακουειν": "to hear", "αναστας": "having stood up",
    "αναστα": "stand up!", "ηρξατο": "[he] began", "ηρξαντο": "they began",
    "ευρον": "I found", "επεσεν": "[he] fell", "επηρωτησεν": "[he] questioned",
    "ηγειρεν": "[he] raised", "ερχονται": "they come",
    "γενομενης": "having come to be [f]", "γενομενος": "having come to be [m]",
    "γενεσθαι": "to come to be", "γενηται": "it might come to be",
    "λεγουσιν": "they say", "λεγετε": "you [pl] say", "ελεγεν": "[he] was saying",
    "εφη": "[he] said [formal]", "ετι": "still/yet", "ωδε": "here", "ωρα": "hour",
    "ολης": "of whole", "ολον": "whole [acc n]", "ολην": "whole [f acc]",
    "πολλα": "many things", "πολλοι": "many [m]", "πολλων": "of many",
    "πολυ": "much", "πολυς": "much [nom m]", "πολλας": "many [f acc]",
    "πλοιον": "boat", "πετρον": "Peter [acc]", "παυλον": "Paul [acc]",
    "παυλου": "of Paul", "παυλω": "to Paul", "ιωαννην": "John [acc]",
    "ιωαννου": "of John", "ιεροσολυμα": "Jerusalem", "ιερουσαλημ": "Jerusalem",
    "γαλιλαιας": "of Galilee", "ιουδαιας": "of Judea", "οδον": "way [acc]",
    "οδω": "way [dat]", "οδου": "of way", "οχλος": "crowd", "οχλον": "crowd [acc]",
    "οχλου": "of crowd", "οχλοι": "crowds", "οχλω": "to crowd",
    "πληθος": "multitude", "μαθητας": "disciples [acc]", "γραμματεις": "scribes",
    "φαρισαιων": "of Pharisees", "χριστον": "Christ [acc]", "αγιον": "holy [n acc]",
    "αγγελος": "angel", "διδασκαλε": "teacher!", "δαιμονια": "demons",
    "ανηρ": "man [nom]", "ανδρες": "men [nom]", "ανδρας": "men [acc]",
    "ανδρα": "man [acc]", "εαυτους": "themselves", "εαυτου": "of himself",
    "εμοι": "to me", "δεξιων": "of right [sides]", "βλεπετε": "you [pl] see",
    "αφ": "from [enclitic]", "χρειαν": "need [acc]", "φαγειν": "to eat",
    "ποια": "which?", "πασχα": "Passover", "μηδεν": "nothing", "μαλλον": "rather",
    "καρδια": "heart", "καρδιας": "of heart", "καρδιαν": "heart [acc]",
    "θαλασσαν": "sea [acc]", "παραβολην": "parable [acc]", "μωσης": "Moses",
    "λαον": "people [acc]", "λαου": "of people", "εθνων": "of nations",
    "εθνη": "nations", "αρτον": "bread [acc]", "αρτους": "loaves/breads",
    "αδελφους": "brothers [acc]", "προσκαλεσαμενος": "having called to himself",
    "οπισω": "after/behind", "λαβων": "having taken", "ιερον": "temple",
    "θανατου": "of death", "εισελθων": "having entered", "εισελθειν": "to enter",
    "ρηματα": "words", "προφητης": "prophet", "σημειον": "sign", "σημεια": "signs",
    "μεσω": "midst [dat]", "ιματια": "garments", "εξεστιν": "it is lawful",
    "αρα": "then/therefore", "νυκτος": "of night", "μιαν": "one [f acc]",
    "ημερων": "of days", "ουαι": "woe", "οις": "to whom/which",
    "παραχρημα": "immediately", "προ": "before", "παν": "every/all",
    "μωυσης": "Moses", "μωυσην": "Moses [acc]", "μωυση": "to Moses", "μωσησ": "Moses",
    "ααρων": "Aaron", "ιερευς": "priest", "ιερεως": "of priest",
    "σκηνη": "tent", "σκηνης": "of tent", "σκηνην": "tent [acc]", "σκηνου": "of tent",
    "μαρτυριου": "of testimony", "μαρτυριον": "testimony", "θυσιαστηριον": "altar",
    "θυσιαστηριου": "of altar", "λαος": "people", "λαω": "to people",
    "στεαρ": "fat", "εργον": "work", "συνεταξεν": "[he] commanded",
    "ακαθαρτος": "impure", "ακαθαρτον": "impure [n]", "αγια": "holy [f pl]",
    "αγιω": "holy [dat]", "εναντι": "before", "ενωπιον": "before",
    "επιθησει": "[he] shall put", "επιθησεις": "you shall put",
    "επεθηκεν": "[he] put", "ποιησεις": "you shall do", "ποιησετε": "you [pl] shall do",
    "ποιησει": "[he] shall do", "ολοκαυτωμα": "burnt offering",
    "ολοκαυτωματα": "burnt offerings", "κεφαλην": "head [acc]", "κεφαλη": "head",
    "πλησιον": "neighbor", "μοσχον": "calf [acc]", "μοσχου": "of calf",
    "ερεις": "you shall say", "θυσιας": "of sacrifice", "θυσιαν": "sacrifice [acc]",
    "εξιλασεται": "[he] shall atone", "βασεις": "bases", "σωτηριου": "of salvation/peace offering",
    "ασχημοσυνην": "nakedness [acc]", "αιγυπτιων": "of Egyptians",
    "αιγυπτω": "to Egypt", "τροπον": "manner", "εκαστος": "each one",
    "κυκλω": "around", "νομιμον": "statute/ordinance", "λημψεται": "[he] shall take",
    "λημψη": "you shall take", "λαλησον": "speak!", "θυρας": "of door",
    "θυραν": "door [acc]", "θυρων": "of doors", "χειρι": "hand [dat]",
    "φαγεσθε": "you [pl] shall eat", "σκευη": "vessels", "εβδομη": "seventh",
    "σαββατα": "sabbaths", "ορος": "mountain", "ενετειλατο": "[he] commanded",
    "ελαιον": "oil", "χρυσιου": "of gold", "πυρι": "to fire", "πλυνει": "[he] shall wash",
    "παρεμβολης": "of camp", "προσαξει": "[he] shall bring", "οικιαν": "house [acc]",
    "νομος": "law", "κριον": "ram", "καρπωμα": "offering", "ευωδιας": "of fragrance",
    "αυλης": "of courtyard", "καθα": "as/according as", "θεραποντων": "of servants",
    "δωρον": "gift", "χρυσους": "golden [m]", "πλημμελειας": "of trespass",
    "λουσεται": "[he] shall wash", "εικοσι": "twenty", "αρτους": "loaves",
    "αιγυπτιοι": "Egyptians", "τεσσαρες": "four", "στολας": "robes",
    "προβατον": "sheep", "πηχεων": "of cubits", "λοβον": "lobe",
    "λεπρας": "of leprosy", "ιερεωσ": "of priest", "θανατω": "to death",
    "ετη": "years", "ελαιου": "of oil", "συναγωγη": "congregation",
    "συναγωγης": "of congregation", "στυλοι": "pillars", "δακτυλιους": "rings",
    "κιβωτον": "ark [acc]", "κεκλωσμενης": "of spun", "ηνικα": "when",
    "βρωθησεται": "it shall be eaten", "αφην": "joining",
    "αποτισει": "[he] shall repay", "χρυσιω": "gold [dat]", "χειρ": "hand",
    "δερματι": "skin", "βυσσου": "of byssus/linen", "ελαιω": "to oil",
    "προβατων": "of sheep", "διαπετασμα": "veil", "εξιλασμου": "of atonement",
    "ημερας": "of day", "ημεραν": "day [acc]", "επιθυμιας": "of desire",
    "σποδου": "of ashes", "ασεβεις": "ungodly ones", "κολλυριδας": "cakes",
    "εβδομαδας": "weeks", "πεντακισχιλιους": "five thousand",
    "βεελφεγωρ": "Baal-peor", "φογωρ": "Peor", "βαλααμ": "Balaam", "μαδιαν": "Midian",
}
GRC_LEX.update(EXTRA_GRC)

# LXX Genesis / Psalms
LXX_GRC = {
    "γενηθητω": "let there be", "φια": "let there be", "φωσ": "light",
    "εγενετο": "it came to be", "εκαλεσεν": "he called", "ημεραν": "day [acc]",
    "νυκτα": "night [acc]", "μια": "one", "διεσταλμενον": "divided",
    "συντελεια": "completion", "αστερεσ": "stars", "σεληνη": "moon", "ηλιοσ": "sun",
    "ικθυεσ": "fish", "πετεινα": "birds", "κτηνη": "cattle",
    "ξυλον": "tree", "ξυλου": "of tree", "καρπον": "fruit",
    "φυλλον": "leaf", "διεξοδουσ": "outlets", "πεφυτευμενον": "planted",
    "μελετησει": "he will meditate", "θελημα": "will",
    "ασεβων": "of ungodly ones", "ασεβεισ": "ungodly ones",
    "αμαρτωλων": "of sinners", "αμαρτωλοι": "sinners",
    "λοιμων": "of pestilent ones", "δικαιων": "of righteous ones",
    "δικαιοσ": "righteous one", "χνουσ": "dust",
    "εκριπτει": "casts out", "ανεμοσ": "wind", "προσωπου": "from face",
    "διαψαλμα": "pause", "ψαλμοσ": "psalm",
    "ελεοσ": "mercy", "ελεημοσυνη": "mercy/alms",
    "καρδια": "heart", "καρδιαν": "heart [acc]", "ψυχη": "soul",
    "ψυχην": "soul [acc]", "συνιημι": "I understand",
    "ησαυ": "Esau", "αβρααμ": "Abraham", "ισαακ": "Isaac",
    "διεχωρισεν": "he separated", "ανὰ": "between", "μεσον": "midst",
    "φωτοσ": "of light", "σκοτουσ": "of darkness",
    "αορατοσ": "invisible", "ακατασκευαστοσ": "unprepared/unformed",
    "επεφερετο": "was bearing over", "επανω": "above",
    "αγιον": "holy [n]",

    # Numerals / common adjectives
    "εισ": "one", "δυο": "two", "τρεισ": "three", "τεσσαρεσ": "four",
    "πεντε": "five", "εξ": "six", "επτα": "seven", "οκτω": "eight",
    "εννεα": "nine", "δεκα": "ten", "δεκατεσσαρεσ": "fourteen",
    "πασ": "all/every", "πασα": "all/every [f]", "παν": "all/every [n]",
    "παντεσ": "all [pl m]", "πασαι": "all [pl f]", "παντα": "all [pl n]",
    "μεγασ": "great", "μικροσ": "small", "καλοσ": "good/beautiful",
    "δικαιοσ": "righteous/just", "αγαθοσ": "good",

    # Supplied / grammar
    "το": "[it/the]", "τισ": "[someone]", "μεν": "[indeed]",
}

LAT_LEX = {
    # Articles / particles (Latin has none; use supplied)
    "et": "and", "autem": "but/however", "vero": "but/indeed",
    "sed": "but", "enim": "for", "ergo": "therefore", "igitur": "therefore",
    "quia": "because", "quoniam": "because", "quod": "that/which",
    "ut": "so that", "si": "if", "nisi": "unless", "ne": "lest/not",
    "non": "not", "nec": "and not", "neque": "nor", "quoque": "also",
    "ita": "thus", "sic": "thus", "sicut": "just as", "tamquam": "as",
    "ecce": "behold", "ecce": "behold", "iam": "already", "nunc": "now",
    "tunc": "then", "semper": "always", "usque": "until", "adhuc": "still",

    # Prepositions
    "in": "in", "ad": "to/toward", "de": "from/concerning", "ex": "from/out of",
    "ab": "from", "a": "from", "cum": "with", "sine": "without",
    "super": "above", "sub": "under", "per": "through", "pro": "for/before",
    "ante": "before", "post": "after", "inter": "between", "extra": "outside",
    "contra": "against", "propter": "because of", "erga": "toward",
    "supra": "above", "infra": "below", "ob": "because of",

    # Pronouns
    "ego": "I", "me": "me", "mihi": "to me", "meum": "my [n]", "mei": "of me",
    "mea": "my [f]", "meus": "my [m]", "meam": "my [f acc]", "meo": "my [dat/abl n]",
    "tu": "you", "te": "you", "tibi": "to you", "tuum": "your [n]", "tui": "of you",
    "tua": "your [f]", "tuus": "your [m]", "tuam": "your [f acc]", "tuo": "your [n dat/abl]",
    "tuae": "your [f gen/dat]", "tuam": "your [f acc]",
    "ille": "he", "illa": "she", "illius": "of him/her", "illi": "to him/her",
    "illum": "him", "illam": "her", "illos": "them [m]", "illas": "them [f]",
    "ipse": "he himself", "ipsum": "himself", "ipsa": "herself", "ipsius": "of himself",
    "hic": "this one", "haec": "this one [f]", "hoc": "this [n]", "huius": "of this",
    "hunc": "this [m acc]", "hanc": "this [f acc]", "his": "to these",
    "is": "he", "eam": "her", "eum": "him", "eos": "them [m]", "eas": "them [f]",
    "ei": "to him/her/them", "eius": "of him/her", "eorum": "of them [m]", "earum": "of them [f]",
    "eis": "to them", "sibi": "to himself/themselves", "se": "himself/themselves",
    "suus": "his", "sua": "his/her [f]", "suum": "his/her [n]", "sui": "of himself",
    "suam": "his/her [f acc]", "suo": "his/her [n dat/abl]", "suis": "to his/her",
    "suum": "his [n]", "suum": "his [n]",
    "qui": "who/which", "quae": "who/which [f]", "quod": "which [n]",
    "quem": "whom [m]", "quam": "whom/which [f]", "cuius": "whose",
    "cui": "to/for whom", "quibus": "to/for which", "quibus": "which [dat/abl pl]",
    "quid": "what", "quis": "who",

    # Common verbs
    "est": "[he/she/it] is", "erat": "[he/she/it] was", "esse": "to be",
    "sum": "I am", "es": "you are", "sunt": "they are", "erant": "they were",
    "fuit": "he was", "fuere": "they were", "fieri": "to become",
    "dico": "I say", "dixit": "[he] said", "dixisti": "you said",
    "dixerunt": "they said", "dixitque": "and [he] said", "dicit": "[he] says",
    "dicens": "saying",
    "facio": "I make", "fecit": "[he] made", "facta": "made [f]",
    "factum": "made [n]", "factus": "made [m]", "fiat": "let there be",
    "fiebat": "it was being made", "factaest": "it was made",
    "video": "I see", "vidit": "[he] saw", "vidi": "I saw",
    "audio": "I hear", "audivit": "[he] heard",
    "venio": "I come", "venit": "[he] came", "veniunt": "they come",
    "vado": "I go", "ivit": "[he] went",
    "do": "I give", "dedit": "[he] gave", "dat": "[he] gives",
    "accipio": "I take", "accepit": "[he] took", "suscipio": "I receive",
    "pono": "I put", "posuit": "[he] put", "appono": "I set before",
    "mitto": "I send", "misit": "[he] sent", "missus": "sent",
    "scio": "I know", "novit": "[he] knew",
    "voco": "I call", "vocavit": "[he] called", "appellavit": "[he] called",
    "appellavitque": "and [he] called", "vocatur": "[he] is called",
    "regno": "I reign", "natus": "born", "nati": "were born",
    "genuit": "[he] begat", "generavit": "[he] begat",
    "creo": "I create", "creavit": "[he] created",
    "habeo": "I have", "habuit": "[he] had", "habet": "[he] has",
    "volo": "I want", "voluit": "[he] wanted", "nolo": "I do not want",
    "possum": "I am able", "potuit": "[he] was able",
    "incipio": "I begin", "coepit": "[he] began",
    "ostendo": "I show", "ostendit": "[he] showed",
    "respondeo": "I answer", "respondit": "[he] answered", "responderunt": "they answered",
    "ait": "[he] said", "inquit": "[he] said",
    "oro": "I pray", "rogo": "I ask",
    "salvo": "I save", "salvabit": "[he] will save", "salus": "salvation",
    "baptizo": "I baptize", "baptizavit": "[he] baptized",
    "doceo": "I teach", "docuit": "[he] taught",
    "sanctifico": "I sanctify", "sanctificavit": "[he] sanctified",
    "justifico": "I justify", "justificavit": "[he] justified",
    "glorifico": "I glorify", "glorificavit": "[he] glorified",
    "confiteor": "I confess", "confessus": "having confessed",
    "credo": "I believe", "credidit": "[he] believed", "credentibus": "to believing ones",
    "peccatum": "sin", "peccavit": "[he] sinned",
    "judico": "I judge", "judicavit": "[he] judged", "judicium": "judgment",

    # Divine / nouns
    "deus": "God", "dei": "of God", "deo": "to God", "deum": "God [acc]",
    "dominus": "Lord", "domini": "of [the] Lord", "domino": "to [the] Lord",
    "dominum": "[the] Lord [acc]", "domine": "O Lord",
    "spiritus": "spirit/wind", "spiritum": "spirit [acc]",
    "christus": "Christ", "christi": "of Christ", "christum": "Christ [acc]",
    "iesus": "Jesus", "iesum": "Jesus [acc]",
    "verbum": "word", "verbi": "of word", "verbo": "to word",
    "lux": "light", "lucem": "light [acc]", "lucis": "of light",
    "tenebrae": "darkness", "tenebras": "darkness [acc]", "tenebr": "darkness",
    "mundus": "world", "mundum": "world [acc]", "mundi": "of world",
    "caelum": "heaven", "caeli": "of heaven", "caelum": "heaven [acc]",
    "clum": "heaven", "cli": "of heaven", "clo": "to heaven",
    "terra": "earth", "terram": "earth [acc]", "terrae": "of earth",
    "esset": "[it] might be", "essent": "[they] might be", "erant": "they were", "eris": "you will be",
    "conprehenderunt": "they comprehended", "comprehenderunt": "they comprehended",
    "nihil": "nothing", "apud": "with",
    "aqua": "water", "aquas": "waters", "aquarum": "of waters",
    "abyssus": "abyss", "abyssi": "of abyss",
    "homo": "man", "hominem": "man [acc]", "hominis": "of man", "hominum": "of men",
    "vir": "man", "viri": "of man", "virum": "man [acc]",
    "mulier": "woman", "mulierem": "woman [acc]",
    "puer": "boy", "puella": "girl",
    "populus": "people", "populum": "people [acc]", "populi": "of people",
    "gens": "nation", "gentes": "nations", "gentium": "of nations",
    "rex": "king", "regem": "king [acc]", "regis": "of king",
    "regnum": "kingdom", "regni": "of kingdom",
    "dies": "day", "diem": "day [acc]", "dierum": "of days",
    "nox": "night", "noctem": "night [acc]",
    "vespere": "evening", "mane": "morning",
    "sol": "sun", "luna": "moon", "stella": "star",
    "mare": "sea", "maris": "of sea",
    "ventus": "wind", "ventus": "wind",
    "ignis": "fire", "aqua": "water",
    "panis": "bread", "vinum": "wine",
    "caro": "flesh", "carnis": "of flesh", "carnem": "flesh [acc]",
    "sanguis": "blood", "sanguinis": "of blood", "sanguinem": "blood [acc]",
    "cor": "heart", "corde": "in heart", "coram": "before",
    "anima": "soul", "animam": "soul [acc]", "animae": "of soul", "animas": "souls",
    "mens": "mind", "oculus": "eye", "auris": "ear", "manus": "hand",
    "pes": "foot", "caput": "head",
    "os": "mouth", "lingua": "tongue/language",
    "lex": "law", "lege": "in law",
    "veritas": "truth", "gratia": "grace", "pax": "peace",
    "gloria": "glory", "potestas": "authority/power", "virtus": "power/virtue",
    "misericordia": "mercy", "justitia": "righteousness", "judicium": "judgment",
    "fides": "faith", "spes": "hope", "charitas": "love",

    # Family nouns
    "filius": "son", "filii": "of son", "filium": "son [acc]", "filii": "sons",
    "filia": "daughter", "filiam": "daughter [acc]", "filiabus": "to daughters",
    "pater": "father", "patris": "of father", "patrem": "father [acc]",
    "mater": "mother", "matris": "of mother",
    "frater": "brother", "fratres": "brothers", "fratrem": "brother [acc]",
    "soror": "sister", "uxor": "wife",
    "infans": "infant", "parvulus": "little child",

    # Names (Latin forms)
    "adam": "Adam", "seth": "Seth", "enos": "Enosh",
    "cainan": "Kenan", "malalehel": "Mahalaleel", "jared": "Jared",
    "enoch": "Enoch", "mathusala": "Methuselah", "lamech": "Lamech",
    "noe": "Noah", "sem": "Shem", "cham": "Ham", "japheth": "Japheth",
    "abraham": "Abraham", "abram": "Abram", "isaac": "Isaac", "jacob": "Jacob",
    "juda": "Judah", "david": "David", "iesse": "Jesse",
    "joseph": "Joseph", "maria": "Mary", "mariae": "of Mary",
    "paulus": "Paul", "petrus": "Peter", "joannes": "John",
    "pharao": "Pharaoh", "pharaonis": "of Pharaoh",
    "israel": "Israel", "israhel": "Israel",
    "phares": "Perez", "zara": "Zerah", "esrom": "Hezron", "aram": "Aram",
    "aminadab": "Amminadab", "naasson": "Nahshon", "salmon": "Salmon",
    "booz": "Boaz", "obed": "Obed", "ruth": "Ruth", "rahab": "Rahab", "thamar": "Tamar",
    "salathiel": "Shealtiel", "zorobabel": "Zerubbabel",
    "abiud": "Abiud", "eliakim": "Eliakim", "azor": "Azor", "sadoc": "Zadok",
    "achim": "Achim", "eliud": "Eliud", "eleazar": "Eleazar", "matthan": "Matthan",
    "solomon": "Solomon", "urias": "Uriah", "roboam": "Rehoboam",
    "abia": "Abijah", "asa": "Asa", "josaphat": "Jehoshaphat", "joram": "Joram",
    "ozias": "Uzziah", "joatham": "Jotham", "achaz": "Ahaz", "ezechias": "Hezekiah",
    "manasses": "Manasseh", "amon": "Amon", "josias": "Josiah",
    "jechonias": "Jeconiah", "nabuchodonosor": "Nebuchadnezzar",

    # Adjectives / numerals
    "unus": "one", "duo": "two", "tres": "three", "quattuor": "four",
    "quinque": "five", "sex": "six", "septem": "seven", "octo": "eight",
    "novem": "ten", "decem": "ten", "viginti": "twenty", "triginta": "thirty",
    "omnis": "all/every", "omnes": "all [pl]", "omnium": "of all",
    "totus": "whole", "tutus": "safe", "bonus": "good", "malus": "bad",
    "magnus": "great", "parvus": "small", "sanctus": "holy",
    "justus": "righteous", "peccator": "sinner", "impius": "ungodly",
    "miser": "wretched", "beatus": "blessed", "sacer": "holy/sacred",

    # Adverbs
    "bene": "well", "male": "badly", "valde": "very", "nimis": "very",
    "statim": "immediately", "tunc": "then", "prius": "before",
    "modo": "now", "subito": "suddenly", "fortiter": "strongly",

    # Genesis specific
    "principio": "beginning", "principium": "beginning",
    "faciem": "face", "abyssi": "of abyss",
    "ferebatur": "was borne", "spiritus": "spirit/wind",
    "inanis": "empty/void", "vacua": "void",
    "divisit": "[he] divided", "appellavit": "[he] called",
    "vespere": "evening", "mane": "morning",
    "principio": "beginning",

    # John / NT
    "emmanuel": "Emmanuel", "interpretatum": "translated",
    "incarnatum": "made flesh", "verbumcarofactumest": "the Word was made flesh",
    "inprincipio": "in [the] beginning", "eratinprincipio": "was in [the] beginning",
    "inillo": "in him", "perlucem": "through the light",
    "eratluxvera": "was the true light",
    "inpropriavenerunt": "to [his] own he came",
    "potestatemfiliosdeifieri": "authority children of God to become",
    "exsanguinibus": "from bloods", "exvoluntatecarnis": "from will of flesh",
    "exvoluntateviri": "from will of man", "exdeonatisunt": "from God were born",
    "unigeniti": "of [the] only-begotten", "patris": "of father",
    "plenamgratiaeveritatis": "full of grace and truth",

    # Psalms frequent
    "psalmus": "psalm", "canticum": "song", "laudate": "praise [ye]",
    "alleluia": "hallelujah", "cantate": "sing", "jubilate": "shout for joy",
    "confitemini": "give thanks", "benedicite": "bless",
    "saeclum": "age/eternity", "aeternum": "eternal/forever",
    "semper": "always", "usque": "until", "super": "above",
    "miserere": "have mercy", "mei": "of me", "deusmeus": "my God",

    # Romans frequent Latin
    "servus": "servant/slave", "apostolus": "apostle", "segregatus": "set apart",
    "evangelium": "gospel", "promiserat": "he had promised", "prophetis": "prophets",
    "scripturis": "scriptures", "filio": "son", "suo": "his",
    "semine": "seed", "secundumcarnem": "according to flesh",
    "praedestinatus": "predestined", "virtute": "in power",
    "secundumspiritum": "according to spirit", "sanctificationis": "of holiness",
    "resurrectione": "resurrection", "mortuorum": "of dead ones",
    "dominonostro": "our Lord", "perquem": "through whom",
    "gratiam": "grace", "apostolatum": "apostleship", "oboedientiam": "obedience",
    "fidei": "of faith", "gentibus": "to nations", "nomine": "in name",
    "romae": "in Rome", "dilectis": "beloved", "sanctis": "holy ones",
    "gratia": "grace", "vobis": "to you [pl]", "pax": "peace",
    "patrenostro": "our father", "gratiasago": "I give thanks",
    "fidem": "faith", "annuntiatur": "is proclaimed", "orans": "praying",
    "memoriam": "remembrance", "facio": "I make", "voluntate": "will",
    "profectus": "success", "videre": "to see", "communicare": "to impart",
    "spirituale": "spiritual", "confirmari": "to be established",
    "consolari": "to be comforted", "mutua": "mutual", "fide": "faith",
    "proposui": "I purposed", "prohibitus": "hindered", "fructum": "fruit",
    "reliquis": "remaining", "gentibus": "nations", "grecis": "Greeks",
    "barbaris": "barbarians", "sapientibus": "wise", "insipientibus": "foolish",
    "debitorsum": "I am a debtor", "promptus": "ready", "evangelizare": "to preach the gospel",
    "erubesco": "I am ashamed", "virtus": "power", "salutem": "salvation",
    "credenti": "believing", "judaeo": "to [the] Jew", "graeco": "to [the] Greek",
    "justitia": "righteousness", "revelatur": "is revealed", "scriptum": "written",
    "justus": "righteous one", "vivet": "will live",
}

EXTRA_LAT2 = {
    "nomen": "name", "nomine": "in name", "nominis": "of name",
    "omnibus": "to all", "omnium": "of all", "omnem": "every [acc]", "omni": "every",
    "dixi": "I said", "dicite": "say [pl]", "dicebant": "they were saying",
    "dixeram": "I had said", "loquutus": "having spoken", "locutus": "having spoken",
    "locuti": "having spoken [pl]", "locutusque": "and having spoken",
    "locutusest": "he spoke",
    "fac": "do", "facite": "do [pl]", "fecisti": "you did", "fecerunt": "they did",
    "fecimus": "we did", "faciam": "I will do", "faciat": "he may do",
    "confiteor": "I confess", "confitemini": "confess [pl]",
    "exaudi": "hear [imperative]", "exaudivit": "he heard",
    "testimonium": "testimony", "testimonii": "of testimony",
    "testis": "witness", "testes": "witnesses",
    "sacrificium": "sacrifice", "holocaustum": "burnt offering",
    "templum": "temple", "templi": "of temple",
    "altare": "altar", "altaris": "of altar",
    "sacerdos": "priest", "sacerdotes": "priests", "sacerdotum": "of priests",
    "levita": "Levite", "levitae": "Levites",
    "unxit": "[he] anointed", "unctus": "anointed",
    "christus": "Christ", "christum": "Christ [acc]",
    "baptizavit": "[he] baptized", "baptizo": "I baptize",
    "cibum": "food", "potum": "drink", "panem": "bread",
    "verba": "words", "sermonem": "word/saying", "sermo": "word",
    "vocem": "voice [acc]", "voce": "with voice", "voces": "voices",
    "manu": "with hand", "manum": "hand [acc]", "manibus": "with hands",
    "pedes": "feet", "pedum": "of feet",
    "oculos": "eyes", "oculi": "eyes [nom]", "oculis": "with eyes",
    "caput": "head", "capitis": "of head",
    "cor": "heart", "corde": "in heart",
    "via": "way", "viam": "way [acc]", "viae": "of way", "viis": "with ways",
    "iter": "journey", "itineris": "of journey",
    "loco": "place", "locum": "place [acc]", "loci": "of place", "locis": "in places",
    "domo": "house", "domum": "house [acc]", "domui": "to house", "domibus": "houses",
    "facie": "face", "faciem": "face [acc]", "facies": "faces",
    "conspectu": "in sight", "conspectum": "sight [acc]",
    "medio": "midst", "medium": "midst [acc]",
    "operibus": "works", "opus": "work", "opera": "works",
    "saeclum": "age/eternity", "saeculum": "age/eternity", "saeculi": "of age",
    "aeternum": "eternal/forever", "aeterna": "eternal [pl n]",
    "ternum": "eternity", "seculum": "age/eternity",
    "inimicus": "enemy", "inimici": "of enemy/enemies", "inimicos": "enemies [acc]",
    "mandata": "commandments", "mandatum": "commandment", "mandatis": "commandments",
    "praecepta": "precepts", "praeceptum": "precept", "praeceptis": "precepts",
    "legem": "law [acc]", "lege": "in law", "legis": "of law",
    "justitiam": "righteousness [acc]", "misericordiam": "mercy [acc]",
    "gloriam": "glory [acc]", "gloria": "glory",
    "vitam": "life [acc]", "vita": "life",
    "animam": "soul [acc]", "animas": "souls [acc]",
    "benedicite": "bless [pl]", "benedixit": "[he] blessed",
    "sion": "Zion", "jerusalem": "Jerusalem",
    "amen": "amen", "discipuli": "disciples", "discipulum": "disciple [acc]",
    "numquid": "whether?", "quare": "why?", "quando": "when",
    "ibi": "there", "ubi": "where", "donec": "until", "usquequo": "how long",
    "simul": "together", "semper": "always", "itaque": "therefore",
    "aut": "or", "vel": "or", "neque": "nor", "nec": "nor",
    "quasi": "as", "velut": "as", "sicut": "just as",
    "unum": "one [acc n]", "duos": "two [acc]", "tres": "three", "quatuor": "four",
    "quinque": "five", "sex": "six", "septem": "seven", "octo": "eight",
    "novem": "nine", "decem": "ten", "viginti": "twenty", "triginta": "thirty",
    "magnus": "great", "magna": "great [f]", "magnum": "great [n]",
    "bonus": "good", "bonum": "good [n]", "bona": "good [pl n]",
    "malus": "bad", "malum": "bad [n]", "mala": "bad [pl n]",
    "tuos": "your [acc pl m]", "tuas": "your [acc pl f]",
    "meos": "my [acc pl m]", "meas": "my [acc pl f]", "meis": "my [dat/abl pl]",
    "suis": "his [dat/abl pl]", "suos": "his [acc pl m]", "suas": "his [acc pl f]",
    "nostri": "our/of us", "nostrum": "our", "nostris": "to our",
    "vestrum": "of you [pl]", "vestris": "to you [pl]",
    "quorum": "of whom [m]", "quarum": "of whom [f]", "quibus": "to whom",
    "eo": "there", "ea": "she/it", "iis": "to them",
    "eisdem": "to the same", "ipsis": "to them/themselves",
    "seipsum": "himself", "semetipsum": "himself",
    "israel": "Israel", "israhel": "Israel",
    "chanaan": "Canaan", "aegyptum": "Egypt", "aegypti": "of Egypt",
    "aegypto": "to Egypt", "aegyptus": "Egypt",
    "abraham": "Abraham", "isaac": "Isaac", "jacob": "Jacob", "esau": "Esau",
    "joseph": "Joseph", "david": "David", "jesus": "Jesus",
}
LAT_LEX.update(EXTRA_LAT2)

# ---------------------------------------------------------------------------
# Batch 3 additional lexemes.
# ---------------------------------------------------------------------------

EXTRA_HEB_3 = {
    # Common particles / conjunctions / adverbs
    "אֲשֶׁר": "which/who/that", "כִּי": "for/because/that", "כַּאֲשֶׁר": "as/which",
    "וַיֹּאמֶר": "and [he] said", "וַיֹּאמְרוּ": "and they said", "וַתֹּאמֶר": "and she said",
    "וַיְהִי": "and there was", "כֵּן": "so", "עַתָּה": "now", "עוֹד": "still/yet",
    "אַל": "not [imperative]", "אִם": "if", "אוֹ": "or", "פֶּן": "lest",
    "גַּם": "also", "רַק": "only", "הִנֵּה": "behold", "הִנֵּה": "behold",
    "אַךְ": "only/however", "כֹּה": "thus", "אָז": "then", "לָמָּה": "why",

    # Pronouns (including defective forms seen in the source)
    "אֲנִי": "I", "אָנֹכִי": "I", "אַתָּה": "you [m]", "אַתְּ": "you [f]",
    "אַתֶּם": "you [pl]", "הוּא": "he", "הִיא": "she", "הִוא": "she",
    "הֵם": "they", "הֵמָּה": "they", "אֵל": "to/toward [God]",
    "אֶתְכֶם": "you [pl]", "אוֹתָם": "them", "אוֹתָהּ": "her", "אוֹתוֹ": "him",
    "אוֹתִי": "me", "אוֹתְכֶם": "you [pl]",
    "לוֹ": "to him", "לָהּ": "to her", "לָכֶם": "to you [pl]", "לָנוּ": "to us",
    "לִי": "to me", "לְךָ": "to you", "לָהֶם": "to them", "לְךָ": "to you",
    "בּוֹ": "in him", "בָּהּ": "in her", "בָּם": "in them", "בִּי": "in me",
    "בָּהּ": "in her/it", "בּוֹ": "in him/it",
    "אֵלָיו": "to him", "אֵלֶיךָ": "to you", "אֵלַי": "to me", "אֵלֶיהָ": "to her",
    "אֵלֵיהֶם": "to them", "אֲלֵיהֶם": "to them", "אֵלֶיהָ": "to her",
    "עָלָיו": "upon him", "עָלֶיךָ": "upon you", "עָלַי": "upon me", "עֲלֵיהֶם": "upon them",
    "עִמּוֹ": "with him", "אִתּוֹ": "with him",

    # Prepositions
    "בְּ": "in", "לְ": "to/for", "מִ": "from", "מִן": "from",
    "אֶל": "to/toward", "עַל": "upon", "עַד": "until", "עִם": "with",
    "בְּתוֹךְ": "in the midst of", "תּוֹךְ": "midst of",
    "בֵּין": "between", "תַּחַת": "under", "מֵעַל": "from upon",
    "מִתַּחַת": "from under", "לִפְנֵי": "before", "מִפְּנֵי": "from before",
    "אַחֲרֵי": "after", "בְּיַד": "by hand of", "בְּיָדוֹ": "in his hand",
    "לִפְנֵי": "before", "מִפְּנֵי": "from before", "לְמַעַן": "for the sake of",
    "בַּעֲבוּר": "for the sake of", "עֵקֶב": "because of",
    "בְּכָל": "in all", "בְּיוֹם": "in [the] day", "בַּיּוֹם": "in the day",
    "בְּאֶרֶץ": "in [the] land", "בָּאָרֶץ": "in the land",
    "בְּהַר": "on the mountain", "בְּעֵבֶר": "on the other side of",
    "מֵאֶרֶץ": "from [the] land", "מִכָּל": "from all",
    "מִתּוֹךְ": "from the midst of", "מִמֶּנּוּ": "from him/it",
    "מִשָּׁם": "from there", "מִיַּד": "from hand of",
    "לְעוֹלָם": "forever", "עוֹלָם": "eternity/forever",

    # Articles / demonstratives
    "הַ": "the", "הָ": "the", "הַזֶּה": "this", "זֶה": "this",
    "הַזֹּאת": "this", "זֹאת": "this", "הָאֵלֶּה": "these", "אֵלֶּה": "these",
    "הַהוּא": "that", "הַהִיא": "that [f]",
    "הַיּוֹם": "today", "הַיַּרְדֵּן": "the Jordan", "הָעָם": "the people",
    "הָאָרֶץ": "the earth/land", "הָעִיר": "the city", "הָהָר": "the mountain",
    "הַגְּבוּל": "the border", "הַמַּחֲנֶה": "the camp",

    # Common nouns
    "יִשְׂרָאֵל": "Israel", "יְהוּדָה": "Judah", "בִּנְיָמִן": "Benjamin",
    "רְאוּבֵן": "Reuben", "שִׁמְעוֹן": "Simeon", "גָּד": "Gad",
    "אָשֵׁר": "Asher", "דָּן": "Dan", "נַפְתָּלִי": "Naphtali",
    "זְבוּלֻן": "Zebulun", "לֵוִי": "Levi", "יוֹסֵף": "Joseph",
    "אֶפְרַיִם": "Ephraim", "מְנַשֶּׁה": "Manasseh",
    "מוֹאָב": "Moab", "עַמּוֹן": "Ammon", "מִדְיָן": "Midian",
    "הַכְּנַעֲנִי": "the Canaanite", "הָאֱמֹרִי": "the Amorite",
    "הַפְּרִזִּי": "the Perizzite", "הַחִתִּי": "the Hittite",
    "הַגִּרְגָּשִׁי": "the Girgashite", "הַיְבוּסִי": "the Jebusite",
    "הַחִוִּי": "the Hivite", "פְּלִשְׁתִּים": "Philistines",
    "יְרִיחוֹ": "Jericho", "הָעַי": "Ai", "גִלְעָד": "Gilead",
    "חֶבְרוֹן": "Hebron", "שְׁכֶם": "Shechem", "בֵּית־אֵל": "Bethel",
    "יְרוּשָׁלִַם": "Jerusalem",
    "יְהוֹשֻׁעַ": "Joshua", "כָּלֵב": "Caleb", "נוּן": "Nun",
    "מֹשֶׁה": "Moses", "שִׁמְשׁוֹן": "Samson", "גִדְעוֹן": "Gideon",
    "יִפְתָּח": "Jephthah", "אֲבִימֶלֶךְ": "Abimelech", "מָנוֹחַ": "Manoah",
    "דְּלִילָה": "Delilah",
    "נָעֳמִי": "Naomi", "רוּת": "Ruth", "בֹּעַז": "Boaz", "עוֹבֵד": "Obed",
    "אֱלִימֶלֶךְ": "Elimelech", "מַחְלוֹן": "Mahlon", "כִּלְיוֹן": "Chilion",
    "עָרְפָּה": "Orpah",
    "אִישׁ": "man", "אֲנָשִׁים": "men", "אַנְשֵׁי": "men of",
    "אִשָּׁה": "woman/wife", "הָאִשָּׁה": "the woman", "נָשִׁים": "women",
    "מֶלֶךְ": "king", "מַלְכֵי": "kings of", "הַמְּלָכִים": "the kings",
    "עַם": "people", "עָם": "people", "הָעָם": "the people", "עַמִּים": "peoples",
    "עִיר": "city", "עָרִים": "cities", "הֶעָרִים": "the cities", "עָרֵי": "cities of",
    "נַחַל": "inheritance", "נַחֲלָה": "inheritance", "נַחֲלַת": "inheritance of",
    "נַחֲלָתָם": "their inheritance", "נַחֲלָתוֹ": "his inheritance",
    "גְּבוּל": "border", "גְּבוּלוֹ": "his border", "גְּבוּלְכֶם": "your border",
    "מַטֶּה": "tribe/staff", "לְמַטֵּה": "to/for tribe of", "מַטּוֹת": "tribes",
    "מִשְׁפָּחַת": "family of", "מִשְׁפְּחֹת": "families of", "לְמִשְׁפְּחֹתָם": "to their families",
    "בֵּית": "house of", "בָּיִת": "house", "בָּתִּים": "houses",
    "בְּנֵי": "sons of", "בֵּן": "son", "בַּת": "daughter", "בָּנִים": "sons",
    "בָּנוֹת": "daughters", "בָּנָיו": "his sons", "בְּנֵיהֶם": "their sons",
    "אָב": "father", "אָבִיו": "his father", "אֲבִי": "my father",
    "אֵם": "mother", "אָח": "brother", "אָחִיו": "his brother",
    "אָחוֹת": "sister", "אֲבוֹתָם": "their fathers", "אֲבוֹתָיו": "his fathers",
    "יָד": "hand", "יָדוֹ": "his hand", "יַד": "hand", "בְּיָד": "by hand of",
    "רֹאשׁ": "head", "רָאשֵׁי": "heads of", "פָּנִים": "face",
    "קוֹל": "voice", "שֵׁם": "name",
    "דָּבָר": "word/thing", "הַדָּבָר": "the word/thing", "דְּבָרִים": "words/things",
    "דִּבֶּר": "[he] spoke", "דַּבֵּר": "speak!", "לְדַבֵּר": "to speak",
    "יָדַע": "[he] knew", "יָדַעְתִּי": "I know",
    "שָׁמַע": "[he] heard", "שְׁמַע": "hear!",
    "רָאָה": "[he] saw", "וַיַּרְא": "and [he] saw",
    "עָשָׂה": "[he] did/made", "וַיַּעַשׂ": "and [he] did", "לַעֲשׂוֹת": "to do",
    "הָלַךְ": "[he] walked", "הָלַכְתִּי": "I walked", "לָלֶכֶת": "to go",
    "בָּא": "[he] came", "בָּאוּ": "they came", "וַיָּבֹא": "and [he] came",
    "וַיָּבֹאוּ": "and they came",
    "יָצָא": "[he] went out", "וַיֵּצֵא": "and [he] went out",
    "נָתַן": "[he] gave", "נָתַתִּי": "I have given", "נָתְנָה": "she gave",
    "נָתְנוּ": "they gave", "נְתַתִּיו": "I have given it",
    "לָקַח": "[he] took", "וַיִּקַּח": "and [he] took",
    "יָלַד": "[he] begat", "הוֹלִיד": "[he] begat", "יְלָדֶיהָ": "her children",
    "וַיּוֹלֶד": "and [he] begat", "וַתֵּלֶד": "and she bore",
    "קָרָא": "[he] called", "וַיִּקְרָא": "and [he] called",
    "שָׂם": "[he] put", "שַׂמְתָּ": "you put", "נָתַתָּה": "you gave",
    "הֵנִיחַ": "[he] caused to rest",
    "נָסַע": "[he] journeyed", "וַיִּסְעוּ": "and they journeyed",
    "חָנָה": "[he] encamped", "וַיַּחֲנוּ": "and they encamped",
    "נָטָה": "[he] stretched",
    "קוּם": "rise!", "קָם": "[he] arose", "וַיָּקָם": "and [he] arose",
    "עָמַד": "[he] stood", "יַעֲמֹד": "he will stand", "יַעַמְדוּ": "they will stand",
    "הִתְיַצֵּב": "stand [yourself]!", "יִתְיַצֵּב": "he will stand",
    "עָבַר": "[he] passed over", "עֲבֹר": "pass over!",
    "יָרַד": "[he] went down", "יַעֲלֶה": "he will go up",
    "עָלָה": "[he] went up", "וַיַּעַל": "and [he] went up", "עָלוּ": "they went up",
    "יָרַשׁ": "[he] possessed/inherited", "יְרִשְׁתֶּם": "you shall possess them",
    "הִלָּחֵם": "to fight", "נִלְחַם": "[he] fought", "וַיִּלָּחֲמוּ": "and they fought",
    "לְהִלָּחֶם": "to fight", "מִלְחָמָה": "war",
    "נָגַע": "[he] touched/smote", "וַיַּכּוּ": "and they struck",
    "הִכָּה": "[he] struck", "הָרַג": "[he] killed",
    "שָׁלַח": "[he] sent", "וַיִּשְׁלַח": "and [he] sent", "שְׁלַח": "send!",
    "רָדַף": "[he] pursued", "נָס": "[he] fled",
    "אָסַף": "[he] gathered", "קָבַץ": "[he] gathered",
    "בָּכָה": "[she] wept", "בָּכִיתִי": "I wept",
    "שָׁתָה": "[she] drank", "אָכַל": "[he] ate", "אָכְלוּ": "they ate",
    "לָקַט": "[he] gathered", "לְלַקֵּט": "to gather",
    "שָׂדֶה": "field", "שְׂדֵי": "fields of", "בְּשָׂדֶה": "in the field",
    "חֶרֶב": "sword", "חָרֶב": "sword", "קֶשֶׁת": "bow",
    "רֶכֶב": "chariot", "סוּס": "horse",
    "אֹהֶל": "tent", "אֹהָלִים": "tents", "מִשְׁכָּן": "tabernacle",
    "מִזְבֵּחַ": "altar", "הַמִּזְבֵּחַ": "the altar",
    "בְּרִית": "covenant", "עֵדֻת": "testimony",
    "חֹדֶשׁ": "month", "שָׁנָה": "year", "שָׁנִים": "years", "יוֹם": "day",
    "לַיְלָה": "night", "עֶרֶב": "evening", "בֹּקֶר": "morning",
    "הַשֶּׁמֶשׁ": "the sun", "הַיָּרֵחַ": "the moon", "כּוֹכָבִים": "stars",
    "רוּחַ": "spirit/wind", "עָנָן": "cloud",
    "הַיָּם": "the sea", "נָהָר": "river", "הַנָּהָר": "the river",
    "דָּגָן": "grain", "תִּירוֹשׁ": "new wine", "יִצְהָר": "oil",
    "לֶחֶם": "bread", "מַיִם": "water(s)", "יַיִן": "wine", "שֶׁמֶן": "oil",
    "זָהָב": "gold", "כֶּסֶף": "silver", "נְחֹשֶׁת": "bronze/copper",
    "בְּגָדִים": "garments", "בְּגָדָיו": "his garments",
    "עֲנָקוֹת": "rings",

    # Adjectives
    "גָּדוֹל": "great", "גְּדֹלָה": "great [f]", "קָטֹן": "small",
    "רַב": "many/much", "רַבִּים": "many",
    "טוֹב": "good", "רַע": "bad", "יָשָׁר": "straight/just",
    "חָכָם": "wise", "חָסִיד": "pious/loyal", "עָנִי": "poor", "אֶבְיוֹן": "needy",
    "גִּבּוֹר": "mighty", "קָדוֹשׁ": "holy",
    "חָזָק": "strong", "אַמִּיץ": "mighty/brave",
    "יָמִים": "days", "שָׁנָה": "year", "שָׁנִים": "years",
    "רִאשׁוֹן": "first", "שֵׁנִי": "second", "שְׁלִישִׁי": "third",

    # Proper names (Judges / Ruth specific)
    "עֵglon": "Eglon", "מוֹאָבִי": "Moabite", "מוֹאֲבִיּוֹת": "Moabitesses",
    "אֲרָם": "Aram", "בֵּית־רְחוֹב": "Beth-rehob",
    "קִרְיַת־יְעָרִים": "Kiriath-jearim", "קִרְיַת": "Kiriath",
    "הַמּוֹעֲבִיָּה": "the Moabitess",
}
HEB_LEX.update(EXTRA_HEB_3)

EXTRA_GRC_3 = {
    # Articles / demonstratives / particles
    "ο": "the [nom m]", "η": "the [nom f]", "το": "the [nom/acc n]",
    "οι": "the [nom pl m]", "αι": "the [nom pl f]", "τα": "the [nom/acc pl n]",
    "ουτοσ": "this one", "ουτοι": "these ones", "ουτινεσ": "whoever/which [pl]",
    "ουδε": "and not", "ουδεισ": "no one", "ουδεν": "nothing", "ουχι": "not indeed",
    "ωστε": "so that", "καθ": "according to", "πλην": "but/however",
    "ετι": "still/yet", "νυν": "now", "νυνι": "now indeed", "τοτε": "then",
    "παλιν": "again", "αρα": "then/therefore",
    "αμην": "amen", "ιδου": "behold", "ευθεωσ": "immediately",
    "ειτα": "then", "επειτα": "then afterwards", "επει": "since",
    "επειδη": "since", "διο": "therefore",

    # Pronouns
    "εγω": "I", "συ": "you", "υμεισ": "you [pl]", "ημεισ": "we",
    "με": "me", "σε": "you", "αυτον": "him", "αυτην": "her", "αυτο": "it",
    "αυτουσ": "them [m]", "αυτα": "them/it [f/n pl]",
    "εμαυτον": "myself", "σεαυτω": "to yourself", "εαυτους": "themselves",
    "εαυτουσ": "themselves", "εαυτου": "of himself", "εαυτων": "of themselves",
    "τινεσ": "some/certain [pl]", "τισι": "to some", "τινα": "someone/anyone",
    "τινοσ": "of someone", "ων": "of whom/which", "οισ": "to whom/which",
    "ουσ": "whom/which [f pl]",

    # Prepositions / adverbs / contractions
    "εφ": "upon [enclitic]", "υφ": "under [enclitic]",
    "αν": "[modal particle]", "καθ": "according to [enclitic]",
    "μεσου": "midst", "μεσον": "midst [acc]",
    "εναντι": "before", "εναντιον": "before",
    "περαν": "beyond", "εκειθεν": "from there", "εξω": "outside",
    "κυκλω": "around", "προσωπον": "face", "προσωπου": "of face",

    # Common verbs
    "λεγων": "saying", "λεγοντεσ": "saying [pl]", "λεγουσιν": "they say",
    "ελεγον": "they were saying", "ειπαν": "they said", "ειπον": "they said",
    "ελαλησεν": "[he] spoke", "λαλων": "speaking", "λαλουμεν": "we speak",
    "ποιειν": "to do", "ποιησεισ": "you shall do", "ποιησετε": "you [pl] shall do",
    "ποιησαι": "to do", "ποιει": "[he] does", "ποιουντεσ": "doing",
    "διδωσιν": "[he] gives", "δεδωκα": "I have given", "δουναι": "to give",
    "λαμβανειν": "to take", "λαβων": "having taken",
    "γινομαι": "I become", "γενηται": "it might become", "γενοιτο": "may it become",
    "γινεσθε": "be/become! [pl]",
    "εγενετο": "it came to be", "εγενηθη": "it became",
    "ηλθον": "they came", "ερχεται": "he comes",
    "εισηλθεν": "he entered", "εξηλθεν": "he went out",
    "ευρον": "I found", "ευρεθη": "was found",
    "εχοντεσ": "having", "εχομεν": "we have", "εχειν": "to have",
    "θελω": "I want", "θελετε": "you [pl] want", "θελημα": "will",
    "δυναται": "he is able", "δυνασθε": "you are able [pl]",
    "αποθανη": "he might die", "αποθανειται": "he will die",
    "φαγη": "he might eat", "φαγεσθε": "you [pl] shall eat",
    "ωμοσεν": "he swore", "ωσπερ": "just as",
    "ελπιζω": "I hope", "ελθω": "I might come",
    "εγραψα": "I wrote", "εγραφη": "it was written", "γραφω": "I write",
    "ηγειρεν": "[he] raised", "εγηγερται": "he has been raised",
    "εγειρεται": "he is raised",

    # Divine / theological
    "θεοσ": "God", "θεου": "of God", "θεω": "to God", "θεον": "God [acc]",
    "κυριοσ": "Lord", "κυριου": "of [the] Lord", "κυριω": "to [the] Lord",
    "κυριον": "[the] Lord [acc]",
    "χριστοσ": "Christ", "χριστου": "of Christ", "χριστω": "to Christ",
    "χριστον": "Christ [acc]", "ιησουσ": "Jesus", "ιησου": "of Jesus",
    "ιησουν": "Jesus [acc]", "ιησουσ": "Jesus",
    "πνευμα": "spirit", "πνευματοσ": "of spirit", "πνευματι": "in spirit",
    "πνευματικον": "spiritual", "πνευματικοσ": "spiritual [m]",
    "εκκλησια": "church/assembly", "εκκλησιασ": "of church/assembly",
    "εκκλησιαισ": "to churches/assemblies", "εκκλησιων": "of churches/assemblies",
    "ευαγγελιον": "gospel", "ευαγγελιου": "of gospel",
    "δοξα": "glory", "δοξαν": "glory [acc]", "δοξησ": "of glory", "δοξη": "glory [dat]",

    # Common nouns
    "σωμα": "body", "σωματοσ": "of body", "σωματι": "in body",
    "σαρξ": "flesh", "σαρκοσ": "of flesh", "σαρκα": "flesh [acc]",
    "σαρκι": "in flesh", "σαρκα": "flesh [acc]",
    "μελη": "members", "καρδια": "heart", "καρδιασ": "of heart",
    "ψυχη": "soul", "ψυχησ": "of soul", "ψυχην": "soul [acc]",
    "νομοσ": "law", "νομον": "law [acc]", "νομου": "of law", "νομω": "in law",
    "αγαπη": "love", "αγαπην": "love [acc]", "αγαπησ": "of love",
    "χαρισ": "grace", "χαριν": "grace", "χαριτι": "in grace",
    "αληθεια": "truth", "αληθειασ": "of truth",
    "δικαιοσυνη": "righteousness", "δικαιοσυνησ": "of righteousness",
    "εξουσια": "authority", "εξουσιαν": "authority [acc]",
    "αποστολοσ": "apostle", "αποστολουσ": "apostles [acc]",
    "αποστολων": "of apostles",
    "διακονια": "service/ministry", "διακονοι": "servants/ministers",
    "κοσμοσ": "world", "κοσμου": "of world", "κοσμω": "to world",
    "σοφια": "wisdom", "σοφιαν": "wisdom [acc]", "σοφιασ": "of wisdom",
    "γνωσισ": "knowledge", "γνωσεωσ": "of knowledge", "γνωσει": "in knowledge",
    "πιστισ": "faith", "πιστεωσ": "of faith", "πιστιν": "faith [acc]",
    "ελπισ": "hope", "σωτηριασ": "of salvation",
    "επιστολη": "letter", "επιστολων": "of letters",
    "οικοδομην": "edification/building",
    "κοινωνια": "fellowship/partnership",
    "χαρισματα": "gifts", "χαρισμα": "gift",
    "ελευθερια": "freedom", "ελευθεροσ": "free",
    "μακεδονιαν": "Macedonia [acc]", "μακεδονιασ": "of Macedonia",
    "αχρισ": "Ananias [?]", "αναθεμα": "curse",
    "ποτηριον": "cup", "ζυμη": "leaven",
    "εθνοσ": "nation", "εθνεσιν": "to nations",

    # Numerals
    "δεκα": "ten", "εικοσι": "twenty", "τριακοντα": "thirty",
    "τεσσερακοντα": "forty", "πεντηκοντα": "fifty", "εβδομηκοντα": "seventy",
    "εκατον": "hundred", "χιλιαδεσ": "thousands",
    "δυο": "two", "τρεισ": "three", "πεντε": "five", "επτα": "seven",

    # Adjectives
    "παντεσ": "all [m pl]", "πασασ": "all [f acc pl]", "πασαν": "all/every [f acc]",
    "παντασ": "all [acc pl m]", "παντοσ": "of all/every", "παντι": "to every",
    "παση": "all/every [f dat]", "πασησ": "of all/every [f]",
    "αλλοσ": "other", "αλλη": "other [f]", "αλλω": "to other",
    "ετεροσ": "another", "τοιουτοσ": "such", "τοιουτον": "such [n acc]",
    "τοιουτοι": "such ones", "πλεον": "more",
    "σοφοσ": "wise", "πιστοσ": "faithful", "νεκροι": "dead ones",

    # People / names
    "αβρααμ": "Abraham", "ισαακ": "Isaac", "ιακωβ": "Jacob",
    "ιουδασ": "Judah", "δαβιδ": "David", "δαυειδ": "David",
    "παυλοσ": "Paul", "τιτοσ": "Titus", "απολλω": "Apollos",
    "βαλααμ": "Balaam", "βαλακ": "Balak", "μωαβ": "Moab",
    "ιορδανην": "Jordan [acc]", "ιορδανου": "of Jordan",
    "σεινα": "Sinai", "καδησ": "Kadesh",
    "ρουβην": "Reuben", "συμεων": "Simeon", "λευι": "Levi",
    "ζαβουλων": "Zebulun", "ισσαχαρ": "Issachar", "ασηρ": "Asher",
    "γαδ": "Gad", "δαν": "Dan", "ναφθαλι": "Naphtali",
    "μανασση": "Manasseh", "εφραιμ": "Ephraim",
    "βασαν": "Bashan", "σηων": "Sihon", "γαλααδ": "Gilead",
    "αμορραιων": "of Amorites", "αμορραιοσ": "Amorite",
    "καθοτι": "according as", "τροπον": "manner",
    "παρενεβαλον": "they encamped", "απηραν": "they set out",
    "συνεταξεν": "[he] commanded", "ενετειλατο": "[he] commanded",
    "επισκεψισ": "census/visitation", "αριθμον": "number",
    "οσμην": "smell", "ευωδιασ": "of fragrance",
    "χιμαρον": "he-goat", "αμνον": "lamb", "κριον": "ram",
    "μοσχον": "calf", "ταυρον": "bull", "αιγων": "of goats",
    "προβατων": "of sheep", "κτηνη": "cattle",
    "ελαιω": "to oil", "σεμιδαλεωσ": "of fine flour",
    "δωρον": "gift", "θυσιαν": "sacrifice [acc]", "θυσιαι": "sacrifices",
    "σκηνη": "tent", "σκηνην": "tent [acc]", "σκηνησ": "of tent",
    "μαρτυριου": "of testimony", "μαρτυριον": "testimony",
    "παρεμβολησ": "of camp", "στρατοπεδον": "camp",
    "πολισ": "city", "πολεσιν": "in cities", "πολεων": "of cities",
    "ορουσ": "mountain", "ορια": "borders", "κληρονομησαι": "to inherit",
    "κληρονομιαν": "inheritance [acc]", "κληρω": "by lot",
    "δημοσ": "tribe/people", "δημουσ": "tribes/peoples",
    "φυλησ": "of tribe", "φυλην": "tribe [acc]", "φυλαι": "tribes",
    "πατριων": "of paternal [houses]", "πατρασιν": "to fathers",
    "συναγωγη": "congregation", "συναγωγην": "congregation [acc]",
    "συναγωγησ": "of congregation", "συναγωγαι": "congregations",
    "λευει": "Levi [dat]", "λευειταισ": "to Levites", "λευειτασ": "Levites [acc]",
    "ιερευσ": "priest", "αρχων": "ruler", "αρχοντεσ": "rulers",
    "εκαστοσ": "each one", "εκαστω": "to each",

    # Galatians / Corinthians specific
    "εθνη": "nations", "γλωσσαισ": "tongues/languages", "γλωσση": "tongue/language",
    "προφητευων": "prophesying", "προφητων": "of prophets",
    "βασιλειαν": "kingdom [acc]", "γυναικι": "to woman/wife", "ανδρι": "to man/husband",
    "ακροβυστια": "uncircumcision", "περιτομη": "circumcision",
    "ευηγγελισαμην": "I preached the gospel",
    "ευαγγελιζομαι": "I preach the gospel", "ευαγγελισασθαι": "to preach the gospel",
    "ευαγγελιω": "to gospel", "ευαγγελιου": "of gospel",
    "συνειδησιν": "conscience", "συνειδησιν": "conscience",
    "μεριμνα": "care/anxiety", "καυχημα": "boast", "καυχησισ": "boasting",
    "καυχησομαι": "I will boast", "υστερημα": "deficiency/lack",
    "κινδυνοισ": "in dangers", "περισσοτερωσ": "more abundantly",
    "οφθαλμοσ": "eye", "βρωμα": "food", "ναοσ": "temple",
    "παρουσια": "presence/coming", "υπαρχων": "being",
    "πορνεια": "fornication", "ελευθεροσ": "free",
    "δουλοσ": "slave/servant", "δουλου": "of slave",
    "κερδησω": "I will gain", "ζημιουμαι": "I suffer loss",
    "αληθειασ": "of truth",
}
GRC_LEX.update(EXTRA_GRC_3)

EXTRA_LAT_3 = {
    # Particles / conjunctions / adverbs
    "vos": "you [pl]", "nobis": "to us", "vobis": "to you [pl]",
    "aut": "or", "vel": "or", "sive": "or", "seu": "or",
    "ita": "thus", "itaque": "therefore", "igitur": "therefore",
    "quando": "when", "quoniam": "because", "quasi": "as",
    "usque": "until", "adhuc": "still", "subito": "suddenly",
    "statim": "immediately", "confestim": "immediately",
    "jam": "already", "modo": "now", "tunc": "then",
    "donec": "until", "numquid": "whether?",
    "quidquid": "whatever", "quicquid": "whatever",
    "etiam": "also", "quoque": "also",
    "ac": "and", "atque": "and", "at": "but",
    "hic": "here", "illic": "there", "illic": "there",
    "inde": "from there", "rursus": "again", "iterum": "again",
    "praeterea": "moreover", "insuper": "besides",
    "tamen": "however", "vero": "indeed", "enimvero": "indeed",

    # Demonstratives / pronouns
    "hii": "these", "hi": "these", "his": "to these",
    "hac": "this [f abl]", "hanc": "this [f acc]", "hoc": "this [n]",
    "hujus": "of this", "huius": "of this",
    "ille": "he/that", "illa": "she/that", "illud": "it/that",
    "illius": "of him/her", "illi": "to him/her", "illis": "to them",
    "illum": "him", "illam": "her", "illos": "them [m]", "illas": "them [f]",
    "ipse": "he himself", "ipsum": "himself/it", "ipsa": "herself",
    "ipsi": "to himself/themselves", "ipsis": "to them",
    "id": "it/that", "is": "he", "ea": "she/it",
    "eius": "of him/her", "ejus": "of him/her",
    "eorum": "of them [m]", "earum": "of them [f]",
    "eis": "to them", "ei": "to him/her",
    "quis": "who?", "quid": "what?", "quem": "whom", "quam": "whom/which [f]",
    "cujus": "whose", "cui": "to whom", "cuius": "whose",
    "quos": "whom [m pl]", "quas": "whom [f pl]", "quibus": "to whom/which",
    "quorum": "of whom [m]", "quarum": "of whom [f]",
    "vestrum": "of you [pl]", "vester": "your [m]", "vestra": "your [f/n pl]",
    "vestris": "to your [pl]", "vestri": "of you [pl]",
    "nostrum": "our", "noster": "our [m]", "nostra": "our [f/n]",
    "nostris": "to our", "nostri": "of us",
    "suae": "his/her [gen/dat f]", "sui": "of himself",
    "sibi": "to himself/themselves", "se": "himself/themselves",
    "suos": "his [acc pl m]", "suas": "his [acc pl f]",
    "suis": "his [dat/abl pl]", "suo": "his [dat/abl n]",

    # Verbs
    "fuit": "[he] was", "fuere": "they were", "fuerit": "he may have been",
    "erit": "he will be", "erunt": "they will be", "erant": "they were",
    "erat": "[he/she/it] was", "esset": "[he/she/it] might be",
    "essent": "they might be", "eris": "you will be",
    "sum": "I am", "es": "you are", "estis": "you are [pl]", "sunt": "they are",
    "dixit": "[he] said", "dixerunt": "they said", "dixitque": "and [he] said",
    "dicunt": "they say", "dicentes": "saying [pl]", "dicere": "to say",
    "dicebat": "[he] was saying", "dicebant": "they were saying",
    "dixerit": "he will have said", "dicet": "he will say",
    "dicit": "[he] says", "dicens": "saying",
    "fecit": "[he] made/did", "fecerunt": "they did", "fecisti": "you did",
    "faciam": "I will do", "faciat": "he may do", "faciet": "he will do",
    "facietis": "you [pl] will do", "facias": "you may do",
    "facere": "to do", "factum": "made [n]", "facta": "made [f]",
    "factus": "made [m]", "facti": "made [m pl]",
    "venit": "[he] came", "veniunt": "they come", "venerunt": "they came",
    "venire": "to come", "veni": "come!", "veni": "I came",
    "habet": "[he] has", "habent": "they have", "habebant": "they had",
    "habere": "to have", "habens": "having", "habentes": "having [pl]",
    "habetis": "you [pl] have",
    "potest": "[he] is able", "possunt": "they are able",
    "potuit": "[he] was able", "poterit": "[he] will be able",
    "coepit": "[he] began", "ceperunt": "they began",
    "cpit": "[he] began", "cperunt": "they began",
    "respondens": "answering", "respondit": "[he] answered",
    "responderunt": "they answered", "respondere": "to answer",
    "mitto": "I send", "misit": "[he] sent", "mittit": "[he] sends",
    "ponit": "[he] puts", "posuit": "[he] put",
    "oravit": "[he] prayed",
    "baptizavit": "[he] baptized", "baptizabantur": "they were baptized",
    "docebat": "[he] was teaching",
    "doctrina": "teaching", "praedicans": "preaching",
    "praedicavit": "[he] preached",
    "sanctificavit": "[he] sanctified",
    "justificavit": "[he] justified",
    "glorificavit": "[he] glorified",
    "peccata": "sins", "peccatis": "sins",
    "vidi": "I saw", "vidit": "[he] saw", "viderunt": "they saw",
    "videns": "seeing", "videre": "to see", "videte": "see [pl]",
    "vidisset": "he had seen", "viderit": "he will have seen",
    "audientes": "hearing [pl]", "audivit": "[he] heard",
    "abiit": "[he] went away", "egressus": "having gone out",
    "egressi": "having gone out [pl]", "profectique": "and having set out",
    "profecti": "having set out [pl]",
    "ingressus": "having entered",
    "ascendens": "ascending", "ascendit": "[he] ascended",
    "surge": "rise!", "surgens": "rising",
    "juravit": "[he] swore",
    "dedit": "[he] gave", "dedi": "I gave", "dedisti": "you gave",
    "dederit": "he will have given", "dederunt": "they gave",
    "accipit": "[he] takes", "accepit": "[he] took",
    "scripsit": "[he] wrote", "scriptum": "written",
    "tulit": "[he] bore/took", "stetit": "[he] stood",
    "misit": "[he] sent", "missus": "sent",
    "natus": "born", "nati": "were born", "genuit": "[he] begat",
    "creavit": "[he] created",
    "interrogavit": "[he] asked", "interrogabant": "they were asking",
    "interrogare": "to ask",
    "loquebatur": "[he] was speaking", "locutus": "having spoken",
    "locutusque": "and having spoken",
    "faciam": "I will make", "faciat": "he may make",
    "aperuit": "[he] opened", "clausit": "[he] closed",
    "comedere": "to eat", "manducare": "to eat",
    "manducabat": "[he] was eating", "manducaverunt": "they ate",
    "bibere": "to drink",

    # Divine / theological
    "deus": "God", "dei": "of God", "deo": "to God", "deum": "God [acc]",
    "dominus": "Lord", "domini": "of [the] Lord", "domino": "to [the] Lord",
    "dominum": "[the] Lord [acc]", "domine": "O Lord",
    "christus": "Christ", "christi": "of Christ", "christo": "to Christ",
    "christum": "Christ [acc]", "jesus": "Jesus", "iesus": "Jesus",
    "jesum": "Jesus [acc]", "iesum": "Jesus [acc]", "jesu": "of Jesus",
    "spiritus": "spirit", "spiritu": "in spirit", "spiritum": "spirit [acc]",
    "sanctus": "holy", "sancti": "of holy", "sanctum": "holy [n acc]",
    "sanctis": "to holy ones",
    "evangelium": "gospel", "evangelii": "of gospel",
    "gratia": "grace", "gratiae": "of grace", "gratiam": "grace [acc]",
    "pax": "peace",
    "fides": "faith", "fidem": "faith [acc]", "fidei": "of faith",
    "spes": "hope", "charitas": "charity/love",
    "baptisma": "baptism", "baptismum": "baptism [acc]",
    "remissionem": "remission [acc]", "peccatorum": "of sins",
    "penitentiae": "of repentance", "paenitentiae": "of repentance",

    # Common nouns
    "populus": "people", "populum": "people [acc]", "populi": "of people",
    "populo": "to people", "populum": "people [acc]",
    "populorum": "of peoples",
    "gens": "nation", "gentes": "nations", "gentium": "of nations",
    "gentibus": "to nations",
    "regnum": "kingdom", "regni": "of kingdom", "regno": "in kingdom",
    "rex": "king", "regem": "king [acc]", "regis": "of king",
    "reges": "kings",
    "tribu": "tribe", "tribus": "tribe/tribes", "tribuum": "of tribes",
    "familia": "family", "familias": "families [acc]",
    "familiae": "of family", "familiis": "to families",
    "cognatio": "kindred", "cognationes": "kindreds",
    "cognationum": "of kindreds", "cognationibus": "to kindreds",
    "domus": "house", "domum": "house [acc]", "domui": "to house",
    "domo": "house", "domibus": "houses",
    "tabernaculum": "tabernacle", "tabernaculi": "of tabernacle",
    "tabernaculo": "in tabernacle", "tabernacula": "tabernacles",
    "altare": "altar", "altaris": "of altar", "holocaustum": "burnt offering",
    "holocausta": "burnt offerings",
    "sacrificium": "sacrifice", "sacrificia": "sacrifices",
    "sacerdos": "priest", "sacerdotis": "of priest",
    "sacerdotes": "priests", "sacerdotum": "of priests",
    "levita": "Levite", "levitae": "Levites", "levitarum": "of Levites",
    "mundus": "world", "mundi": "of world", "mundum": "world [acc]",
    "caelum": "heaven", "caeli": "of heaven", "caelo": "in heaven",
    "caelis": "in heavens", "clum": "heaven", "clis": "in heavens",
    "terra": "earth", "terram": "earth [acc]", "terrae": "of earth",
    "terris": "in earths", "terr": "earth",
    "mare": "sea", "mari": "in sea", "mari": "to sea", "maris": "of sea",
    "sol": "sun", "luna": "moon", "stella": "star",
    "dies": "day", "diem": "day [acc]", "dierum": "of days", "diebus": "in days",
    "nox": "night", "noctem": "night [acc]", "nocte": "by night",
    "vespere": "evening", "mane": "morning",
    "aqua": "water", "aquas": "waters", "aquarum": "of waters",
    "ignis": "fire", "flumen": "river", "jordanis": "of Jordan",
    "jordanem": "Jordan [acc]", "jordanem": "Jordan [acc]",
    "via": "way", "viam": "way [acc]", "viae": "of way", "viis": "in ways",
    "iter": "journey", "itineris": "of journey",
    "loco": "place", "locum": "place [acc]", "loci": "of place",
    "medio": "midst", "medium": "midst [acc]",
    "cor": "heart", "corde": "in heart", "coram": "before",
    "anima": "soul", "animam": "soul [acc]", "animae": "of soul", "animas": "souls",
    "mens": "mind", "oculus": "eye", "oculis": "with eyes", "oculorum": "of eyes",
    "auris": "ear", "manus": "hand", "manu": "with hand", "manum": "hand [acc]",
    "manibus": "with hands", "pedes": "feet", "pedum": "of feet",
    "caput": "head", "capitis": "of head",
    "os": "mouth", "lingua": "tongue/language",
    "lex": "law", "legem": "law [acc]", "legis": "of law", "lege": "in law",
    "verbum": "word", "verbi": "of word", "verbo": "to word", "verba": "words",
    "sermo": "speech/word", "sermonem": "speech/word [acc]",
    "vocem": "voice [acc]", "voce": "with voice", "voces": "voices",
    "nomen": "name", "nomine": "in name", "nominis": "of name",
    "opus": "work", "opera": "works", "operibus": "in works",
    "gloria": "glory", "gloriam": "glory [acc]", "gloriae": "of glory",
    "justitia": "righteousness", "justitiam": "righteousness [acc]",
    "misericordia": "mercy", "misericordiam": "mercy [acc]",
    "veritas": "truth", "veritatem": "truth [acc]",
    "potestas": "power", "potestatem": "power [acc]",
    "virtus": "power/virtue", "virtutem": "power/virtue [acc]",
    "sanguis": "blood", "sanguinem": "blood [acc]", "sanguinis": "of blood",
    "caro": "flesh", "carnem": "flesh [acc]", "carnis": "of flesh",
    "panis": "bread", "panem": "bread [acc]", "panes": "loaves",
    "vinum": "wine", "templum": "temple", "templi": "of temple",
    "discipulus": "disciple", "discipuli": "disciples",
    "discipulis": "to disciples", "discipulos": "disciples [acc]",
    "magister": "teacher", "scriba": "scribe", "scribae": "scribes",
    "pharisaei": "Pharisees", "pharisaeorum": "of Pharisees",
    "pharisi": "Pharisees",
    "summi": "highest [pl]", "sacerdotum": "of priests",
    "pontifex": "high priest",
    "turbam": "crowd [acc]", "turba": "crowd", "turbae": "of crowd",
    "turbas": "crowds [acc]",
    "daemonium": "demon", "daemonia": "demons", "dmonia": "demons",
    "nubes": "clouds", "plenum": "full [n]", "pleni": "full [m pl]",
    "vestimenta": "garments", "vestimentum": "garment",

    # Family nouns
    "filius": "son", "filii": "of son", "filium": "son [acc]", "filii": "sons",
    "filiis": "to sons", "filiorum": "of sons", "filios": "sons [acc]",
    "filia": "daughter", "filiam": "daughter [acc]", "filiabus": "to daughters",
    "pater": "father", "patris": "of father", "patrem": "father [acc]",
    "patres": "fathers", "patrum": "of fathers", "patribus": "to fathers",
    "mater": "mother", "matris": "of mother", "matrem": "mother [acc]",
    "frater": "brother", "fratrem": "brother [acc]", "fratres": "brothers",
    "fratribus": "to brothers", "fratris": "of brother",
    "soror": "sister", "uxor": "wife", "uxorem": "wife [acc]",
    "vir": "man/husband", "viri": "of man/husband", "virum": "man/husband [acc]",
    "viros": "men [acc]",
    "mulier": "woman/wife", "mulierem": "woman/wife [acc]",
    "homo": "man", "hominem": "man [acc]", "hominis": "of man", "hominum": "of men",
    "infans": "infant", "parvulus": "little child",
    "puer": "boy", "puella": "girl",

    # Names
    "moyses": "Moses", "moysen": "Moses [acc]", "moysi": "to Moses", "mosi": "to Moses",
    "mosen": "Moses [acc]", "mosis": "of Moses",
    "aaron": "Aaron", "josue": "Joshua",
    "israel": "Israel", "israhel": "Israel",
    "abraham": "Abraham", "abram": "Abram", "isaac": "Isaac", "jacob": "Jacob",
    "juda": "Judah", "david": "David", "iesse": "Jesse",
    "joseph": "Joseph", "maria": "Mary", "paulus": "Paul", "petrus": "Peter",
    "joannes": "John", "iohannes": "John", "iohannem": "John [acc]", "joannem": "John [acc]",
    "iohannis": "of John",
    "pharao": "Pharaoh", "pharaonis": "of Pharaoh",
    "balaam": "Balaam", "balac": "Balak", "moab": "Moab",
    "ruben": "Reuben", "simeon": "Simeon", "levy": "Levi", "levi": "Levi",
    "zabulon": "Zebulun", "issachar": "Issachar", "aser": "Asher",
    "gad": "Gad", "dan": "Dan", "neptalim": "Naphtali", "nephtali": "Naphtali",
    "manasse": "Manasseh", "ephraim": "Ephraim",
    "basan": "Bashan", "seon": "Sihon", "sehon": "Sihon", "galaad": "Gilead",
    "amorrhaeis": "to Amorites", "amorrhaeorum": "of Amorites",
    "chanaan": "Canaan", "aegyptus": "Egypt", "aegypti": "of Egypt",
    "aegyptum": "Egypt [acc]", "aegypto": "to Egypt", "gypto": "to Egypt",
    "gypti": "of Egypt",
    "jerosolyma": "Jerusalem", "jerusalem": "Jerusalem", "jerosolymam": "Jerusalem [acc]",
    "galilaeae": "of Galilee", "galilaeam": "Galilee [acc]",
    "jordanis": "Jordan", "jordanem": "Jordan [acc]",

    # Numerals / adjectives
    "unus": "one", "unum": "one [acc n]", "duo": "two", "duos": "two [acc]",
    "duas": "two [f acc]", "tres": "three", "quattuor": "four",
    "quinque": "five", "sex": "six", "septem": "seven", "octo": "eight",
    "novem": "nine", "decem": "ten", "viginti": "twenty", "triginta": "thirty",
    "quadraginta": "forty", "quinquaginta": "fifty", "septuaginta": "seventy",
    "centum": "hundred", "milia": "thousands", "millia": "thousands",
    "omnis": "all/every", "omnes": "all [pl]", "omnium": "of all",
    "omnem": "every [acc]", "omni": "every", "omnibus": "to all",
    "totus": "whole", "tota": "whole [f]", "totum": "whole [n]",
    "magnus": "great", "magna": "great [f]", "magnum": "great [n]",
    "bonus": "good", "bonum": "good [n]", "bona": "good [pl n]",
    "malus": "bad", "malum": "bad [n]", "mala": "bad [pl n]",
    "parvus": "small", "multus": "much", "multi": "many [m]", "multae": "many [f]",
    "magis": "more", "maxime": "especially", "valde": "very",

    # Sacrificial / Levitical terms
    "agnus": "lamb", "agnos": "lambs", "arietem": "ram [acc]", "arietes": "rams",
    "vitulus": "calf", "vitulos": "calves",
    "bovem": "ox", "boves": "oxen", "boum": "of oxen",
    "capram": "goat [acc]", "capras": "goats",
    "libamenta": "libations", "spondae": "drink offerings",
    "siclus": "shekel", "siclos": "shekels",
    "oleo": "with oil", "olei": "of oil",
    "electa": "chosen", "elegerit": "he will have chosen",
    "praecepit": "[he] commanded", "praeceperat": "[he] had commanded",
    "praecepit": "[he] commanded", "prcepta": "precepts", "prcipio": "I command",
    "mandatum": "commandment", "mandata": "commandments", "mandatis": "commandments",
    "recensiti": "counted", "numerus": "number", "numerati": "counted [pl]",
    "anniculos": "year-old [pl]",
    "solitudo": "wilderness", "desertum": "wilderness",
    "caerimonias": "ceremonies", "cremonias": "ceremonies",
    "judicia": "judgments", "judicium": "judgment",
    "possessio": "possession", "possessionem": "possession [acc]",
    "sorte": "by lot", "sortem": "lot [acc]", "sortes": "lots",
    "turma": "company", "turmas": "companies",
    "adpendens": "weighing out", "appendens": "weighing out",
    "absque": "without", "extra": "outside", "intra": "within",
    "contra": "against", "adversus": "against",
    "prope": "near", "longe": "far",
    "nemo": "no one", "nihil": "nothing", "nullus": "none",
    "semen": "seed", "seminis": "of seed",
    "foederis": "of covenant", "fderis": "of covenant",
    "sanctuarii": "of sanctuary", "sanctuarium": "sanctuary",
    "sacrificia": "sacrifices", "victimas": "victims",
    "propitius": "gracious", "propitium": "propitious",
}
LAT_LEX.update(EXTRA_LAT_3)

KJV_FALLBACK = {}

def load_kjv_fallback(path):
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = re.match(r'^([A-Za-z0-9]+)\s+(\d+):(\d+)\s+(.+)$', line)
            if not m:
                continue
            b, c, v, text = m.groups()
            KJV_FALLBACK[(b, int(c), int(v))] = text

load_kjv_fallback(os.path.join(SRC_DIR, "kjv.txt"))


def normalize_greek_word(w):
    w = w.lower()
    w = unicodedata.normalize('NFKD', w)
    out = []
    for ch in w:
        cat = unicodedata.category(ch)
        if cat == 'Mn':
            continue
        if cat.startswith('L') or cat.startswith('N'):
            out.append(ch)
    w = ''.join(out)
    w = w.replace('ς', 'σ')
    # remove any leftover non-Greek/non-Latin trailing junk (numerals in parentheses, etc.)
    w = re.sub(r'[^\u0370-\u03ffa-z0-9]+$', '', w)
    return w


def normalize_latin_word(w):
    w = w.lower()
    w = unicodedata.normalize('NFKD', w)
    out = []
    for ch in w:
        if unicodedata.category(ch) == 'Mn':
            continue
        if unicodedata.category(ch).startswith('L') or unicodedata.category(ch).startswith('N'):
            out.append(ch)
    w = ''.join(out)
    w = re.sub(r'[^a-z0-9]+$', '', w)
    w = re.sub(r'^[^a-z0-9]+', '', w)
    return w


def normalize_hebrew_word(w):
    w = unicodedata.normalize('NFD', w)
    out = []
    for ch in w:
        cat = unicodedata.category(ch)
        if cat.startswith('P') or ch in '־':
            continue
        if cat.startswith('L') or cat.startswith('M'):
            out.append(ch)
    return ''.join(out)


def hebrew_word_split(text):
    parts = re.split(r'[\s\u05be]+', text)
    return [p.strip('׃:,.;!?־') for p in parts if p]


def lxx_word_split(text):
    parts = re.split(r'[\s,;:.·!?]+', text)
    return [p.strip() for p in parts if p]


def latin_word_split(text):
    parts = re.split(r'[\s,;:.!?]+', text)
    return [p.strip() for p in parts if p]


def tr_word_split(text):
    parts = re.split(r'[\s,;:.·!?]+', text)
    return [p.strip() for p in parts if p]


def lookup_best(tok, lex, normalizer, lang):
    if normalizer:
        key = normalizer(tok)
    else:
        key = tok
    if key in lex:
        return lex[key]
    # try without ending sigma / nu / final forms for Greek
    if lang == "grc":
        for end in ('σ', 'ν', 'τον', 'την', 'ται', 'ταισ', 'τοισ', 'οσ', 'ον', 'ησ', 'ουσ'):
            if key.endswith(end):
                base = key[:-len(end)]
                if base in lex:
                    return lex[base]
        # try swapping contracted prepositions
        if key.endswith('ʼ') or key.endswith('’') or key.endswith("'"):
            base = key[:-1]
            if base in lex:
                return lex[base]
        # map elided enclitics: μεν, δε, γε, τοι
        for suffix in ('μεν', 'δε', 'γε', 'τοι', 'τε', 'νυν'):
            if key.endswith(suffix):
                base = key[:-len(suffix)]
                if base in lex:
                    return lex[base] + f" [enclitic: {suffix}]"
    # try leading preposition contraction
    if lang == "grc" and key.startswith(('επ', 'απ', 'υπ', 'δι', 'κατ', 'μεθ', 'παρ', 'ανθ')):
        # try the full uncontracted forms
        for full in ('επι', 'απο', 'υπο', 'δια', 'κατα', 'μετα', 'παρα', 'αντι'):
            if key.startswith(full):
                rest = key[len(full):]
                if rest in lex:
                    return lex[full] + ' ' + lex[rest]
    # Latin enclitic -que
    if lang == "lat" and key.endswith('que'):
        base = key[:-3]
        if base in lex:
            return "and " + lex[base]
    return None


def gloss_token(tok, lex, normalizer=None, lang=""):
    g = lookup_best(tok, lex, normalizer, lang)
    if g:
        return g
    return f"[{tok}]"


def gloss_line(text, lex, normalizer, splitter, lang):
    words = splitter(text)
    if not words:
        return ""
    glossed = []
    for w in words:
        if not w:
            continue
        g = gloss_token(w, lex, normalizer, lang)
        glossed.append(g)
    return " ".join(glossed)


def process(source_fn, out_fn, books, lex, normalizer, splitter, lang):
    src_path = os.path.join(SRC_DIR, source_fn)
    out_path = os.path.join(OUT_DIR, out_fn)
    lines_out = []
    with open(src_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n').rstrip('\r')
            if not line:
                continue
            m = re.match(r'^([A-Za-z0-9]+)\s+(\d+):(\d+)\s+(.+)$', line)
            if not m:
                continue
            b, c, v, text = m.groups()
            if b not in books:
                continue
            if lang == "heb":
                text = text.replace('פ', '').replace('ס', '').strip()
            gloss = gloss_line(text, lex, normalizer, splitter, lang)
            k = (b, int(c), int(v))
            # If the gloss is mostly untranslated bracketed tokens, append KJV fallback as a guide.
            toks = gloss.split()
            bracketed = [x for x in toks if x.startswith('[')]
            if (not gloss or len(bracketed) > len(toks) * 0.55) and k in KJV_FALLBACK:
                fallback = KJV_FALLBACK[k]
                gloss = gloss + " | [KJV:] " + fallback if gloss else "[KJV:] " + fallback
            lines_out.append(f"{b} {c}:{v} {gloss}")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines_out))
        if lines_out:
            f.write('\n')
    return len(lines_out)


TASKS = [
    ("wlc.txt", "wlc-Gen-en.txt", ["Gen"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Exod-en.txt", ["Exod"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Ps-en.txt", ["Ps"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("lxx.txt", "lxx-Gen-en.txt", ["Gen"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Ps-en.txt", ["Ps"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("vulg.txt", "vulg-Gen-en.txt", ["Gen"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Ps-en.txt", ["Ps"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-John-en.txt", ["John"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Gen-en.txt", ["Gen"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Ps-en.txt", ["Ps"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-John-en.txt", ["John"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("tr.txt", "tr-Matt-en.txt", ["Matt"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-John-en.txt", ["John"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-Rom-en.txt", ["Rom"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
]

BATCH2_TASKS = [
    ("wlc.txt", "wlc-Lev-en.txt", ["Lev"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Num-en.txt", ["Num"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Deut-en.txt", ["Deut"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("lxx.txt", "lxx-Exod-en.txt", ["Exod"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Lev-en.txt", ["Lev"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("vulg.txt", "vulg-Exod-en.txt", ["Exod"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Lev-en.txt", ["Lev"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Matt-en.txt", ["Matt"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Exod-en.txt", ["Exod"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Lev-en.txt", ["Lev"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Matt-en.txt", ["Matt"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("tr.txt", "tr-Mark-en.txt", ["Mark"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-Luke-en.txt", ["Luke"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-Acts-en.txt", ["Acts"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
]

BATCH3_TASKS = [
    ("wlc.txt", "wlc-Josh-en.txt", ["Josh"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Judg-en.txt", ["Judg"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Ruth-en.txt", ["Ruth"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("lxx.txt", "lxx-Num-en.txt", ["Num"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Deut-en.txt", ["Deut"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("vulg.txt", "vulg-Num-en.txt", ["Num"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Deut-en.txt", ["Deut"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Mark-en.txt", ["Mark"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Num-en.txt", ["Num"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Deut-en.txt", ["Deut"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Mark-en.txt", ["Mark"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("tr.txt", "tr-1Cor-en.txt", ["1Cor"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-2Cor-en.txt", ["2Cor"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-Gal-en.txt", ["Gal"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
]

BATCH4_TASKS = [
    ("wlc.txt", "wlc-1Sam-en.txt", ["1Sam"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-2Sam-en.txt", ["2Sam"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-1Kgs-en.txt", ["1Kgs"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("lxx.txt", "lxx-Josh-en.txt", ["Josh"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Judg-en.txt", ["Judg"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Ruth-en.txt", ["Ruth"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("vulg.txt", "vulg-Luke-en.txt", ["Luke"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Acts-en.txt", ["Acts"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Luke-en.txt", ["Luke"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Acts-en.txt", ["Acts"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("tr.txt", "tr-Eph-en.txt", ["Eph"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-Phil-en.txt", ["Phil"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-Col-en.txt", ["Col"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-1Thess-en.txt", ["1Thess"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
]

BATCH5_TASKS = [
    ("wlc.txt", "wlc-2Kgs-en.txt", ["2Kgs"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-1Chr-en.txt", ["1Chr"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-2Chr-en.txt", ["2Chr"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("lxx.txt", "lxx-1Sam-en.txt", ["1Sam"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-2Sam-en.txt", ["2Sam"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-1Kgs-en.txt", ["1Kgs"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("vulg.txt", "vulg-Rom-en.txt", ["Rom"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-1Cor-en.txt", ["1Cor"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Rom-en.txt", ["Rom"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-1Cor-en.txt", ["1Cor"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("tr.txt", "tr-2Thess-en.txt", ["2Thess"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-1Tim-en.txt", ["1Tim"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-2Tim-en.txt", ["2Tim"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-Titus-en.txt", ["Titus"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
]

BATCH6_TASKS = [
    ("wlc.txt", "wlc-Esth-en.txt", ["Esth"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Job-en.txt", ["Job"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Prov-en.txt", ["Prov"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("lxx.txt", "lxx-2Kgs-en.txt", ["2Kgs"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-1Chr-en.txt", ["1Chr"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-2Chr-en.txt", ["2Chr"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("vulg.txt", "vulg-2Cor-en.txt", ["2Cor"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Gal-en.txt", ["Gal"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-2Cor-en.txt", ["2Cor"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Gal-en.txt", ["Gal"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("tr.txt", "tr-Phlm-en.txt", ["Phlm"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-Heb-en.txt", ["Heb"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-Jas-en.txt", ["Jas"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-1Pet-en.txt", ["1Pet"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
]

BATCH7_TASKS = [
    ("wlc.txt", "wlc-Eccl-en.txt", ["Eccl"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Song-en.txt", ["Song"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Isa-en.txt", ["Isa"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("lxx.txt", "lxx-Esth-en.txt", ["Esth"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Tob-en.txt", ["Tob"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Jdt-en.txt", ["Jdt"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("vulg.txt", "vulg-Eph-en.txt", ["Eph"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Phil-en.txt", ["Phil"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Eph-en.txt", ["Eph"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Phil-en.txt", ["Phil"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("tr.txt", "tr-2Pet-en.txt", ["2Pet"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-1John-en.txt", ["1John"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-2John-en.txt", ["2John"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-3John-en.txt", ["3John"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
]

BATCH8_TASKS = [
    ("wlc.txt", "wlc-Jer-en.txt", ["Jer"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Lam-en.txt", ["Lam"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Ezek-en.txt", ["Ezek"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("lxx.txt", "lxx-Wis-en.txt", ["Wis"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Sir-en.txt", ["Sir"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-PsSol-en.txt", ["PsSol"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("vulg.txt", "vulg-Col-en.txt", ["Col"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-1Thess-en.txt", ["1Thess"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-2Thess-en.txt", ["2Thess"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Col-en.txt", ["Col"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-1Thess-en.txt", ["1Thess"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-2Thess-en.txt", ["2Thess"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("tr.txt", "tr-Jude-en.txt", ["Jude"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
    ("tr.txt", "tr-Rev-en.txt", ["Rev"], GRC_LEX, normalize_greek_word, tr_word_split, "grc"),
]

BATCH9_TASKS = [
    ("wlc.txt", "wlc-Dan-en.txt", ["Dan"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Hos-en.txt", ["Hos"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Joel-en.txt", ["Joel"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("lxx.txt", "lxx-Job-en.txt", ["Job"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Prov-en.txt", ["Prov"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Song-en.txt", ["Song"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("vulg.txt", "vulg-1Tim-en.txt", ["1Tim"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-2Tim-en.txt", ["2Tim"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Titus-en.txt", ["Titus"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-1Tim-en.txt", ["1Tim"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-2Tim-en.txt", ["2Tim"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Titus-en.txt", ["Titus"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Phlm-en.txt", ["Phlm"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Phlm-en.txt", ["Phlm"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
]

BATCH10_TASKS = [
    ("wlc.txt", "wlc-Amos-en.txt", ["Amos"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Obad-en.txt", ["Obad"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Jonah-en.txt", ["Jonah"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("lxx.txt", "lxx-Isa-en.txt", ["Isa"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Jer-en.txt", ["Jer"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Lam-en.txt", ["Lam"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("vulg.txt", "vulg-Heb-en.txt", ["Heb"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Jas-en.txt", ["Jas"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-1Pet-en.txt", ["1Pet"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Heb-en.txt", ["Heb"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Jas-en.txt", ["Jas"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-1Pet-en.txt", ["1Pet"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-2Pet-en.txt", ["2Pet"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-2Pet-en.txt", ["2Pet"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
]

BATCH11_TASKS = [
    ("wlc.txt", "wlc-Mic-en.txt", ["Mic"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Nah-en.txt", ["Nah"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Hab-en.txt", ["Hab"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("lxx.txt", "lxx-Ezek-en.txt", ["Ezek"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-DanOG-en.txt", ["DanOG"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-DanTh-en.txt", ["DanTh"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("vulg.txt", "vulg-1John-en.txt", ["1John"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-2John-en.txt", ["2John"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-3John-en.txt", ["3John"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-1John-en.txt", ["1John"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-2John-en.txt", ["2John"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-3John-en.txt", ["3John"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Jude-en.txt", ["Jude"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Jude-en.txt", ["Jude"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
]

BATCH12_TASKS = [
    ("wlc.txt", "wlc-Zeph-en.txt", ["Zeph"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Hag-en.txt", ["Hag"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Zech-en.txt", ["Zech"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Mal-en.txt", ["Mal"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("lxx.txt", "lxx-Bar-en.txt", ["Bar"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-EpJer-en.txt", ["EpJer"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Hos-en.txt", ["Hos"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Joel-en.txt", ["Joel"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("vulg.txt", "vulg-Rev-en.txt", ["Rev"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Josh-en.txt", ["Josh"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Judg-en.txt", ["Judg"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Rev-en.txt", ["Rev"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Josh-en.txt", ["Josh"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Judg-en.txt", ["Judg"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
]

BATCH13_TASKS = [
    ("lxx.txt", "lxx-Amos-en.txt", ["Amos"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Obad-en.txt", ["Obad"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Jonah-en.txt", ["Jonah"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Mic-en.txt", ["Mic"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Nah-en.txt", ["Nah"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Hab-en.txt", ["Hab"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("vulg.txt", "vulg-Ruth-en.txt", ["Ruth"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-1Sam-en.txt", ["1Sam"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Ruth-en.txt", ["Ruth"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-1Sam-en.txt", ["1Sam"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-2Sam-en.txt", ["2Sam"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-1Kgs-en.txt", ["1Kgs"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-2Sam-en.txt", ["2Sam"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-1Kgs-en.txt", ["1Kgs"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
]

BATCH14_TASKS = [
    ("lxx.txt", "lxx-Zeph-en.txt", ["Zeph"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Hag-en.txt", ["Hag"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Zech-en.txt", ["Zech"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Mal-en.txt", ["Mal"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("vulg.txt", "vulg-2Kgs-en.txt", ["2Kgs"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-1Chr-en.txt", ["1Chr"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-2Chr-en.txt", ["2Chr"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-2Kgs-en.txt", ["2Kgs"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-1Chr-en.txt", ["1Chr"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-2Chr-en.txt", ["2Chr"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Esth-en.txt", ["Esth"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Job-en.txt", ["Job"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Esth-en.txt", ["Esth"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Job-en.txt", ["Job"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
]

BATCH15_TASKS = [
    ("lxx.txt", "lxx-1Macc-en.txt", ["1Macc"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-2Macc-en.txt", ["2Macc"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-3Macc-en.txt", ["3Macc"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-4Macc-en.txt", ["4Macc"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Odae-en.txt", ["Odae"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-BelOG-en.txt", ["BelOG"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("vulg.txt", "vulg-Prov-en.txt", ["Prov"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Eccl-en.txt", ["Eccl"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Song-en.txt", ["Song"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Prov-en.txt", ["Prov"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Eccl-en.txt", ["Eccl"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Song-en.txt", ["Song"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Isa-en.txt", ["Isa"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Isa-en.txt", ["Isa"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
]

BATCH16_TASKS = [
    ("lxx.txt", "lxx-BelTh-en.txt", ["BelTh"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-SusOG-en.txt", ["SusOG"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-SusTh-en.txt", ["SusTh"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Ezra-en.txt", ["Ezra"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("lxx.txt", "lxx-Neh-en.txt", ["Neh"], GRC_LEX, normalize_greek_word, lxx_word_split, "grc"),
    ("vulg.txt", "vulg-Jer-en.txt", ["Jer"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Lam-en.txt", ["Lam"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Ezek-en.txt", ["Ezek"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Jer-en.txt", ["Jer"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Lam-en.txt", ["Lam"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Ezek-en.txt", ["Ezek"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Dan-en.txt", ["Dan"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Dan-en.txt", ["Dan"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
]

BATCH17_TASKS = [
    ("vulg.txt", "vulg-Hos-en.txt", ["Hos"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Joel-en.txt", ["Joel"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Amos-en.txt", ["Amos"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Obad-en.txt", ["Obad"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Jonah-en.txt", ["Jonah"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Mic-en.txt", ["Mic"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Nah-en.txt", ["Nah"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Hos-en.txt", ["Hos"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Joel-en.txt", ["Joel"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Amos-en.txt", ["Amos"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Obad-en.txt", ["Obad"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Jonah-en.txt", ["Jonah"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Mic-en.txt", ["Mic"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Nah-en.txt", ["Nah"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
]

BATCH18_TASKS = [
    ("vulg.txt", "vulg-Hab-en.txt", ["Hab"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Zeph-en.txt", ["Zeph"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Hag-en.txt", ["Hag"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Zech-en.txt", ["Zech"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Mal-en.txt", ["Mal"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Ezra-en.txt", ["Ezra"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("vulg.txt", "vulg-Neh-en.txt", ["Neh"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Hab-en.txt", ["Hab"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Zeph-en.txt", ["Zeph"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Hag-en.txt", ["Hag"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Zech-en.txt", ["Zech"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Mal-en.txt", ["Mal"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Ezra-en.txt", ["Ezra"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
    ("clem.txt", "clem-Neh-en.txt", ["Neh"], LAT_LEX, normalize_latin_word, latin_word_split, "lat"),
]

BATCH19_TASKS = [
    ("wlc.txt", "wlc-Ezra-en.txt", ["Ezra"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
    ("wlc.txt", "wlc-Neh-en.txt", ["Neh"], HEB_LEX, normalize_hebrew_word, hebrew_word_split, "heb"),
]

if __name__ == "__main__":
    import sys
    os.makedirs(OUT_DIR, exist_ok=True)
    if len(sys.argv) > 1 and sys.argv[1] == "--batch2":
        tasks = BATCH2_TASKS
    elif len(sys.argv) > 1 and sys.argv[1] == "--batch3":
        tasks = BATCH3_TASKS
    elif len(sys.argv) > 1 and sys.argv[1] == "--batch4":
        tasks = BATCH4_TASKS
    elif len(sys.argv) > 1 and sys.argv[1] == "--batch5":
        tasks = BATCH5_TASKS
    elif len(sys.argv) > 1 and sys.argv[1] == "--batch6":
        tasks = BATCH6_TASKS
    elif len(sys.argv) > 1 and sys.argv[1] == "--batch7":
        tasks = BATCH7_TASKS
    elif len(sys.argv) > 1 and sys.argv[1] == "--batch8":
        tasks = BATCH8_TASKS
    elif len(sys.argv) > 1 and sys.argv[1] == "--batch9":
        tasks = BATCH9_TASKS
    elif len(sys.argv) > 1 and sys.argv[1] == "--batch10":
        tasks = BATCH10_TASKS
    elif len(sys.argv) > 1 and sys.argv[1] == "--batch11":
        tasks = BATCH11_TASKS
    elif len(sys.argv) > 1 and sys.argv[1] == "--batch12":
        tasks = BATCH12_TASKS
    elif len(sys.argv) > 1 and sys.argv[1] == "--batch13":
        tasks = BATCH13_TASKS
    elif len(sys.argv) > 1 and sys.argv[1] == "--batch14":
        tasks = BATCH14_TASKS
    elif len(sys.argv) > 1 and sys.argv[1] == "--batch15":
        tasks = BATCH15_TASKS
    elif len(sys.argv) > 1 and sys.argv[1] == "--batch16":
        tasks = BATCH16_TASKS
    elif len(sys.argv) > 1 and sys.argv[1] == "--batch17":
        tasks = BATCH17_TASKS
    elif len(sys.argv) > 1 and sys.argv[1] == "--batch18":
        tasks = BATCH18_TASKS
    elif len(sys.argv) > 1 and sys.argv[1] == "--batch19":
        tasks = BATCH19_TASKS
    else:
        tasks = TASKS
    for task in tasks:
        count = process(*task)
        print(f"{task[1]}: {count} verses")
    print(f"\nOutput directory: {OUT_DIR}")
