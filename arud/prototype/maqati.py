"""Block 2: split a kitāba into maqāṭiʿ (long "-" / short "ن")."""
import sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from kitaba import kitaba, split_letters, FATHA, DAMMA, KASRA, SUKUN, SHADDA, TANWIN

VOWELS = (FATHA, DAMMA, KASRA)
ALIFS = {"ا", "ى"}
HAMZA_START = {"أ", "إ", "آ"}


def units(text):
    """Letters of the hemistich as (letter, marks, is_word_start, is_word_end)."""
    out = []
    for word in text.split():
        items = split_letters(word)
        for k, (ch, marks) in enumerate(items):
            out.append((ch, marks, k == 0, k == len(items) - 1))
    return out


def harakat(text):
    """Sequence of 1 (mutaḥarrik) and 0 (sākin), one or two per letter."""
    items = units(text)
    states = []
    for i, (ch, marks, start, end) in enumerate(items):
        nxt = items[i + 1] if i + 1 < len(items) else None
        has_vowel = any(v in marks for v in VOWELS + tuple(TANWIN))
        if SHADDA in marks:
            states.append(0)                          # doubled letter: first copy is sākin
        if ch == "آ":
            states += [1, 0]                          # hamza + long ā
        elif has_vowel:
            states.append(1)
            if any(t in marks for t in TANWIN):
                states.append(0)                      # tanwīn: an extra nūn sākin
        elif SUKUN in marks:
            states.append(0)
        elif ch == "ا" and i == 0:
            states.append(1)                          # hemistich-initial alif (al-): pronounced
        elif ch in ALIFS:
            states.append(0)                          # long ā
        elif ch in "وي" and not start and not (nxt and nxt[0] in ALIFS) and states and states[-1] == 1:
            states.append(0)                          # long ū / ī (or diphthong)
        elif start or ch == "إ" or (ch in "أؤئ" and i > 0 and items[i - 1][2] and items[i - 1][0] in "وفبكل"):
            states.append(1)                          # word start (also after a prefix), or إ
        elif nxt and not nxt[2] and (nxt[0] in ALIFS or (nxt[0] in "وي" and not nxt[1] and not (
                i + 2 < len(items) and not items[i + 2][2] and items[i + 2][0] in "اىوي"))):
            states.append(1)                          # unmarked consonant before a long vowel
        else:
            states.append(0)                          # unmarked consonant: sukūn not written
    return states


def maqati(text):
    """Group into syllables: mutaḥarrik + sākin = long "-", mutaḥarrik alone = short "ن"."""
    states = harakat(text)
    out, i = [], 0
    while i < len(states):
        if states[i] == 1 and i + 1 < len(states) and states[i + 1] == 0:
            out.append("-")
            i += 2
        elif states[i] == 1:
            out.append("ن")
            i += 1
        else:
            i += 1                                    # stray sākin (e.g. a final consonant): ignored
    return "".join(out)


if __name__ == "__main__":
    for h in ["لَوْ كانَ قَلْبِي مَعِي ما اخْتَرْتُ غَيْرَكُمُ", "وَلا رَضِيتُ سِواكُمْ فِي الهَوَى بَدَلا"]:
        print(maqati(kitaba(h)))
