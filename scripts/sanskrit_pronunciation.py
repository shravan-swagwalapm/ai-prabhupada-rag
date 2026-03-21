#!/usr/bin/env python3
"""
Sanskrit Pronunciation Preprocessor for ElevenLabs Voice Synthesis
Converts IAST diacriticals and Sanskrit terms to phonetic English that
ElevenLabs can pronounce via its Hindi phoneme set.

Prabhupada's ~200 most common Sanskrit terms are mapped to how he actually
pronounced them in his lectures.

Usage:
    from sanskrit_pronunciation import preprocess_for_voice
    voice_text = preprocess_for_voice("Kṛṣṇa says in Bhagavad-gītā 2.20...")
    # → "Krishna says in Bhagavad Geeta, chapter two, verse twenty..."
"""

import re

# =============================================================================
# PART 1: Common Sanskrit Terms — mapped to Prabhupada's actual pronunciation
# =============================================================================
# These are the terms Prabhupada used most frequently across his lectures.
# Phonetic spellings match how HE pronounced them (Bengali-accented English).

SANSKRIT_TERMS = {
    # --- Divine Names ---
    "Kṛṣṇa": "Krishna",
    "Krsna": "Krishna",
    "Rāma": "Raama",
    "Śrī": "Shree",
    "Śrīla": "Shreela",
    "Śrīmad": "Shreemad",
    "Viṣṇu": "Vishnu",
    "Nārāyaṇa": "Naaraayana",
    "Govinda": "Govinda",
    "Mādhava": "Maadhava",
    "Hari": "Hari",
    "Caitanya": "Chaitanya",
    "Mahāprabhu": "Mahaaprabhu",
    "Nityānanda": "Nityaananda",
    "Rādhā": "Raadhaa",
    "Rādhārāṇī": "Raadhaa Raanee",
    "Arjuna": "Arjuna",
    "Brahmā": "Brahmaa",
    "Śiva": "Shiva",
    "Śaṅkara": "Shankara",
    "Śaṅkarācārya": "Shankaraachaarya",

    # --- Core Philosophical Terms ---
    "ātmā": "aatmaa",
    "paramātmā": "paramaatmaa",
    "Paramātmā": "Paramaatmaa",
    "jīva": "jeeva",
    "jīvātmā": "jeevaatmaa",
    "brahman": "brahman",
    "Brahman": "Brahman",
    "Parabrahman": "Para-brahman",
    "māyā": "maayaa",
    "karma": "karma",
    "dharma": "dharma",
    "adharma": "adharma",
    "saṁsāra": "samsaara",
    "mokṣa": "moksha",
    "mukti": "mukti",
    "bhakti": "bhakti",
    "yoga": "yoga",
    "jñāna": "gyaana",
    "vijñāna": "vigyaana",
    "vairāgya": "vairaagya",
    "tattva": "tattva",
    "guṇa": "guna",
    "sattva": "sattva",
    "rajas": "rajas",
    "tamas": "tamas",
    "ahaṅkāra": "ahankaar",
    "buddhi": "buddhi",
    "manas": "manas",
    "citta": "chitta",
    "prāṇa": "praana",
    "puruṣa": "purusha",
    "prakṛti": "prakriti",
    "svabhāva": "svabhaava",
    "saṅkalpa": "sankalpa",
    "vikalpa": "vikalpa",
    "nirvāṇa": "nirvaana",
    "kaivalya": "kaivalya",

    # --- Yoga Types ---
    "karma-yoga": "karma yoga",
    "bhakti-yoga": "bhakti yoga",
    "jñāna-yoga": "gyaana yoga",
    "dhyāna-yoga": "dhyaana yoga",
    "aṣṭāṅga-yoga": "ashtaanga yoga",
    "rāja-yoga": "raaja yoga",
    "haṭha-yoga": "hatha yoga",

    # --- Scripture Names ---
    "Bhagavad-gītā": "Bhagavad Geeta",
    "Bhagavad-gita": "Bhagavad Geeta",
    "Bhāgavatam": "Bhaagavatam",
    "Śrīmad-Bhāgavatam": "Shreemad Bhaagavatam",
    "Upaniṣad": "Upanishad",
    "Vedānta": "Vedaanta",
    "Vedānta-sūtra": "Vedaanta Sootra",
    "Caitanya-caritāmṛta": "Chaitanya Charitaamrita",
    "Purāṇa": "Puraana",
    "Mahābhārata": "Mahaabhaarata",
    "Rāmāyaṇa": "Raamaayana",
    "Īśopaniṣad": "Eeshopanishad",

    # --- Devotional Practice ---
    "kīrtana": "keertana",
    "saṅkīrtana": "sankeertana",
    "mantra": "mantra",
    "mahā-mantra": "mahaa mantra",
    "japa": "japa",
    "pūjā": "poojaa",
    "ārati": "aarati",
    "darśana": "darshana",
    "sevā": "sevaa",
    "prasādam": "prasaadam",
    "prasāda": "prasaada",
    "tilaka": "tilaka",
    "tulasī": "tulasi",
    "śāstra": "shaastra",
    "guru": "guru",
    "ācārya": "aachaarya",
    "dīkṣā": "deekshaa",
    "sādhu": "saadhu",
    "sannyāsa": "sannyaasa",
    "sannyāsī": "sannyaasi",
    "gṛhastha": "grihastha",
    "brahmacārī": "brahmachaari",
    "vānaprastha": "vaanaprastha",
    "varṇāśrama": "varnaashrama",

    # --- Places and Abodes ---
    "Vṛndāvana": "Vrindaavana",
    "Vaikuṇṭha": "Vaikuntha",
    "Goloka": "Goloka",
    "Dvārakā": "Dwaarakaa",
    "Mathurā": "Mathuraa",
    "Jagannātha": "Jagannatha",
    "Kurukṣetra": "Kurukshetra",

    # --- Common Phrases Prabhupada Used ---
    "Hare Kṛṣṇa": "Hare Krishna",
    "Hare Rāma": "Hare Raama",
    "oṁ": "om",
    "namaḥ": "namaha",
    "praṇāma": "pranaam",
    "daṇḍavat": "dandavat",

    # --- Bhagavad Gita Key Terms ---
    "kṣetra": "kshetra",
    "kṣetra-jña": "kshetra-gya",
    "avyakta": "avyakta",
    "akṣara": "akshara",
    "vibhūti": "vibhooti",
    "avatāra": "avataar",
    "līlā": "leelaa",
    "rasa": "rasa",
    "prema": "prema",
    "sneha": "sneha",
    "karuṇā": "karunaa",
    "dayā": "dayaa",
    "kṣamā": "kshamaa",
    "ahiṁsā": "ahimsaa",
    "satya": "satya",
    "śānti": "shaanti",
    "sukha": "sukha",
    "duḥkha": "duhkha",
    "saṅga": "sanga",
    "tyāga": "tyaaga",
    "yajña": "yagya",
    "tapas": "tapas",
    "dāna": "daana",
    "śraddhā": "shraddhaa",
    "niṣkāma": "nishkaama",
    "sakāma": "sakaama",

    # --- Titles and Honorifics ---
    "Svāmī": "Swaami",
    "Gosvāmī": "Goswami",
    "Prabhupāda": "Prabhupaada",
    "Mahārāja": "Mahaaraaja",
    "Ṭhākura": "Thaakura",
    "dāsa": "daasa",
    "devī": "devi",
    "deva": "deva",

    # --- ISKCON Related ---
    "saṅkīrtana": "sankeertana",
    "Gauḍīya": "Gaudiya",
    "Vaiṣṇava": "Vaishnava",
    "sampradāya": "sampradaaya",

    # --- Verse Fragments Claude Quotes ---
    "na jāyate": "na jaayate",
    "kadāchin": "kadaachin",
    "nityaḥ": "nityaha",
    "śāśvataḥ": "shaashvataha",
    "purāṇaḥ": "puraanaha",

    # --- Terms from Bhagavatam Chunks ---
    "brahma-jyotir": "brahma jyotir",
    "vāsudevāya": "vaasudevaaya",
    "abhijñaḥ": "abhigyaha",

    # --- Compound Words Claude Generates ---
    "sat-cit-ānanda": "sat chit aananda",
    "sac-cid-ānanda": "sach chid aananda",
    "ādi-kavaye": "aadi kavaye",

    # --- Terms from Nectar of Instruction ---
    "atyāhāra": "atyaahaara",
    "prayāsa": "prayaasa",
    "niyamāgraha": "niyamaagraha",

    # --- Common Verb/Adjective Forms ---
    "jānāti": "jaanaati",
    "paśyati": "pashyati",
    "bhajanīya": "bhajaneeya",

    # --- Additional Divine Names & Avatars ---
    "Bhagavān": "Bhagavaan",
    "bhagavān": "bhagavaan",
    "Nṛsiṁha": "Nrisimha",
    "Narasiṁha": "Narasimha",
    "Varāha": "Varaaha",
    "kṣatriya": "kshatriya",
    "avatāras": "avataars",

    # --- Common Compound Terms ---
    "niṣkāma-karma": "nishkaama karma",
    "sādhu-saṅga": "saadhu sanga",
    "param brahman": "param brahman",
    "bhakti-yoga": "bhakti yoga",
}

