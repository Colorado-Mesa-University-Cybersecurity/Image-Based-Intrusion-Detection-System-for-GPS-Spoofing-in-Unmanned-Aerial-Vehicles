# Bug / Fix Register

Every defect found, the exact line that was wrong, and the line that replaced it.
Notebook locations are given as cell index, since `.ipynb` files have no stable
line numbers.

Verification was by execution wherever the notebook was fast enough to run;
where it was not, the method is stated. Nothing below is assumed.

Narrative context for each item is in `FINDINGS.md`. Environment and dataset
setup is in `SETUP.md`.

---

## Summary

| # | Bug | Files | Severity | Verified by |
|---|---|---|---|---|
| 1 | Train/test split inverted vs the paper | 35 | Critical | execution |
| 2 | `accuracy` / `f1score` written to each other's columns | 2 | Critical | execution + sentinel test |
| 3 | Predicting on unscaled `X_test` after training on scaled | 3 | Critical | execution |
| 4 | `NameError: RANDOMSTATE` — notebook could not run | 1 | Blocker | execution |
| 5 | 4-class head on a 2-class dataset | 1 | High | execution |
| 6 | Image `Resize` distorted/transposed the encoded bits | 8 | High | forward pass |
| 7 | Duplicate columns in a feature set | 2 | High | static |
| 8 | `organize_photos_in_folders()` silently moved 0 files | 2 | High | unit test |
| 9 | `GAN.ipynb` wrote outside the repository | 1 | High | path resolution |
| 10 | Results written to the wrong file or directory | 4 | Medium | path resolution |
| 11 | Incomplete / misnamed results schema | 5 | Medium | execution + static |
| 12 | `filter.ipynb` wrong depth, no 2D branch | 1 | Medium | execution |
| 13 | Redundant second split desynchronising X and y | 1 | Medium | execution |
| 14 | `.gitignore` re-included 510k generated images | 1 | Medium | `git check-ignore` |
| 15 | Root results CSVs not ignored | 1 | Medium | `git check-ignore` |
| 16 | Stale paths from an old directory layout | 2 | Medium | execution |
| 17 | `gen_synth.py` accepted truncated output as complete | 1 | Medium | static |
| 18 | LSTM / CNN batch sizes disagreed with the paper | 5 | Low | static |
| 19 | `Fix results.ipynb` corrupted the file it claimed to repair | 1 | Medium | removed |
| 20 | Plotting scripts looked for their inputs in the wrong directory | 2 | High | execution |
| 21 | 2D image split left at 20% train after the 80/20 correction | 1 + data | High | counts |
| 22 | UAV stacking model fitted on unscaled features | 1 | High | execution |
| 23 | `CGAN.ipynb` printed a path nothing writes | 1 | Low | static |
| 24 | `filter.ipynb` crashed on a short header | 1 | Low | static |
| 25 | `SDV_Synthetic.ipynb` was a syntax error on Python 3.11 | 1 | Blocker | compile + execution |
| 26 | UAV synthesizers fitted on GAN output, not real data | 1 + data | Critical | measured |
| 27 | Stacked ensembles scored on their own training rows | 3 | High | measured |

---

## 1. Train/test split inverted — trains on 20%, tests on 80%

The paper states *"we use an 80/20 train-test split."* The code passed
`train_size=TRAIN_SIZE` with `TRAIN_SIZE = 0.2`, which makes `train_size` the
**training** fraction — so it trained on 20% and tested on 80%, the exact
inverse.

**Before / after** (one line, same in all 35 notebooks):

```python
TRAIN_SIZE = 0.2      # before
TRAIN_SIZE = 0.8      # after
```

The `train_test_split(...)` calls were deliberately left alone; they all pass
`train_size=TRAIN_SIZE`, so the constant governs them.

Files: all 35 notebooks that pass `train_size=TRAIN_SIZE` — everything under
`Models/2D/`, `Models/2D_SYNTHETIC/`, `Models/UAV_ATTACK/`,
`Models/UAV_ATTACK_SYNTHETIC/` that splits, plus the ten
`Synthetic_Data_Generation/*/Smote/` notebooks and
`Models/UAV_ATTACK/One class/OneClassSVM.ipynb`.

**Deliberately NOT changed** — these two pass `test_size=TRAIN_SIZE`, so the
same edit would have broken them in the opposite direction:

- `Models/UAV_ATTACK/One class/Local Outlier Factor.ipynb`
- `Models/UAV_ATTACK/One class/transform data.ipynb`

Both still read `TRAIN_SIZE = 0.2`, which is correct for a `test_size`.

**Verified by execution** — the split demonstrably flipped:

| Notebook | train rows before → after | test rows before → after |
|---|---|---|
| `Models/2D/Regular/2DLogRegres.ipynb` | 102,106 → **408,424** | 408,424 → **102,106** |
| `Models/UAV_ATTACK/Regular/logRegressSpoofGPS.ipynb` | 725 → **2,897** | 2,897 → **725** |

A repo-wide scan confirms no hardcoded `train_size=0.2` remains in any notebook
or script.

---

## 2. `accuracy` and `f1score` written into each other's columns

Two notebooks built the results dict with `accuracy` before `f1score`; the other
48 use `f1score` before `accuracy`, which is also the CSV header order. Because
these append with `to_csv(mode='a', header=not file_exists)`, pandas writes
values in the **DataFrame's** column order and ignores the header already in the
file, so the two metrics landed in each other's columns.

