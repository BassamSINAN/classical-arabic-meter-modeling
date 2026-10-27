"""Download the Ashaar corpus (arbml/ashaar on Hugging Face) into this folder (data/1_raw/ashaar/)."""
import pathlib
import urllib.request

# Pinned dataset revision, so the download is reproducible.
REVISION = "9b5e723df1c5b13b9e4428caff758fe2f3c737f6"
BASE_URL = f"https://huggingface.co/datasets/arbml/ashaar/resolve/{REVISION}/data/"
# The script sits in the folder that receives the data.
DEST = pathlib.Path(__file__).resolve().parent
FILES = ["train-00000-of-00002.parquet", "train-00001-of-00002.parquet"]

DEST.mkdir(parents=True, exist_ok=True)
for name in FILES:
    with urllib.request.urlopen(BASE_URL + name, timeout=600) as response:
        (DEST / name).write_bytes(response.read())