# =============================================================================
# PART 2: IAST Diacritical → Phonetic Mappings
# =============================================================================
# For any Sanskrit words NOT in the dictionary above, these character-level
# replacements approximate correct pronunciation via Hindi phonemes.

IAST_PHONETIC_MAP = [
    # Must be ordered: longer sequences first to avoid partial matches
    ("kṣ", "ksh"),
    ("jñ", "gya"),
    ("śr", "shr"),
    ("ṣṭ", "sht"),
    ("ṇḍ", "nd"),
    ("ṅk", "nk"),
    ("ṅg", "ng"),
    # Note: NOT mapping "ch" → "chh" because it corrupts English words like "chapter", "change"
    # Sanskrit aspirated 'ch' (छ) is handled by specific terms in the dictionary above

    # Vowels (long)
    ("ā", "aa"),
    ("ī", "ee"),
    ("ū", "oo"),
    ("ṛ", "ri"),
    ("ṝ", "ree"),
    ("ai", "ai"),
    ("au", "au"),

    # Consonants
    ("ś", "sh"),
    ("ṣ", "sh"),
    ("ṭ", "t"),
    ("ḍ", "d"),
    ("ṇ", "n"),
    ("ñ", "ny"),
    ("ṅ", "ng"),
    ("ṁ", "m"),
    ("ḥ", "ha"),  # Visarga as soft 'ha'
    ("ḻ", "l"),
]