Files:
- `Models/2D/Feature Enginnering/Features.ipynb` (cell 5, `add_results`)
- `Models/UAV_ATTACK/Feature Enginnering/Features.ipynb` (cell 5, `add_results`)

**Before:**
```python
        "model": f"{model_name} ({feature_set})",
        "dataset": ...,
        "accuracy": accuracy,
        "f1score": f1,
```
**After:**
```python
        "model": f"{model_name} ({feature_set})",
        "dataset": ...,
        "f1score": f1,
        "accuracy": accuracy,
```

**Verified** with sentinel values (`f1score=0.1111`, `accuracy=0.9999`) appended
under the canonical header and read back with `csv.reader`:

```
['model','dataset','f1score','accuracy', ...]
['OLD_ORDER','d.csv','0.9999','0.1111', ...]   <- transposed
['NEW_ORDER','d.csv','0.1111','0.9999', ...]   <- correct
```

Then confirmed on real output: after the fix, `MLP Classifier (Explainability
Features)` records `accuracy = 0.9972413793103448`, which is exactly 723/725 — a
correct-count over sample-count ratio, i.e. genuinely an accuracy. Its
`f1score` is `0.9972296502537772`, not a simple fraction, consistent with a
weighted F1.

The now-deleted published data carried the symptom: `Logistic Regression
(Explainability Features)` read f1 `0.7787` / acc `0.6825`, while plain
`Logistic Regression` read f1 `0.6825` / acc `0.7789` — the same pair, swapped.

---

## 3. Trained on scaled features, predicted on raw ones

Three notebooks fit a `StandardScaler`, trained on `X_train_scaled`, then called
`.predict(X_test)` on the unscaled test set, so the model saw inputs on a
completely different scale at inference.

**Before / after** (one line each):
```python
y_pred = model.predict(X_test)          # before
y_pred = model.predict(X_test_scaled)   # after
```

| File | cell | accuracy before | after |
|---|---|---|---|
| `Models/2D/Regular/RandomForest.ipynb` | 5 | 6.27% | **92.89%** |
| `Models/2D/Regular/2DXgboost.ipynb` | 6 | 13.15% | **93.02%** |
| `Models/UAV_ATTACK/Regular/Random Forest.ipynb` | 5 | 13.73% | **99.83%** |

Measured by execution. Before the fix the 2D Random Forest predicted class 3 for
every single row. (These numbers were measured on the old 20/80 split; they will
differ after fix 1, but the direction is unambiguous.)

---

## 4. `NameError` — the notebook could not run at all

`Synthetic_Data_Generation/UAV Synthetic Data Generation/Smote/RandomForestSmote.ipynb`
defines `RANDOM_STATE` but referenced `RANDOMSTATE`, which is never assigned.

**Before / after** (cell 3, two lines):
```python
    X, y, train_size=TRAIN_SIZE, random_state=RANDOMSTATE, stratify=y
smote = SMOTE(random_state=RANDOMSTATE, sampling_strategy=desired_strategy)
```
```python
    X, y, train_size=TRAIN_SIZE, random_state=RANDOM_STATE, stratify=y
smote = SMOTE(random_state=RANDOM_STATE, sampling_strategy=desired_strategy)
```

Before: `NameError: name 'RANDOMSTATE' is not defined`. After: exit 0, accuracy
99.86%, F1 0.9986.

The committed notebook carried no error output, which means it had last been run
in a kernel where `RANDOMSTATE` leaked in from a sibling notebook — its three
siblings in that folder all use the no-underscore spelling. The saved results
were therefore not reproducible standalone.

---

## 5. Four-class classifier head on a two-class dataset

`binaryImageTransformation/UAVATTACK tubular data/CnnLstm.ipynb`, cell 6. The
UAVATTACK images have two classes (`benign`, `malicious`).

**Before / after:**
```python
model = CNN_LSTM_Model(num_classes=4).to(device)
model = CNN_LSTM_Model(num_classes=len(classes)).to(device)
```

`classes = train_dataset.classes` is already defined in cell 4; this matches how
sibling `CNN.ipynb` does it. It was the only one of the eight image notebooks
with a mismatch.

**Verified:** final layer is now `Linear(in_features=512, out_features=2)`, was
`out_features=4`. Executed: accuracy **99.59%**, F1 0.9958. The old majority-class
plateau (train 0.8624 / val 0.8631, exactly 2500/2899 and 624/723) previously
held for the entire run; it now breaks at epoch 9 and reaches 0.9872/0.9862.

---

## 6. Image `Resize` distorted the encoded bit pattern

The binary encoder writes **one row per feature** and **64 columns of bits**, so
native geometry (height, width) is `(64, 64)` for 2D and `(82, 64)` for UAV —
matching the paper. All 16 transform definitions requested
`transforms.Resize((64, 82))`, which torchvision reads as (height, width). That
stretched 2D's width 64→82, and for UAV squashed height 82→64 while stretching
width 64→82 — transposing the aspect and interpolating across the very bit
columns and feature rows the encoding exists to expose.

**Before / after** (two occurrences per file — train and test pipelines):

