"""Blocks 3-4: recognise the tafāʿīl and the baḥr of a verse (the function f)."""
import sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from kitaba import kitaba
from maqati import maqati

# Each tafʿīla with its allowed forms: (pattern, name, ziḥāf). "-" long, "ن" short.
TAFAIL = {
    "faʿūlun":     [("ن--", "فَعُولُن", None), ("ن-ن", "فَعُولُ", "qabḍ")],
    "mafāʿīlun":   [("ن---", "مَفَاعِيلُن", None), ("ن-ن-", "مَفَاعِلُن", "qabḍ"), ("ن--ن", "مَفَاعِيلُ", "kaff"), ("ن--", "فَعُولُن", "ḥaḏf")],
    "mustafʿilun": [("--ن-", "مُسْتَفْعِلُن", None), ("ن-ن-", "مُتَفْعِلُن", "ḫabn"), ("-نن-", "مُسْتَعِلُن", "ṭayy")],
    "fāʿilun":     [("-ن-", "فَاعِلُن", None), ("نن-", "فَعِلُن", "ḫabn"), ("--", "فَعْلُن", "qaṭʿ")],
    "mutafāʿilun": [("نن-ن-", "مُتَفَاعِلُن", None), ("--ن-", "مُتْفَاعِلُن", "iḍmār")],
    "mufāʿalatun": [("ن-نن-", "مُفَاعَلَتُن", None), ("ن---", "مُفَاعَلْتُن", "ʿaṣb")],
}
# Tāmm form of each baḥr, per hemistich (its miftāḥ).
BUHUR = {
    "ṭawīl": ["faʿūlun", "mafāʿīlun", "faʿūlun", "mafāʿīlun"],
    "basīṭ": ["mustafʿilun", "fāʿilun", "mustafʿilun", "fāʿilun"],
    "kāmil": ["mutafāʿilun", "mutafāʿilun", "mutafāʿilun"],
    "wāfir": ["mufāʿalatun", "mufāʿalatun", "faʿūlun"],
}

def match(notation, feet):
    """All ways to cut the notation into the given feet; each way is a list of forms."""
    if not feet:
        return [[]] if notation == "" else []
    ways = []
    for pattern, arabic, zihaf in TAFAIL[feet[0]]:
        if notation.startswith(pattern):
            for rest in match(notation[len(pattern):], feet[1:]):
                ways.append([(pattern, arabic, zihaf)] + rest)
    return ways

def f(sadr, ajuz):
    """Return the buḥūr whose miftāḥ fits both hemistichs, with the tafāʿīl found."""
    notes = [maqati(kitaba(h)) for h in (sadr, ajuz)]
    found = {}
    for bahr, feet in BUHUR.items():
        ways = [match(n, feet) for n in notes]
        if all(ways):
            found[bahr] = [w[0] for w in ways]
    return notes, found

if __name__ == "__main__":
    sadr = "لَوْ كانَ قَلْبِي مَعِي ما اخْتَرْتُ غَيْرَكُمُ"
    ajuz = "وَلا رَضِيتُ سِواكُمْ فِي الهَوَى بَدَلا"
    notes, found = f(sadr, ajuz)
    print("notation:", notes)
    for bahr, halves in found.items():
        print(f"baḥr: {bahr}")
        for name, half in zip(("ṣadr", "ʿaǧuz"), halves):
            print(f"  {name:6} " + "  ".join(a for _, a, _ in half))
            print(f"  {'':6} ziḥāfāt: " + ", ".join(f"{a} ({z})" for _, a, z in half if z) )
    if not found:
        print("no baḥr found")
