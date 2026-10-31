# Image-Based Intrusion Detection System for GPS Spoofing in Unmanned Aerial Vehicles

Research artifacts for the paper "Image-Based Intrusion Detection System for Global Positioning System Spoofing in Unmanned Aerial Vehicles."

Two original datasets drive everything in the repository:

| Dataset | File | Classes |
|---|---|---|
| UAV-ATTACK | `Datasets/csv/UAVATTACK/spoofing-merged-gps-only.csv` | benign, malicious |
| 2D Spoofing | `Datasets/excel/2dSpoofingDataset/GPS_Data_Simplified_2D_Feature_Map.xlsx` | benign, simple, intermediate, sophisticated |

Everything else is derived from them: the synthetic tables, the binary images, and every results row.

## Layout

```
Datasets/          the two original datasets, plus the generated tables that live beside them
DataGeneration/    everything that produces derived data
  BinaryImages/    tabular rows -> binary images, per dataset
  SyntheticData/   SDV / GAN / CGAN generators and the sampling script, per dataset
Models/            every model, grouped by dataset
  2D/ UAV_ATTACK/              models trained on the original data
  2D_SYNTHETIC/ UAV_ATTACK_SYNTHETIC/   models trained on synthetic data, tested on real
Visualization/     figures and explainability notebooks
gps_ids/           the modules the notebooks are built on
eval_metrics.py    the results schema and metric computation
```

The model folders mirror each other: a family present for one dataset is present for the other, under the same folder and file names. See the per-dataset table in `SETUP.md`.

## Where to start

1. `SETUP.md` — environment, dataset placement, and how to run anything.
2. `Datasets/readme.md` — download links, expected paths, and which files are generated rather than downloaded.
3. `DataGeneration/readme.md` — how the synthetic tables and binary images are produced.

A notebook is a thin caller: it builds an experiment protocol and asks the training harness for one model, so reading `gps_ids/` tells you what every notebook actually does.

## Contact and citation

For author contact, citation text, licensing, or to request the original datasets, see `Datasets/readme.md` or open an issue.