| Files | before | after |
|---|---|---|
| `binaryImageTransformation/2d tubular data/{CNN,CnnLstm,ResnetCnn,ResnetLstm}.ipynb` | `transforms.Resize((64, 82))` | `transforms.Resize((64, 64))` |
| `binaryImageTransformation/UAVATTACK tubular data/{CNN,ResnetLstm,CnnLstm,ResnetCnn}.ipynb` | `transforms.Resize((64, 82))` | `transforms.Resize((82, 64))` |

Two hidden dependencies on the old geometry were also corrected:

```python
dummy = torch.zeros(1, 1, 64, 82)   # before
dummy = torch.zeros(1, 1, 64, 64)   # after  - 2d tubular data/ResnetLstm.ipynb
dummy = torch.zeros(1, 1, 82, 64)   # after  - UAVATTACK tubular data/ResnetLstm.ipynb
```

These feed `nn.LSTM(input_size=W*C, ...)`. The UAV LSTM's input size correctly
drops 3072 → 2048 as a result.

The remaining `2*2*512` and `view(batch_size, 2, -1)` literals were audited and
left alone — they derive from `AdaptiveAvgPool2d((2,2))`, not from image size.

**Verified:** each notebook's own `test_transforms` applied to a real PNG now
yields `(1, 64, 64)` and `(1, 82, 64)` — the resize is a no-op. All eight models
build and forward-pass at the new geometry with correct class counts
(2D → 4 logits, UAV → 2 logits).

---

## 7. Duplicate columns in the UAV "Explainability Features" set

`hdop` and `lat_x` each appeared twice, so `df[feature_cols_1]` materialised 12
perfectly-collinear columns for 10 distinct features.

**Before:**
```python
['vdop', 'ax', 'hdop', 'cog_rad', 'hdop', 'jamming_indicator',
 'terrain_alt_valid', 'dist_bottom_valid', 'terrain_alt', 'lat_x', 'lat_x', 'lat_y']
```
**After:**
```python
['vdop', 'ax', 'hdop', 'cog_rad', 'jamming_indicator',
 'terrain_alt_valid', 'dist_bottom_valid', 'terrain_alt', 'lat_x', 'lat_y']
```

Files: `Models/UAV_ATTACK/Feature Enginnering/Features.ipynb` (cell 3,
`feature_cols_1`) and `Models/UAV_ATTACK/Feature Enginnering/LSTM-features.ipynb`
(cell 2, the `"LSTM Classifier (Explainability Features)"` entry only — the
XGBoost list is untouched and still 10 unique).

This mattered most for the LSTM variant, which sets `SEQUENCE_LENGTH` from the
column count: the sequence was 12 long with two positions repeated. The 2D
equivalents had no duplicates.

---

## 8. `organize_photos_in_folders()` silently moved zero files

`type_counts` was keyed by the integer labels from `Y.unique()` but looked up
with the string parsed from the filename, so every lookup raised `KeyError` into
a bare `except: continue`. Both byte-identical copies were fixed and remain
identical.

Files: `binaryImageTransformation/2d tubular data/helper_functions.py` and
`binaryImageTransformation/UAVATTACK tubular data/helper_functions.py`.

**Before:**
```python
    type_counts = {value: 0 for value in dirs}
    for file in os.listdir(image_directory):
        try:
            dir = file.split("-")[0]
            type_counts[dir] += 1
        except:
            continue
        shutil.move(...)
```
**After:**
```python
    type_counts = {str(value): 0 for value in dirs}
    for file in os.listdir(image_directory):
        parts = file.split("-")
        if len(parts) < 2:
            continue
        dir = parts[0]
        if dir not in type_counts:
            continue
        type_counts[dir] += 1
        shutil.move(...)
```

The bare `except` is gone, so `shutil.move` failures now propagate instead of
being swallowed.

**Verified** by a temp-directory unit test with `0-1.png`, `0-2.png`, `1-1.png`
and one non-matching file: 3 files moved (was 0), counts `{'0': 2, '1': 1}`, and
the junk file correctly left in place.

---

## 9. `GAN.ipynb` wrote its output outside the repository

Four `../` segments where three reach the repo root, so the ~8.9 MB result landed
beside the repository and the notebooks that read
`syntheticSpoofing_gan_data.csv` never saw it.

File: `Synthetic_Data_Generation/UAV Synthetic Data Generation/GAN/GAN.ipynb`, cell 10.

```python
synthetic_df.to_csv("../../../../Datasets/csv/UAVATTACK/syntheticSpoofing_gan_data.csv", index=False)   # before
synthetic_df.to_csv("../../../Datasets/csv/UAVATTACK/syntheticSpoofing_gan_data.csv", index=False)      # after
```
The matching `print(...)` string was corrected with it.

---

## 10. Results written to the wrong file or directory

| File | cell | before | after |
|---|---|---|---|
| `Synthetic_Data_Generation/2D Synthetic Data Generation/Smote/XGboost2DSmote.ipynb` | 1 | `RESULTS_CSV = "../../2D_Results.csv"` | `"../../../2D_Results.csv"` |
| `Models/UAV_ATTACK_SYNTHETIC/Stacking/stackingSpoofGPS.ipynb` | 1 | `RESULTS_CSV = "../../../2D_Results.csv"` | `"../../../UAVATTACK_Results.csv"` |
| `Models/2D/Stacking/ensemble.ipynb` | 2 | `RESULTS_CSV = "../../../2D_Results_full.csv"` | `"../../../2D_Results.csv"` |
| `Synthetic_Data_Generation/2D Synthetic Data Generation/Smote/stacked ensemble.ipynb` | 1 | `RESULTS_CSV = "../../../2D_Results_full.csv"` | `"../../../2D_Results.csv"` |

