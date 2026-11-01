"""Kitāba ʿarūḍiyya as an ordered list of rules.

Guiding principle of the kitāba ʿarūḍiyya: «كل ما يُنطق يُكتب، وما لا يُنطق لا يُكتب»
("everything pronounced is written, and nothing that is not pronounced is
written"). Every rule below applies this principle to one case: a hidden alif
is written (هذا → هاذا), a doubled letter is written twice (قَدَّمَ → قَدْدَمَ),
an alif that is not pronounced is removed (ما اخترت → مخترت), and so on.

Each rule is a small function that takes the words of a hemistich and returns
them rewritten. It is registered with a name, a one-line description and
examples (input, expected output) that serve as tests. To add a rule: write a
function, decorate it with @rule, give it at least one example.
"""
import unicodedata

FATHA, DAMMA, KASRA, SUKUN, SHADDA = "\u064E", "\u064F", "\u0650", "\u0652", "\u0651"
FATHATAN, DAMMATAN, KASRATAN = "\u064B", "\u064C", "\u064D"
TANWIN = {FATHATAN: FATHA, DAMMATAN: DAMMA, KASRATAN: KASRA}   # tanwīn -> its vowel
VOWELS = (FATHA, DAMMA, KASRA)
MARKS = "\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652"   # tanwīn, short vowels, šadda, sukūn
LONG = {"ا": FATHA, "ى": FATHA, "و": DAMMA, "ي": KASRA}       # long-vowel letter -> its short vowel
SOLAR = set("تثدذرزسشصضطظلن")
PREFIXES = set("وفبكلت")                                       # one-letter prefixes

RULES = []


def rule(name, description, examples):
    """Register a rule. The rules are applied in the order they are written."""
    def register(function):
        RULES.append({"name": name, "description": description,
                      "examples": examples, "apply": function})
        return function
    return register


# ---------------------------------------------------------------- tools

def norm(text):
    """Write the marks of each letter in one fixed order, so that equal texts compare equal.

    A letter can carry several marks (e.g. šadda and ḍamma), and they can be typed
    in any order: "دّ" + "ُ" or "دُ" + "ّ". On screen both look the same, but for
    the computer they are two different strings. Unicode defines a standard order
    for these marks (NFC normalisation); norm() rewrites the text in that order.

        norm("د" + SHADDA + DAMMA) == norm("د" + DAMMA + SHADDA)   # True
    """
    return unicodedata.normalize("NFC", text)


def bare(word):
    """The word with all its marks removed (vowels, tanwīn, šadda, sukūn).

    Used to recognise a word whatever its vocalisation: "هَذا", "هذَا" and "هذا"
    all give "هذا", so one dictionary entry is enough for the three spellings.

        bare("هَذَا") == "هذا"
    """
    return "".join(ch for ch in word if ch not in MARKS)


def cut_word_into_letters(word):
    """Cut a word into letters, each letter keeping its own marks.

    In a text, the marks (vowels, šadda, sukūn, tanwīn) are separate characters
    placed after their letter: هَذَا is 5 characters for 3 letters. Working on
    those characters directly is risky: inserting an alif "after the first
    letter" would put it between the ه and its fatḥa (هاَذَا, wrong).

    This function returns one [letter, marks] pair per letter, so that a rule can
    insert, remove or change letters without separating them from their marks:

        cut_word_into_letters("هَذَا")  == [["ه", FATHA], ["ذ", FATHA], ["ا", ""]]
        cut_word_into_letters("قَدَّمَ") == [["ق", FATHA], ["د", FATHA + SHADDA], ["م", FATHA]]

    A letter with several marks keeps them together, in the order they were typed.
    Almost every rule does:
        cut_word_into_letters(word) -> change the list -> join_letters_into_word(list)
    """
    out = []
    for ch in word:
        if ch in MARKS and out:
            out[-1][1] += ch
        elif ch not in MARKS:
            out.append([ch, ""])
    return out