# =============================================================================
# PART 3: Verse Reference Normalization
# =============================================================================
# Convert "BG 2.20" or "Bhagavad-gītā 2.20" to spoken form

SCRIPTURE_ABBREVS = {
    "BG": "Bhagavad Geeta",
    "SB": "Shreemad Bhaagavatam",
    "CC": "Chaitanya Charitaamrita",
    "NOD": "Nectar of Devotion",
    "NOI": "Nectar of Instruction",
    "ISO": "Shree Eeshopanishad",
}


def _normalize_verse_references(text: str) -> str:
    """Convert verse references to spoken form.
    '2.20' → 'chapter two, verse twenty'
    'BG 2.20' → 'Bhagavad Geeta, chapter two, verse twenty'
    """
    # Number to word mapping (for chapters/verses up to 90)
    num_words = {
        0: "zero", 1: "one", 2: "two", 3: "three", 4: "four",
        5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
        10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen",
        14: "fourteen", 15: "fifteen", 16: "sixteen", 17: "seventeen",
        18: "eighteen", 19: "nineteen", 20: "twenty",
        21: "twenty-one", 22: "twenty-two", 23: "twenty-three",
        24: "twenty-four", 25: "twenty-five", 26: "twenty-six",
        27: "twenty-seven", 28: "twenty-eight", 29: "twenty-nine",
        30: "thirty", 31: "thirty-one", 32: "thirty-two", 33: "thirty-three",
        34: "thirty-four", 35: "thirty-five", 36: "thirty-six",
        37: "thirty-seven", 38: "thirty-eight", 39: "thirty-nine",
        40: "forty", 41: "forty-one", 42: "forty-two", 43: "forty-three",
        44: "forty-four", 45: "forty-five", 46: "forty-six",
        47: "forty-seven", 48: "forty-eight", 49: "forty-nine",
        50: "fifty", 51: "fifty-one", 52: "fifty-two", 53: "fifty-three",
        54: "fifty-four", 55: "fifty-five", 56: "fifty-six",
        57: "fifty-seven", 58: "fifty-eight", 59: "fifty-nine",
        60: "sixty", 61: "sixty-one", 62: "sixty-two", 63: "sixty-three",
        64: "sixty-four", 65: "sixty-five", 66: "sixty-six",
        67: "sixty-seven", 68: "sixty-eight", 69: "sixty-nine",
        70: "seventy", 71: "seventy-one", 72: "seventy-two",
        73: "seventy-three", 74: "seventy-four", 75: "seventy-five",
        76: "seventy-six", 77: "seventy-seven", 78: "seventy-eight",
        80: "eighty", 81: "eighty-one", 82: "eighty-two",
        83: "eighty-three", 84: "eighty-four", 85: "eighty-five",
        90: "ninety",
    }

    def num_to_word(n):
        if n in num_words:
            return num_words[n]
        return str(n)

    # Replace SB canto.chapter.verse first (3 numbers): "SB 10.14.8"
    sb_pattern = r'\bSB\s+(\d+)\.(\d+)\.(\d+)\b'
    def repl_sb(m):
        ca = num_to_word(int(m.group(1)))
        ch = num_to_word(int(m.group(2)))
        vs = num_to_word(int(m.group(3)))
        return f"Shreemad Bhaagavatam, canto {ca}, chapter {ch}, verse {vs}"
    text = re.sub(sb_pattern, repl_sb, text)

    # Replace other scripture abbreviation + verse: "BG 2.20" → "Bhagavad Geeta, chapter two, verse twenty"
    for abbrev, full_name in SCRIPTURE_ABBREVS.items():
        if abbrev == "SB":
            continue  # Already handled above
        pattern = rf'\b{abbrev}\s+(\d+)\.(\d+)\b'
        def repl_abbrev(m, name=full_name):
            ch = num_to_word(int(m.group(1)))
            vs = num_to_word(int(m.group(2)))
            return f"{name}, chapter {ch}, verse {vs}"
        text = re.sub(pattern, repl_abbrev, text)

    # Replace standalone verse refs in context: "2.20" after "chapter" or "verse"
    # But also standalone like "Bhagavad Geeta 2.20"
    def repl_verse_ref(m):
        ch = num_to_word(int(m.group(1)))
        vs = num_to_word(int(m.group(2)))
        return f"chapter {ch}, verse {vs}"

    # Handle "Geeta 2.20" or "Geeta, 2.20"
    def repl_geeta_ref(m):
        ch = num_to_word(int(m.group(1)))
        vs = num_to_word(int(m.group(2)))
        return f"Geeta, chapter {ch}, verse {vs}"
    text = re.sub(r'Geeta[,]?\s+(\d+)\.(\d+)', repl_geeta_ref, text)

    # Handle "Bhaagavatam 10.14.8" (canto.chapter.verse)
    def repl_sb_ref(m):
        ca = num_to_word(int(m.group(1)))
        ch = num_to_word(int(m.group(2)))
        vs = num_to_word(int(m.group(3)))
        return f"Bhaagavatam, canto {ca}, chapter {ch}, verse {vs}"
    text = re.sub(r'Bhaagavatam[,]?\s+(\d+)\.(\d+)\.(\d+)', repl_sb_ref, text)

    return text


