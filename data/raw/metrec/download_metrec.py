"""Download the MetRec corpus into this folder (data/raw/metrec/)."""
import io
import pathlib
import urllib.request
import zipfile

URL = "https://raw.githubusercontent.com/zaidalyafeai/Arabic-Poetry/master/final_baits.zip"
# The script sits in the folder that receives the data.
DEST = pathlib.Path(__file__).resolve().parent
FILES = ["labels.txt", "train.txt", "test.txt"]

DEST.mkdir(parents=True, exist_ok=True)
with urllib.request.urlopen(URL, timeout=120) as response:
    archive = zipfile.ZipFile(io.BytesIO(response.read()))

# The archive stores the files in a sub-folder (final_baits/):
# write them directly into this folder.
for member in archive.namelist():
    name = pathlib.PurePosixPath(member).name
    if name in FILES:
        (DEST / name).write_bytes(archive.read(member))
