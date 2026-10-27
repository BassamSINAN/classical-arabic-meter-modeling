# 2. Clean corpus

`clean_ashaar.py` turns the raw Ashaar corpus into one verse per row, following
the decisions of `../1_raw/`:

1. split each poem into verses (*ṣadr*, *ʿaǧuz*), leaving out poems with an
   odd number of strings;
2. normalise the meter label into a *baḥr* and a variant (مجزوء, مخلع, ...),
   leaving out labels that are not *buḥūr*;
3. keep the verses with an adjusted vocalisation ratio above 0.7;
4. remove the *tatwīl* and extra spaces;
5. remove duplicates on the text without diacritics.

Run `python clean_ashaar.py` to write `ashaar_clean.parquet` (not versioned).
Columns: `sadr`, `ajuz`, `bahr`, `variant`, `poet`, `era`, `source`,
`adjusted_ratio`.

`filter_bahr(verses, "طويل")` returns the verses of one *baḥr*, without its
variants unless `variants=True`. Variants will only be studied once the main
objectives are reached.

`clean_tawil.ipynb` gives a quick look at the *ṭawīl* verses.
