"""Clean the Ashaar corpus: one well-vocalised verse per row, with a normalised baḥr.

Steps (decided in the notebooks of data/1_raw/):
1. split each poem into verses (ṣadr, ʿaǧuz); poems with an odd number of
   strings are left out;
2. normalise the meter label into a baḥr (طويل, كامل, ...) and a variant
   (مجزوء, مخلع, ...); labels that name none of the sixteen buḥūr are left out;
3. keep the verses with an adjusted vocalisation ratio above 0.7;
4. remove the tatwīl and extra spaces;
5. remove duplicates on the text without diacritics, keeping the most
   vocalised copy.

Run as a script to write ashaar_clean.parquet in this folder.
"""
import pathlib
import re

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
RAW = HERE.parent / "1_raw" / "ashaar"
OUTPUT = HERE / "ashaar_clean.parquet"

THRESHOLD = 0.7

# The sixteen buḥūr of classical ʿarūḍ.
BUHUR = ["طويل", "مديد", "بسيط", "وافر", "كامل", "هزج", "رجز", "رمل", "سريع",
         "منسرح", "خفيف", "مضارع", "مقتضب", "مجتث", "متقارب", "متدارك"]

DIACRITICS = re.compile("[\u064B-\u0652]")                 # fatḥatān ... sukūn
LETTERS = re.compile("[\u0621-\u063A\u0641-\u064A]")     # hamza ... yāʾ, tatwīl excluded
# Letters that carry no mark even in a fully vocalised text: ا, آ, ى,
# and و / ي without any mark (read as long vowels).
NO_MARK = re.compile("[\u0627\u0622\u0649]|[\u0648\u064A](?![\u064B-\u0652])")
TATWIL = "\u0640"


def parse_meter(label):
    """Split a meter label into (baḥr, variant), e.g. بحر مجزوء الطويل -> (طويل, مجزوء).

    The article ال is dropped from both, so المنهوك and منهوك give the same variant.

    Return (None, None) when the label names none of the sixteen buḥūr.
    """
    if not isinstance(label, str):
        return None, None
    bahr, others = None, []
    for word in label.split():
        if word == "بحر":
            continue
        name = word.removeprefix("ال")
        if bahr is None and name in BUHUR:
            bahr = name
        else:
            others.append(name)
    if bahr is None:
        return None, None
    return bahr, " ".join(others) or None


def adjusted_ratio(text):
    """Diacritics divided by the letters that can carry a mark."""
    letters = len(LETTERS.findall(text)) - len(NO_MARK.findall(text))
    return len(DIACRITICS.findall(text)) / letters if letters > 0 else 0.0


def tidy(text):
    """Remove the tatwīl and collapse spaces."""
    return " ".join(text.replace(TATWIL, "").split())


def load_raw():
    return pd.concat([pd.read_parquet(path) for path in sorted(RAW.glob("*.parquet"))],
                     ignore_index=True)


def clean(raw=None):
    """Return the cleaned corpus, one verse per row."""
    poems = load_raw() if raw is None else raw
    poems = poems[poems["poem verses"].map(len).pipe(lambda n: (n > 0) & (n % 2 == 0))]
    poems = poems.assign(source=poems["poem url"].str.extract(
        r"^(?:https?:)?//(?:www\.)?([^/]+)")[0])
    meters = poems["poem meter"].map(parse_meter)
    poems = poems.assign(bahr=meters.str[0], variant=meters.str[1])
    poems = poems[poems["bahr"].notna()]

    verses = poems[["bahr", "variant", "poet name", "poet era", "source", "poem verses"]].copy()
    verses["pair"] = verses["poem verses"].map(
        lambda v: [(v[i], v[i + 1]) for i in range(0, len(v), 2)])
    verses = verses.drop(columns="poem verses").explode("pair", ignore_index=True)
    verses["adjusted_ratio"] = verses["pair"].map(lambda p: adjusted_ratio(p[0] + " " + p[1]))
    verses = verses[verses["adjusted_ratio"] > THRESHOLD]

    verses["sadr"] = verses["pair"].str[0].map(tidy)
    verses["ajuz"] = verses["pair"].str[1].map(tidy)
    key = (verses["sadr"] + " # " + verses["ajuz"]).str.replace(DIACRITICS, "", regex=True)
    verses = (verses.assign(key=key.map(lambda k: " ".join(k.split())))
              .sort_values("adjusted_ratio", ascending=False)
              .drop_duplicates("key")
              .sort_index())

    verses = verses.rename(columns={"poet name": "poet", "poet era": "era"})
    columns = ["sadr", "ajuz", "bahr", "variant", "poet", "era", "source", "adjusted_ratio"]
    return verses[columns].reset_index(drop=True)


def filter_bahr(verses, bahr, variants=False):
    """Verses of one baḥr (e.g. "طويل"). Variants (مجزوء, ...) are left out unless asked."""
    selected = verses[verses["bahr"] == bahr]
    return selected if variants else selected[selected["variant"].isna()]


if __name__ == "__main__":
    corpus = clean()
    corpus.to_parquet(OUTPUT, index=False)
    print(f"{len(corpus):,} verses written to {OUTPUT.name}")
