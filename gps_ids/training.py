import gc
import random
import time
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

import eval_metrics
from . import protocol as _protocol
from . import results as _results

STACK_NAME = "StackingClassifier(LogisticRegression RandomForest SVC)"

MIN_BENIGN_FIT_ROWS = 10


class ExperimentUnusable(ValueError):
    pass

VARIANT_FAMILIES = {
    " (SMOTE)": "SMOTE",
    " (Explainability Features)": "FeatureEngineering",
    " (Xgboost Features)": "FeatureEngineering",
    " (XGBoost Features)": "FeatureEngineering",
}


@dataclass
class Run:
    row: dict
    model: Any
    y_pred: np.ndarray
    y_proba: Optional[np.ndarray]


def _seed(seed, use_torch):
    np.random.seed(seed)
    random.seed(seed)
    if use_torch:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False


def _build_lr(exp, seed, p):
    from sklearn.linear_model import LogisticRegression

    return LogisticRegression(
        random_state=seed, max_iter=p["max_iter"], solver=p["solver"]
    )


def _build_rf(exp, seed, p):
    from sklearn.ensemble import RandomForestClassifier

    return RandomForestClassifier(
        n_estimators=p["n_estimators"], n_jobs=-1, random_state=seed
    )


def _build_xgb(exp, seed, p):
    from xgboost import XGBClassifier

    k = len(exp.class_names)
    if k == 2:
        return XGBClassifier(
            objective="binary:logistic", random_state=seed, eval_metric=p["eval_metric"]
        )
    return XGBClassifier(
        objective="multi:softprob",
        num_class=k,
        eval_metric=p["eval_metric"],
        random_state=seed,
    )


def _build_mlp(exp, seed, p):
    from sklearn.neural_network import MLPClassifier

    return MLPClassifier(
        hidden_layer_sizes=p["hidden_layer_sizes"],
        activation=p["activation"],
        solver=p["solver"],
        random_state=seed,
        learning_rate=p["learning_rate"],
        early_stopping=p["early_stopping"],
    )


def _build_stack(exp, seed, p):
    from sklearn.ensemble import RandomForestClassifier, StackingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC

    base_learners = [
        ("lr", LogisticRegression(random_state=seed, max_iter=p["base_max_iter"], solver="saga")),
        ("rf", RandomForestClassifier(random_state=seed)),
        ("svc", SVC(probability=True, random_state=seed)),
    ]
    meta = LogisticRegression(random_state=seed, max_iter=p["base_max_iter"], solver="saga")
    return StackingClassifier(
        estimators=base_learners, final_estimator=meta, passthrough=False, n_jobs=-1
    )


def _build_ocsvm(exp, seed, p):
    from sklearn.svm import OneClassSVM

    return OneClassSVM(kernel=p["kernel"], gamma=p["gamma"], nu=p["nu"])


def _build_lof(exp, seed, p):
    from sklearn.neighbors import LocalOutlierFactor

    return LocalOutlierFactor(
        n_neighbors=p["n_neighbors"],
        algorithm="auto",
        novelty=True,
        contamination="auto",
    )


