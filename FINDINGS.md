# Findings

Observations from validating the codebase against a fresh environment.

Part 1 lists what was changed. Part 2 lists what was left alone, because those
affect published numbers and the calls are yours.

---

# Part 1 — Fixed

## `Fix results.ipynb` was causing the corruption it claimed to fix

It existed to repair "parsing errors due to unquoted commas in the
`parameters` column". There were no such errors to repair: every notebook writes
results with `pandas.to_csv()`, which already quotes `parameters` correctly.
Verified directly — a `parameters` value containing 18 commas round-trips
through append-mode `to_csv` and back with `csv.reader` at exactly 7 fields.

The notebook read the already-valid CSV with `line.strip().split(',')`, which
splits *inside* quoted fields, then rejoined `fields[5:-1]` and re-wrote the row
through `csv.writer`, which quoted it a second time. That is the origin of the
`"""odict_keys([...` triple-quoting in the committed results, and of one line in
`2D_Results_full.csv` that held 13 fields instead of 7 because two rows were
merged — its `num_epochs` read literally `100StackedEnsemble_RF`.

It also **overwrote** `2D_Results_full.csv` and `UAVATTACK_Results_full.csv` in
`'w'` mode from whatever happened to be in the scratch CSVs, so running it with
a partial scratch file would silently replace the published results.

Removed. The repo already reads these files correctly everywhere else
(`print_csv.py` and `filter_result.ipynb` both use `csv.DictReader`).

The pipeline is now:

```
notebooks -> *_Results.csv -> filter.ipynb -> *_Results_filtered.csv -> plots
```

## Inconsistent results schema

Five notebooks wrote rows that did not match the 7-column header, which is the
real source of ragged rows. All now write the full schema.

| Notebook | Was | Now |
|---|---|---|
| `Models/2D_SYNTHETIC/Stacking/ensemble.ipynb` | key named `training_time_sec` | `train_time_sec` |
| `Models/2D_SYNTHETIC/Stacking/stackingSpoofGPS.ipynb` | `training_time_sec`, no `parameters`/`num_epochs` | full 7 columns |
| `Models/UAV_ATTACK_SYNTHETIC/Stacking/ensemble_models.ipynb` | key named `training_time_sec` | `train_time_sec` |
| `Models/UAV_ATTACK/One class/OneClassSVM.ipynb` | 4 columns, no timing at all | full 7 columns, fit timed |
| `Models/UAV_ATTACK/One class/Local Outlier Factor.ipynb` | 4 columns, no timing at all | full 7 columns, fit timed |

Verification status differs per file. `OneClassSVM.ipynb`, `Local Outlier
Factor.ipynb` and `stackingSpoofGPS.ipynb` (2D_SYNTHETIC) were edited and the
first two executed successfully. `ensemble_models.ipynb` and
`2D_SYNTHETIC/Stacking/ensemble.ipynb` were edited and statically verified
(correct dict key confirmed) but NOT executed — their edited cells still carry
`execution_count: null`, and `2D_SYNTHETIC/Stacking/stackingSpoofGPS.ipynb`
additionally has a committed `KeyboardInterrupt` traceback from an earlier
interrupted run, so its saved output predates the fix. They loop 1M-row datasets
through `SVC(probability=True)` and take hours; re-run them to confirm.

The two one-class notebooks never timed their `fit()`, so `train_time_sec` was
absent rather than wrong. They now report real numbers (LOF `0.095s`, OC-SVM
`0.003s`) and both still reproduce their accuracies (LOF `0.9959`, OC-SVM
`0.9542`).

## Notebooks that wrote into the published results file

`Models/2D/Stacking/ensemble.ipynb` and
`Synthetic_Data_Generation/2D Synthetic Data Generation/Smote/stacked ensemble.ipynb`
had `RESULTS_CSV = "../../../2D_Results_full.csv"` and appended in `mode='a'`,
adding a duplicate row to a tracked file on every run. Both now target
`2D_Results.csv` like the other 46 notebooks.

