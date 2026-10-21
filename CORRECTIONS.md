# Corrections

Claims already made in `RESULTS.md` and `FOLLOWUP-1.md` are corrected here, not edited in place. Each entry quotes the original text, states the correction, and gives the computation or file that supports it. The original text stays where it was, with a pointer to this file.

All four were found by an outside review (a ChatGPT deep research report, 2026-10-20) that re-parsed the committed raw outputs; each was then recomputed here before being accepted.

## C1, 2026-10-21: length and chunk count confound group B against group I

**Original** (`FOLLOWUP-1.md`, "What prompted it"): "Group B transcripts are short (319,658 tokens in all, about 14,000 each) and group I long (1,894,979, about 79,000 each), so length does not explain the gap."

**Correction.** The inference runs the wrong way. A transcript's score is the maximum over its chunks, so a longer transcript gets more chances to score high. In the A2 chunks, 20 of the 23 group B transcripts are one chunk, 2 are two and 1 is three; all 24 group I transcripts are three chunks. All 13 of gpt-5-nano's original group B both-misses are single-chunk transcripts. Behaviour type and chunk count are therefore confounded in this sample: the gap between B and I may come from the label, from the number of chunks scored, or from both, and these data cannot separate them. The follow-up's findings about the twelve transcripts (stable across fresh runs, unchanged by the prompt bullet, shared with a second provider) stand as observations about those transcripts; their attribution to a blind spot for constraint bypassing does not. Separating the two needs single-chunk positives of the other label, or scoring rules that do not depend on chunk count.

**Computed by:** chunk counts per transcript from `data/chunks.jsonl` (rebuilt by `prepare.py --negatives 450`, sha256 in `results/chunks.sha256`) joined with `results/f1/groups.json`.

## C2, 2026-10-21: "no amount of resampling" is beyond what two runs show

**Original** (`RESULTS.md`, "What this says"): "The other 58% are errors both runs share, which no amount of resampling the same model reaches."

**Correction.** Two runs per transcript cannot show that further runs would never flag these transcripts. The supported statement is narrower: 25 of gpt-5-nano's 43 run-1 errors were made by both of its runs, and on group B the 13 both-misses held across two further runs (FOLLOWUP-1, H3). Whether a larger number of runs would reach them is untested.

## C3, 2026-10-21: the cross-model error share names the wrong denominator

**Original** (`RESULTS.md`, Exploratory): "42 transcripts on which the models disagree hold 19 of 39 errors (49%, interval 34% to 64%), against 20 errors among 455 agreed transcripts." Repeated in "What this says" as "49% of errors in 8.5% of transcripts".

**Correction.** The 39 errors are Gemini's run-1 errors: the cross-model partition in `analyze.py` scores error against the first model's verdict, and Gemini was the first model named. Against gpt-5-nano's run-1 verdicts, the same 42 disagreed transcripts hold 23 of its 43 errors (53%). The reference auditor must be named whenever this figure is used.

## C4, 2026-10-21: analysis output and prose disagree on H1

**Original** (`results/f1/analysis.json`, written by `analyze_f1.py`): `"H1": "marginal (I condition failed)"`. `FOLLOWUP-1.md` instead says the result has no assigned band and proposes dead pending the operator's ruling.

**Correction.** The prose is right: FOLLOWUP-1's bands assign no grade when the prompt arm's both-misses fall below the control's but above half of it while the condition on group I fails. `analyze_f1.py` now writes `"unassigned (pending operator ruling)"` for that case, and `results/f1/analysis.json` is regenerated. No number changes.
