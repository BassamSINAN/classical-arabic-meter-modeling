# Prototype of f (exploration)

First prototype of the scansion function `f`, following the chain of the
thesis (chapter 2): kitāba ʿarūḍiyya → maqāṭiʿ → tafāʿīl → baḥr.

- `kitaba.py`: prosodic spelling (hamzat al-waṣl, article, hidden alif, ṣila, išbāʿ, ...).
- `maqati.py`: split into long (`-`) and short (`ن`) syllables.
- `f.py`: recognise the tafāʿīl (with ziḥāfāt) and the baḥr, for ṭawīl, basīṭ, kāmil, wāfir.
- `evaluate.py`: run `f` on 40 random ṭawīl and basīṭ verses of the clean corpus.

Status: exploration, not validated. About 63% of verses recognised on fresh
samples; failures come from missing vowels in the text, some label errors in
Ashaar, and kitāba rules not yet written. Ziḥāfāt are accepted at any position.