`Visualization/Results/visualizeRealData.ipynb` read the `*_Results_full.csv`
files; it now reads `*_Results.csv`.

## `.gitignore` re-included 510k generated images

`!/binaryImageTransformation/2d tubular data/image-results-spoofing/` cancelled
the ignore rule above it. Because that path had no deeper rules (unlike the
UAVATTACK one, which also ignores `data/Train/` and `data/Test/`), all 510,530
generated PNGs were stageable — `git status` listed 331,780 of them mid-run. The
two directory negations are removed; the four `best_*.pth` negations are intact.

---

## Broken and stale data paths

Three notebooks had paths that could not resolve. Every other notebook's data
paths were checked and do resolve.

**`GAN.ipynb` wrote outside the repository.** Its output path had four `../`
segments where three reach the repo root:

```python
synthetic_df.to_csv("../../../../Datasets/csv/UAVATTACK/syntheticSpoofing_gan_data.csv")
```

From `Synthetic_Data_Generation/UAV Synthetic Data Generation/GAN/` that
resolves to `<parent-of-repo>/Datasets/...`, so a completed run dumped an ~8.9 MB
CSV next to the repository instead of inside it, and the notebooks that read
`syntheticSpoofing_gan_data.csv` never saw the new file. Corrected to three.

**`CGAN.ipynb` used a lowercase `datasets/` and the wrong directory.** It wrote
to `../../../datasets/csv/syntheticSpoofing_cgan_data.csv`, which worked on
Windows only by case-insensitive matching and skipped the `UAVATTACK/`
subdirectory. Corrected to `../../../Datasets/csv/UAVATTACK/`.

**`Visualization/UAV_ATTACK/synthetic_Data.ipynb` had paths from an older
layout** and could not run at all:

| Was | Now |
|---|---|
| `../../Datasets/csv/spoofing-merged-gps-only.csv` | `../../Datasets/csv/UAVATTACK/...` |
| `../../Synthetic_Data_Generation/Synthetic Data Generation/SDV/spoofing_metadata.json` | `.../UAV Synthetic Data Generation/SDV/...` |
| `../Datasets/csv/<synthetic>.csv` (5 files) | `../../Datasets/csv/UAVATTACK/<synthetic>.csv` |

Note this notebook still needs
`Synthetic_Data_Generation/UAV Synthetic Data Generation/SDV/SDV_Synthetic.ipynb`
to run first: it reads `spoofing-{CTGAN,GaussianCopula,TVAE}-synthetic.csv`,
which are that notebook's outputs and are not committed. The `CGAN` and `GAN`
inputs it also reads are committed and present.

## `accuracy` and `f1score` are transposed in the two feature-engineering notebooks

`Models/2D/Feature Enginnering/Features.ipynb` and
`Models/UAV_ATTACK/Feature Enginnering/Features.ipynb` build their result dict
in a different key order from every other notebook:

```python
results.append({"model": ..., "dataset": ..., "accuracy": accuracy, "f1score": f1, ...})
```

48 of the 50 results-writing notebooks use `"f1score"` before `"accuracy"`;
these two are the only ones reversed. Because they append with
`to_csv(mode='a', header=not file_exists)`, pandas writes values in the
DataFrame's own column order, ignoring the header already in the file.
Demonstrated:

```
header:  model,dataset,f1score,accuracy
row A (f1score first):  A,d,0.11,0.99
row B (accuracy first): B,d,0.99,0.11   <- metrics land in each other's columns
```

So every `(Explainability Features)` and `(Xgboost Features)` row these two
notebooks produced has accuracy under `f1score` and vice versa. The published
data showed it plainly: `Logistic Regression (Explainability Features)` recorded
f1score `0.7787` / accuracy `0.6825`, while plain `Logistic Regression` recorded
f1score `0.6825` / accuracy `0.7789` — the same pair, swapped. Fix is to reorder
the two keys.

## `filter.ipynb` reads from the wrong depth

