import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from . import schema as _schema
from .paths import repo_root

MODELS = {
    "Logistic Regression": "LR",
    "Logistic Regression (SMOTE)": "LR+SM",
    "Logistic Regression (Explainability Features)": "LR+EXPL",
    "Logistic Regression (Xgboost Features)": "LR+XGBF",
    "Logistic Regression (Quadratic Features)": "LR+QUAD",
    "Random Forest": "RF",
    "Random Forest (SMOTE)": "RF+SM",
    "Random Forest (Explainability Features)": "RF+EXPL",
    "Random Forest (Xgboost Features)": "RF+XGBF",
    "XGBoost": "XGB",
    "XGBoost (SMOTE)": "XGB+SM",
    "XGBoost (Explainability Features)": "XGB+EXPL",
    "XGBoost (Xgboost Features)": "XGB+XGBF",
    "MLP Classifier": "MLP",
    "MLP Classifier (SMOTE)": "MLP+SM",
    "MLP Classifier (Explainability Features)": "MLP+EXPL",
    "MLP Classifier (Xgboost Features)": "MLP+XGBF",
    "LSTM Classifier": "LSTM",
    "LSTM Classifier (SMOTE)": "LSTM+SM",
    "LSTM Classifier (Explainability Features)": "LSTM+EXPL",
    "LSTM Classifier (Xgboost Features)": "LSTM+XGBF",
    "LSTM Classifier (XGBoost Features)": "LSTM+XGBF",
    "CNN": "CNN",
    "CNN-LSTM": "C-LSTM",
    "ResNet-CNN": "ResNet",
    "ResNet-LSTM": "ResNet-LSTM",
    "OneClassSVM": "OCSVM",
    "LocalOutlierFactor": "LOF",
    "StackedEnsemble_RF": "SE-RF",
    "StackedEnsemble_RF (SMOTE)": "SE-RF+SM",
    "StackingClassifier(LogisticRegression RandomForest SVC)": "STACK",
}

FAMILIES = {
    "Regular",
    "SMOTE",
    "Stacking",
    "OneClass",
    "LSTM",
    "FeatureEngineering",
    "Image",
    "Synthetic",
    "Synthetic-LSTM",
    "Synthetic-Stacking",
}

SYNTH_FAMILIES = {"Synthetic", "Synthetic-Stacking", "Synthetic-LSTM", "SMOTE"}

TEST_SET_TAGS = {
    "real_heldout_20pct": "",
    "real_full": " [full-real]",
    "real_heldout_benign_plus_malicious": " [benign-ho]",
}

VARIANT_SUFFIXES = ("+SM", "+EXPL", "+XGBF", "+QUAD")


@dataclass(frozen=True)
class DatasetInfo:
    short: str
    kind: str
    datasets: tuple
    generator: Optional[str] = None
    size: Optional[int] = None


def _sdv_entries():
    entries = {}
    for gen, label in (("gc", "GC"), ("ctgan", "CTGAN"), ("tvae", "TVAE")):
        for size, tag in ((10_000, "10k"), (100_000, "100k"), (1_000_000, "1M")):
            entries[f"spoofing_{gen}_{size}.csv"] = DatasetInfo(
                short=f"{label}-{tag}",
                kind="synthetic",
                datasets=("uav", "2d"),
                generator=gen,
                size=size,
            )
    return entries


DATASETS = {
    "spoofing-merged-gps-only.csv": DatasetInfo(
        short="SPOOF-GPS", kind="real", datasets=("uav",)
    ),
    "GPS_Data_Simplified_2D_Feature_Map.xlsx": DatasetInfo(
        short="GPS-2D", kind="real", datasets=("2d",)
    ),
    "syntheticSpoofing_gan_data.csv": DatasetInfo(
        short="GAN", kind="synthetic", datasets=("uav", "2d"), generator="gan", size=10_000
    ),
    "syntheticSpoofing_cgan_data.csv": DatasetInfo(
        short="CGAN", kind="synthetic", datasets=("uav", "2d"), generator="cgan", size=10_000
    ),
    **_sdv_entries(),
}

