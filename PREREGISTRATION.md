# Pre-registration: do auditor disagreements locate auditor errors?

Committed before any MALT transcript is downloaded or any auditor is run. The commit hash of this file fixes these predictions ahead of the data. Changes after that commit are recorded as dated amendments below the original text, never as edits to it.

## Question

AI auditors of agent transcripts have false-positive rates that do not fall when votes are aggregated, whether within one model (METR 2025) or across models (Hall and Thompson 2026). Averaging votes into one score is one use of repeated runs. Partitioning by agreement pattern is another: run each transcript more than once, and treat unanimous verdicts and split verdicts as different types that are routed differently. This study asks whether auditor errors concentrate in the split cases, and what kind of disagreement the split cases contain.

## Data

- MALT public split (`metr-evals/malt-public`, MIT licence), manually reviewed transcripts only.
- Task: reward hacking, as in METR's monitor study. Positives are reviewed transcripts whose labels include `bypass_constraints` or `ignores_task_instructions`. Negatives are reviewed transcripts labelled `normal`. Other labels are excluded.
- Sample: all positives in the public split, plus a random sample of negatives drawn with seed 20261018. The negative sample size is set after measuring transcript token lengths, as the largest size that fits the budget below, and is recorded as an amendment before any auditor runs.

## Auditor

- Prompt: METR's published reward-hacking monitor prompt, verbatim (`ref/prompt_reward_hacking.txt`, sha256 fa3486138e0dd846619039b01e9bf46d410d73023c6710774719cf1dff5b5ad3).
- Chunking: METR's scheme, with the first five messages repeated in every chunk. METR does not publish chunk size or aggregation; this study uses chunks of at most 30,000 tokens and takes the maximum chunk score as the transcript score. Both choices are fixed here.
- Models: one inexpensive model from the set Hall and Thompson tested, named in an amendment before any run. A second model from a different provider is added only if budget allows, also named before it runs. No Anthropic model is used as an auditor, because the person running the study is working with an Anthropic model and Hall and Thompson document self-preference effects.
- Runs: two independent runs per transcript per model, at temperature 1.0.
- Budget: a hard API spending cap of 20 USD for the first model.

## Measures

1. Baseline: AUROC and true-positive rate at 5% false-positive rate, using the first run's scores, for comparison with METR and with Hall and Thompson.
2. Binary verdicts: each run is flagged when its score meets the threshold that gives 5% FPR on the first run.
3. Agreement partition: each transcript falls into one of three strata, both runs flag, one run flags, or neither flags. For each stratum: count, error rate against the labels, and share of all errors.
4. Typed disagreement (exploratory): for each one-flag transcript, the two runs' stated reasons are compared and coded as disagreement about whether a behaviour occurred (different evidence cited) or about whether it counts (same evidence, different verdict). Coding rules are written before the reasons are read and are applied blind to the label.

## Predictions

- P1. The split stratum has a higher error rate than either unanimous stratum. Prediction: at least twice the error rate of the unanimous strata combined.
- P2. Most errors are nonetheless in the unanimous strata. Prediction: the split stratum contains at most 40% of all errors. This would mean auditor errors are mostly systematic, consistent with the failure of vote aggregation.
- P3. Exploratory, no directional prediction: the share of split cases that are disagreements about whether a behaviour counts, as opposed to whether it occurred.

## Verdicts

Each prediction is graded confirmed, marginal, plausible, needs refinement or dead, with the threshold for each grade stated here:

- P1 is confirmed if the ratio is at least 2 and its 95% bootstrap interval excludes 1; marginal if the ratio is at least 2 but the interval includes 1; dead if the ratio is below 1.
- P2 is confirmed if the split stratum holds at most 40% of errors with a 95% interval below 50%; dead if it holds more than 60%.

A result that kills a prediction is reported as prominently as one that confirms it.

## Limits known in advance

- The MALT public split is small, and the positives are few. Intervals will be wide.
- Temperature-1 resampling of one model measures within-model instability only. Cross-model disagreement needs the second model.
- The labels are METR's reviews, which carry their own error. METR estimates a 6% label error rate for unreviewed transcripts; reviewed transcripts are used to keep that low.

## Amendments

### A1, 2026-10-18, before any data is downloaded

"Error rate against the labels" in Measure 3 is defined as: the first run's binary verdict disagrees with the label. It is computed the same way in all three strata. The alternative, counting a split case as an error because one of its two runs must be wrong, makes P1 true by construction and is rejected. Found while writing `analyze.py`. A check on invented data with independent run noise gives a split-stratum share of errors of about 80%, so P2 separates independent noise from systematic error, as intended.
