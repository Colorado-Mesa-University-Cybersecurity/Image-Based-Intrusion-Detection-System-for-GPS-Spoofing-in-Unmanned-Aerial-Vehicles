# Environment & Dataset Setup

Working setup for reproducing the experiments. Verified on Windows 11, RTX 4060.

## 1. Python environment

**Python 3.11 is required.** The system interpreter here is 3.14, which has no
wheels for `torch` or `sdv`. Build an isolated 3.11 env with `uv`:

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv -r requirements.txt
```

### CUDA

`requirements.txt` pulls the default **CPU** torch wheels. On an NVIDIA GPU,
replace them with the CUDA build — this matters a lot for the CNN / ResNet /
LSTM image notebooks:

```bash
uv pip install --python .venv --reinstall-package torch --reinstall-package torchvision \
    torch torchvision --index-url https://download.pytorch.org/whl/cu126
```

Verify:

```bash
.venv/Scripts/python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
# 2.14.1+cu126 True
```

### SDV must stay on 1.x

`sdv>=2` **breaks this repo**: SDV 2.0 removed the `Synthesizer.load()`
classmethod that `scripts/gen_synth.py` and `SDV_Synthetic.ipynb` both call, and the
committed `spoofing-*-synthesizer.pkl` files were fitted with 1.x. The pin in
`requirements.txt` (`sdv>=1.17,<2`) is deliberate — don't relax it.

## 2. Datasets

| Dataset | Target path | Status |
|---|---|---|
| 2D Spoofing (`GPS_Data_Simplified_2D_Feature_Map.xlsx`, 72 MB) | `Datasets/excel/2dSpoofingDataset/` | Public — direct download |
| UAV-ATTACK (`spoofing-merged-gps-only.csv`, 3,622 x 84) | `Datasets/csv/UAVATTACK/` | **Needs an IEEE account** |
| SDV synthetic CSVs (18 files) | `Datasets/{csv/UAVATTACK,excel/2dSpoofingDataset}/` | Generated locally |
| UAVATTACK binary images (3,622 PNG) | `binaryImageTransformation/UAVATTACK tubular data/image-results-spoofing/` | From authors' Drive |
| 2D binary images (510,530 PNG) | `binaryImageTransformation/2d tubular data/image-results-spoofing/` | Generated locally |

### 2D Spoofing dataset

Downloads without an account from Mendeley:

```bash
mkdir -p Datasets/excel/2dSpoofingDataset
curl -L "https://data.mendeley.com/public-files/datasets/z7dj3yyzt8/files/67e5bd6e-1d2e-4a7d-bef0-248fda7c91a0/file_downloaded" \
  -o Datasets/excel/2dSpoofingDataset/GPS_Data_Simplified_2D_Feature_Map.xlsx