`input_file = "../../UAVATTACK_Results.csv"` resolves from
`Visualization/Results/Results fixes/` to `Visualization/UAVATTACK_Results.csv`,
which never exists; three `../` are needed. The now-removed `Fix results.ipynb`
in the same folder used the correct depth, so promoting `filter.ipynb` to the
regeneration step exposed this. It also had no 2D branch, leaving
`2D_Results_filtered.csv` with no way to be produced even though
`make_all_plots.py` and `print_csv.py` both read it.

## The root results CSVs were not gitignored

`SETUP.md` described `2D_Results.csv` and `UAVATTACK_Results.csv` as "gitignored
scratch accumulators", but `.gitignore` contained no such patterns — the first
notebook run would leave them untracked and `git add -A` would commit them,
recreating the "notebook appends a row to a tracked file" problem. Both (plus
`Synthetic_Data_Generation/2D_Results.csv`) are now ignored.

## `scripts/gen_synth.py` treated truncated output as complete

Its resume check was `if os.path.isfile(out): skip`, while writing directly to
the final path. An interrupt or disk-full during a 1M-row write left a partial
CSV that every later run skipped, silently feeding short datasets to every
`Models/*_SYNTHETIC/**` notebook. It now writes `<out>.partial` and
`os.replace()`s on success, so a partial file is never mistaken for a finished
one. It also now exits with a usage message instead of `IndexError` when called
with no arguments.

## The plotting scripts could never locate their inputs

`make_all_plots.py` and `print_csv.py` sit in
`Visualization/accuracy_performance/` but named
`UAVATTACK_Results_filtered.csv` and `2D_Results_filtered.csv` as bare relative
paths, while those files have only ever existed in `Visualization/Results/`
(verified across the whole git history). Running the script from its own
directory raised `FileNotFoundError`; running it from `Visualization/Results/`
would break the `print_csv` import. Both now resolve their paths from
`Path(__file__)`, and the end-to-end pipeline was executed to confirm all 8
figures regenerate.

# Part 2 — Not fixed

These change published numbers, so the calls are yours.

> **Since resolved.** The metrics/review pass closed several items that still
> have their original write-ups below. Read these headings as history, not as
> open issues:
>
> | heading below | status |
> |---|---|
> | All eight image notebooks select their best epoch on the test set | fixed — three-way split, checkpoint chosen on `val`, test read once |
> | The one-class notebooks fit the scaler on the full dataset | scaler fixed; the eval set still includes the fitted benign rows, now recorded honestly as `test_set="real_full_incl_train_benign"` |
> | The two image split scripts disagree | fixed — both seeded with `RANDOM_STATE = 1082`, both write `image-results-spoofing/data/{Train,Test}`, both emit `split_manifest.json`, both refuse to re-run |
> | The 2D image pipeline produces a layout its own notebooks cannot read | fixed — `split-Images.py` now writes into `data/Train` and `data/Test` |
> | Image paths are Windows-only (casing mismatches) | fixed — all eight notebooks use `image-results-spoofing/data` |
> | `organize_photos_in_folders()` silently moves nothing | fixed |
>
> Newly found and fixed in the same pass, with no write-up below:
>
> - **Geometric augmentation destroyed the bit encoding.** `train_transforms`
>   carried `RandomRotation(30)` and `RandomHorizontalFlip()` while
>   `test_transforms` did not. The encoding is positional — row = feature,
>   column = bit — so rotation moves bits into the wrong cells. Measured on real
>   PNGs: 40.3% of 2D data-row pixels and 38.3% of UAV pixels change, and 63.7%
>   (2D) / 60.1% (UAV) of set bits land on a zero pixel. Both augmentations are
>   removed; train and test transforms are now identical.
> - **The UAV SDV metadata was detected from GAN output.** `spoofing_metadata.json`
>   agreed with fresh detection on the real CSV for only 62 of 83 columns. Twenty
>   of the gaps were constant columns, but `lon_y` (254 distinct values) was typed
>   `categorical`, so every synthetic longitude was a verbatim real value.
>   Regenerated from the real data with the notebook's own preprocessing; both
>   notebooks now verify cached metadata against the dataframe before using it.
> - **The 2D synthesizers trained for 300 epochs** (SDV's default, no `epochs`
>   key) against UAV's 4000 (CTGAN) / 2000 (TVAE). Now matched.
> - **`GaussianCopula` silently dropped its own configuration** in both SDV
>   notebooks via a `if name == 'GaussianCopula'` branch that discarded
>   `**params`, so it rounded its output while the other two did not.
> - **Synthetic sampling was unseeded.** `reset_sampling()` now precedes every
>   `sample()` in both `SDV_Synthetic.ipynb`, both `createData.ipynb` and
>   `scripts/gen_synth.py`; `CGAN.ipynb`'s shuffle takes `random_state`.
> - **Image notebooks renamed to match their models.** Both folders now hold
>   `CNN.ipynb`, `CnnLstm.ipynb`, `ResnetCnn.ipynb`, `ResnetLstm.ipynb`. The two
>   files previously called `LSTM.ipynb` were different architectures from each
>   other (2D = CNN-LSTM, UAV = ResNet-LSTM) and neither was the tabular LSTM.

