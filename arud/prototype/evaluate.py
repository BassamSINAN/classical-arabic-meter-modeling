"""Run f on a random sample of clean ṭawīl and basīṭ verses and report the hits.

Usage: python evaluate.py [seed]   (needs data/2_clean/ashaar_clean.parquet)
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
CLEAN = HERE.parent.parent / "data" / "2_clean"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(CLEAN))
import pandas as pd
from clean_ashaar import filter_bahr
from f import f
from kitaba import kitaba
from maqati import maqati

BAHR = {"طويل": "ṭawīl", "بسيط": "basīṭ"}
corpus = pd.read_parquet(CLEAN / "ashaar_clean.parquet")
sample = pd.concat([filter_bahr(corpus, b).sample(20, random_state=int(sys.argv[1]) if len(sys.argv) > 1 else 0)
                    for b in BAHR])
hits, rows = 0, []
for _, v in sample.iterrows():
    notes, found = f(v["sadr"], v["ajuz"])
    expected = BAHR[v["bahr"]]
    ok = expected in found
    hits += ok
    rows.append((ok, expected, list(found), notes, v["sadr"], v["ajuz"]))
print(f"{hits}/{len(sample)} verses recognised")
for ok, expected, found, notes, s, a in rows:
    if not ok:
        print(f"\n✗ expected {expected}, found {found}")
        print(f"  {s}  #  {a}")
        print(f"  {notes[0]}  #  {notes[1]}")