Row 1 wrote into `Synthetic_Data_Generation/2D_Results.csv` instead of the repo
root, so its `XGBoost (SMOTE)` row never reached the results the plots read.
Row 2 is a UAV notebook that was filing its results under 2D. Rows 3–4 appended
into the committed, published `*_Results_full.csv` on every run.

---

## 11. Incomplete or misnamed results schema

The CSV header has 7 columns. Five notebooks wrote rows that did not match.

**Misnamed key** — `Models/2D_SYNTHETIC/Stacking/ensemble.ipynb` (cell 5),
`Models/2D_SYNTHETIC/Stacking/stackingSpoofGPS.ipynb` (cell 6),
`Models/UAV_ATTACK_SYNTHETIC/Stacking/ensemble_models.ipynb` (cell 5):
```python
"training_time_sec": training_time_sec,   # before
"train_time_sec": training_time_sec,      # after
```
The local variable keeps its own name; only the dict key changed.

**Missing keys** — `Models/2D_SYNTHETIC/Stacking/stackingSpoofGPS.ipynb` also
gained:
```python
"parameters": str(stacking_model.get_params()),
"num_epochs": "N/A"
```

**Four-column rows with no timing at all** —
`Models/UAV_ATTACK/One class/OneClassSVM.ipynb` and `Local Outlier Factor.ipynb`
never timed their `fit()`. Added `import time` (cell 0), wrapped the fit (cell 4):
```python
start_time = time.time()
ocsvm.fit(X_train)                      # lof.fit(X_train) in the LOF notebook
train_time = time.time() - start_time
```
and completed the dict (cell 7):
```python
"accuracy": accuracy,
"train_time_sec": train_time,
"parameters": str(ocsvm.get_params()),
"num_epochs": "N/A"
```

All 50 results-writing notebooks now emit the identical 7-key schema in the
identical order — verified by a repo-wide scan.

**Verification caveat, stated honestly:** `OneClassSVM`, `Local Outlier Factor`
and the 2D_SYNTHETIC `stackingSpoofGPS` edits were executed. The two
`ensemble*.ipynb` edits were statically verified only — their edited cells still
carry `execution_count: null`, and `2D_SYNTHETIC/Stacking/stackingSpoofGPS.ipynb`
carries a committed `KeyboardInterrupt` from an older interrupted run. They loop
1M-row data through `SVC(probability=True)` and take hours.

---

## 12. `filter.ipynb` read from the wrong depth and had no 2D branch

`Visualization/Results/Results fixes/filter.ipynb`, cell 0. Two `../` resolve to
`Visualization/UAVATTACK_Results.csv`, which never exists. It also produced only
the UAVATTACK filtered file, while `make_all_plots.py` and `print_csv.py` both
read a 2D one as well.

**Before:**
```python
input_file = "../../UAVATTACK_Results.csv"
output_file = "../UAVATTACK_Results_filtered.csv"
```
**After:**
```python
file_pairs = [
    ("../../../UAVATTACK_Results.csv", "../UAVATTACK_Results_filtered.csv"),
    ("../../../2D_Results.csv", "../2D_Results_filtered.csv"),
]
```
with the existing `csv.DictReader`/`DictWriter` body moved into a loop and a
`os.path.isfile` skip so a missing input prints a message instead of raising.
`keep_columns` is unchanged.

**Verified** end to end with fixture CSVs whose `parameters` field contained
embedded commas: both filtered files were produced with the correct 6 columns
and row counts, proving CSV quoting survived.

---

## 13. Redundant second split desynchronising features from labels

`Models/UAV_ATTACK/Regular/XgboostSpoofGPS.ipynb`. Cell 3 split the data and
built `X_train_scaled`/`X_test_scaled`; cell 4 then re-split, rebinding
`X_train/X_test/y_train/y_test` but **not** the scaled arrays, so the subsequent
`model.fit(X_train_scaled, y_train)` mixed one split's features with the other's
labels.

**Removed** — the whole of cell 4, which contained only:
```python
# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    train_size=0.2,
    random_state=RANDOMSTATE,
    stratify=y
)
```

Both splits passed identical arguments, so results were correct at the time; the
hazard was latent, since cell 1's `TRAIN_SIZE` governed only the first split
while cell 4 hardcoded `0.2`. With fix 1 changing `TRAIN_SIZE` to `0.8`, leaving
this cell would have actively broken the notebook.

**Verified:** 21 deletions / 0 insertions, and the notebook still reaches 99.79%
accuracy, confirming the two splits had been equivalent.

---

## 14. `.gitignore` re-included 510,530 generated images

Two `!` negations cancelled the ignore rules above them. The 2D path had no
deeper rules to catch the contents, so `git status` listed 331,780 stageable
PNGs mid-generation and `git add -A` would have committed them all.

**Removed:**
```
!/binaryImageTransformation/2d tubular data/image-results-spoofing/
!/binaryImageTransformation/UAVATTACK tubular data/image-results-spoofing/
```
The four `!.../best_*.pth` negations were kept and still match.