```

Expected `sha256`: `de6f7e95efb9df3708b5b0d2a8408e25d062867ab1a233b6b39f9838ff04afee`
Loads as 510,530 rows x 14 cols, 4 classes (`Output` = 0/1/2/3), no nulls.

Note the filename: `Datasets/readme.md` calls it `Simplified_2D_Feature_Map.xlsx`,
but every notebook opens `GPS_Data_Simplified_2D_Feature_Map.xlsx`. Use the
latter.

### UAV-ATTACK dataset -- manual step

"Open access" here still requires a **free IEEE account**. The file list does
not render for anonymous visitors, and there is no public mirror, so this step
cannot be scripted.

1. Create or sign in to a free IEEE account (an IEEE *membership* is not
   needed): <https://www.ieee.org/profile/public/createwebaccount/showCreateAccount.html>
2. Signed in, open the dataset page:
   <https://ieee-dataport.org/open-access/uav-attack-dataset> (DOI
   `10.21227/00dg-0d12`). The "Datasets and Files" table appears only once you
   are authenticated.
3. Download **`UAVAttackData_zip`** and extract it outside this repo.
4. Copy the merged file into place:

```bash
cp "<extracted>/Live GPS Spoofing and Jamming/GPS Spoofing/Processed/spoofing-merged-gps-only.csv"    Datasets/csv/UAVATTACK/
```

If the sign-in loops or the file table stays hidden, it is usually the IEEE SSO
redirect: go to <https://ieee-dataport.org> first, confirm your name shows
top-right, then navigate to the dataset page.

`spoofing-merged-gps-only.csv` ships **inside** the download, under
`GPS Spoofing/Processed/` -- it does not need to be rebuilt from the ULOG files.
It is 3,622 rows x 84 columns, 3,124 `benign` / 498 `malicious`, no nulls. Its 83
non-`timestamp` columns match the committed SDV synthesizers exactly once the
notebooks' own `df.columns.str.replace('[\[\]<>]', '_')` cleanup is applied
(`q[0]` -> `q_0_`), and its class counts match the UAVATTACK image folders
exactly (2,500+624 benign, 399+99 malicious).

A sibling `jamming-merged-gps-only.csv` sits under `GPS Jamming/Processed/`; no
notebook in this repo references it.

Authors: Jason Whelan, Thanigajan Sangarapillai, Omar Minawi, Abdulaziz
Almehmadi, Khalil El-Khatib (Ontario Tech University / University of Tabuk).
Captured with PX4 on a Pixhawk 4; live spoofing used a HackRF with GPS-SDR-SIM.
The authors note the *simulated* runs are less accurate and recommend the
**live** GPS spoofing/jamming data.

### Synthetic CSVs

Samples the committed synthesizers into both dataset folders, through the
canonical dataset schema (`gps_ids/schema.py`), for `gc` / `ctgan` / `tvae`
at 10k / 100k / 1M rows:

```bash
.venv/Scripts/python -I scripts/gen_synth.py . 10000 100000 1000000
```

Roughly 5.5 GB total; skips files that already exist, so it is resumable.

### Binary images

The UAVATTACK images come from the authors' Drive folder linked in
`binaryImageTransformation/readme.md` (`UAVATTACK_image-results-spoofing.rar`) —
2,899 train / 723 test across `benign` and `malicious`.

The 2D images are **not** distributed and must be generated:

```bash
cd "binaryImageTransformation/2d tubular data"
../../.venv/Scripts/python -m jupyter nbconvert --to notebook --execute tabToImage.ipynb
../../.venv/Scripts/python split-Images.py
```

`tabToImage.ipynb` writes every image into `image-results-spoofing/data/Train/<class>`,
and `split-Images.py` moves 20% of each class into `.../data/Test/<class>` — the
layout the four 2D notebooks read, and the same one the UAVATTACK archive ships.
`organize.py` is only needed if a run left images loose in
`image-results-spoofing/`; `split-Images.py` accepts that layout too, and refuses
to write a manifest when it finds nothing to split.

This yields 408,423 train / 102,107 test across classes `0`–`3`.

## 3. Scope notes

With every dataset in place, all 69 notebooks have their inputs. Two caveats on
run time rather than availability:

- The four 2D image notebooks (`binaryImageTransformation/2d tubular data/`
  `CNN`, `ResNet`, `ResnetLSTM`, `LSTM`) took 29-110 hours each in the published
  results. Reduce `num_epochs` for a smoke test.
- `Models/*_SYNTHETIC/**` and the SMOTE notebooks loop over all nine synthetic
  sizes including 1M rows; the stacking variants fit `SVC(probability=True)`,
  which is superlinear in sample count.

## 4. Results files

Model notebooks append to `2D_Results.csv` / `UAVATTACK_Results.csv` at the repo
root, creating them with a header if absent. Both are gitignored scratch
accumulators and are written by `pandas.to_csv()`, so they are valid quoted CSV
-- read them with `csv.DictReader` or `pd.read_csv`, never by splitting on
commas.

Every model notebook records its results through `eval_metrics.py` at the repo
root, so all families and both datasets produce the identical 50-column schema:

```python
from eval_metrics import append_row, evaluate, summary, time_inference

row = evaluate(y_test, y_pred, model_name=MODEL_NAME, dataset_name=DATASET_NAME,
               family="Regular", labels=[0, 1, 2, 3], class_names=[...],
               y_proba=proba, y_train=y_train, train_time_sec=train_time,
               parameters=model.get_params(), seed=RANDOM_STATE)
append_row(row, RESULTS_CSV)
```

Each notebook locates the module by walking up from its own directory, so the
notebooks keep working from their existing folders. `append_row` reindexes every
row to `eval_metrics.COLUMNS`, which is what keeps the schema identical across
families; columns that do not apply to a given run are written as `N/A` rather
than omitted. Per-class columns use fixed slots `recall_c0..c3`, so the 2-class
UAV rows leave `c2`/`c3` empty.

The pipeline is:

```
notebooks -> *_Results.csv -> make_all_plots.py / make_metric_plots.py
```

The plots read only the raw `*_Results.csv` at the repo root, through
`gps_ids/results.py`: one reader, plus the registry of canonical model names,
dataset files, families, and protocol tags that every notebook row is validated
against on write (`append_validated`). The lossy `*_Results_filtered.csv` step
and its `filter.ipynb` are gone; adding a model or dataset is one registry
entry in `gps_ids/results.py`.

Rows carry the evaluation protocol in `test_set`, and both plot scripts append it
to the model label (`[full-real]`, `[benign-ho]`) so runs measured on different
test sets are never pooled into one bar or one ranking. An untagged label means
the standard held-out 20% of the real data.

The previously committed `*_Results_full.csv` files and the
`Results fixes/Fix results.ipynb` step that produced them have been removed.

Reproduction spot-checks against the published numbers, before they were
removed:

| Notebook | | f1 | accuracy |
|---|---|---|---|
| `Models/2D/Regular/2DLogRegres.ipynb` | published | 0.6825183052421334 | 0.7789307190566666 |
| | fresh run | 0.6825183052421334 | 0.7789307190566666 |
| `Models/UAV_ATTACK/Regular/logRegressSpoofGPS.ipynb` | published | 0.9979229851190652 | 0.9979296066252588 |
| | fresh run | 0.9979 | 0.9979 |

No results ship with the repo -- `*_Results_full.csv` and both
`*_Results_filtered.csv` were removed so they can be regenerated cleanly. The
plotting stage therefore needs a model run first:

```bash
# 1. run model notebooks -> 2D_Results.csv / UAVATTACK_Results.csv at the repo root
# 2. draw the figures
cd Visualization/accuracy_performance
../../.venv/Scripts/python make_all_plots.py
../../.venv/Scripts/python make_metric_plots.py
```

Run before step 1, both scripts print which CSV they expected and exit without
writing anything.

`make_all_plots.py` writes one subdirectory of `plots_out/` per metric in its
`METRICS` list, each with the scatter and best-per-dataset figures; the accuracy
figures carry the majority-class baseline as a reference line and mark models
that predicted a single class. `make_metric_plots.py` writes `plots_out/metrics/`
with the figures that need the imbalance-aware columns: accuracy-vs-MCC,
per-class recall heatmaps, the five-metric disagreement bars, lift over the
majority baseline, prior shift for the synthetic and SMOTE families, and
batch-vs-online inference latency.
