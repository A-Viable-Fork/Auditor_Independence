# Role: download the MALT public split (gated, needs HF_TOKEN) into data/raw and print its schema.
# Contract: python3 download.py ; reads HF_TOKEN from the environment; writes data/raw/*.parquet and data/schema.txt.
import os, sys, glob
from huggingface_hub import snapshot_download
import pandas as pd

token = os.environ.get("HF_TOKEN")
if not token:
    sys.exit("Set HF_TOKEN (a Hugging Face read token, after accepting the dataset terms).")
path = snapshot_download("metr-evals/malt-public", repo_type="dataset", token=token,
                         local_dir="data/raw", allow_patterns=["data/*.parquet", "README.md", "LICENSE"])
files = sorted(glob.glob("data/raw/data/*.parquet"))
df = pd.read_parquet(files[0])
with open("data/schema.txt", "w") as f:
    f.write(f"{len(files)} files\ncolumns: {list(df.columns)}\n\n{df.dtypes}\n\nfirst row:\n")
    for c in df.columns:
        f.write(f"--- {c}\n{str(df.iloc[0][c])[:1500]}\n")
print(open("data/schema.txt").read()[:4000])