def join_letters_into_word(items):
    """Glue a list of [letter, marks] back into a word: the inverse of cut_word_into_letters().

    Once a rule has changed the list, join_letters_into_word() gives back an
    ordinary text, which the next rule receives:

        items = cut_word_into_letters("هَذَا")          # [ه+FATHA] [ذ+FATHA] [ا]
        items = items[:1] + [["ا", ""]] + items[1:]   # [ه+FATHA] [ا] [ذ+FATHA] [ا]
        join_letters_into_word(items) == "هَاذَا"
    """
    return "".join(ch + marks for ch, marks in items)


def short_vowel_of(marks):
    """The short vowel (fatḥa, ḍamma or kasra) among the marks of a letter, or None.

    Used by the rules to ask "is this letter vowelled, and with which vowel?",
    whatever other marks it carries:

        short_vowel_of(FATHA)          == FATHA
        short_vowel_of(SHADDA + DAMMA) == DAMMA
        short_vowel_of(SUKUN)          is None
        short_vowel_of("")             is None
    """
    return next((v for v in VOWELS if v in marks), None)


def split_prefix(word):
    """Split a one-letter prefix (و ف ب ك ل ت) from the rest of the word.

    Returns (prefix, rest), the prefix keeping its marks; ("", word) if the word
    does not start with such a letter or has only two letters. The function does
    not check that the split is meaningful: the rule that uses it does, by looking
    at the rest (e.g. it starts with ال, or it is a word of with_alif). Main use:
    the hamzat al-waṣl after a prefix, which is not pronounced.

        split_prefix("بالفُنْدُقِ") == ("ب", "الفُنْدُقِ")     # بالفندق -> بلفندق
        split_prefix("وَهَذا")     == ("وَ", "هَذا")
        split_prefix("وَلَدٌ")     == ("وَ", "لَدٌ")          # cut, but لد matches no rule
        split_prefix("لا")        == ("", "لا")             # two letters: not cut
    """
    items = cut_word_into_letters(word)
    if len(items) > 2 and items[0][0] in PREFIXES:
        return join_letters_into_word(items[:1]), join_letters_into_word(items[1:])
    return "", word


# ---------------------------------------------------------------- rules

@rule("alif marks",
      "Marks typed on an alif belong to the letter before it (a frequent typing habit "
      "in the corpus): لاَ is لَا, إلاَّ is إلَّا, لآِمِرِ is لِآمِرِ.",
      [("ولاَ", "ولَا"), ("إلاَّ", "إلَّا"), ("لآِمِرِ", "لِآمِرِ")])
def alif_marks(words):
    out = []
    for w in words:
        items = cut_word_into_letters(w)
        for k in range(1, len(items)):
            ch, marks = items[k]
            if ch in "اىآ" and marks and not any(t in marks for t in TANWIN):
                if not short_vowel_of(items[k - 1][1]):
                    items[k - 1][1] += marks
                items[k][1] = ""
        out.append(join_letters_into_word(items))
    return out


@rule("hidden alif",
      "Some words are pronounced with an alif that is not written: هذا is read hāḏā, الله allāh. "
      "Also after a one-letter prefix (وَهَذا، وَاللَّهِ), and for لكن / ذلك before a pronoun (لَكِنَّها).",
      [("هذا الأَمْرُ", "هاذا الأَمْرُ"), ("هَذا", "هَاذا"), ("لَكِنْ", "لَاكِنْ"),
       ("الرَّحْمَنِ", "الرَّحْمَانِ"), ("شَهِدَ اللَهُ", "شَهِدَ اللَاهُ"), ("لِلَّهِ", "لِلَّاهِ"),
       ("وَهَذا", "وَهَاذا"), ("وَاللَّهِ", "وَاللَّاهِ"), ("وَلَدٌ", "وَلَدٌ"),
       ("لَكِنَّها", "لَاكِنَّها"), ("وَلَكِنَّهُ", "وَلَاكِنَّهُ"), ("ذَلِكُمْ", "ذَالِكُمْ")])
