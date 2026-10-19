# Algorithmic Modeling of Classical Arabic Meter

Code accompanying a master's thesis in Arabic Studies: automatic recognition of the *buḥūr*
(meters) of classical Arabic poetry. The thesis itself is written in French.

## Goal

Given a *bayt* (verse), determine whether it follows one of the *buḥūr* of
the *ʿarūḍ* tradition, and if so, which one. The approach follows the
processing chain formalised in Chapter 2 of the thesis:

1. *kitāba ʿarūḍiyya*: prosodic transcription of the verse;
2. *taqṭīʿ*: segmentation into *maqāṭiʿ* (short and long segments);
3. identification of the *tafāʿīl*, accounting for *zihāfāt* and *ʿilal*;
4. recognition of the *baḥr* by matching against the *mafātīḥ*.

Automation is limited to the four most frequent *buḥūr* in the classical
corpus (Golston & Riad, 1997): *ṭawīl*, *kāmil*, *wāfir* and *basīṭ*, which
together cover about 93% of attested verses.

## Project stages

| Stage | Content | Folders | Status |
|---|---|---|---|
| 1 | Corpus building: download, cleaning, statistics | `scripts/`, `data/` | to do |
| 2 | Rule-based algorithm `f(bayt)` grounded in *ʿarūḍ* rules | `arud/` | to do |
| 3 | Learning model trained on the errors of `f` | `model/` | to do, depending on data |
| 4 | Web interface | `web/` | to do |

## Directory structure

```
classical-arabic-meter-modeling/
├── README.md
├── data/
│   ├── raw/        corpora as downloaded (not versioned)
│   ├── clean/      cleaned corpora, ready to use
│   └── gold/       hand-annotated verses, reference for evaluating f
├── scripts/        stage 1: data pipeline
├── arud/           stage 2: the f(bayt) algorithm (planned modules)
│   ├── kitaba.py       kitāba ʿarūḍiyya
│   ├── taqti.py        segmentation into maqāṭiʿ
│   ├── tafail.py       tafāʿīl recognition
│   ├── zihafat.py      permitted variations
│   ├── buhur.py        mafātīḥ of the buḥūr
│   └── f.py            full pipeline
├── model/          stage 3: learning
├── web/            stage 4: interface
├── tests/          automated code checks
└── reports/        statistics and figures for the thesis
```

The modules in `arud/` mirror the sections of Chapter 2 of the thesis, so that
each file corresponds to a concept already defined there.

## Candidate corpora

- **MetRec** (Al-shaibani, Alyafeai & Ahmad, 2020): 55,440 verses labelled by
  *baḥr* (14 *buḥūr*). Initial findings: artificially balanced, no poet or era
  metadata, highly uneven vocalisation.
- **Ashaar** (`arbml/ashaar`, Hugging Face): about 254,000 poems with poet,
  era and *baḥr*. Priority source, as it allows filtering for classical poetry.

## Notation

As in the thesis: `ن` for a *maqṭaʿ qaṣīr* (short segment) and `-` for a
*maqṭaʿ ṭawīl* (long segment), read right to left.
