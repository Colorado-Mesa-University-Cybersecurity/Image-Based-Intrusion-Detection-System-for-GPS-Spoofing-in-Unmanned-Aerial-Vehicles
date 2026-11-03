from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from . import schema as _schema

SEED = 1082
N_JOBS = -1
TRAIN_SIZE = 0.8

TAG_REAL_HELDOUT = "real_heldout_20pct"
TAG_REAL_FULL = "real_full"
TAG_BENIGN_HELDOUT = "real_heldout_benign_plus_malicious"


@dataclass
class Experiment:
    schema: _schema.DatasetSchema
    dataset_name: str
    test_set: str
    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: np.ndarray
    y_test: np.ndarray
    scaler: StandardScaler
    X_fit: Optional[pd.DataFrame] = None
    X_test_raw: Optional[pd.DataFrame] = None
    seed: int = SEED

    @property
    def labels(self):
        return list(range(len(self.schema.class_names)))

    @property
    def class_names(self):
        return list(self.schema.class_names)

    @property
    def feature_names(self):
        return list(self.X_train.columns)

    @property
    def n_train(self):
        return len(self.y_train)

    @property
    def n_features(self):
        return self.X_train.shape[1]

    @property
    def results_csv(self):
        return str(_schema.results_path(self.schema))

    def eval_kwargs(self):
        return {
            "dataset_name": self.dataset_name,
            "labels": self.labels,
            "class_names": self.class_names,
            "y_train": self.y_train,
            "seed": self.seed,
            "n_train": self.n_train,
            "n_features": self.n_features,
            "test_set": self.test_set,
        }


def _scaled(scaler, X):
    return pd.DataFrame(scaler.transform(X), columns=X.columns, index=X.index)


def _select_features(X, features):
    if features is None:
        return X
    cleaned = list(_schema.clean_column_names(features))
    missing = [c for c in cleaned if c not in X.columns]
    if missing:
        raise ValueError("unknown feature column(s): %s" % missing)
    return X[cleaned]


def real_heldout(dataset, features=None, *, seed=None):
    seed = SEED if seed is None else seed
    schema = _schema.get(dataset)
    X, y = _schema.load_real(schema)
    X = _select_features(X, features)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, train_size=TRAIN_SIZE, random_state=seed, stratify=y
    )
    scaler = StandardScaler().fit(X_train)
    return Experiment(
        schema=schema,
        dataset_name=schema.real_file,
        test_set=TAG_REAL_HELDOUT,
        X_train=_scaled(scaler, X_train),
        X_test=_scaled(scaler, X_test),
        y_train=np.asarray(y_train),
        y_test=np.asarray(y_test),
        scaler=scaler,
        seed=seed,
    )


def real_train_rows(dataset, features=None, *, seed=None):
    schema = _schema.get(dataset)
    X, _ = _schema.load_real(schema)
    X = _select_features(X, features)
    exp = real_heldout(dataset, features=features, seed=seed)
    return X.loc[exp.X_train.index], exp.y_train


def build_smote(seed, strategy, k_neighbors=5):
    from imblearn.over_sampling import SMOTE
    from sklearn.neighbors import NearestNeighbors

    return SMOTE(
        random_state=seed,
        sampling_strategy=strategy,
        k_neighbors=NearestNeighbors(n_neighbors=k_neighbors + 1, n_jobs=N_JOBS),
    )


def smote_heldout(dataset, features=None, *, seed=None):
    seed = SEED if seed is None else seed
    base = real_heldout(dataset, features=features, seed=seed)
    unique, counts = np.unique(base.y_train, return_counts=True)
    majority = unique[np.argmax(counts)]
    target = counts.max()
    strategy = {cls: target for cls in unique if cls != majority}
    smote = build_smote(seed, strategy)
    X_res, y_res = smote.fit_resample(base.X_train, base.y_train)
    base.X_train = X_res
    base.y_train = np.asarray(y_res)
    return base