def hidden_alif(words):
    # Bare word -> the same word with its hidden alif written.
    with_alif = {"هذا": "هاذا", "هذه": "هاذه", "ذلك": "ذالك", "لكن": "لاكن",
                 "الرحمن": "الرحمان", "الله": "اللاه", "لله": "للاه", "اللهم": "اللاهم"}

    # Words that keep their hidden alif before a pronoun suffix: لكنها، لكنه، ذلكم.
    with_suffix = {"لكن", "ذلك"}

    def key_of(word):
        # The dictionary entry this word belongs to, or None.
        b = bare(word)
        if b in with_alif:
            return b
        return next((k for k in with_suffix if b.startswith(k)), None)

    def insert(word, key):
        # How many letters come before the alif: the first place where the two spellings differ.
        n = next(i for i, (a, b) in enumerate(zip(key, with_alif[key])) if a != b)
        items = cut_word_into_letters(word)
        return join_letters_into_word(items[:n] + [["ا", ""]] + items[n:])   # every letter keeps its own marks

    out = []
    for w in words:
        prefix, rest = split_prefix(w)
        if key_of(w):
            w = insert(w, key_of(w))
        elif prefix and key_of(rest):
            w = prefix + insert(rest, key_of(rest))
        out.append(w)
    return out


@rule("article",
      "In the article ال, the lām is pronounced (with sukūn) before a moon letter, "
      "and assimilated before a sun letter, which is then doubled.",
      [("الهَوَى", "الْهَوَى"), ("الشَّمْسُ", "اشَّمْسُ"), ("الدُجى", "ادُّجى"),
       ("وَالضُّحَى", "وَاضُّحَى"), ("بِالقَلْبِ", "بِالْقَلْبِ"), ("بالقَلْبِ", "بالْقَلْبِ"),
       ("الَّذِي", "الَّذِي"), ("وَالِدِي", "وَالِدِي"), ("والي", "والي")])
def article(words):
    # Exceptions: words (bare) that start with prefix + ال but have no article: the
    # و / ب belongs to the word itself. Only needed when the lām has no vowel in the
    # text (a vowelled lām, as in وَالِدِي, is recognised without this list).
    # Known limit: the list is filled as cases appear in the corpus.
    not_article = {"والي", "بالي", "والد"}

    def apply(word):
        # The word starts with ال (no prefix here).
        items = cut_word_into_letters(word)
        if len(items) < 3 or SHADDA in items[1][1] or short_vowel_of(items[1][1]):
            return word                  # too short; الّذي; or a vowelled lām (وَالِدِي): not an article
        nxt = items[2]
        if nxt[0] in SOLAR:
            if SHADDA not in nxt[1]:
                nxt[1] = SHADDA + nxt[1]
            items = items[:1] + items[2:]                         # lām dropped
        else:
            items[1][1] = SUKUN                                   # lām with sukūn
        return join_letters_into_word(items)

    out = []
    for w in words:
        prefix, rest = split_prefix(w)
        if bare(w) in not_article:
            pass
        elif bare(w).startswith("ال"):
            w = apply(w)
        elif prefix and bare(rest).startswith("ال"):              # وَال، بِال
            w = prefix + apply(rest)
        out.append(w)
    return out


@rule("šadda",
      "A doubled letter is written twice, as it is pronounced: the first copy with sukūn, "
      "the second with the vowel (قَدَّمَ → قَدْدَمَ).",
      [("قَدَّمَ", "قَدْدَمَ"), ("رَبُّنا", "رَبْبُنا"), ("اشَّمْسُ", "اشْشَمْسُ")])
def shadda(words):
    out = []
    for w in words:
        items = []
        for ch, marks in cut_word_into_letters(w):
            if SHADDA in marks:
                items += [[ch, SUKUN], [ch, marks.replace(SHADDA, "")]]
            else:
                items.append([ch, marks])
        out.append(join_letters_into_word(items))
    return out