**Verified:** stageable files under both image directories went 331,780 → **0**;
`git check-ignore` confirms every image path at every level.

---

## 15. Root results CSVs were not ignored

`SETUP.md` claimed they were; `.gitignore` had no such pattern, so the first
notebook run left them untracked and committable.

**Added to `.gitignore`:**
```
/2D_Results.csv
/UAVATTACK_Results.csv
/Synthetic_Data_Generation/2D_Results.csv
```
Verified with `git check-ignore`. The `SETUP.md` wording was corrected too.

---

## 16. Stale paths from an older directory layout

`Visualization/UAV_ATTACK/synthetic_Data.ipynb` could not run at all.

| before | after |
|---|---|
| `"../../Datasets/csv/spoofing-merged-gps-only.csv"` | `"../../Datasets/csv/UAVATTACK/spoofing-merged-gps-only.csv"` |
| `"../../Synthetic_Data_Generation/Synthetic Data Generation/SDV/spoofing_metadata.json"` | `".../UAV Synthetic Data Generation/SDV/spoofing_metadata.json"` |
| `"../Datasets/csv/<name>.csv"` (5 entries) | `"../../Datasets/csv/UAVATTACK/<name>.csv"` |

Also `Synthetic_Data_Generation/UAV Synthetic Data Generation/CGAN/CGAN.ipynb`
cell 11, which used a lowercase `datasets/` (working only by Windows
case-insensitivity) and skipped the `UAVATTACK/` subdirectory:
```python
df_gan.to_csv("../../../datasets/csv/syntheticSpoofing_cgan_data.csv", index=False)              # before
df_gan.to_csv("../../../Datasets/csv/UAVATTACK/syntheticSpoofing_cgan_data.csv", index=False)    # after
```

**Verified:** `synthetic_Data.ipynb` now executes to completion (exit 0) and
produces SDV diagnostic scores.

---

## 17. `gen_synth.py` treated a truncated file as complete

`scripts/gen_synth.py` (added this session). Its resume check was
`if os.path.isfile(out): skip` while writing straight to the final path, so an
interrupt during a 1M-row write left a partial CSV that every later run skipped.

**Before / after:**
```python
df.to_csv(out, index=False)
```
```python
tmp = out + ".partial"
df.to_csv(tmp, index=False)
os.replace(tmp, out)
```
Plus argv validation, which previously raised a bare `IndexError`:
```python
if len(sys.argv) < 3:
    sys.exit("usage: gen_synth.py <repo_root> <size> [<size> ...]")
```

---

## 18. Batch sizes disagreed with the paper

Paper Table 8 specifies batch 64 for the LSTM on both datasets, and batch 100 for
the UAV Attack CNN.

```python
BATCH_SIZE = 32   # before
BATCH_SIZE = 64   # after
```
- `Models/2D/Feature Enginnering/LSTM-Features.ipynb` (cell 1)
- `Models/UAV_ATTACK/Feature Enginnering/LSTM-features.ipynb` (cell 1)
- `Models/UAV_ATTACK/LSTM/LSTM.ipynb` (cell 1)
- `Synthetic_Data_Generation/UAV Synthetic Data Generation/Smote/LSTMSmote.ipynb` (cell 2)

```python
batch_size = 32    # before
batch_size = 100   # after
```
- `binaryImageTransformation/UAVATTACK tubular data/CNN.ipynb` (cell 1)

The four LSTM notebooks that already used 64 were left alone. The test
`DataLoader(..., batch_size=1)` is intentional and untouched.

> Worth a second look: batch 100 for the UAV CNN is the only image model not on
> 32, and sits in the same table row as "100 iterations". It may be a
> transcription slip in Table 8 rather than a real setting. The code now follows
> the paper as written.

---

## 19. `Fix results.ipynb` corrupted the file it claimed to repair

**Deleted:** `Visualization/Results/Results fixes/Fix results.ipynb`.

It existed to repair "parsing errors due to unquoted commas in the `parameters`
column". No such errors existed: every notebook writes via `pandas.to_csv`, which
quotes `parameters` correctly — verified by round-tripping a value containing 18
commas through append-mode `to_csv` and back via `csv.reader` at exactly 7
fields.

The notebook read that valid CSV with `line.strip().split(',')`, which splits
*inside* quoted fields, rejoined `fields[5:-1]`, and re-wrote through
`csv.writer`, quoting a second time. That produced the `"""odict_keys([...`
triple-quoting in the published results and one 13-field row where two rows had
merged — its `num_epochs` read literally `100StackedEnsemble_RF`.

It also overwrote `2D_Results_full.csv` and `UAVATTACK_Results_full.csv` in `'w'`
mode from whatever was in the scratch CSVs.

The pipeline is now:
```
notebooks -> *_Results.csv -> filter.ipynb -> *_Results_filtered.csv -> make_all_plots.py
```

---

## 20. The plotting scripts could never find their inputs

`make_all_plots.py` and `print_csv.py` live in
`Visualization/accuracy_performance/` and referenced their inputs as bare
filenames, which Python resolves against the current working directory. The
filtered CSVs have only ever lived in `Visualization/Results/` — confirmed
against the full git history; no `*_filtered.csv` was ever committed under
`accuracy_performance/`. So running `python make_all_plots.py` from its own
directory raised `FileNotFoundError` pointing at
`Visualization/accuracy_performance/UAVATTACK_Results_filtered.csv`, and running
it from `Visualization/Results/` instead would fail on
`from print_csv import read_csv_dicts`. There was no directory from which the
script could work.