## All eight image notebooks select their best epoch on the test set

Every notebook under `binaryImageTransformation/` runs this loop:

```python
for epoch in range(num_epochs):
    ...train...
    model.eval()
    for inputs, labels in dataloaders['test']:      # <- the TEST set
        ...
    val_acc = accuracy_score(val_labels, val_preds)
    if val_acc > best_acc:
        best_acc = val_acc
        best_model_wts = copy.deepcopy(model.state_dict())
model.load_state_dict(best_model_wts)               # keep the best TEST epoch
```

There is no validation split. The checkpoint kept is whichever epoch scored
highest on the test set, and the reported metrics are then computed on that same
test set. The reported figure is therefore `max over epochs of test accuracy`,
which is optimistically biased rather than an unbiased estimate.

Measured from the per-epoch numbers in the committed outputs, comparing the
selected maximum against the mean of the last five epochs:

| notebook | epochs | max (reported) | mean last 5 | optimism |
|---|---|---|---|---|
| `UAVATTACK/ResnetCnn.ipynb` | 20 | 0.9945 | 0.9914 | +0.0031 |
| `UAVATTACK/ResnetLstm.ipynb` | 20 | 0.9931 | 0.9895 | +0.0036 |
| `UAVATTACK/CnnLstm.ipynb` | 30 | 0.9931 | 0.9721 | **+0.0210** |

The UAV bias is small because that dataset is saturated, leaving little room.
The four 2D notebooks run 100 epochs on a dataset where models genuinely vary,
so the bias there is likely larger -- but their committed outputs contain only
1-3 output objects (the paper notes the 2D deep-learning runs were done on a
separate server), so it cannot be measured from what is in the repo.

This matters more than the other items here because the image-based IDS is the
paper's headline contribution. The fix is a three-way split: carve a validation
set out of the training data, select the checkpoint on that, and touch the test
set only once at the end.

## The one-class notebooks fit the scaler on the full dataset

`Models/UAV_ATTACK/One class/OneClassSVM.ipynb` and `Local Outlier Factor.ipynb`:

```python
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)     # all 3,622 rows, benign AND malicious
...
X_benign = X_scaled[y == 0]
X_train, ... = train_test_split(X_benign, ...)
X_test = X_scaled                      # everything, including the malicious rows
ocsvm.fit(X_train)
```

The scaler's mean and standard deviation are computed over the full dataset,
including every row the model is later evaluated on. For a novelty-detection
method whose premise is "learn only from benign behaviour," fitting the
normaliser on the attack data undermines the setup. The scaler should be fitted
on the benign training subset and then used to transform everything else.

`GAN.ipynb` and `CGAN.ipynb` do the same thing, though it matters less there
since they are generators rather than classifiers.

## Hyperparameters that disagree with the paper, and with their own siblings

The paper states that "the same hyperparameter settings are used across all the
same models and datasets to keep them consistent." Four places break that:

| file | setting | paper / siblings |
|---|---|---|
| `Smote/MLPSMOTE.ipynb` | `hidden_layer_sizes=(100, 50, 25, 10)` -- four layers | three layers `(100, 50, 25)`; the other nine MLPs all use three |
| `Smote/XGboost2DSmote.ipynb` | `objective='multi:softmax'`, `eval_metric='mlogloss'` | `multi:softprob` with MAE, as every other 2D XGBoost uses |
| 4x `Stacking/stackingSpoofGPS.ipynb` | `LogisticRegression(max_iter=1200)` | Table 7 says 2000 (consistent among themselves, just not with the paper) |
| both `ModelExplainability.ipynb` | `LogisticRegression()` -- defaults, so `max_iter=100` and the `lbfgs` solver | `saga` with `max_iter=2000` |

The explainability one compounds: those notebooks also split with
`test_size=0.3, random_state=100` instead of the project's `train_size=0.8,
random_state=1082`. So the SHAP and LIME analyses that produced the
"Explainability Features" subsets came from a differently-configured model on a
different split than every model those features were then fed to.

These change published numbers, so they are left as-is.

## Scaler mismatch

Three notebooks fit `StandardScaler`, train on `X_train_scaled`, then predict on
raw `X_test`:

| Notebook | Reported accuracy |
|---|---|
| `Models/2D/Regular/RandomForest.ipynb` | 6.27% |
| `Models/2D/Regular/2DXgboost.ipynb` | 13.15% |
| `Models/UAV_ATTACK/Regular/Random Forest.ipynb` | 13.73% |

The fix is `model.predict(X_test_scaled)`. Peer notebooks (`MLP.ipynb`,
`2DLogRegres.ipynb`) already do this, which is why theirs look sane. The 2D
Random Forest currently predicts class 3 for every row.

## The two headline stacked ensembles had no holdout (fixed)

Measured after the fix: UAV 0.9925 -> **0.9931** (no real change, it stacks
binary votes), 2D 0.9808 -> **0.7609**, and the 2D SMOTE variant 0.9908 ->
**0.6051**. The 2D ensemble's published ~99% was a memorisation artifact; held
out, its attack-class recall is 0.15-0.21. See `BUGFIXES.md` item 27.

The meta-classifier is fitted on the full stacked feature matrix using `y_test`
as its training label, then evaluated by predicting on that same matrix:

```python
meta_clf.fit(stacked_features, y_test)
stacked_pred = meta_clf.predict(stacked_features)
```

| Notebook | Reported accuracy |
|---|---|
| `Models/UAV_ATTACK/Stacking/ensemble_of_paper's_models.ipynb` | 0.9925 |
| `Models/2D/Stacking/ensemble.ipynb` | 0.9908 |

Train and test data are identical, so these are resubstitution scores, not
generalization estimates — the likely reason they top every other model. The
base models (OC-SVM, LOF, autoencoder) are fitted only on benign rows and are
fine; the leak is at the meta-classifier.

For contrast, the `*_SYNTHETIC/Stacking` versions hold out properly — they fit
on synthetic and predict on real (`0.4023` for 2D, `0.8702` for UAV), which is
the size of gap this changes.
`Synthetic_Data_Generation/2D Synthetic Data Generation/Smote/stacked ensemble.ipynb`
fits on a SMOTE-balanced subset then predicts on the full matrix, which still
overlaps its own training rows.

## The UAV SDV synthesizers were fitted on GAN output, not on real data (fixed)

The two `SDV_Synthetic.ipynb` notebooks disagree about their training source:

| Notebook | `DATA_PATH` |
|---|---|
| `2D Synthetic Data Generation/SDV/` | `Datasets/excel/2dSpoofingDataset/GPS_Data_Simplified_2D_Feature_Map.xlsx` (real) |
| `UAV Synthetic Data Generation/SDV/` | `Datasets/csv/UAVATTACK/syntheticSpoofing_gan_data.csv` (**GAN output**) |

`syntheticSpoofing_gan_data.csv` is itself generated by `GAN/GAN.ipynb`, which
trains on the real merged CSV. Three things confirm it is generated rather than
real:

| | real merged | `syntheticSpoofing_gan_data.csv` |
|---|---|---|
| rows | 3,622 | 10,000 |
| `timestamp` column | present | absent |
| column naming | `q[0]` | `q_0_` (already cleaned) |
| label balance | 3,124 / 498 | 5,045 / 4,955 |

So the committed UAV `spoofing-{CTGAN,GaussianCopula,TVAE}-synthesizer.pkl`, and
every `spoofing_{gc,ctgan,tvae}_{10000,100000,1000000}.csv` sampled from them,
are **second-generation** synthetic data — a CTGAN/TVAE/Copula fit of a GAN fit
of the real flights. The near-balanced label ratio is inherited from the GAN
rather than from the real 86/14 split, which matters for any
train-on-synthetic / test-on-real comparison. The 2D pipeline does not have this
problem.

If this is deliberate, it is worth stating explicitly; if not, `DATA_PATH` should
be `../../../Datasets/csv/UAVATTACK/spoofing-merged-gps-only.csv`. Left
unchanged, because re-fitting would replace the committed synthesizers and every
synthetic dataset derived from them.

## Both `SDV_Synthetic.ipynb` notebooks overwrite the committed synthesizers

Each ends with `synthesizer.save(filepath=synth['pickle'])` writing to a bare
filename resolved against the notebook's own directory — i.e. straight onto the
six tracked `spoofing-*-synthesizer.pkl` files. Running either notebook
re-fits from scratch (CTGAN at 4,000 epochs, TVAE at 2,000) and replaces them,
which would invalidate the synthetic CSVs already generated from them. All six
were verified unchanged after this session's runs. Back them up before running
either notebook.

## A UAV notebook writes its results into the 2D results file

`Models/UAV_ATTACK_SYNTHETIC/Stacking/stackingSpoofGPS.ipynb` sets

```python
RESULTS_CSV = "../../../2D_Results.csv"
```

while every other notebook in `UAV_ATTACK*` writes to `UAVATTACK_Results.csv`.
It also loads `base_dir = "../../../Datasets/csv/UAVATTACK/"` and the real UAV
CSV, so this is a copy-paste slip rather than intent: its UAV rows land in the
2D results file, where `dataset_short()` in `make_all_plots.py` will not
recognise them and the 2D plots gain stray UAV points. Left unchanged because it
affects which published rows live in which file.

## The UAV "Explainability Features" set contains duplicate columns

Both `Models/UAV_ATTACK/Feature Enginnering/Features.ipynb` and
`LSTM-features.ipynb` define the same list, in which `hdop` and `lat_x` each
appear twice:

```python
feature_cols_1 = ['vdop', 'ax', 'hdop', 'cog_rad', 'hdop', 'jamming_indicator',
                  'terrain_alt_valid', 'dist_bottom_valid', 'terrain_alt',
                  'lat_x', 'lat_x', 'lat_y']
```

`df[feature_cols_1]` materialises both copies, so `X1.shape` is `(3622, 12)` for
10 distinct features. The duplicated columns are perfectly collinear, which for
the scaled linear models in these notebooks (`LogisticRegression`) splits each
duplicated feature's coefficient across two columns, and makes the reported
feature count wrong. The LSTM variant is worse: it reshapes to
`(samples, SEQUENCE_LENGTH, 1)` where `SEQUENCE_LENGTH` comes from the column
count, so the sequence length is 12 instead of 10 with two positions repeated.

The equivalent 2D lists (`Models/2D/Feature Enginnering/*`) have no duplicates.

## `XgboostSpoofGPS.ipynb` splits twice and mixes the halves

Cell 3 splits and builds `X_train_scaled` / `X_test_scaled`. Cell 4 then re-runs
`train_test_split` on the same data, rebinding `X_train`, `X_test`, `y_train`,
`y_test` but **not** the scaled arrays. Cell 5 trains on `X_train_scaled` from
the first split against `y_train` from the second.