@rule("tanwīn",
      "The tanwīn is pronounced as a vowel followed by a nūn sākin: رَجُلٌ → رَجُلُنْ. "
      "A final alif or yāʾ that only carries the tanwīn (يَوْماً، حَصىً) is not pronounced. "
      "At the end of the hemistich (pause), only the vowel remains.",
      [("رَجُلٌ قَامَ", "رَجُلُنْ قَامَ"), ("يَوْماً مِنَ", "يَوْمَنْ مِنَ"),
       ("حَصىً لَهُ", "حَصَنْ لَهُ"), ("جَاءَ رَجُلٌ", "جَاءَ رَجُلُ")])
def tanwin(words):
    out = []
    for k, w in enumerate(words):
        items = cut_word_into_letters(w)
        # A tanwīn written on (or next to) a final alif / alif maqṣūra belongs to the letter before it.
        if len(items) >= 2 and items[-1][0] in "اى" and any(t in items[-1][1] + items[-2][1] for t in TANWIN):
            mark = next(t for t in TANWIN if t in items[-1][1] + items[-2][1])
            items = items[:-1]
            items[-1][1] = "".join(m for m in items[-1][1] if m not in TANWIN and m not in VOWELS) + mark
        last = items[-1]
        mark = next((t for t in TANWIN if t in last[1]), None)
        if mark:
            last[1] = last[1].replace(mark, TANWIN[mark])
            if k < len(words) - 1:
                items.append(["ن", SUKUN])        # inside the hemistich: the nūn is pronounced
        out.append(join_letters_into_word(items))
    return out


@rule("tāʾ marbūṭa",
      "Inside the hemistich, a vowelled tāʾ marbūṭa is pronounced t (عِزَّةُ القَوْمِ → عِزَّتُ). "
      "At the end of the hemistich without a vowel, it is a pause: written ه.",
      [("عِزَّةُ القَوْمِ", "عِزَّتُ القَوْمِ"), ("رَحْمَةٍ", "رَحْمَتٍ"), ("جَاءَتْ رَحْمَة", "جَاءَتْ رَحْمَه")])
def taa_marbuta(words):
    out = []
    for k, w in enumerate(words):
        items = cut_word_into_letters(w)
        if items and items[-1][0] == "ة":
            if short_vowel_of(items[-1][1]) or any(t in items[-1][1] for t in TANWIN):
                items[-1][0] = "ت"
            elif k == len(words) - 1:
                items[-1][0] = "ه"
        out.append(join_letters_into_word(items))
    return out


@rule("silent letters",
      "Letters written but not pronounced are removed: the alif after the plural wāw "
      "(جاهَدوا → جاهَدو), the wāw of عَمْرو and of أُولَئِك.",
      [("جاهَدوا", "جاهَدو"), ("شَرَوا", "شَرَو"), ("عَمْرٌو", "عَمْرٌ"), ("أُولَئِكَ", "أُلَئِكَ")])
def silent_letters(words):
    out = []
    for w in words:
        items = cut_word_into_letters(w)
        b = bare(w)
        if len(items) >= 3 and items[-1][0] == "ا" and items[-2][0] == "و" and not short_vowel_of(items[-2][1]):
            items = items[:-1]                                   # alif al-fāṣila
        elif b == "عمرو":
            items = items[:-1]
        elif b.startswith(("أولئك", "أولو", "أولي", "أولات")):
            items = items[:1] + items[2:]
        out.append(join_letters_into_word(items))
    return out


@rule("madda",
      "آ is a hamza followed by a long ā: it is written أَا.",
      [("آمَالِي", "أَامَالِي"), ("القُرْآنِ", "القُرْأَانِ")])
def madda(words):
    return [w.replace("آ", "أ" + FATHA + "ا") for w in words]