SPECS = {
    "Logistic Regression": {
        "kind": "sklearn",
        "build": _build_lr,
        "params": {"max_iter": 2000, "solver": "saga"},
    },
    "Random Forest": {
        "kind": "sklearn",
        "build": _build_rf,
        "params": {"n_estimators": 200},
    },
    "XGBoost": {
        "kind": "sklearn",
        "build": _build_xgb,
        "params": {"eval_metric": "mae"},
    },
    "MLP Classifier": {
        "kind": "sklearn",
        "build": _build_mlp,
        "params": {
            "hidden_layer_sizes": (100, 50, 25),
            "activation": "tanh",
            "solver": "adam",
            "learning_rate": "adaptive",
            "early_stopping": True,
        },
        "report_epochs": True,
    },
    STACK_NAME: {
        "kind": "sklearn",
        "build": _build_stack,
        "params": {"base_max_iter": 1200},
    },
    "OneClassSVM": {
        "kind": "one_class",
        "build": _build_ocsvm,
        "params": {"kernel": "rbf", "gamma": "auto", "nu": 0.04},
    },
    "LocalOutlierFactor": {
        "kind": "one_class",
        "build": _build_lof,
        "params": {"n_neighbors": 60},
    },
    "LSTM Classifier": {
        "kind": "lstm",
        "params": {
            "input_size": 1,
            "hidden_size": 64,
            "num_layers": 2,
            "epochs": 100,
            "batch_size": 64,
            "lr": 0.001,
        },
    },
    "StackedEnsemble_RF": {
        "kind": "stacked",
        "params": {
            "pca_detectors": 0.85,
            "pca_autoencoder": 0.95,
            "ocsvm_nu": 0.011,
            "ocsvm_gamma": 0.000211,
            "lof_neighbors": 1000,
            "ae_hidden_layer_sizes": (3,),
            "ae_activation": "relu",
            "ae_max_iter": 100,
            "threshold_pct": 97.2,
            "meta_features": "auto",
            "smote_meta": False,
            "timing_rows": 2000,
        },
    },
}


def _resolve(model_name):
    if model_name not in _results.MODELS:
        raise ValueError(
            "model %r is not in gps_ids.results.MODELS; known models: %s"
            % (model_name, sorted(_results.MODELS))
        )
    if model_name in SPECS:
        return model_name, ""
    for suffix in VARIANT_FAMILIES:
        if model_name.endswith(suffix):
            base = model_name[: -len(suffix)]
            if base in SPECS:
                return base, suffix
    raise ValueError(
        "no training spec for %r; spec bases: %s" % (model_name, sorted(SPECS))
    )


def _family(model_name, base, suffix, kind, exp):
    if _results.synthetic_info(exp.dataset_name) is not None:
        if kind == "stacked" or base == STACK_NAME:
            return "Synthetic-Stacking"
        if kind == "lstm":
            return "Synthetic-LSTM"
        return "Synthetic"
    if suffix == " (SMOTE)" and kind == "stacked":
        return "SMOTE"
    if suffix in VARIANT_FAMILIES:
        return VARIANT_FAMILIES[suffix]
    if kind == "stacked" or base == STACK_NAME:
        return "Stacking"
    if kind == "lstm":
        return "LSTM"
    if kind == "one_class":
        return "OneClass"
    return "Regular"


def _run_sklearn(exp, spec, params, seed):
    model = spec["build"](exp, seed, params)
    start = time.time()
    model.fit(exp.X_train, exp.y_train)
    train_time = time.time() - start
    y_pred = np.asarray(model.predict(exp.X_test))
    y_proba = (
        model.predict_proba(exp.X_test) if hasattr(model, "predict_proba") else None
    )
    timing = eval_metrics.time_inference(model.predict, exp.X_test)
    num_epochs = (
        int(np.max(model.n_iter_))
        if spec.get("report_epochs") and hasattr(model, "n_iter_")
        else "N/A"
    )
    return {
        "model": model,
        "y_pred": y_pred,
        "y_proba": y_proba,
        "train_time": train_time,
        "timing": timing,
        "num_epochs": num_epochs,
        "parameters": model.get_params(),
        "eval_overrides": {},
    }


def _run_one_class(exp, spec, params, seed):
    model = spec["build"](exp, seed, params)
    start = time.time()
    model.fit(exp.X_train)
    train_time = time.time() - start
    y_pred = (np.asarray(model.predict(exp.X_test)) == -1).astype(int)
    return {
        "model": model,
        "y_pred": y_pred,
        "y_proba": None,
        "train_time": train_time,
        "timing": None,
        "num_epochs": "N/A",
        "parameters": model.get_params(),
        "eval_overrides": {},
    }