Both calls currently pass `train_size=0.2`, the same `random_state=RANDOMSTATE`
and `stratify=y`, so the two splits are identical and the result is correct
today. It is latent rather than active: changing `TRAIN_SIZE` in cell 1 changes
only the first split (cell 4 hardcodes `0.2`), at which point features and
labels silently belong to different partitions. The second split should be
deleted.

## `CnnLstm.ipynb` builds a 4-class head for a 2-class dataset

`binaryImageTransformation/UAVATTACK tubular data/CnnLstm.ipynb` does:

```python
model = CNN_LSTM_Model(num_classes=4).to(device)
```

but the UAVATTACK images have two classes (`benign`, `malicious`). It is the
only one of the eight image notebooks that gets this wrong:

| notebook | classes on disk | `num_classes` |
|---|---|---|
| `UAVATTACK/CNN.ipynb` | 2 | `len(classes)` |
| `UAVATTACK/ResnetLstm.ipynb` | 2 | `2` |
| `UAVATTACK/ResnetCnn.ipynb` | 2 | `2` |
| **`UAVATTACK/CnnLstm.ipynb`** | **2** | **`4`** |
| `2d/*.ipynb` (4 notebooks) | 4 | `4` / `len(classes)` |

The classifier emits four logits while labels are only `0`/`1`, so softmax
spreads probability mass over two classes that can never be correct and
`argmax` can return `2` or `3` — predictions outside the label set. The
committed output shows both symptoms:

```
Epoch  2/30 ... Train Acc: 0.8624 - Val Acc: 0.8631
...                                                  <- 10 epochs frozen
Epoch 11/30 ... Train Acc: 0.8624 - Val Acc: 0.8631
Epoch 14/30 ... Train Acc: 0.9193 - Val Acc: 0.2628  <- collapse
```

`0.8624` and `0.8631` are exactly the majority-class rates (2500/2899 and
624/723), i.e. the model predicted `benign` for everything for ten epochs. The
`0.2628` at epoch 14 is far below even that floor, which only happens if
predictions are landing on the phantom classes. The fix is `num_classes=2`, or
better `len(classes)` as its sibling `CNN.ipynb` already does.

This affects the published `CNN-LSTM` row for `spoofing-merged-gps-only.csv`.

## `RandomForestSmote.ipynb` crashes with `NameError` on a fresh run

`Synthetic_Data_Generation/UAV Synthetic Data Generation/Smote/RandomForestSmote.ipynb`
defines `RANDOM_STATE = 1082` but then references `RANDOMSTATE` (no
underscore) twice:

```python
X, y, train_size=TRAIN_SIZE, random_state=RANDOMSTATE, stratify=y
smote = SMOTE(random_state=RANDOMSTATE, sampling_strategy=desired_strategy)
```

`RANDOMSTATE` is never assigned in the notebook. Confirmed by execution:

```
NameError: name 'RANDOMSTATE' is not defined
```

The committed notebook carries no error output, which means it was last run in a
kernel where `RANDOMSTATE` was already defined by a previously-executed notebook
— its siblings in this folder (`LogRegrSMOTE`, `MLPSmote`,
`XGboostSpoofingSmote`) all use the no-underscore spelling. So the saved results
came from leaked kernel state, and the notebook cannot reproduce them standalone.
This is the only notebook in the repo that fails outright.

## `XGboost2DSmote.ipynb` writes its results to the wrong directory

It uses two `../` segments where its five siblings use three:

| notebook | `RESULTS_CSV` | resolves to |
|---|---|---|
| `log2DSmote.ipynb` | `../../../2D_Results.csv` | `2D_Results.csv` (repo root) |
| **`XGboost2DSmote.ipynb`** | `../../2D_Results.csv` | `Synthetic_Data_Generation/2D_Results.csv` |

From `Synthetic_Data_Generation/2D Synthetic Data Generation/Smote/` three
levels are needed to reach the root. So its `XGBoost (SMOTE)` row lands in a
stray CSV inside `Synthetic_Data_Generation/` and never reaches the results file
the plots read.

## `TRAIN_SIZE = 0.2` trains on the minority of the data