@rule("hamzat al-waṣl (start)",
      "At the start of the hemistich, the hamzat al-waṣl is pronounced: with a fatḥa "
      "for the article (الْهَوَى → أَلْهَوَى), with a kasra otherwise (اخْتَرْ → إِخْتَرْ).",
      [("الْهَوَى غَلَبْ", "أَلْهَوَى غَلَبْ"), ("اشْشَمْسُ", "أَشْشَمْسُ"), ("اخْتَرْ", "إِخْتَرْ")])
def wasl_start(words):
    items = cut_word_into_letters(words[0])
    if len(items) < 2 or items[0][0] != "ا":
        return words
    vowel = short_vowel_of(items[0][1])
    if not vowel:
        is_article = (items[1][0] == "ل" and SUKUN in items[1][1]) or \
                     (len(items) > 2 and items[1][0] == items[2][0] and SUKUN in items[1][1])
        vowel = FATHA if is_article else KASRA
    items[0] = ["أ" if vowel != KASRA else "إ", vowel]
    return [join_letters_into_word(items)] + words[1:]


@rule("hamzat al-waṣl (prefix)",
      "After a one-letter prefix, the hamzat al-waṣl is not pronounced: وَالضُّحَى → وَضْضُحَى, "
      "بِالْقَلْبِ → بِلْقَلْبِ, فَاِعْلَمْ → فَعْلَمْ. The prefix may be written without its vowel (بالْفُنْدُقِ).",
      [("وَاضْضُحَى", "وَضْضُحَى"), ("بِالْقَلْبِ", "بِلْقَلْبِ"), ("فَاِعْلَمْ", "فَعْلَمْ"),
       ("بالْفُنْدُقِ", "بلْفُنْدُقِ"), ("فَاضِلٌ", "فَاضِلٌ"), ("كانَ", "كانَ")])
def wasl_prefix(words):
    out = []
    for w in words:
        prefix, rest = split_prefix(w)
        items = cut_word_into_letters(rest)
        # prefix + ا (no mark, or kasra) + a letter with sukūn: the ا is a hamzat al-waṣl.
        if (prefix and items[0][0] == "ا" and items[0][1] in ("", KASRA)
                and (SUKUN in items[1][1] or items[0][1] == KASRA)):
            w = prefix + join_letters_into_word(items[1:])
        out.append(w)
    return out


@rule("hamzat al-waṣl",
      "A word-initial alif without hamza is not pronounced after another word; "
      "a long vowel just before it is shortened, and both words are read together.",
      [("ما اخْتَرْتُ", "مَخْتَرْتُ"), ("فِي الهَوَى", "فِلهَوَى"), ("عَلَى الْأَرْضِ", "عَلَلْأَرْضِ")])
def hamzat_al_wasl(words):
    out = []
    for w in words:
        if out and w.startswith("ا"):
            prev = cut_word_into_letters(out[-1])
            if prev[-1][0] in LONG and not prev[-1][1]:            # ما -> مَ ; في -> فِ
                vowel = LONG[prev[-1][0]]
                prev = prev[:-1]
                if not short_vowel_of(prev[-1][1]):
                    prev[-1][1] += vowel
            out[-1] = join_letters_into_word(prev) + w[1:]
        else:
            out.append(w)
    return out


@rule("alif maqṣūra",
      "A final ى pronounced ā is written ا (الهَوَى → الهَوَا); after a kasra it is a yāʾ (فِى → فِي).",
      [("الهَوَى", "الهَوَا"), ("عَلَى", "عَلَا"), ("فِى", "فِي")])
def alif_maqsura(words):
    out = []
    for w in words:
        items = cut_word_into_letters(w)
        if items and items[-1][0] == "ى":
            items[-1][0] = "ي" if len(items) > 1 and KASRA in items[-2][1] else "ا"
        out.append(join_letters_into_word(items))
    return out


