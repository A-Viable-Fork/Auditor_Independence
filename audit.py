# Role: run an auditor model over prepared chunks, twice per chunk, through OpenRouter, with a hard spending cap.
# Contract: python3 audit.py MODEL [--runs 2] [--cap-usd 20] [--concurrency 8] [--chunks FILE] [--outdir DIR] [--run-start K]
#   reads data/chunks.jsonl ({tid, chunk, prompt}); appends to data/results/<model>.jsonl one record per
#   (tid, chunk, run): raw text, parsed score and reason, usage, cost. Resumable: finished keys are skipped.
# max_tokens is 16,000 so a provider default (65,536 on Gemini) does not reserve credit the run never uses.
# Invariant: stops issuing calls once recorded spend reaches the cap; never edits finished records.
import os, sys, json, re, asyncio, argparse, time
from openai import AsyncOpenAI

ap = argparse.ArgumentParser()
ap.add_argument("model"); ap.add_argument("--runs", type=int, default=2)
ap.add_argument("--cap-usd", type=float, default=20.0); ap.add_argument("--concurrency", type=int, default=8)
ap.add_argument("--limit", type=int, default=0, help="audit only the first N chunks (smoke test)")
ap.add_argument("--chunks", default="data/chunks.jsonl"); ap.add_argument("--run-start", type=int, default=1); ap.add_argument("--outdir", default="data/results")
a = ap.parse_args()

key = os.environ.get("OPENROUTER_API_KEY") or sys.exit("Set OPENROUTER_API_KEY.")
client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)
os.makedirs(a.outdir, exist_ok=True)
out = f"{a.outdir}/{a.model.replace('/', '__')}.jsonl"

done, spent = set(), 0.0
if os.path.exists(out):
    for line in open(out):
        r = json.loads(line); done.add((r["tid"], r["chunk"], r["run"])); spent += r.get("cost") or 0.0
chunks = [json.loads(l) for l in open(a.chunks)]
if a.limit: chunks = chunks[: a.limit]
jobs = [(c, run) for c in chunks for run in range(a.run_start, a.run_start + a.runs) if (c["tid"], c["chunk"], run) not in done]
print(f"{len(jobs)} calls to make; {spent:.4f} USD already spent of {a.cap_usd} cap", flush=True)

def parse(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    if m:
        try:
            j = json.loads(m.group(0)); return float(j["score"]), str(j.get("reason", ""))
        except Exception: pass
    m = re.search(r'"score"\s*:\s*"?(\d+(?:\.\d+)?)', text or "")
    return (float(m.group(1)) if m else None), (text or "")[:2000]

lock, sem, stop = asyncio.Lock(), asyncio.Semaphore(a.concurrency), False
async def one(c, run, fh):
    global spent, stop
    async with sem:
        if stop: return
        for attempt in range(5):
            try:
                resp = await client.chat.completions.create(
                    model=a.model, temperature=1.0, max_tokens=16000, messages=[{"role": "user", "content": c["prompt"]}],
                    extra_body={"usage": {"include": True}})
                break
            except Exception as e:
                if attempt == 4: print(f"fail {c['tid']}/{c['chunk']}/{run}: {e}", flush=True); return
                await asyncio.sleep(2 ** attempt * 3)
        text = resp.choices[0].message.content
        score, reason = parse(text)
        u = resp.usage.model_dump() if resp.usage else {}
        cost = u.get("cost") or 0.0
        rec = {"tid": c["tid"], "chunk": c["chunk"], "run": run, "model": a.model, "score": score,
               "reason": reason, "raw": text, "usage": u, "cost": cost, "t": time.time()}
        async with lock:
            fh.write(json.dumps(rec) + "\n"); fh.flush(); spent += cost
            if spent >= a.cap_usd and not stop:
                stop = True; print(f"cap reached at {spent:.4f} USD; stopping", flush=True)

async def main():
    with open(out, "a") as fh:
        await asyncio.gather(*(one(c, r, fh) for c, r in jobs))
    print(f"done; spent {spent:.4f} USD", flush=True)
asyncio.run(main())
