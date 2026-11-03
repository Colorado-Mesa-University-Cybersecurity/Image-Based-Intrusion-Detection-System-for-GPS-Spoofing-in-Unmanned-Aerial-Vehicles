import csv
import os
import time

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    log_loss,
    matthews_corrcoef,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
    roc_auc_score,
)

MAX_CLASSES = 4
NA = "N/A"

COLUMNS = [
    "model",
    "dataset",
    "family",
    "test_set",
    "seed",
    "n_classes",
    "class_names",
    "n_train",
    "n_test",
    "n_features",
    "mcc",
    "balanced_accuracy",
    "f1_macro",
    "g_mean",
    "precision_macro",
    "recall_macro",
    "accuracy",
    "majority_baseline_accuracy",
    "accuracy_lift_over_majority",
    "f1_weighted",
    "is_degenerate",
    "n_classes_predicted",
    "min_class_recall",
    "worst_class",
]
COLUMNS += ["recall_c%d" % i for i in range(MAX_CLASSES)]
COLUMNS += ["precision_c%d" % i for i in range(MAX_CLASSES)]
COLUMNS += ["support_c%d" % i for i in range(MAX_CLASSES)]
COLUMNS += [
    "train_prior",
    "test_prior",
    "pred_prior",
    "prior_shift_tv",
    "pred_prior_tv",
    "log_loss",
    "pr_auc_macro",
    "roc_auc_ovr_macro",
    "train_time_sec",
    "infer_batch_us_per_row",
    "infer_online_p50_us",
    "infer_online_p95_us",
    "num_epochs",
    "parameters",
]


def _prior(y, labels):
    y = np.asarray(y)
    if y.ndim > 1:
        if y.ndim == 2 and y.shape[1] == len(labels):
            y = y.argmax(axis=1)
        else:
            y = y.ravel()
    n = len(y)
    if n == 0:
        return np.zeros(len(labels), dtype=float)
    return np.array([float((y == c).sum()) / n for c in labels])


def _tv(p, q):
    return float(0.5 * np.abs(np.asarray(p) - np.asarray(q)).sum())


def _fmt_prior(p):
    return ";".join("%.4f" % v for v in p)


def _g_mean(recalls):
    r = np.asarray(recalls, dtype=float)
    if len(r) == 0:
        return np.nan
    return float(np.prod(r) ** (1.0 / len(r)))


def time_inference(predict_batch, X, predict_one=None, n_online=200, repeats=3):
    out = {
        "infer_batch_us_per_row": NA,
        "infer_online_p50_us": NA,
        "infer_online_p95_us": NA,
    }
    if predict_batch is None or X is None or len(X) == 0:
        return out
    try:
        predict_batch(X[:1])
        best = np.inf
        for _ in range(repeats):
            t = time.perf_counter()
            predict_batch(X)
            best = min(best, time.perf_counter() - t)
        out["infer_batch_us_per_row"] = best * 1e6 / len(X)
    except Exception:
        pass
    fn = predict_one if predict_one is not None else predict_batch
    try:
        k = int(min(n_online, len(X)))
        fn(X[:1])
        lat = np.empty(k, dtype=float)
        for i in range(k):
            t = time.perf_counter()
            fn(X[i : i + 1])
            lat[i] = (time.perf_counter() - t) * 1e6
        out["infer_online_p50_us"] = float(np.percentile(lat, 50))
        out["infer_online_p95_us"] = float(np.percentile(lat, 95))
    except Exception:
        pass
    return out


def time_inference_torch(model, sample_batch, n_online=200, repeats=3):
    import torch

    out = {
        "infer_batch_us_per_row": NA,
        "infer_online_p50_us": NA,
        "infer_online_p95_us": NA,
    }
    if model is None or sample_batch is None or len(sample_batch) == 0:
        return out
    was_training = model.training
    model.eval()
    try:
        with torch.no_grad():
            model(sample_batch[:1])
            n = len(sample_batch)
            best = np.inf
            for _ in range(repeats):
                t = time.perf_counter()
                model(sample_batch)
                best = min(best, time.perf_counter() - t)
            out["infer_batch_us_per_row"] = best * 1e6 / n
            k = int(min(n_online, n))
            lat = np.empty(k, dtype=float)
            for i in range(k):
                t = time.perf_counter()
                model(sample_batch[i : i + 1])
                lat[i] = (time.perf_counter() - t) * 1e6
            out["infer_online_p50_us"] = float(np.percentile(lat, 50))
            out["infer_online_p95_us"] = float(np.percentile(lat, 95))
    except Exception:
        pass
    if was_training:
        model.train()
    return out