DATASET_KEY_SUFFIX = {"uav": " (UAV)", "2d": " (2D)"}

CLASS_LABELS = {
    info.short: list(_schema.get(info.datasets[0]).class_names)
    for info in DATASETS.values()
    if info.kind == "real"
}


def normalize_label(name):
    n = (name or "").strip()
    return MODELS.get(n, n)


def collapse_variants(short):
    for suffix in VARIANT_SUFFIXES:
        if short.endswith(suffix):
            return short[: -len(suffix)]
    return short


def family_for(short):
    s = short
    if s.startswith("ResNet-LSTM") or s.startswith("C-LSTM"):
        return "CNN/ResNet-LSTM"
    if s.startswith("ResNet") or s == "CNN":
        return "CNN"
    if s.startswith("SE-") or s.startswith("STACK"):
        return "Ensemble"
    if s.startswith("RF"):
        return "RF"
    if s.startswith("LR"):
        return "LR"
    if s.startswith("XGB"):
        return "XGB"
    if s.startswith("MLP"):
        return "MLP"
    if s.startswith("OCSVM") or s.startswith("LOF"):
        return "OneClass"
    if s.startswith("LSTM"):
        return "LSTM"
    return s


def dataset_short(name, dataset_key=None):
    n = (name or "").strip()
    info = DATASETS.get(n)
    if info is None:
        return n
    if dataset_key and len(info.datasets) > 1 and dataset_key in DATASET_KEY_SUFFIX:
        return info.short + DATASET_KEY_SUFFIX[dataset_key]
    return info.short


def synthetic_info(name):
    info = DATASETS.get((name or "").strip())
    if info is None or info.kind != "synthetic":
        return None
    return info


def synthetic_files(dataset_key, generators=None):
    return [
        name
        for name, info in DATASETS.items()
        if info.kind == "synthetic"
        and dataset_key in info.datasets
        and (generators is None or info.generator in generators)
    ]


def protocol_tag(row):
    ts = (row.get("test_set", "") or "").strip()
    if ts in TEST_SET_TAGS:
        return TEST_SET_TAGS[ts]
    return " [%s]" % ts if ts and ts != "N/A" else ""


def results_files():
    found = []
    for schema in _schema.SCHEMAS.values():
        path = _schema.results_path(schema)
        if path.exists():
            found.append(path)
    return found


def _dataset_key_for_source(source_name):
    if "UAVATTACK" in source_name:
        return "uav"
    if source_name.startswith("2D"):
        return "2d"
    return None


def load_rows(files=None):
    files = results_files() if files is None else [Path(f) for f in files]
    rows = []
    for f in files:
        with open(f, "r", encoding="utf-8", newline="") as handle:
            for raw in csv.DictReader(handle):
                row = {
                    (k or "").strip().lstrip("﻿"): (v or "").strip()
                    for k, v in raw.items()
                }
                row["_source"] = Path(f).name
                row["_dataset_key"] = _dataset_key_for_source(Path(f).name)
                rows.append(row)
    return rows


def validate_row(row):
    problems = []
    model = row.get("model")
    if model not in MODELS:
        problems.append("model %r is not in gps_ids.results.MODELS" % model)
    dataset = row.get("dataset")
    if dataset not in DATASETS:
        problems.append("dataset %r is not in gps_ids.results.DATASETS" % dataset)
    family = row.get("family")
    if family not in FAMILIES:
        problems.append("family %r is not in gps_ids.results.FAMILIES" % family)
    test_set = row.get("test_set")
    if test_set not in TEST_SET_TAGS:
        problems.append(
            "test_set %r is not in gps_ids.results.TEST_SET_TAGS" % test_set
        )
    if problems:
        raise ValueError(
            "results row failed vocabulary validation:\n  " + "\n  ".join(problems)
        )


def append_validated(row_or_rows, path):
    import eval_metrics

    rows = row_or_rows if isinstance(row_or_rows, list) else [row_or_rows]
    for row in rows:
        validate_row(row)
    return eval_metrics.append_row(rows, path)
