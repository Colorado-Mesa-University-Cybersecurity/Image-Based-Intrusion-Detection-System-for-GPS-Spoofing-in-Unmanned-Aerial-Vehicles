# Tuning measurements

Scripts that reproduce the two hyperparameter claims the study rests on. They read
`gps_ids.training.SPECS` rather than hardcoding a configuration, so each one measures
whatever is committed and keeps reporting the truth as the specs change.

Run them from the repository root with the project interpreter:

```
python tuning/rf_max_features.py --dataset 2d --seeds 1082 7 42
python tuning/lstm_stability.py  --dataset uav
```

Both print to stdout and write nothing unless `--out <csv>` is given, so neither can
contaminate the canonical results files.

## rf_max_features.py

Compares `max_features=None` against `sqrt` on the same splits. This is the only
hyperparameter change in the study with a reproducible performance margin, and `None`
costs about 3.7x the training time, so the margin has to justify that cost on every
Random Forest fit across both datasets and every variant.

Measured 2026-11-01 on 2D at full scale, three seeds, with the committed
`class_weight='balanced'` in both arms:

```
mcc                +0.0227 +/- 0.0007   per seed [0.0230, 0.0220, 0.0232]
balanced_accuracy  +0.0196 +/- 0.0010
min_class_recall   +0.0404 +/- 0.0029
train time         None is 3.68x sqrt (118s vs 32s mean)
```

An earlier measurement on an unweighted forest gave +0.0214 +/- 0.0010, so the margin
is unchanged by balanced weighting. Expect roughly 10 minutes per seed pair on 2D at
full scale.

## lstm_stability.py

Reports the spread, the degenerate count and the best epochs across seeds. Before the
`tanh`-bounded head the committed configuration was a coin flip on UAV: 0.8441 +/-
0.2949 with one run in ten collapsing to MCC 0.000.

Measured 2026-11-01 on UAV, ten seeds, current committed configuration:

```
MCC          0.9672 +/- 0.0128   min 0.9471  max 0.9884
degenerate   0 of 10
best epochs  [5, 5, 17, 26, 34, 35, 53, 91, 93, 96]  (budget 100)
any at the budget: False
```

No best epoch at the budget is the point: the original failure was evaluating whatever
epoch 100 happened to produce. Takes about five minutes for ten UAV seeds.

Note the spread here covers both the split and the model's randomness, because each
seed builds a fresh `real_heldout`. The figures quoted from the original study varied
network seeds at a fixed split, so the two spreads are not interchangeable and the
means should not be compared directly.

## What is not here

The wider sweep that produced the rejected candidates — solvers, activations, boosters,
image learning rates — was run across five parallel agents and is recorded in the
appendix rather than as scripts. These two are here because they are the claims a
referee is most likely to ask about: the one performance margin, and the one stability
fix.