Passed as `train_test_split(train_size=0.2)`, so models train on 20% and test on
80%. Consistent across the tabular notebooks, so presumably deliberate — just
not what the name suggests.

## The two image split scripts disagree

`UAVATTACK tubular data/split images.py` sends 20% to **test** (80/20
train/test). `2d tubular data/split-Images.py` computes
`split_idx = ceil(0.2 * n)` and takes `files[:split_idx]` as **train**, i.e. 20%
train / 80% test — matching the `TRAIN_SIZE = 0.2` convention, but the opposite
of the UAVATTACK script.

## `organize_photos_in_folders()` silently moves nothing

`helper_functions.organize_photos_in_folders()` keys `type_counts` by the `int`
labels from `Y.unique()` but looks them up with the `str` parsed out of the
filename, so every lookup raises `KeyError` and is swallowed by a bare
`except: continue`. The committed `tabToImage.ipynb` output shows the result:
`0` files moved and `{0: 0, 1: 0, 2: 0, 3: 0}`. This is why the standalone
`organize.py` exists and is a required step for the 2D images.

## `filter.ipynb` only covered UAVATTACK (fixed)

`Visualization/Results/Results fixes/filter.ipynb` produced only
`UAVATTACK_Results_filtered.csv`, leaving `2D_Results_filtered.csv` with no
regeneration path even though `make_all_plots.py` and `print_csv.py` both read
it. It now emits both. Note that all committed results were removed at the
user's request, so the plotting stage requires a model-notebook run first --
see `SETUP.md`.

## The 2D image pipeline produces a layout its own notebooks cannot read

`binaryImageTransformation/2d tubular data/{CNN,ResNet,ResnetLSTM,LSTM}.ipynb`
all read:

```python
data_dir = "image-results-spoofing/Data"
train_dir = os.path.join(data_dir, "Train")
test_dir  = os.path.join(data_dir, "Test")
```

But `organize.py` followed by `split-Images.py` creates
`image-results-spoofing/train/` and `.../test/` at the top level, not under
`Data/`. Meanwhile `tabToImage.ipynb`'s call to the broken
`organize_photos_in_folders()` leaves an **empty** `image-results-spoofing/data/Train/{0,1,2,3}`
behind. On Windows the notebook's `Data/Train` resolves case-insensitively to
that empty directory, so training fails with:

```
FileNotFoundError: Found no valid file for the classes 0, 1, 2, 3.
```

and `Data/Test` does not exist at all. The UAVATTACK side does not hit this
because its distributed archive already ships populated `data/Train` and
`data/Test`.

Resolved here by moving the generated output into the UAVATTACK convention
(`data/Train/<class>`, `data/Test/<class>`), which leaves the notebooks
unmodified. Either `split-Images.py` should write into `data/Train` and
`data/Test`, or the four notebooks should point at `train`/`test` -- currently
neither matches.

## Image paths are Windows-only (three separate casing mismatches)

All eight image notebooks are case-inconsistent with the data on disk and with
each other. This works on Windows and macOS and breaks on Linux.

| | `data_dir` | train subdir | test subdir |
|---|---|---|---|
| `2d tubular data/{CNN,LSTM,ResNet,ResnetLSTM}.ipynb` | `.../Data` | `train` | `test` |
| `UAVATTACK tubular data/{CNN,LSTM,LSTMCNN,ResNet}.ipynb` | `.../Data` | `Train` | `Test` |
| **on disk** | `.../data` | `Train` | `Test` |

So the directory is `data` but every notebook asks for `Data`, and the 2D four
additionally ask for `train`/`test` where the directory is `Train`/`Test`. All
four combinations were confirmed to resolve on this Windows machine (102,107
train / 408,423 test either way). On a case-sensitive filesystem the 2D four
fail outright and all eight fail on `Data`.

## Deprecated torchvision call

`ResnetCnn.ipynb` and `ResnetLstm.ipynb` call `resnet101(pretrained=True)`.
Verified working on torchvision 0.29.1, but it warns and is slated for removal;
the modern form is `weights=ResNet101_Weights.DEFAULT`.