def _run_lstm(exp, spec, params, seed):
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset

    class LSTMClassifier(nn.Module):
        def __init__(self, input_size, hidden_size, num_classes, num_layers):
            super().__init__()
            self.lstm = nn.LSTM(
                input_size=input_size,
                hidden_size=hidden_size,
                batch_first=True,
                num_layers=num_layers,
            )
            self.fc = nn.Linear(hidden_size, num_classes)

        def forward(self, x):
            out, _ = self.lstm(x)
            out = out[:, -1, :]
            out = self.fc(out)
            return out

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    X_train = np.asarray(exp.X_train, dtype="float32")
    X_test = np.asarray(exp.X_test, dtype="float32")
    seq_len = X_train.shape[1]
    X_train = X_train.reshape(-1, seq_len, params["input_size"])
    X_test = X_test.reshape(-1, seq_len, params["input_size"])
    y_train = np.asarray(exp.y_train, dtype="int64")
    y_test = np.asarray(exp.y_test, dtype="int64")

    train_loader = DataLoader(
        TensorDataset(torch.tensor(X_train), torch.tensor(y_train)),
        batch_size=params["batch_size"],
        shuffle=True,
    )
    test_loader = DataLoader(
        TensorDataset(torch.tensor(X_test), torch.tensor(y_test)),
        batch_size=params["batch_size"],
    )

    model = LSTMClassifier(
        params["input_size"],
        params["hidden_size"],
        len(exp.class_names),
        params["num_layers"],
    ).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=params["lr"])

    start = time.time()
    for epoch in range(params["epochs"]):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        for X_batch, y_batch in train_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            optimizer.zero_grad()
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * X_batch.size(0)
            _, predicted = torch.max(outputs, 1)
            correct += (predicted == y_batch).sum().item()
            total += y_batch.size(0)
        if (epoch + 1) % 10 == 0 or epoch == 0 or epoch == params["epochs"] - 1:
            print(
                "Epoch %d/%d, Loss: %.4f, Accuracy: %.4f"
                % (
                    epoch + 1,
                    params["epochs"],
                    running_loss / len(train_loader.dataset),
                    correct / total,
                )
            )
    train_time = time.time() - start

    model.eval()
    all_preds, all_probs = [], []
    with torch.no_grad():
        for X_batch, _ in test_loader:
            outputs = model(X_batch.to(device))
            _, preds = torch.max(outputs, 1)
            all_probs.extend(torch.softmax(outputs, dim=1).cpu().numpy())
            all_preds.extend(preds.cpu().numpy())

    timing = eval_metrics.time_inference_torch(
        model, next(iter(test_loader))[0].to(device)
    )
    return {
        "model": model,
        "y_pred": np.asarray(all_preds),
        "y_proba": np.asarray(all_probs),
        "train_time": train_time,
        "timing": timing,
        "num_epochs": params["epochs"],
        "parameters": list(dict(model.named_parameters()).keys()),
        "eval_overrides": {},
    }


class StackedDetector:
    def __init__(self, scaler, pca_detectors, pca_autoencoder, ocsvm, lof, ae, threshold, mode, meta):
        self._scaler = scaler
        self._pca_detectors = pca_detectors
        self._pca_autoencoder = pca_autoencoder
        self._ocsvm = ocsvm
        self._lof = lof
        self._ae = ae
        self._threshold = threshold
        self._mode = mode
        self._meta = meta

    def meta_features(self, X_detectors, X_autoencoder):
        recon = self._ae.predict(X_autoencoder)
        error = np.mean((X_autoencoder - recon) ** 2, axis=1)
        if self._mode == "binary":
            return np.vstack(
                [
                    np.where(self._ocsvm.predict(X_detectors) == -1, 1, 0),
                    np.where(self._lof.predict(X_detectors) == -1, 1, 0),
                    np.where(error > self._threshold, 1, 0),
                ]
            ).T
        return np.vstack(
            [
                self._ocsvm.decision_function(X_detectors),
                self._lof.decision_function(X_detectors),
                error,
            ]
        ).T

    def transform_scaled(self, X_scaled):
        return self.meta_features(
            self._pca_detectors.transform(X_scaled),
            self._pca_autoencoder.transform(X_scaled),
        )

    def predict_scaled(self, X_scaled):
        return self._meta.predict(self.transform_scaled(np.asarray(X_scaled)))

    def predict_raw(self, X_raw):
        return self.predict_scaled(self._scaler.transform(X_raw))