This predates every change in this session. It was found by executing the full
pipeline, not by reading the code.

`Visualization/accuracy_performance/make_all_plots.py`, before:

```python
FILES = [
    "UAVATTACK_Results_filtered.csv",
    "2D_Results_filtered.csv",
]
OUTDIR = Path("plots_out")
```

after:

```python
RESULTS_DIR = Path(__file__).resolve().parent.parent / "Results"
FILES = [
    RESULTS_DIR / "UAVATTACK_Results_filtered.csv",
    RESULTS_DIR / "2D_Results_filtered.csv",
]
OUTDIR = Path(__file__).resolve().parent / "plots_out"
```

`Visualization/accuracy_performance/print_csv.py`, before:

```python
    for fp in ["UAVATTACK_Results_filtered.csv", "2D_Results_filtered.csv"]:
```

after:

```python
    results_dir = Path(__file__).resolve().parent.parent / "Results"
    for fp in [results_dir / "UAVATTACK_Results_filtered.csv",
               results_dir / "2D_Results_filtered.csv"]:
```

Both are now anchored to the script's own location, so they work from any
working directory. `load_rows()` still calls `Path(f).name` for its `_source`
tag, so the UAVATTACK / 2D row separation is unaffected.

**Verified** by running the complete pipeline after the fix: seven UAV notebooks
plus `2DLogRegres.ipynb` produced `*_Results.csv`, `filter.ipynb` produced both
`*_Results_filtered.csv`, and `make_all_plots.py` wrote all 8 figures
(`fig_all`, `fig_trimmed_p1p99`, `fig_uavattack_only`, `fig_2d_only`, three
`fig_zoom_*`, and `fig_best_by_dataset`) as both `.pdf` and `.png`.
`print_csv.py` now prints both files. All generated artifacts were then removed.

---

## 21. The 2D image split still used the old 20% / 80% ratio

Fix 1 moved every tabular notebook to 80% train, but
`binaryImageTransformation/2d tubular data/split-Images.py` was left at the old
ratio, so the four 2D image models would have trained on 20% of the data while
every other 2D model trained on 80% -- with both sets of rows written into the
same `2D_Results.csv` and plotted side by side by `make_all_plots.py`. The
UAVATTACK sibling script already sends 20% to *test*, so the two were also
inconsistent with each other.

```python
    split_idx = math.ceil(0.2 * len(files))   # before -> 20% train, 80% test
    split_idx = math.ceil(0.8 * len(files))   # after  -> 80% train, 20% test
```

The images already generated on disk carried the old ratio too. Every class was
split exactly 20/80, so `data/Train` and `data/Test` were swapped -- two
directory renames rather than moving 510,530 files -- which preserves the
per-class stratification exactly.

| | before | after |
|---|---|---|
| Train | 102,107 (20%) | **408,423 (80%)** |
| Test | 408,423 (80%) | **102,107 (20%)** |

Per class after the swap: 318,260 / 29,166 / 35,385 / 25,612 train and
79,565 / 7,292 / 8,847 / 6,403 test -- 80.0% / 20.0% in every class. This now
matches the tabular split (`2DLogRegres.ipynb` reports 408,424 / 102,106).

**Verified** by loading both splits through `ImageFolder` with the notebooks'
own transform: 408,423 and 102,107 images, 4 classes, tensors `(1, 64, 64)`.

---

## 22. The UAV stacking model was fitted on unscaled features

The paper states *"For all tabular datasets, we use an 80/20 train-test split
and scale the features with Scikit-learn's StandardScaler."*
`Models/UAV_ATTACK/Stacking/stackingSpoofGPS.ipynb` did not scale, while its 2D
counterpart did. Its base learners include an RBF `SVC` and
`LogisticRegression`, which are badly distorted by unscaled GPS features where
latitude and longitude are around 1e7. Both notebooks write the identical
`MODEL_NAME` into the shared results files, so the two rows were being presented
as the same model under different preprocessing.

Added the import and the scaling step, matching the 2D notebook exactly:

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
```
and switched the two call sites:
```python
stacking_model.fit(X_train, y_train)            # before
stacking_model.fit(X_train_scaled, y_train)     # after

y_pred = stacking_model.predict(X_test)         # before
y_pred = stacking_model.predict(X_test_scaled)  # after
```

**Verified** by execution: all 8 cells ran with no error output, accuracy
100.00%, F1 1.0000. (`Models/UAV_ATTACK/One class/transform data.ipynb` also has
no scaler, but it trains no model -- it only prepares splits -- so it was left
alone.)

---

## 23. `CGAN.ipynb` printed a path nothing writes

Fix 16 corrected the `to_csv` target but not the `print` on the following line,
which named both the wrong directory and the wrong file (`gan`, not `cgan`).

```python
print("Synthetic data saved to ../../../syntheticSpoofing_gan_data.csv")                                   # before
print("Synthetic data saved to ../../../Datasets/csv/UAVATTACK/syntheticSpoofing_cgan_data.csv")           # after
```

---

## 24. `filter.ipynb` crashed on a short header

`filtered_row = {col: row[col] for col in keep_columns}` raises `KeyError` if an
input CSV lacks one of the six kept columns -- for instance a `*_Results.csv`
accumulated before the schema fix in item 11, when two notebooks wrote 4-column
rows and three wrote `training_time_sec`. Because `writer.writeheader()` has
already run by then, the crash leaves a header-only file that the next stage
reads as "0 results".

```python
filtered_row = {col: row[col] for col in keep_columns}          # before
filtered_row = {col: row.get(col, "") for col in keep_columns}  # after
```

---

## 25. `SDV_Synthetic.ipynb` would not parse on Python 3.11

`Synthetic_Data_Generation/UAV Synthetic Data Generation/SDV/SDV_Synthetic.ipynb`
ended its generation loop with an f-string broken across lines by a stray
newline inside the braces:

```python
    print(f"Trained synthesizer saved to {

    synth['pickle']}")
