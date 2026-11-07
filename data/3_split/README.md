# 3. Split of the corpus

This folder splits the clean corpus into a **training** part, used to build
`f`, a **validation** part, used to check it along the way, and a **test**
part, used only once, at the end.

## The parts

| Part | Share | Role |
|---|---|---|
| **Training (C)** | 75 % of the corpus | train `f` and `f*` |
| ↳ A | at most 60 % of C | train `f` (write its rules), step by step |
| ↳ B | at least 40 % of C | train the network of `f*`; never looked at while `f` is trained |
| **Validation** | 10 % | check `f` on new verses, tune the networks |
| **Test** | 15 % | used once, at the end: `f` alone, then `f*` |

**A is the part of C that `f` is trained on: it grows step by step, up to 60 %
of C. B is what is left of C when `f` is frozen: at least 40 % of C.**

## Why it is done this way

- **Whole poems**: verses of one poem look alike, so a poem is never split.
- **Each baḥr on its own**: every baḥr has the same proportions everywhere.
- **Training in steps**: `f` is trained on 0.5 % of C, then 1 %, 2 %, 5 %,
  10 %, ... up to 60 % (the *grid*), until the target is reached. Small steps
  first, where most rules are found. At least 40 % of C stays reserved for the
  network of `f*`.
- **Rare buḥūr** (المتدارك, المقتضب, المضارع: 58, 20 and 4 poems): a network
  learns from many errors of `f`; with a few dozen verses, it would have almost
  nothing to learn from, and could break answers that `f` got right. So there
  is no B and no `f*` for them: `f*` returns the answer of `f`. Their scores are
  only indicative.
- **Poems already seen** by the first prototype of `f` are put first in C.

## Tracking the steps

**`training_step.txt` holds a single line: the step reached, for example
`0.005`. Everything in C below this step is seen, everything else is not.**

**`seen_poems.tsv` is the history: one line per poem seen, with when and why.**

```
poem_id   bahr   step    date        reason
732       طويل   proto   2026-11-01  prototype of f (evaluate.py, 160 verses)
...
5021      طويل   0.005   2026-11-08  step 0.5 %
```

Both files are written by the code only, never by hand.

```python
from split_corpus import load_split, get_step, update_step, training_pool

corpus = load_split()
get_step()                        # -> 0.005: the step reached so far
train = training_pool(corpus)     # the verses of that step, and nothing else
# ... train f (write and test its rules) on `train`, measure on validation ...
update_step(0.01)                 # move up to the next step of the grid
```

## For the code

`python split_corpus.py` (after `../2_clean/clean_ashaar.py`) writes
`ashaar_split.parquet`, with two more columns: `split` (C, validation or test)
and `pool_share` (place of the poem in C, from 0 to 1). `split_corpus.ipynb`
shows the counts. `update_step` refuses a step outside `STEP_GRID` or below
the one reached. The `proto` lines of `seen_poems.tsv` must never be changed.
