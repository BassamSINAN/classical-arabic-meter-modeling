# 1. Raw corpora

The corpora as downloaded, without any change. Each corpus has its own folder
with its download script and an exploration notebook.

| Folder | Corpus | Data versioned |
|---|---|---|
| `metrec/` | MetRec (Al-shaibani et al., 2020), 55,440 verses | yes |
| `ashaar/` | Ashaar (`arbml/ashaar` on Hugging Face), 254,630 poems | no (277 MB): run `download_ashaar.py` |

`vocalisation.ipynb` measures how vocalised both corpora are and compares
them. What we decided from this folder:

- **Ashaar only**: MetRec is almost entirely contained in Ashaar (95.6% of its
  verses, all of its *ṭawīl* verses).
- **Vocalisation**: a verse is kept if its adjusted ratio (diacritics per
  letter, without the letters that carry no mark) is above 0.7.
- **Structure**: poems with an odd number of strings are left out.
- **Meter labels**: they are normalised; labels that are not *buḥūr* are left
  out.
