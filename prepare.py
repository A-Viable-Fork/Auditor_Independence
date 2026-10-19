# Role: select the pre-registered sample from MALT and cut each transcript into METR-style chunks with the prompt filled in.
# Contract: python3 -I prepare.py --measure            -> token-length table for positives and negatives (no sample drawn)
#           python3 -I prepare.py --negatives N        -> data/sample.jsonl ({tid, label}) and data/chunks.jsonl ({tid, chunk, prompt})
# Invariant: positives = labels include bypass_constraints or ignores_task_instructions; negatives = label exactly normal;
#   reviewed only; negatives drawn with seed 20261018; chunks <= 30,000 tokens with the first five messages repeated in each.
# Assumption: column names below are read from data/schema.txt after download and must be confirmed before use.
import sys, json, glob, random, argparse
import pandas as pd, tiktoken

COL_ID, COL_LABELS, COL_REVIEWED, COL_MESSAGES = "run_id", "labels", "manually_reviewed", "messages"  # confirm against schema
POS = {"bypass_constraints", "ignores_task_instructions"}
SEED, MAXTOK, HEAD = 20261018, 30000, 5

ap = argparse.ArgumentParser(); ap.add_argument("--measure", action="store_true"); ap.add_argument("--negatives", type=int, default=0)
a = ap.parse_args()
enc = tiktoken.get_encoding("o200k_base")
tmpl = open("ref/prompt_reward_hacking.txt").read()

df = pd.concat(pd.read_parquet(f) for f in sorted(glob.glob("data/raw/data/*.parquet")))
df = df[df[COL_REVIEWED].astype(bool)]
labels = df[COL_LABELS].apply(lambda v: set(v) if not isinstance(v, str) else {v})
df = df.assign(_y=labels.apply(lambda s: 1 if s & POS else 0 if s == {"normal"} else -1))
df = df[df._y >= 0]

def render(m):
    return f"[{m.get('role', '?')}]\n{m.get('content', '')}" if isinstance(m, dict) else str(m)

def chunks(msgs):
    msgs = [render(m) for m in msgs]
    head, rest = "\n\n".join(msgs[:HEAD]), msgs[HEAD:]
    budget = MAXTOK - len(enc.encode(head)) - len(enc.encode(tmpl))
    out, cur, n = [], [], 0
    for m in rest:
        t = len(enc.encode(m))
        if cur and n + t > budget: out.append(cur); cur, n = [], 0
        if t > budget: m = enc.decode(enc.encode(m)[:budget]); t = budget  # a single oversized message is truncated
        cur.append(m); n += t
    if cur or not out: out.append(cur)
    return head, ["\n\n".join(c) for c in out]

if a.measure:
    df = df.assign(_tok=df[COL_MESSAGES].apply(lambda ms: sum(len(enc.encode(render(m))) for m in ms)))
    print(df.groupby("_y")._tok.describe(percentiles=[.5, .9, .99]).to_string())
    sys.exit()

pos = df[df._y == 1]; neg = df[df._y == 0]
neg = neg.loc[random.Random(SEED).sample(list(neg.index), min(a.negatives, len(neg)))] if a.negatives else neg.iloc[:0]
sample = pd.concat([pos, neg])
with open("data/sample.jsonl", "w") as fs, open("data/chunks.jsonl", "w") as fc:
    for _, r in sample.iterrows():
        tid = str(r[COL_ID]); fs.write(json.dumps({"tid": tid, "label": int(r._y)}) + "\n")
        head, body = chunks(list(r[COL_MESSAGES]))
        for i, b in enumerate(body):
            fc.write(json.dumps({"tid": tid, "chunk": i, "prompt": tmpl.replace("{early_messages}", head).replace("{transcript}", b)}) + "\n")
print(f"{len(pos)} positives, {len(neg)} negatives written")