def one_class(dataset, *, seed=None):
    seed = SEED if seed is None else seed
    schema = _schema.get(dataset)
    X, y = _schema.load_real(schema)
    benign = y == 0
    X_benign, y_benign = X[benign], y[benign]
    X_train_raw, X_val_raw, y_train, y_val = train_test_split(
        X_benign, y_benign, train_size=TRAIN_SIZE, random_state=seed
    )
    scaler = StandardScaler().fit(X_train_raw)
    X_test = pd.concat([X_val_raw, X[~benign]])
    y_test = np.concatenate([y_val, y[~benign]])
    return Experiment(
        schema=schema,
        dataset_name=schema.real_file,
        test_set=TAG_BENIGN_HELDOUT,
        X_train=_scaled(scaler, X_train_raw),
        X_test=_scaled(scaler, X_test),
        y_train=np.asarray(y_train),
        y_test=y_test,
        scaler=scaler,
        seed=seed,
    )


def ensemble_heldout(dataset, *, seed=None):
    seed = SEED if seed is None else seed
    schema = _schema.get(dataset)
    X, y = _schema.load_real(schema)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, train_size=TRAIN_SIZE, random_state=seed, stratify=y
    )
    y_train = np.asarray(y_train)
    X_fit_raw = X_train[y_train == 0]
    scaler = StandardScaler().fit(X_fit_raw)
    return Experiment(
        schema=schema,
        dataset_name=schema.real_file,
        test_set=TAG_REAL_HELDOUT,
        X_train=_scaled(scaler, X_train),
        X_test=_scaled(scaler, X_test),
        y_train=y_train,
        y_test=np.asarray(y_test),
        scaler=scaler,
        X_fit=_scaled(scaler, X_fit_raw),
        X_test_raw=X_test,
        seed=seed,
    )


def synthetic_vs_full_real(dataset, synth_file, *, seed=None):
    seed = SEED if seed is None else seed
    schema = _schema.get(dataset)
    X_s, y_s = _schema.load_synthetic(schema, synth_file)
    X_r, y_r = _schema.load_real(schema)
    X_train, _, y_train, _ = train_test_split(
        X_s, y_s, train_size=TRAIN_SIZE, random_state=seed, stratify=y_s
    )
    scaler = StandardScaler().fit(X_train)
    return Experiment(
        schema=schema,
        dataset_name=synth_file,
        test_set=TAG_REAL_FULL,
        X_train=_scaled(scaler, X_train),
        X_test=_scaled(scaler, X_r),
        y_train=np.asarray(y_train),
        y_test=np.asarray(y_r),
        scaler=scaler,
        seed=seed,
    )


def synthetic_ensemble_vs_full_real(dataset, synth_file, *, seed=None):
    seed = SEED if seed is None else seed
    schema = _schema.get(dataset)
    X_s, y_s = _schema.load_synthetic(schema, synth_file)
    X_r, y_r = _schema.load_real(schema)
    y_s = np.asarray(y_s)
    X_fit_raw = X_s[y_s == 0]
    scaler = StandardScaler().fit(X_fit_raw)
    return Experiment(
        schema=schema,
        dataset_name=synth_file,
        test_set=TAG_REAL_FULL,
        X_train=_scaled(scaler, X_s),
        X_test=_scaled(scaler, X_r),
        y_train=y_s,
        y_test=np.asarray(y_r),
        scaler=scaler,
        X_fit=_scaled(scaler, X_fit_raw),
        X_test_raw=X_r,
        seed=seed,
    )


def synthetic_vs_real_heldout(dataset, synth_file, *, seed=None):
    seed = SEED if seed is None else seed
    schema = _schema.get(dataset)
    X_s, y_s = _schema.load_synthetic(schema, synth_file)
    X_r, y_r = _schema.load_real(schema)
    _, X_test, _, y_test = train_test_split(
        X_r, y_r, train_size=TRAIN_SIZE, random_state=seed, stratify=y_r
    )
    scaler = StandardScaler().fit(X_s)
    return Experiment(
        schema=schema,
        dataset_name=synth_file,
        test_set=TAG_REAL_HELDOUT,
        X_train=_scaled(scaler, X_s),
        X_test=_scaled(scaler, X_test),
        y_train=np.asarray(y_s),
        y_test=np.asarray(y_test),
        scaler=scaler,
        seed=seed,
    )