@rule("ṣila",
      "Inside the hemistich, the pronoun hāʾ after a vowelled letter is pronounced long "
      "(رَبِّهِ → رَبِّهِي، لَهُ → لَهُو), and so is the plural mīm with ḍamma (كُمُ → كُمُو).",
      [("إِلى رَبْبِهِ في", "إِلى رَبْبِهِي في"), ("لَهُ وَلَدٌ", "لَهُو وَلَدٌ"), ("فِيهِ رَجُلٌ", "فِيهِ رَجُلٌ"),
       ("لِغَيْرِكُمُ يَوْمَنْ", "لِغَيْرِكُمُو يَوْمَنْ")])
def sila(words):
    out = []
    for k, w in enumerate(words):
        items = cut_word_into_letters(w)
        if k < len(words) - 1 and len(items) >= 2:
            ch, marks = items[-1]
            before = items[-2]
            if ch == "ه" and marks in (DAMMA, KASRA) and short_vowel_of(before[1]):
                items.append(["و" if marks == DAMMA else "ي", ""])
            elif ch == "م" and marks == DAMMA and before[0] in "كهت" and DAMMA in before[1]:
                items.append(["و", ""])
        out.append(join_letters_into_word(items))
    return out


@rule("rhyme hāʾ",
      "A final hāʾ without a mark, at the end of the hemistich after a vowelled letter, "
      "is the rhyme pronoun: it is read with a vowel, lengthened by the išbāʿ.",
      [("لابِسِه", "لابِسِهِ")])
def rhyme_ha(words):
    items = cut_word_into_letters(words[-1])
    if len(items) >= 2 and items[-1][0] == "ه" and not items[-1][1] and short_vowel_of(items[-2][1]):
        items[-1][1] = KASRA
    return words[:-1] + [join_letters_into_word(items)]


@rule("išbāʿ",
      "The final short vowel of the hemistich is lengthened.",
      [("غَيْرَكُمُ", "غَيْرَكُمُو"), ("بَدَلا", "بَدَلا"), ("لابِسِهِ", "لابِسِهِي")])
def ishba(words):
    items = cut_word_into_letters(words[-1])
    vowel = short_vowel_of(items[-1][1])
    if vowel and SUKUN not in items[-1][1]:
        items.append([{DAMMA: "و", FATHA: "ا", KASRA: "ي"}[vowel], ""])
    return words[:-1] + [join_letters_into_word(items)]


# ---------------------------------------------------------------- engine

def kitaba(hemistich, trace=False):
    """Apply every rule in order. With trace=True, print which rules changed the text."""
    words = hemistich.split()
    for r in RULES:
        new = r["apply"](words)
        if trace and new != words:
            print(f"  [{r['name']}] {' '.join(words)}  →  {' '.join(new)}")
        words = new
    return norm(" ".join(words))


def check():
    """Run the examples of every rule; report the ones that fail."""
    failures = 0
    for r in RULES:
        for given, expected in r["examples"]:
            got = r["apply"](given.split())
            if norm(" ".join(got)) != norm(expected):
                failures += 1
                print(f"✗ {r['name']}: {given} → {' '.join(got)} (expected {expected})")
    print(f"{len(RULES)} rules, {sum(len(r['examples']) for r in RULES)} examples, {failures} failure(s)")


if __name__ == "__main__":
    check()
    print()
    for hemistich in ["لَوْ كانَ قَلْبِي مَعِي ما اخْتَرْتُ غَيْرَكُمُ", "وَلا رَضِيتُ سِواكُمْ فِي الهَوَى بَدَلا",
                      "بَلَى وَالضُّحَى وَاللَّيلِ يَا بَدرُ إِذ سَجَى", "رَمَانِي بسَهمٍ مِن سِهامِ صُدُودِهِ",
                      "إِن قَدَّمَ اللَهُ أَقواماً وَأَخَّرَني", "الجودُ أَخشَنُ مَسّاً يابَني مَطَرٍ"]:
        print(hemistich)
        print("→", kitaba(hemistich, trace=True))
        print()
