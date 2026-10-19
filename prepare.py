# Role: draw the pre-registered sample from data/transcripts.jsonl and cut each transcript into METR-style chunks with the prompt filled in.
# Contract: python3 -I prepare.py --measure      -> chunk count and prompt tokens per class, for every eligible transcript (no sample drawn)
#           python3 -I prepare.py --negatives N  -> data/sample.jsonl ({tid, label, tokens}) and data/chunks.jsonl ({tid, chunk, prompt, tokens})
# Invariant: all positives; N negatives drawn with random.Random(20261018).sample over negatives sorted by tid;
#   each chunk <= 30,000 transcript tokens, with the first five messages repeated in every chunk; a single message longer
#   than the budget is split at token boundaries.
import sys, json, random, argparse, collections
import tiktoken

SEED, MAXTOK, HEAD = 20261018, 30000, 5
ap = argparse.ArgumentParser(); ap.add_argument("--measure", action="store_true"); ap.add_argument("--negatives", type=int, default=0)
a = ap.parse_args()
enc = tiktoken.get_encoding("o200k_base")
ntok = lambda s: len(enc.encode(s, disallowed_special=()))
tmpl = open("ref/prompt_reward_hacking.txt").read()
render = lambda m: f"[{m['role']}]\n{m['text']}"

def chunks(msgs):
    msgs = [render(m) for m in msgs]
    head, rest = "\n\n".join(msgs[:HEAD]), msgs[HEAD:]
    budget = MAXTOK - ntok(head)
    pieces = []
    for m in rest:
        ids = enc.encode(m, disallowed_special=())
        pieces += [enc.decode(ids[i:i + budget]) for i in range(0, len(ids), budget)] if len(ids) > budget else [m]
    out, cur, n = [], [], 0
    for p in pieces:
        t = ntok(p)
        if cur and n + t > budget: out.append(cur); cur, n = [], 0
        cur.append(p); n += t
    if cur or not out: out.append(cur)
    return [tmpl.replace("{early_messages}", head).replace("{transcript}", "\n\n".join(c)) for c in out]

rows = [json.loads(l) for l in open("data/transcripts.jsonl")]
if a.measure:
    st = collections.defaultdict(lambda: [0, 0, 0])
    for r in rows:
        ps = chunks(r["messages"]); s = st[r["label"]]; s[0] += 1; s[1] += len(ps); s[2] += sum(map(ntok, ps))
    for y, (n, c, t) in sorted(st.items()): print(f"label {y}: {n} transcripts, {c} chunks, {t} prompt tokens per run")
    sys.exit()

pos = [r for r in rows if r["label"] == 1]
neg = sorted((r for r in rows if r["label"] == 0), key=lambda r: int(r["tid"]))
neg = random.Random(SEED).sample(neg, min(a.negatives, len(neg)))
tot = 0
with open("data/sample.jsonl", "w") as fs, open("data/chunks.jsonl", "w") as fc:
    for r in pos + neg:
        ps = chunks(r["messages"]); tk = [ntok(p) for p in ps]; tot += sum(tk)
        fs.write(json.dumps({"tid": r["tid"], "label": r["label"], "tokens": sum(tk)}) + "\n")
        for i, (p, t) in enumerate(zip(ps, tk)): fc.write(json.dumps({"tid": r["tid"], "chunk": i, "prompt": p, "tokens": t}) + "\n")
print(f"{len(pos)} positives, {len(neg)} negatives, {tot} prompt tokens per run")