```

Multi-line f-string expressions only became legal in Python 3.12 (PEP 701). On
3.11 the whole cell raises

```
SyntaxError: unterminated string literal (detected at line 15)
```

so the notebook could not run at all, and the committed
`spoofing-*-synthesizer.pkl` files cannot have been produced by a 3.11
environment. Joined onto one line, which is valid on every version:

```python
    print(f"Trained synthesizer saved to {synth['pickle']}")
```

A compile check of every code cell in all 69 notebooks under the project's
Python 3.11 found this as the only failure; the 2D `SDV_Synthetic.ipynb` is
clean.

---

## 26. UAV synthesizers were fitted on GAN output instead of the real dataset

`Synthetic_Data_Generation/UAV Synthetic Data Generation/SDV/SDV_Synthetic.ipynb`:

```python
DATA_PATH = "../../../Datasets/csv/UAVATTACK/syntheticSpoofing_gan_data.csv"   # before
DATA_PATH = "../../../Datasets/csv/UAVATTACK/spoofing-merged-gps-only.csv"     # after
```

The 2D equivalent already fitted on its real `.xlsx`. The paper's Table 1 lists
the Source for all three synthetic rows as "UAV Attack and 2D", so the real
dataset was the stated intent.

`syntheticSpoofing_gan_data.csv` is itself the output of `GAN/GAN.ipynb`. Fitting
SDV on it made every UAV synthetic dataset second-generation synthetic, with
three measured consequences:

| | class balance | mean abs z-gap from real | RF acc | LogReg acc |
|---|---|---|---|---|
| real data | 86.3 / 13.7 | 0.000 | — | — |
| GC fitted on GAN output | 51.4 / 48.6 | 0.734 | 0.9763 | **0.1334** |
| GC fitted on real data | 85.8 / 14.2 | **0.336** | 0.9486 | **0.8727** |

(z-gap computed over the 49 features that actually vary in the real data; the
GAN additionally introduces spurious variance into all 33 features that are
constant in real flights, and emits impossible values such as negative
`satellites_used` and negative `vel_m_s`.)

The `0.1334` matters: logistic regression collapses to near-random on
GAN-derived synthetic data purely because of the distorted feature scales, which
would otherwise read as a finding about linear models. Note the reverse holds
for trees — RandomForest scores *higher* on GAN-derived data (0.9763 vs 0.9486),
because trees are scale-invariant and the artificial 50/50 balance helps them
learn the minority class. So the old setup flattered tree models and broke
linear ones.

The synthesizers were refitted on the real data and all nine UAV sized datasets
regenerated. The previous pickles and metadata are backed up outside the repo.

---

## 27. Stacked ensembles evaluated the meta-classifier on its own training rows

Three notebooks fitted the `RandomForestClassifier` meta-classifier and then
scored it on the same rows. The base detectors (OC-SVM, LOF, autoencoder) are
fitted on benign rows only and were left alone; the leak was only at the
meta-classifier.

| Notebook | before | after |
|---|---|---|
| `Models/UAV_ATTACK/Stacking/ensemble_of_paper's_models.ipynb` | `fit(stacked_features, y_test)` then `predict(stacked_features)` | 80/20 stratified split; fit on train, predict on held-out |
| `Models/2D/Stacking/ensemble.ipynb` | same | same |
| `Synthetic_Data_Generation/2D Synthetic Data Generation/Smote/stacked ensemble.ipynb` | SMOTE applied to all rows, fit on balanced, predict on full matrix | split first, SMOTE the training half only, predict on untouched held-out half |

The `*_SYNTHETIC/Stacking` variants already held out correctly (fit on synthetic,
predict on real) and the UAV SMOTE ensemble already split properly; those were
used as the template.

How much the leak actually inflated things depends on what was stacked, and the
two main notebooks differ:

- **UAV stacks three binary votes.** Only 5 distinct input patterns occur across
  3,622 rows, so there is almost nothing for the meta-classifier to memorise.
  Measured independently: 0.9925 as published (an exact reproduction of the
  committed figure) versus **0.9931** with a proper holdout. The published UAV
  number was sound; the fix simply makes it defensible.
- **2D stacks three continuous scores** over 510,530 rows, where every row is a
  distinct float triple and an unconstrained RandomForest can memorise freely.
  This is where the leak has room to bite.

Worth noting separately: on UAV the best single base detector (OC-SVM) reaches
0.9901 on its own, so the ensemble adds roughly 0.24 points over its best member.

### Measured outcome

