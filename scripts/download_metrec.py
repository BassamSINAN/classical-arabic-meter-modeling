"""Download the MetRec corpus into data/raw/metrec/."""
import io
import pathlib
import urllib.request
import zipfile

URL = "https://raw.githubusercontent.com/zaidalyafeai/Arabic-Poetry/master/final_baits.zip"
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = REPO_ROOT / "data" / "raw" / "metrec"
FILES = ["labels.txt", "train.txt", "test.txt"]

DEST.mkdir(parents=True, exist_ok=True)
with urllib.request.urlopen(URL, timeout=120) as response:
    archive = zipfile.ZipFile(io.BytesIO(response.read()))

# The archive stores the files in a sub-folder (final_baits/):
# write them directly into data/raw/metrec/.
for member in archive.namelist():
    name = pathlib.PurePosixPath(member).name
    if name in FILES:
        (DEST / name).write_bytes(archive.read(member))