def evaluate(
    y_true,
    y_pred,
    model_name,
    dataset_name,
    family,
    labels,
    class_names=None,
    y_proba=None,
    y_train=None,
    train_time_sec=None,
    num_epochs=NA,
    parameters="",
    seed=NA,
    n_features=None,
    n_train=None,
    test_set="real_heldout_20pct",
    timing=None,
):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    labels = list(labels)
    k = len(labels)
    if k > MAX_CLASSES:
        raise ValueError(
            "evaluate() got %d labels but the fixed schema has %d per-class slots; "
            "raise MAX_CLASSES in eval_metrics.py and regenerate every results CSV "
            "so the schema stays identical across families." % (k, MAX_CLASSES)
        )
    if class_names is None:
        class_names = [str(c) for c in labels]
    class_names = list(class_names)

    prec, rec, _, sup = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average=None, zero_division=0
    )
    present = [c for c in labels if (y_true == c).any()]
    rec_present = rec[[labels.index(c) for c in present]]
    k_present = len(present)
    test_prior = _prior(y_true, labels)
    pred_prior = _prior(y_pred, labels)
    train_prior = _prior(y_train, labels) if y_train is not None else None
    baseline = float(test_prior.max()) if k else np.nan
    acc = float(accuracy_score(y_true, y_pred))
    worst = labels.index(present[int(np.argmin(rec_present))]) if k_present else 0

    row = {c: NA for c in COLUMNS}
    row.update(
        {
            "model": model_name,
            "dataset": dataset_name,
            "family": family,
            "test_set": test_set,
            "seed": seed,
            "n_classes": k,
            "class_names": ";".join(class_names),
            "n_train": n_train if n_train is not None else NA,
            "n_test": int(len(y_true)),
            "n_features": n_features if n_features is not None else NA,
            "mcc": float(matthews_corrcoef(y_true, y_pred)),
            "balanced_accuracy": float(np.mean(rec_present)) if k_present else np.nan,
            "f1_macro": float(
                f1_score(y_true, y_pred, labels=present, average="macro", zero_division=0)
            ),
            "g_mean": _g_mean(rec_present),
            "precision_macro": float(
                precision_score(y_true, y_pred, labels=present, average="macro", zero_division=0)
            ),
            "recall_macro": float(
                recall_score(y_true, y_pred, labels=present, average="macro", zero_division=0)
            ),
            "accuracy": acc,
            "majority_baseline_accuracy": baseline,
            "accuracy_lift_over_majority": acc - baseline,
            "f1_weighted": float(
                f1_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)
            ),
            "is_degenerate": bool(len(np.unique(y_pred)) < k_present),
            "n_classes_predicted": int(len(np.unique(y_pred))),
            "min_class_recall": float(rec_present.min()) if k_present else NA,
            "worst_class": class_names[worst] if k_present else NA,
            "test_prior": _fmt_prior(test_prior),
            "pred_prior": _fmt_prior(pred_prior),
            "pred_prior_tv": _tv(pred_prior, test_prior),
            "train_time_sec": train_time_sec if train_time_sec is not None else NA,
            "num_epochs": num_epochs,
            "parameters": str(parameters),
        }
    )
    for i in range(MAX_CLASSES):
        if i < k:
            row["recall_c%d" % i] = float(rec[i])
            row["precision_c%d" % i] = float(prec[i])
            row["support_c%d" % i] = int(sup[i])
    if train_prior is not None:
        row["train_prior"] = _fmt_prior(train_prior)
        row["prior_shift_tv"] = _tv(train_prior, test_prior)

    if y_proba is not None:
        P = np.asarray(y_proba, dtype=float)
        if P.ndim == 1:
            P = np.column_stack([1.0 - P, P])
        try:
            row["log_loss"] = float(log_loss(y_true, P, labels=labels))
        except Exception:
            pass
        srt = sorted(labels)
        col_of = {c: srt.index(c) for c in labels}
        try:
            if k == 2:
                pos = labels[1]
                score = P[:, col_of[pos]]
                row["pr_auc_macro"] = float(average_precision_score(y_true == pos, score))
                row["roc_auc_ovr_macro"] = float(roc_auc_score(y_true == pos, score))
            else:
                aps = [
                    average_precision_score(y_true == c, P[:, col_of[c]])
                    for c in labels
                    if (y_true == c).any()
                ]
                row["pr_auc_macro"] = float(np.mean(aps)) if aps else np.nan
                row["roc_auc_ovr_macro"] = float(
                    roc_auc_score(y_true, P, multi_class="ovr", average="macro", labels=srt)
                )
        except Exception:
            pass

    if timing:
        row.update({k2: v for k2, v in timing.items() if k2 in row})
    return row


def _check_header(path):
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            first = f.readline()
    except OSError:
        return True
    if not first.strip():
        return False
    existing = next(csv.reader([first]), [])
    if existing == COLUMNS:
        return True
    raise ValueError(
        "%s has a different schema and would be corrupted by appending.\n"
        "  existing: %d columns, first few %s\n"
        "  expected: %d columns, first few %s\n"
        "Move or delete that file, then re-run so it is written fresh."
        % (path, len(existing), existing[:4], len(COLUMNS), COLUMNS[:4])
    )


def append_row(row, path):
    rows = row if isinstance(row, list) else [row]
    df = pd.DataFrame(rows)
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = NA
    df = df[COLUMNS]
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    has_header = os.path.isfile(path) and _check_header(path)
    df.to_csv(path, mode="a", header=not has_header, index=False)
    return df


def summary(row):
    keys = [
        "mcc",
        "balanced_accuracy",
        "f1_macro",
        "g_mean",
        "accuracy",
        "majority_baseline_accuracy",
        "accuracy_lift_over_majority",
        "is_degenerate",
    ]
    return "  ".join(
        "%s=%s" % (k, ("%.4f" % row[k]) if isinstance(row[k], float) else row[k]) for k in keys
    )
