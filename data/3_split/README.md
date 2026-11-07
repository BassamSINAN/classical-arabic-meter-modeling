# 3. Split of the corpus

`split_corpus.py` splits the clean corpus (`../2_clean/`) into a development
pool **C**, a **validation** set and a **test** set, and keeps track of the part
of C already used to write the rules of `f`.

Run `python split_corpus.py` (after `../2_clean/clean_ashaar.py`) to write
`ashaar_split.parquet` (not versioned): the clean corpus with two more columns,
`split` (C, validation or test) and `pool_share` (position of the poem in C,
from 0 to 1, within its *baḥr*). `split_corpus.ipynb` shows the lots and tiers
(counts only, never verses).

## Lots

| Lot | Share | Role |
|---|---|---|
| **A** | at most 60 % of C | write the rules of `f`, tier by tier |
| **B** | at least 40 % of C | train the network of `f*`; never looked at while `f` is written |
| **C** = A + B | 75 % of the corpus | development pool |
| **validation** | 10 % | check the rules of `f` on unseen verses, tune the networks |
| **test** | 15 % | used once, at the end: `f` alone, then `f*` |

C is not split into A and B in advance. **A is the part of C that `f` is
written on: it grows tier by tier, and is at most 60 % of C. B is what is left
of C when `f` is frozen: it is at least 40 % of C.** If `f` is frozen at an
earlier tier, A is smaller and B larger. C, validation and test make up the
corpus (75 + 10 + 15 = 100 %); A and B do not add to C, they divide it.

## Method, and the problems it answers

- **By poem.** The verses of a poem share poet, rhyme and style: if a poem had
  verses on both sides, the test would no longer be new. A poem is always in a
  single lot.
- **Baḥr by baḥr.** Each *baḥr* is cut separately, so that every lot has the
  same proportions of each *baḥr*. Small gaps come from the cut between two
  poems.
- **A hash, not a shuffle.** Within a *baḥr*, the poems are ordered by a hash of
  their identifier (`poem_rank`, seed 2026). With a global shuffle, removing a
  few poems from the corpus (as when the conflicting labels were removed)
  moved every poem; with a hash, each poem keeps its place, and so its lot.
- **A separate lot B.** On the verses used to write its rules, `f` looks better
  than it is (70 % of recognition on the 160 verses used to tune the prototype,
  against 63 % on new verses). A network trained on those verses would learn
  to copy `f`, not to correct its real errors. B is kept apart for it.
- **A boundary between A and B set by the data, not in advance.** `f` is
  written on growing tiers of C (`TIERS`: 0.5, 1, 2, 5, 10, 20, 30, 40, 50 and
  60 % of C), measured on the validation set, until the target is reached or
  the limit of 60 % is met. Finer steps at the start, where most rules are
  found. Each tier contains the previous one and takes the same share of every
  *baḥr*, so no *baḥr* can be used up. Verses can later move from B to A (they
  were never used), never the other way round: a lower limit is the safer
  choice.
- **Rare buḥūr** (المتدارك, المقتضب, المضارع: 58, 20 and 4 poems). With so few
  poems, the normal cut left them without validation verses, and a test of a
  poem or two. They have no `f*` (`f*` returns the answer of `f`) and no lot B.
  Their split is made on the number of poems (70 / 15 / 15), and their part of
  C is available from the first tier. Their scores are only indicative; their
  false alarms (`f` announcing one of them by mistake) are measured on the test
  of the other *buḥūr*.
- **Poems already seen.** The 154 poems of the 160 verses used to tune the first
  prototype of `f` (`arud/prototype/evaluate.py`) go first in C, so they are
  never in B, validation or test (`SEEN_POEMS`).

## Tracking the tiers

Two small data files keep the state of the development. They are written by
the code only (`update_tier`), never by hand, and are versioned, so that each
move to a new tier leaves a dated trace in the history of the repository.

**`development_tier.txt` holds a single line: the tier reached, for example
`0.005`. It is the only "state" of the development: everything in C below this
tier is seen, everything else is not.** It starts at `0.0` (before the first
tier).

**`seen_poems.tsv` is the history: one line per poem seen, with when and why.**

```
poem_id   bahr   tier    date        reason
732       طويل   proto   2026-11-01  prototype of f (evaluate.py, 160 verses)
...
5021      طويل   0.005   2026-11-08  tier 0.5 %
```

From the code:

```python
from split_corpus import load_split, get_tier, update_tier, development_pool

corpus = load_split()
get_tier()                        # -> 0.005: the tier reached so far
dev = development_pool(corpus)    # the verses of that tier, and nothing else
# ... write and test rules of f on `dev`, measure on validation ...
update_tier(0.01)                 # move up to the next tier
```

`update_tier` refuses a tier that is not in `TIERS` (so above the limit of
60 % too), or that is not higher than the tier reached: seen poems cannot be
"unseen". `development_pool(corpus)` uses the tier reached by default, so the
code cannot use more of C than the tier allows.
