# Role: compute FOLLOWUP-1 measures and grades for the control, prompt and model arms.
# Contract: python3 analyze_f1.py ; reads results/sample.jsonl, data/groups.json and data/f1/*/*.jsonl; prints JSON, writes data/f1/analysis.json.
# Invariant: thresholds follow the main study's rule (lowest integer score whose run-1 FPR on negatives is at most 5%); grade bands are FOLLOWUP-1.md's.
import json, collections, numpy as np
S = {json.loads(l)["tid"]: json.loads(l)["label"] for l in open("results/sample.jsonl")}
G = json.load(open("data/groups.json")); B, I = G["B"], G["I"]
def load(path):
    mx = collections.defaultdict(lambda: None); bad = 0
    for r in map(json.loads, open(path)):
        if r["score"] is None: bad += 1; continue
        k = (r["tid"], r["run"]); mx[k] = r["score"] if mx[k] is None else max(mx[k], r["score"])
    return mx, bad
def thr(mx):
    neg = [mx[(t, 1)] for t in S if S[t] == 0 and mx[(t, 1)] is not None]
    for th in range(0, 12):
        if np.mean([s >= th for s in neg]) <= 0.05: return th, float(np.mean([s >= th for s in neg]))
def auroc(mx):
    p = np.array([mx[(t, 1)] for t in S if S[t] == 1 and mx[(t, 1)] is not None]); n = np.array([mx[(t, 1)] for t in S if S[t] == 0 and mx[(t, 1)] is not None])
    return float(((p[:, None] > n).sum() + .5 * (p[:, None] == n).sum()) / (len(p) * len(n)))
miss = lambda v: v is None or v < th
out = {}
for arm, path, runs in [("original", "results/openai__gpt-5-nano.jsonl", (1, 2)), ("control", "data/f1/control/openai__gpt-5-nano.jsonl", (3, 4)),
                        ("prompt", "data/f1/variant/openai__gpt-5-nano.jsonl", (1, 2)), ("deepseek", "data/f1/deepseek/deepseek__deepseek-v4.1-flash.jsonl", (1, 2))]:
    mx, bad = load(path)
    th, fpr = (2, None) if arm == "control" else thr(mx)
    a, b = runs
    o = {"threshold": th, "fpr_run1": fpr, "unparsed": bad}
    for name, grp in (("B", B), ("I", I)):
        if arm == "control" and name == "I": continue
        o[f"{name}_both_miss"] = sum(miss(mx[(t, a)]) and miss(mx[(t, b)]) for t in grp)
        o[f"{name}_tpr_first"] = sum(not miss(mx[(t, a)]) for t in grp)
    if arm != "control": o["auroc_run1"] = auroc(mx)
    if arm == "control":
        orig, _ = load("results/openai__gpt-5-nano.jsonl")
        thirteen = [t for t in B if orig[(t, 1)] < 2 and orig[(t, 2)] < 2]
        o["H3_of_13_still_both_miss"] = sum(miss(mx[(t, 3)]) and miss(mx[(t, 4)]) for t in thirteen)
    out[arm] = o
c, p = out["control"]["B_both_miss"], out["prompt"]["B_both_miss"]; iok = out["prompt"]["I_tpr_first"] >= 15
out["H1"] = "dead" if p >= c else ("confirmed" if p <= c / 2 and iok else "needs refinement" if p <= c / 2 else "marginal" if iok else "unassigned (pending operator ruling)")
d = out["deepseek"]; rB, rI = d["B_both_miss"] / len(B), max(d["I_both_miss"], 1) / len(I)
h2 = "confirmed" if rB >= .30 and rB >= 3 * rI else "marginal" if rB >= .15 and rB >= 1.5 * rI else "dead"
out["H2"] = h2 + (" / needs refinement (AUROC < 0.65)" if d["auroc_run1"] < .65 else ""); out["H2_rates"] = [rB, rI]
json.dump(out, open("data/f1/analysis.json", "w"), indent=2); print(json.dumps(out, indent=2))