def _run_stacked(exp, spec, params, seed, smote_meta):
    from sklearn.decomposition import PCA
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.neighbors import LocalOutlierFactor
    from sklearn.neural_network import MLPRegressor
    from sklearn.svm import OneClassSVM

    X_fit = np.asarray(exp.X_fit)
    X_train = np.asarray(exp.X_train)
    X_test = np.asarray(exp.X_test)

    start = time.time()
    pca_detectors = PCA(n_components=params["pca_detectors"], random_state=seed).fit(X_fit)
    pca_autoencoder = PCA(n_components=params["pca_autoencoder"], random_state=seed).fit(X_fit)
    fit_detectors = pca_detectors.transform(X_fit)
    fit_autoencoder = pca_autoencoder.transform(X_fit)

    ocsvm = OneClassSVM(nu=params["ocsvm_nu"], gamma=params["ocsvm_gamma"]).fit(fit_detectors)
    lof = LocalOutlierFactor(n_neighbors=params["lof_neighbors"], novelty=True).fit(fit_detectors)
    ae = MLPRegressor(
        hidden_layer_sizes=params["ae_hidden_layer_sizes"],
        activation=params["ae_activation"],
        max_iter=params["ae_max_iter"],
        random_state=seed,
    ).fit(fit_autoencoder, fit_autoencoder)

    mode = params["meta_features"]
    if mode == "auto":
        mode = "binary" if len(exp.class_names) == 2 else "scores"
    threshold = None
    if mode == "binary":
        fit_error = np.mean((fit_autoencoder - ae.predict(fit_autoencoder)) ** 2, axis=1)
        threshold = np.percentile(fit_error, params["threshold_pct"])

    detector = StackedDetector(
        exp.scaler, pca_detectors, pca_autoencoder, ocsvm, lof, ae, threshold, mode, None
    )
    meta_train = detector.transform_scaled(X_train)
    base_time = time.time() - start

    meta_test = detector.transform_scaled(X_test)
    y_meta = np.asarray(exp.y_train)

    start_meta = time.time()
    if smote_meta:
        from imblearn.over_sampling import SMOTE

        unique, counts = np.unique(y_meta, return_counts=True)
        majority = unique[np.argmax(counts)]
        strategy = {cls: int(counts.max()) for cls in unique if cls != majority}
        smote = SMOTE(random_state=seed, sampling_strategy=strategy)
        meta_train, y_meta = smote.fit_resample(meta_train, y_meta)
        y_meta = np.asarray(y_meta)
    meta = RandomForestClassifier(random_state=seed).fit(meta_train, y_meta)
    train_time = base_time + (time.time() - start_meta)

    detector._meta = meta
    y_pred = meta.predict(meta_test)
    y_proba = meta.predict_proba(meta_test)
    timing = eval_metrics.time_inference(
        detector.predict_raw, exp.X_test_raw[: params["timing_rows"]]
    )
    return {
        "model": detector,
        "y_pred": np.asarray(y_pred),
        "y_proba": y_proba,
        "train_time": train_time,
        "timing": timing,
        "num_epochs": "N/A",
        "parameters": meta.get_params(),
        "eval_overrides": {"y_train": y_meta, "n_train": len(y_meta)},
    }


