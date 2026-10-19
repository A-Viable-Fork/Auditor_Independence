# Role: rebuild one transcript per reviewed MALT run in the study's label classes, streaming file by file.
# Contract: python3 -I extract.py -> data/transcripts.jsonl ({tid, label, labels, model, run_source, task_id, messages:[{role,text}]})
# Invariant: a run's transcript is its longest step snapshot's input plus that step's output; tool calls are rendered
#   into the message text; positives = labels include bypass_constraints or ignores_task_instructions; negatives = exactly normal.
import json, glob, pyarrow.parquet as pq
POS = {"bypass_constraints", "ignores_task_instructions"}
def text(m):
    t = m.get("content") or ""
    fc = m.get("function_call")
    if fc and fc.get("name"): t += f"\n<{fc['name']}>{fc.get('arguments') or ''}</{fc['name']}>"
    return {"role": m.get("role"), "text": t}
n = 0
with open("data/transcripts.jsonl", "w") as out:
    for f in sorted(glob.glob("data/raw/data/*.parquet")):
        pf = pq.ParquetFile(f)
        for b in pf.iter_batches(batch_size=4):
            for r in b.to_pylist():
                md = r["metadata"]; labs = set(md["labels"])
                if not md["manually_reviewed"]: continue
                y = 1 if labs & POS else 0 if labs == {"normal"} else None
                if y is None: continue
                s = max(r["samples"], key=lambda x: len(x["input"]))
                msgs = [text(m) for m in s["input"]] + [text(m) for m in (s["output"][0] if s["output"] else [])]
                out.write(json.dumps({"tid": str(md["run_id"]), "label": y, "labels": sorted(labs), "model": md["model"],
                    "run_source": md["run_source"], "task_id": md["task_id"], "messages": msgs}) + "\n"); n += 1
print(n, "transcripts")