Each notebook was re-executed after the fix. The UAV and 2D figures were also
produced by a second, independent replication written from scratch; both agreed
to four decimal places.

| Notebook | as published | with holdout | held-out n |
|---|---|---|---|
| `Models/UAV_ATTACK/Stacking/ensemble_of_paper's_models.ipynb` | 0.9925 | **0.9931** | 725 |
| `Models/2D/Stacking/ensemble.ipynb` | 0.9808 (repro of 0.9908) | **0.7609** | 102,106 |
| `Synthetic_Data_Generation/.../Smote/stacked ensemble.ipynb` | 0.9908 | **0.6051** | 102,106 |

**UAV is unaffected.** It stacks three binary votes, giving at most 8 possible
input patterns (5 occur), so there was nothing for the meta-classifier to
memorise. The published number was already sound.

**2D collapses.** It stacks three continuous scores across 510,530 rows, of
which 474,929 are distinct. An unconstrained RandomForest fitted on all of them
and scored on the same rows was memorising, not generalising. Held out, the
attack classes are revealed as weak:

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| benign | 0.81 | 0.93 | 0.86 | 79,565 |
| attack1 | 0.46 | 0.21 | 0.29 | 7,292 |
| attack2 | 0.25 | 0.15 | 0.18 | 8,846 |
| attack3 | 0.44 | 0.16 | 0.23 | 6,403 |

Note the reproduction gap on the second row: the as-published figure measured
here is 0.9808 against the committed 0.9908, a one-point difference most likely
from sklearn version drift in the autoencoder. The held-out figure is what
matters and both independent runs agree on it exactly.

### A consequence worth its own note: SMOTE now looks harmful, but it depends on the metric

The two 2D ensembles are otherwise identical — same `OneClassSVM(nu=0.011,
gamma=0.000211)`, same `LocalOutlierFactor(n_neighbors=1000)`, same
`MLPRegressor(hidden_layer_sizes=(3,))`, same PCA variances and seed, same
meta-classifier, and the same 80/20 split with `random_state=1082`. The only
difference is SMOTE on the meta-classifier's training half. So they are directly
comparable:

| | accuracy | weighted F1 | benign recall | attack recall (1/2/3) |
|---|---|---|---|---|
| without SMOTE | **0.7609** | 0.7245 | 0.93 | 0.21 / 0.15 / 0.16 |
| with SMOTE | 0.6051 | 0.6468 | 0.65 | **0.50 / 0.37 / 0.54** |

On accuracy SMOTE is 15.6 points worse, which contradicts the paper's statement
that "for tree-based and ensemble models, SMOTE generally maintained or improved
accuracy and F1 scores" — that improvement was an artifact of the leak.

But accuracy here is dominated by the 78% benign class. SMOTE roughly doubles to
triples recall on all three attack classes, trading benign recall (0.93 to 0.65)
for attack recall. For an intrusion detection system, missing fewer attacks at
the cost of more false alarms is often the preferable operating point. The
honest statement is that SMOTE shifts the trade-off toward attack detection
rather than that it helps or hurts outright, and the paper should report
per-class recall rather than accuracy alone for this comparison.


---

# Paper corrections

Where the paper, not the code, was wrong. Corrected copies with the full diff are
at `C:\Users\antho\Downloads\LaTeX-corrected\` (`CORRECTIONS.diff`,
`main.tex.original`). Applied identically to `main.tex` and
`main_anonymized.tex`; line endings preserved.

| Line | Before | After | Why |
|---|---|---|---|
| 233 | "generate two new datasets for each model ... sample sizes of 100,000 and 1,000,000" | "three new datasets ... 10,000, 100,000 and 1,000,000" | The code generates three sizes, and the paper's own total of 22 datasets only works with three |
| 257 | "For the UAV ATTACK dataset, we oversampled class 2 so it had the same number of samples as class 1." | "For the UAV Attack dataset, which is binary, we oversampled the malicious class so it had the same number of samples as the benign majority class." | UAV Attack is binary; there is no class 2 |
| 272, 274, 276 | `100k, 1M ... & 4` | `10k, 100k, 1M ... & 6` | 3 sizes × 3 synthesizers × 2 datasets = 18, +2 originals +2 image sets = **22**, matching the paper's stated total |
| 409 | "we recorded five classification metrics" | "we recorded four classification metrics" | Only four are listed |
| 776 | "The y-axis reports classification accuracy (0–100\%)." | "The y-axis reports classification accuracy (0–1)." | The committed figures (`fig_all.png` etc.) are plotted on a 0.0–1.0 axis |

---

# Open items — not changed, your call

These affect published conclusions or need a judgement the code cannot settle.

**UAV feature count.** The paper says 83 features. The merged CSV has 84 columns:
`timestamp` + 82 features + `label`. 83 is the non-`timestamp` column count
including the label. Left alone as it may be deliberate.

**Image paths are Windows-only.** All eight image notebooks ask for
`image-results-spoofing/Data` while the directory is `data`, and the four 2D ones
ask for `train`/`test` where the directories are `Train`/`Test`. Works on
Windows and macOS; breaks on Linux.

**Library versions.** The paper records Matplotlib 3.9.2 and NumPy 1.26.4; the
environment resolves to 3.11.2 and 2.1.3. Pin them in `requirements.txt` if the
figures must reproduce byte-for-byte.
