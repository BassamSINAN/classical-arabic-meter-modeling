"""Download the Ashaar corpus (arbml/ashaar on Hugging Face) into data/raw/ashaar/."""
import pathlib
import urllib.request

# Pinned dataset revision, so the download is reproducible.
REVISION = "9b5e723df1c5b13b9e4428caff758fe2f3c737f6"
BASE_URL = f"https://huggingface.co/datasets/arbml/ashaar/resolve/{REVISION}/data/"
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = REPO_ROOT / "data" / "raw" / "ashaar"
FILES = ["train-00000-of-00002.parquet", "train-00001-of-00002.parquet"]

DEST.mkdir(parents=True, exist_ok=True)
for name in FILES:
    with urllib.request.urlopen(BASE_URL + name, timeout=600) as response:
        (DEST / name).write_bytes(response.read())
