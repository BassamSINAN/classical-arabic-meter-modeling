"""Split the clean corpus into a development pool C, a validation set and a test set.

Decided in progress/decisions_log.md of the notes (07/11), summed up in
README.md of this folder:
- by poem, baḥr by baḥr, poems ordered by a hash of their identifier;
- C (75 %), validation (10 %), test (15 %) of the verses of each baḥr;
- f is written on growing tiers of C (TIERS); what is left of C when f is
  frozen (B) is kept for the network of f*;
- the reached tier is kept in development_tier.txt, and the poems seen so far
  in seen_poems.tsv (which also holds the prototype poems, put first in C).
  Only update_tier writes them.

Run as a script to write ashaar_split.parquet (not versioned) from
../2_clean/ashaar_clean.parquet.
"""
import datetime
import hashlib
import pathlib

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
CLEAN = HERE.parent / "2_clean" / "ashaar_clean.parquet"
OUTPUT = HERE / "ashaar_split.parquet"
TIER_FILE = HERE / "development_tier.txt"
SEEN_FILE = HERE / "seen_poems.tsv"

SEED = 2026
# Share of each baḥr (in verses): development pool C, then validation, then test.
POOL, VALIDATION = 0.75, 0.10                     # test: the remaining 0.15
# Development tiers, as shares of C: f is written on C[pool_share <= tier], tier by
# tier, and measured on the validation set. Finer steps at the start, where most
# rules are found. 0.60 is the limit: the rest of C (B) is kept for the network of
# f*, and is never looked at while f is written.
TIERS = [0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60]
# Rare buḥūr: too few poems for a lot B. No f* for them; their split is made on
# the number of poems (70 / 15 / 15), and their part of C is available from the
# first tier.
RARE = {"متدارك", "مقتضب", "مضارع"}


# ---------------------------------------------------------------- split

def poem_rank(poem_id):
    """A fixed pseudo-random rank for a poem, computed from its identifier alone.

    Unlike a global shuffle, a poem keeps its rank (and so its lot) if other poems
    are removed from the corpus later.
    """
    return hashlib.sha256(f"{SEED}-{poem_id}".encode()).hexdigest()


def add_split(verses):
    """Add the columns split (C, validation or test) and pool_share.

    The split is made by poem (the verses of a poem share poet, rhyme and style)
    and baḥr by baḥr, so that every baḥr has the same proportions in each lot.
    Within a baḥr, the poems are ordered by poem_rank, the prototype poems
    (prototype_poems) first, then cut on the number of verses: C (75 %), validation (10 %), test
    (15 %). For the RARE buḥūr, the cut is made on the number of poems instead.

    pool_share is the position of the poem in C, from 0 to 1, within its baḥr: the
    share of the baḥr's C verses up to and including this poem. The first 10 % of
    C are the verses with pool_share <= 0.10 (see development_pool). It is
    TIERS[0] for the rare buḥūr, whose part of C is available from the first tier.
    """
    poems = (verses.groupby("poem_id")
             .agg(bahr=("bahr", "first"), n_verses=("sadr", "size"))
             .reset_index())
    poems["seen"] = poems["poem_id"].isin(prototype_poems())
    poems["rank"] = poems["poem_id"].map(poem_rank)
    poems = poems.sort_values(["bahr", "seen", "rank"], ascending=[True, False, True])

    parts = []
    for bahr, group in poems.groupby("bahr", sort=False):
        group = group.copy()
        if bahr in RARE:
            n = len(group)
            n_validation = n_test = max(1, round(n * 0.15))
            group["split"] = (["C"] * (n - n_validation - n_test)
                              + ["validation"] * n_validation + ["test"] * n_test)
            group["pool_share"] = (group["split"] == "C").map({True: TIERS[0], False: None})
        else:
            share = group["n_verses"].cumsum() / group["n_verses"].sum()
            group["split"] = pd.cut(share, [0, POOL, POOL + VALIDATION, 1],
                                    labels=["C", "validation", "test"]).astype(str)
            in_pool = group["split"] == "C"
            pool_verses = group["n_verses"].where(in_pool, 0)
            group["pool_share"] = (pool_verses.cumsum() / pool_verses.sum()).where(in_pool)
        parts.append(group)
    poems = pd.concat(parts)
    return verses.merge(poems[["poem_id", "split", "pool_share"]], on="poem_id", how="left")




def prototype_poems():
    """The poems used to tune the first prototype of f, read from seen_poems.tsv.

    These are the poems of the 160 verses of arud/prototype/evaluate.py (seeds
    0-3, drawn on the corpus before drop_conflicting_labels), the lines whose tier
    is "proto". add_split puts them first in C, so they are never in B,
    validation or test. Only these lines are used: the poems of the later tiers
    are already first in C by construction, and putting them first as well
    would change the order, and so the split, at each new tier. The "proto"
    lines must therefore never be changed.
    """
    seen = pd.read_csv(SEEN_FILE, sep="\t", dtype={"poem_id": int, "tier": str})
    return set(seen.loc[seen["tier"] == "proto", "poem_id"])


def load_split():
    """The split corpus (run this file as a script first to write it)."""
    return pd.read_parquet(OUTPUT)


# ---------------------------------------------------------------- tiers

def get_tier():
    """The development tier reached so far (0.0 before the first tier)."""
    return float(TIER_FILE.read_text().strip())


def development_pool(verses, tier=None):
    """The verses of C available at a tier (a share of C), by default the tier reached.

    This is the only part of C that may be looked at while f is written.
    """
    tier = get_tier() if tier is None else tier
    return verses[(verses["split"] == "C") & (verses["pool_share"] <= tier)]


def update_tier(new_tier, verses=None):
    """Move up to a higher tier: record the newly seen poems, then the new tier.

    Refuses a tier that is not in TIERS (so above the limit of 0.60 too), or that
    is not higher than the tier reached: seen poems cannot be "unseen".
    """
    current = get_tier()
    if new_tier not in TIERS:
        raise ValueError(f"{new_tier} is not a tier; tiers are {TIERS}")
    if new_tier <= current:
        raise ValueError(f"tier {new_tier} is not above the tier reached ({current})")
    verses = load_split() if verses is None else verses
    seen = pd.read_csv(SEEN_FILE, sep="\t", dtype={"poem_id": int})
    pool = development_pool(verses, new_tier)
    new = (pool[~pool["poem_id"].isin(seen["poem_id"])]
           .groupby("poem_id", as_index=False)["bahr"].first()
           .assign(tier=str(new_tier), date=datetime.date.today().isoformat(),
                   reason=f"tier {new_tier * 100:g} %"))
    pd.concat([seen, new]).to_csv(SEEN_FILE, sep="\t", index=False)
    TIER_FILE.write_text(f"{new_tier}\n")
    return len(new)


def init_tracking():
    """Create the tier file if it does not exist yet (0.0: before the first tier)."""
    if not TIER_FILE.exists():
        TIER_FILE.write_text("0.0\n")


if __name__ == "__main__":
    corpus = add_split(pd.read_parquet(CLEAN))
    corpus.to_parquet(OUTPUT, index=False)
    init_tracking()
    counts = corpus["split"].value_counts()
    print(f"{len(corpus):,} verses written to {OUTPUT.name}: "
          + ", ".join(f"{lot} {counts[lot]:,}" for lot in ["C", "validation", "test"]))