def _apply_term_dictionary(text: str) -> str:
    """Replace known Sanskrit terms with phonetic equivalents.
    Sorted by length (longest first) to avoid partial matches.
    """
    sorted_terms = sorted(SANSKRIT_TERMS.items(), key=lambda x: len(x[0]), reverse=True)
    for sanskrit, phonetic in sorted_terms:
        text = text.replace(sanskrit, phonetic)
    return text


def _apply_iast_fallback(text: str) -> str:
    """Convert remaining IAST diacriticals to phonetic approximations."""
    for iast, phonetic in IAST_PHONETIC_MAP:
        text = text.replace(iast, phonetic)
    return text


def _clean_for_voice(text: str) -> str:
    """Remove characters that confuse voice synthesis."""
    # Remove markdown formatting
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*(.+?)\*', r'\1', text)        # *italic*
    text = re.sub(r'#{1,6}\s+', '', text)            # ### headers
    text = re.sub(r'`(.+?)`', r'\1', text)           # `code`

    # Remove brackets and parenthetical asides
    text = re.sub(r'\[([^\]]+)\]', r'\1', text)      # [bracketed]
    text = re.sub(r'\(([^)]{1,80})\)', r', \1,', text)  # (parenthetical) → commas

    # Replace em-dashes with pauses
    text = text.replace("—", ", ")
    text = text.replace("–", ", ")

    # Replace semicolons with periods (natural pauses)
    text = text.replace(";", ".")

    # Collapse multiple spaces/commas
    text = re.sub(r',\s*,', ',', text)
    text = re.sub(r'\s{2,}', ' ', text)

    return text.strip()


def preprocess_for_voice(text: str) -> str:
    """
    Full preprocessing pipeline for voice synthesis.
    Converts Sanskrit terms, IAST diacriticals, verse references,
    and markdown to clean phonetic text ElevenLabs can speak.

    Args:
        text: Raw answer text from Claude (may contain Sanskrit, markdown, verse refs)

    Returns:
        Clean phonetic text optimized for ElevenLabs voice synthesis
    """
    # Step 1: Replace known Sanskrit terms
    text = _apply_term_dictionary(text)

    # Step 2: Normalize verse references to spoken form
    text = _normalize_verse_references(text)

    # Step 3: Convert remaining IAST diacriticals
    text = _apply_iast_fallback(text)

    # Step 4: Clean markdown and problematic characters
    text = _clean_for_voice(text)

    return text
