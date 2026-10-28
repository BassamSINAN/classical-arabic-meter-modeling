"""Block 1: kitāba ʿarūḍiyya (prosodic spelling) of a vocalised hemistich."""
FATHA, DAMMA, KASRA, SUKUN, SHADDA = "َ", "ُ", "ِ", "ْ", "ّ"
TANWIN = "ًٌٍ"                 # fatḥatān, ḍammatān, kasratān
MARKS = "ًٌٍَُِّْ"
MADD = "اوىي"
SOLAR = set("تثدذرزسشصضطظلن")
PREFIXES = set("وفبكل")                       # one-letter prefixes before the article
SATELLITE = {DAMMA: "و", FATHA: "ا", KASRA: "ي"}

# Words written without the alif they are pronounced with.
HIDDEN_ALIF = {"هذا": "هاذا", "هذه": "هاذه", "هؤلاء": "هاؤلاء", "ذلك": "ذالك",
               "لكن": "لاكن", "الله": "اللاه", "الرحمن": "الرحمان"}
STRIP = str.maketrans("", "", MARKS)


def split_letters(word):
    """List of [letter, marks]. Short vowels or šadda written on an alif move to the letter before."""
    out = []
    for ch in word:
        if ch in MARKS and out:
            out[-1][1] += ch
        elif ch not in MARKS:
            out.append([ch, ""])
    for k in range(1, len(out)):
        if out[k][0] in "اى" and out[k][1] and not any(t in out[k][1] for t in TANWIN):
            if not any(v in out[k - 1][1] for v in (FATHA, DAMMA, KASRA)):
                out[k - 1][1] += out[k][1]
            out[k][1] = ""
    return out


def join_letters(items):
    return "".join(ch + marks for ch, marks in items)


# Where the hidden alif goes (index in the bare word, after an optional one-letter prefix).
ALIF_AFTER = {"هذا": 1, "هذه": 1, "هؤلاء": 1, "ذلك": 1, "لكن": 1, "الله": 3, "لله": 2, "الرحمن": 5}


def restore_alif(word):
    """هذا -> هاذا, لكنها -> لاكنها, لله -> للاه: insert the hidden alif."""
    bare = word.translate(STRIP)
    for offset in (0, 1):
        if offset and (len(bare) < 2 or bare[0] not in PREFIXES):
            continue
        rest = bare[offset:]
        for key, pos in ALIF_AFTER.items():
            exact = key in ("الله", "لله", "الرحمن", "هذا", "هذه")
            if (rest == key) if exact else rest.startswith(key):
                items = split_letters(word)
                k = offset + pos
                return join_letters(items[:k] + [["ا", ""]] + items[k:])
    return word


def drop_wasl(items):
    """Hamzat al-waṣl after a one-letter prefix (وَال، بِال، فَاِعلم): the alif is not pronounced.

    Returns the letters without that alif, and whether the article was found.
    """
    if (len(items) > 2 and items[0][0] in PREFIXES and items[0][1] and items[1][0] == "ا"
            and (items[2][0] == "ل" or KASRA in items[1][1])):
        return items[:1] + items[2:], items[2][0] == "ل"
    return items, False


def article(items, start):
    """Article ال at position `start` (lām): sukūn before a moon letter, assimilated before a solar one."""
    if start + 1 >= len(items) or SHADDA in items[start][1]:
        return items
    nxt = items[start + 1]
    if nxt[0] in SOLAR:
        if SHADDA not in nxt[1]:
            nxt[1] += SHADDA
        return items[:start] + items[start + 1:]          # the lām disappears
    items[start][1] = SUKUN
    return items


def tanwin_alif(items):
    """يَوماً: the tanwīn written on (or before) a final alif belongs to the letter before it."""
    if len(items) >= 2 and items[-1][0] == "ا" and any(t in items[-1][1] + items[-2][1] for t in TANWIN):
        mark = "".join(t for t in TANWIN if t in items[-1][1] + items[-2][1])
        items[-2][1] = items[-2][1].translate(str.maketrans("", "", TANWIN)) + mark
        items = items[:-1]
    return items


def kitaba(hemistich):
    words = [split_letters(restore_alif(w)) for w in hemistich.split()]
    out = []
    for items in words:
        items = tanwin_alif(items)
        # Silent alif after the plural wāw (شَرَوا، جاهَدوا): not pronounced.
        if len(items) >= 3 and items[-1][0] == "ا" and items[-2][0] == "و" and not items[-2][1].strip(SUKUN):
            items = items[:-1]
        items, has_article = drop_wasl(items)
        if has_article:
            items = article(items, 1)
        # Word-initial hamzat al-waṣl (ا without hamza): not pronounced after another word;
        # a long vowel just before it is shortened, and the two words are read together.
        if items[0][0] == "ا" and not items[0][1].strip(KASRA) and out:
            items = items[1:]
            if items and items[0][0] == "ل" and len(items) > 1:
                items = article(items, 0)
            prev = out[-1]
            if prev[-1][0] in MADD and not prev[-1][1]:
                vowel = {"ا": FATHA, "ى": FATHA, "و": DAMMA, "ي": KASRA}[prev[-1][0]]
                prev = prev[:-1]
                if not any(v in prev[-1][1] for v in (FATHA, DAMMA, KASRA)):
                    prev[-1][1] += vowel
            out[-1] = prev + items
            continue
        out.append(items)
    # Ṣila: a final pronoun hāʾ after a vowelled letter, and the plural mīm (كُمُ، هُمُ، تُمُ)
    # with ḍamma, are pronounced long inside the hemistich (rabbihī, kumū).
    for w in out[:-1]:
        if len(w) >= 2 and w[-1][0] == "ه" and w[-1][1] in (DAMMA, KASRA) \
                and any(v in w[-2][1] for v in (FATHA, DAMMA, KASRA)) and SHADDA not in w[-2][1] or \
                (len(w) >= 2 and w[-1][0] == "ه" and w[-1][1] in (DAMMA, KASRA) and SHADDA in w[-2][1]):
            w.append(["و" if w[-1][1] == DAMMA else "ي", ""])
        elif len(w) >= 3 and w[-1][0] == "م" and w[-1][1] == DAMMA and w[-2][0] in "كهت" and DAMMA in w[-2][1]:
            w.append(["و", ""])
    last = out[-1]
    if len(last) >= 2 and last[-1][0] == "ه" and not last[-1][1] and any(v in last[-2][1] for v in (FATHA, DAMMA, KASRA)):
        last[-1][1] = KASRA
    # Išbāʿ: the final short vowel of the hemistich becomes long.
    for vowel, letter in SATELLITE.items():
        if last[-1][1].endswith(vowel) or last[-1][1] == vowel:
            last.append([letter, ""])
            break
    return " ".join(join_letters(w) for w in out)


if __name__ == "__main__":
    for h in ["لَوْ كانَ قَلْبِي مَعِي ما اخْتَرْتُ غَيْرَكُمُ", "وَلا رَضِيتُ سِواكُمْ فِي الهَوَى بَدَلا",
              "بَلَى وَالضُّحَى وَاللَّيلِ يَا بَدرُ إِذ سَجَى", "رَمَانِي بسَهمٍ مِن سِهامِ صُدُودِهِ"]:
        print(kitaba(h))
