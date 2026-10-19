# Results, 2026-10-19

Runs: both models, two runs each, on the A2 sample (47 positives, 450 negatives, 665 chunks); 1,330 calls per model, every score parsed. Spend: 16.12 USD Gemini, 1.04 USD gpt-5-nano, 0.47 USD cost test. Raw outputs, the sample and the analysis are in `results/`; `data/chunks.jsonl` is rebuilt by `prepare.py --negatives 450` and checked against `results/chunks.sha256`. Two checks were run before anything was read: an independent re-parse of every raw response (0 mismatches) and an independent recount of the gpt-5-nano strata (identical).

Grades are proposed against the thresholds in `PREREGISTRATION.md` and are the operator's to rule.

## Baseline (run 1)

| Model | AUROC | Threshold | TPR | FPR | AUROC, transcripts of 30k+ tokens |
|---|---|---|---|---|---|
| gemini-3.8-flash | 0.60 | 1 | 0.21 | 0.004 | 0.57 (27 pos, 71 neg) |
| gpt-5-nano | 0.76 | 2 | 0.55 | 0.049 | 0.75 (27 pos, 71 neg) |

Gemini scores 0 on 1,301 of 1,330 chunk calls. No threshold above 0 reaches 5% FPR, so its operating point sits at 0.4% FPR.

## Agreement partition

Error = run 1's verdict disagrees with the label (A1).

| Model | Stratum | n | errors | error rate |
|---|---|---|---|---|
| gpt-5-nano | both flag | 32 | 11 | 0.34 |
| | neither flags | 429 | 14 | 0.03 |
| | split | 36 | 18 | 0.50 |
| gemini-3.8-flash | both flag | 11 | 2 | 0.18 |
| | neither flags | 484 | 36 | 0.07 |
| | split | 2 | 1 | 0.50 |

## Predictions

**P1, gpt-5-nano: confirmed (proposed).** Split-stratum error rate is 9.2 times the unanimous strata's, 95% bootstrap interval 5.7 to 16.1, which excludes 1.

**P2, gpt-5-nano: marginal [ruling: operator, 2026-10-19].** The split stratum holds 41.9% of errors (interval 27% to 57%). The rule grades at most 40% as confirmed and more than 60% as dead and assigns nothing between; the result lies in that gap, and the operator graded it marginal.

**P1, gemini-3.8-flash: marginal by rule, and uninformative.** The ratio is 6.5, but the interval runs 0 to 16.5 because Gemini split only 2 of 497 transcripts.

**P2, gemini-3.8-flash: confirmed by rule, degenerate in substance.** The split stratum holds 2.6% of errors (interval 0 to 8.8%) because Gemini almost never flags: 36 of its 39 errors are misses both runs agree on. Its errors are systematic, which is what P2 predicts, and the auditor is too weak for that to say much.

**P3:** pending; coding follows `CODING.md`.

## Exploratory

Cross-model, run 1 of each model at its own threshold: 42 transcripts on which the models disagree hold 19 of 39 errors (49%, interval 34% to 64%), against 20 errors among 455 agreed transcripts.

Length: gpt-5-nano's AUROC holds on long transcripts (0.75 against 0.76 overall), so length does not carry its separation. Its splits come with length: 29 of its 36 split transcripts are multi-chunk, against 98 of 497 transcripts overall.

## What this says

For gpt-5-nano, run 1 is right half the time on transcripts where a second run disagrees, a coin flip, and right 95% of the time where the runs agree. Rerunning and routing the 7% of transcripts that split would send 42% of its errors to a second look. The other 58% are errors both runs share, which no amount of resampling the same model reaches. Disagreement between the two models locates more (49% of errors in 8.5% of transcripts), consistent with errors that differ by model more than by sample.

## Limits found in the run

- Gemini's near-constant zero leaves one informative auditor for P1 and P2. The study's within-model claims rest on gpt-5-nano alone.
- 47 positives; every interval is wide.
- The 5% FPR threshold cannot be hit exactly with integer scores; each model's threshold is the lowest whose FPR is at most 5%.
