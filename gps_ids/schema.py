from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from .paths import repo_root

COLUMN_CLEAN_PATTERN = r"[\[\]<>]"


@dataclass(frozen=True)
class DatasetSchema:
    key: str
    real_file: str
    data_dir: str
    label_column: str
    class_names: tuple
    drop_columns: tuple
    results_csv: str
    reader: str


UAV = DatasetSchema(
    key="uav",
    real_file="spoofing-merged-gps-only.csv",
    data_dir="Datasets/csv/UAVATTACK",
    label_column="label",
    class_names=("benign", "malicious"),
    drop_columns=("timestamp",),
    results_csv="UAVATTACK_Results.csv",
    reader="csv",
)

TWO_D = DatasetSchema(
    key="2d",
    real_file="GPS_Data_Simplified_2D_Feature_Map.xlsx",
    data_dir="Datasets/excel/2dSpoofingDataset",
    label_column="Output",
    class_names=("benign", "simple", "intermediate", "sophisticated"),
    drop_columns=(),
    results_csv="2D_Results.csv",
    reader="excel",
)

SCHEMAS = {s.key: s for s in (UAV, TWO_D)}


def get(key):
    if isinstance(key, DatasetSchema):
        return key
    if key not in SCHEMAS:
        raise KeyError(
            "unknown dataset %r; known datasets: %s" % (key, sorted(SCHEMAS))
        )
    return SCHEMAS[key]


def clean_column_names(columns):
    return pd.Index(columns).str.replace(COLUMN_CLEAN_PATTERN, "_", regex=True)


def clean_columns(df):
    out = df.copy()
    out.columns = clean_column_names(out.columns)
    return out


def encode_labels(values, schema):
    schema = get(schema)
    s = pd.Series(values)
    k = len(schema.class_names)
    if pd.api.types.is_numeric_dtype(s):
        arr = s.to_numpy()
        if not np.isfinite(arr).all():
            raise ValueError("%s labels contain non-finite values" % schema.key)
        as_int = arr.astype(np.int64)
        if (as_int != arr).any():
            raise ValueError("%s labels contain non-integer numbers" % schema.key)
        bad = (as_int < 0) | (as_int >= k)
        if bad.any():
            raise ValueError(
                "%s labels outside 0..%d: %s"
                % (schema.key, k - 1, sorted(np.unique(as_int[bad]).tolist()))
            )
        return as_int
    mapping = {name: i for i, name in enumerate(schema.class_names)}
    mapped = s.astype(str).map(mapping)
    if mapped.isna().any():
        unknown = sorted(set(s[mapped.isna()].astype(str)))
        raise ValueError(
            "%s labels not in class vocabulary %s: %s"
            % (schema.key, list(schema.class_names), unknown)
        )
    return mapped.to_numpy(dtype=np.int64)


def real_path(schema) -> Path:
    schema = get(schema)
    return repo_root() / schema.data_dir / schema.real_file


def synthetic_path(schema, filename) -> Path:
    schema = get(schema)
    return repo_root() / schema.data_dir / filename


def results_path(schema) -> Path:
    schema = get(schema)
    return repo_root() / schema.results_csv


def _read(path, reader, **kwargs):
    if reader == "excel":
        return pd.read_excel(path, **kwargs)
    return pd.read_csv(path, **kwargs)


@lru_cache(maxsize=None)
def feature_columns(key):
    schema = get(key)
    head = _read(real_path(schema), schema.reader, nrows=0)
    cleaned = clean_column_names(head.columns)
    reserved = {schema.label_column, *schema.drop_columns}
    return tuple(c for c in cleaned if c not in reserved)


def normalize(df, schema):
    schema = get(schema)
    df = clean_columns(df)
    if schema.label_column not in df.columns:
        raise ValueError(
            "frame has no %r column for dataset %s"
            % (schema.label_column, schema.key)
        )
    y = encode_labels(df[schema.label_column], schema)
    feats = list(feature_columns(schema.key))
    missing = [c for c in feats if c not in df.columns]
    if missing:
        raise ValueError(
            "frame is missing %d feature column(s) for dataset %s, first few: %s"
            % (len(missing), schema.key, missing[:5])
        )
    X = df[feats]
    return X, y


def load_real(schema):
    schema = get(schema)
    return normalize(_read(real_path(schema), schema.reader), schema)


def load_synthetic(schema, filename):
    schema = get(schema)
    path = synthetic_path(schema, filename)
    if not path.is_file():
        raise FileNotFoundError(path)
    return normalize(pd.read_csv(path), schema)


def to_canonical_frame(X, y, schema):
    schema = get(schema)
    X, y = normalize(X.assign(**{schema.label_column: np.asarray(y)}), schema)
    out = X.copy()
    out[schema.label_column] = y
    return out


def write_synthetic(X, y, schema, filename):
    schema = get(schema)
    frame = to_canonical_frame(X, y, schema)
    path = synthetic_path(schema, filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".partial")
    frame.to_csv(tmp, index=False)
    tmp.replace(path)
    return path