def run(model_name, exp, *, overrides=None, append=None, results_csv=None, quiet=False):
    base, suffix = _resolve(model_name)
    spec = SPECS[base]
    kind = spec["kind"]
    params = dict(spec["params"])
    if overrides:
        unknown = sorted(set(overrides) - set(params))
        if unknown:
            raise ValueError(
                "unknown override(s) %s for %r; valid keys: %s"
                % (unknown, base, sorted(params))
            )
        params.update(overrides)
    if append is None:
        append = not overrides
    if overrides and append and results_csv is None:
        raise ValueError(
            "an overridden run cannot append to the canonical results CSV; "
            "pass results_csv= to record it elsewhere, or change the spec in "
            "gps_ids/training.py"
        )

    if kind == "stacked":
        if exp.X_fit is None or exp.X_test_raw is None:
            raise ValueError(
                "the stacked detector needs an ensemble protocol "
                "(protocol.ensemble_heldout or protocol.synthetic_ensemble_vs_full_real)"
            )
        if len(exp.X_fit) < MIN_BENIGN_FIT_ROWS:
            raise ExperimentUnusable(
                "only %d benign rows to fit the stacked detector on (minimum %d)"
                % (len(exp.X_fit), MIN_BENIGN_FIT_ROWS)
            )
    smote_meta = params.pop("smote_meta") if kind == "stacked" else False
    if suffix == " (SMOTE)":
        if kind == "stacked":
            smote_meta = True
        else:
            counts = np.bincount(np.asarray(exp.y_train))
            counts = counts[counts > 0]
            if counts.min() != counts.max():
                raise ValueError(
                    "%r expects a SMOTE-balanced training set; build the "
                    "experiment with protocol.smote_heldout" % model_name
                )

    family = _family(model_name, base, suffix, kind, exp)
    _results.validate_row(
        {
            "model": model_name,
            "dataset": exp.dataset_name,
            "family": family,
            "test_set": exp.test_set,
        }
    )

    _seed(exp.seed, use_torch=(kind == "lstm"))

    if kind == "sklearn":
        out = _run_sklearn(exp, spec, params, exp.seed)
    elif kind == "one_class":
        out = _run_one_class(exp, spec, params, exp.seed)
    elif kind == "lstm":
        out = _run_lstm(exp, spec, params, exp.seed)
    elif kind == "stacked":
        out = _run_stacked(exp, spec, params, exp.seed, smote_meta)
    else:
        raise ValueError("unknown spec kind %r" % kind)

    parameters = out["parameters"]
    if overrides:
        parameters = "%s | overrides=%r" % (parameters, dict(overrides))

    kwargs = exp.eval_kwargs()
    kwargs.update(out["eval_overrides"])
    row = eval_metrics.evaluate(
        exp.y_test,
        out["y_pred"],
        model_name=model_name,
        family=family,
        y_proba=out["y_proba"],
        train_time_sec=out["train_time"],
        num_epochs=out["num_epochs"],
        parameters=parameters,
        timing=out["timing"],
        **kwargs,
    )
    if append:
        path = results_csv or exp.results_csv
        _results.append_validated(row, path)
        if not quiet:
            print(eval_metrics.summary(row))
            print("Results appended to %s" % path)
    elif not quiet:
        print(eval_metrics.summary(row))
    return Run(row=row, model=out["model"], y_pred=out["y_pred"], y_proba=out["y_proba"])


def run_synthetic(
    models,
    dataset,
    *,
    protocol_fn=None,
    files=None,
    generators=None,
    results_csv=None,
    quiet=False,
):
    if isinstance(models, str):
        models = [models]
    if protocol_fn is None:
        protocol_fn = _protocol.synthetic_vs_full_real
    if files is None:
        files = _results.synthetic_files(dataset, generators=generators)
    rows = []
    for synth_file in files:
        try:
            exp = protocol_fn(dataset, synth_file)
        except FileNotFoundError:
            print("Skipping %s: file not found" % synth_file)
            continue
        print("Training on synthetic: %s" % synth_file)
        for model_name in models:
            try:
                result = run(model_name, exp, results_csv=results_csv, quiet=quiet)
            except ExperimentUnusable as error:
                print("Skipping %s: %s" % (synth_file, error))
                break
            rows.append(result.row)
        del exp
        gc.collect()
    return rows
