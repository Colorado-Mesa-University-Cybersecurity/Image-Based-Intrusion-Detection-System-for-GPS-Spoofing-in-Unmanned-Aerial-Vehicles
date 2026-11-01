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

SEEDS = (1082, 7, 42, 2024, 31337)

MIN_BENIGN_FIT_ROWS = 10


class ExperimentUnusable(ValueError):
    pass


def _balanced_sample_weight(exp):
    from sklearn.utils.class_weight import compute_sample_weight

    return compute_sample_weight("balanced", np.asarray(exp.y_train))


def _ce_class_weight(exp, device):
    import torch
    from sklearn.utils.class_weight import compute_class_weight

    y = np.asarray(exp.y_train)
    present = np.unique(y)
    weights = np.ones(len(exp.class_names), dtype=np.float32)
    weights[present] = compute_class_weight("balanced", classes=present, y=y)
    return torch.tensor(weights, dtype=torch.float32, device=device)

VARIANT_FAMILIES = {
    " (SMOTE)": "SMOTE",
    " (Explainability Features)": "FeatureEngineering",
    " (Xgboost Features)": "FeatureEngineering",
    " (XGBoost Features)": "FeatureEngineering",
    " (Quadratic Features)": "FeatureEngineering",
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
        random_state=seed,
        max_iter=p["max_iter"],
        solver=p["solver"],
        class_weight=p["class_weight"],
    )


def _build_rf(exp, seed, p):
    from sklearn.ensemble import RandomForestClassifier

    return RandomForestClassifier(
        n_estimators=p["n_estimators"],
        max_features=p["max_features"],
        class_weight=p["class_weight"],
        n_jobs=-1,
        random_state=seed,
    )


def _rf_params():
    return SPECS["Random Forest"]["params"]


def _lr_solver():
    return SPECS["Logistic Regression"]["params"]["solver"]


def _build_lr_quad(exp, seed, p):
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import PolynomialFeatures

    lr = SPECS["Logistic Regression"]["params"]
    return make_pipeline(
        PolynomialFeatures(degree=p["degree"], include_bias=False),
        LogisticRegression(
            random_state=seed,
            max_iter=lr["max_iter"],
            solver=lr["solver"],
            class_weight=p["class_weight"],
        ),
    )


def _build_xgb(exp, seed, p):
    from xgboost import XGBClassifier

    k = len(exp.class_names)
    if k == 2:
        return XGBClassifier(objective="binary:logistic", random_state=seed)
    return XGBClassifier(
        objective="multi:softprob",
        num_class=k,
        random_state=seed,
    )


def _build_mlp(exp, seed, p):
    from sklearn.neural_network import MLPClassifier

    return MLPClassifier(
        hidden_layer_sizes=p["hidden_layer_sizes"],
        activation=p["activation"],
        solver=p["solver"],
        random_state=seed,
        early_stopping=p["early_stopping"],
    )


def _build_stack(exp, seed, p):
    from sklearn.ensemble import RandomForestClassifier, StackingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC

    base_learners = [
        (
            "lr",
            LogisticRegression(
                random_state=seed,
                max_iter=p["base_max_iter"],
                solver=_lr_solver(),
                class_weight=p["class_weight"],
            ),
        ),
        ("rf", RandomForestClassifier(random_state=seed, **_rf_params())),
        ("svc", SVC(probability=False, random_state=seed, class_weight=p["class_weight"])),
    ]
    meta = LogisticRegression(
        random_state=seed,
        max_iter=p["base_max_iter"],
        solver=_lr_solver(),
        class_weight=p["class_weight"],
    )
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
        "params": {"max_iter": 2000, "solver": "lbfgs", "class_weight": "balanced"},
    },
    "Logistic Regression (Quadratic Features)": {
        "kind": "sklearn",
        "build": _build_lr_quad,
        "params": {"degree": 2, "class_weight": "balanced"},
    },
    "Random Forest": {
        "kind": "sklearn",
        "build": _build_rf,
        "params": {
            "n_estimators": 200,
            "max_features": None,
            "class_weight": "balanced",
        },
    },
    "XGBoost": {
        "kind": "sklearn",
        "build": _build_xgb,
        "params": {},
        "balanced_sample_weight": True,
    },
    "MLP Classifier": {
        "kind": "sklearn",
        "build": _build_mlp,
        "params": {
            "hidden_layer_sizes": (100, 50, 25),
            "activation": "relu",
            "solver": "adam",
            "early_stopping": True,
        },
        "report_epochs": True,
    },
    STACK_NAME: {
        "kind": "sklearn",
        "build": _build_stack,
        "params": {"base_max_iter": 1200, "class_weight": "balanced"},
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
    "CNN": {
        "kind": "image",
        "arch": "cnn",
        "params": {
            "epochs": 100,
            "batch_size": 100,
            "lr": 0.001,
            "momentum": 0.9,
            "checkpoint": "cnn",
        },
    },
    "CNN-LSTM": {
        "kind": "image",
        "arch": "cnn_lstm",
        "params": {
            "epochs": 100,
            "batch_size": 32,
            "lr": 0.001,
            "momentum": 0.9,
            "checkpoint": "cnn_lstm",
        },
    },
    "ResNet-CNN": {
        "kind": "image",
        "arch": "resnet",
        "params": {
            "epochs": 20,
            "batch_size": 32,
            "lr": 0.001,
            "momentum": 0.9,
            "checkpoint": "resnet",
        },
    },
    "ResNet-LSTM": {
        "kind": "image",
        "arch": "resnet_lstm",
        "params": {
            "epochs": 100,
            "batch_size": 32,
            "lr": 0.001,
            "momentum": 0.9,
            "checkpoint": "resnet_lstm",
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
            "ae_learning_rate": "constant",
            "ae_early_stopping": False,
            "threshold_pct": 97.2,
            "meta_features": "auto",
            "smote_meta": False,
            "timing_rows": 2000,
        },
        "synthetic_params": {
            "meta_features": "scores",
            "ae_hidden_layer_sizes": (100, 50),
            "ae_activation": "tanh",
            "ae_max_iter": 1000,
            "ae_learning_rate": "adaptive",
            "ae_early_stopping": True,
        },
    },
}


def image_batch_size(model_name):
    base, _ = _resolve(model_name)
    spec = SPECS[base]
    if spec["kind"] != "image":
        raise ValueError("%r is not an image model" % model_name)
    return spec["params"]["batch_size"]


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
    if suffix in VARIANT_FAMILIES:
        return VARIANT_FAMILIES[suffix]
    for known_suffix, family in VARIANT_FAMILIES.items():
        if model_name.endswith(known_suffix):
            return family
    if kind == "stacked" or base == STACK_NAME:
        return "Stacking"
    if kind == "image":
        return "Image"
    if kind == "lstm":
        return "LSTM"
    if kind == "one_class":
        return "OneClass"
    return "Regular"


def _run_sklearn(exp, spec, params, seed):
    model = spec["build"](exp, seed, params)
    fit_kwargs = {}
    if spec.get("balanced_sample_weight"):
        fit_kwargs["sample_weight"] = _balanced_sample_weight(exp)
    start = time.perf_counter()
    model.fit(exp.X_train, exp.y_train, **fit_kwargs)
    train_time = time.perf_counter() - start
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
    recorded = dict(model.get_params())
    if fit_kwargs:
        recorded["sample_weight"] = "balanced"
    return {
        "model": model,
        "y_pred": y_pred,
        "y_proba": y_proba,
        "train_time": train_time,
        "timing": timing,
        "num_epochs": num_epochs,
        "parameters": recorded,
        "eval_overrides": {},
    }


def _run_one_class(exp, spec, params, seed):
    model = spec["build"](exp, seed, params)
    start = time.perf_counter()
    model.fit(exp.X_train)
    train_time = time.perf_counter() - start
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
    import copy

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
            out = torch.tanh(out)
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

    from sklearn.model_selection import train_test_split

    fit_idx, val_idx = train_test_split(
        np.arange(len(X_train)),
        train_size=_protocol.TRAIN_SIZE,
        random_state=seed,
        stratify=y_train,
    )
    train_loader = DataLoader(
        TensorDataset(torch.tensor(X_train[fit_idx]), torch.tensor(y_train[fit_idx])),
        batch_size=params["batch_size"],
        shuffle=True,
    )
    val_loader = DataLoader(
        TensorDataset(torch.tensor(X_train[val_idx]), torch.tensor(y_train[val_idx])),
        batch_size=params["batch_size"],
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
    criterion = nn.CrossEntropyLoss(weight=_ce_class_weight(exp, device))
    optimizer = optim.Adam(model.parameters(), lr=params["lr"])

    best_wts = copy.deepcopy(model.state_dict())
    best_acc = -1.0
    best_epoch = 0

    start = time.perf_counter()
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
        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                outputs = model(X_batch.to(device))
                _, preds = torch.max(outputs, 1)
                val_correct += (preds.cpu() == y_batch).sum().item()
                val_total += y_batch.size(0)
        val_acc = val_correct / val_total
        if val_acc > best_acc:
            best_acc = val_acc
            best_epoch = epoch + 1
            best_wts = copy.deepcopy(model.state_dict())

        if (epoch + 1) % 10 == 0 or epoch == 0 or epoch == params["epochs"] - 1:
            print(
                "Epoch %d/%d, Loss: %.4f, Accuracy: %.4f, Val Acc: %.4f"
                % (
                    epoch + 1,
                    params["epochs"],
                    running_loss / len(train_loader.dataset),
                    correct / total,
                    val_acc,
                )
            )

    model.load_state_dict(best_wts)
    train_time = time.perf_counter() - start

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
        "num_epochs": best_epoch,
        "parameters": list(dict(model.named_parameters()).keys()),
        "eval_overrides": {},
    }


def _image_model(arch, num_classes, image_shape):
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    def conv_module(in_features, out_features):
        return nn.Sequential(
            nn.Conv2d(in_channels=in_features, out_channels=out_features, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_features),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
        )

    if arch == "cnn":

        class CNN(nn.Module):
            def __init__(self):
                super().__init__()
                self.layer1 = conv_module(1, 64)
                self.layer2 = conv_module(64, 128)
                self.layer3 = conv_module(128, 256)
                self.layer4 = conv_module(256, 512)
                self.gap = nn.AdaptiveAvgPool2d((2, 2))
                self.classifier = nn.Sequential(
                    nn.Flatten(),
                    nn.Linear(2 * 2 * 512, 1024),
                    nn.ReLU(),
                    nn.Linear(1024, 512),
                    nn.ReLU(),
                    nn.Linear(512, num_classes),
                )

            def forward(self, x):
                x = self.layer1(x)
                x = self.layer2(x)
                x = self.layer3(x)
                x = self.layer4(x)
                x = self.gap(x)
                return self.classifier(x)

        return CNN()

    if arch == "cnn_lstm":

        class CNNLSTM(nn.Module):
            def __init__(self, hidden_dim=128, lstm_layers=1):
                super().__init__()
                self.layer1 = conv_module(1, 64)
                self.layer2 = conv_module(64, 128)
                self.layer3 = conv_module(128, 256)
                self.layer4 = conv_module(256, 512)
                self.gap = nn.AdaptiveAvgPool2d((2, 2))
                self.lstm = nn.LSTM(
                    input_size=512 * 2,
                    hidden_size=hidden_dim,
                    num_layers=lstm_layers,
                    batch_first=True,
                )
                self.classifier = nn.Sequential(
                    nn.Linear(hidden_dim, 512),
                    nn.ReLU(),
                    nn.Linear(512, num_classes),
                )

            def forward(self, x):
                batch = x.size(0)
                x = self.layer1(x)
                x = self.layer2(x)
                x = self.layer3(x)
                x = self.layer4(x)
                x = self.gap(x)
                x = x.permute(0, 2, 1, 3)
                x = x.contiguous().view(batch, 2, -1)
                lstm_out, _ = self.lstm(x)
                return self.classifier(lstm_out[:, -1, :])

        return CNNLSTM()

    from torchvision.models import resnet101

    if arch == "resnet":

        class ResNetCNN(nn.Module):
            def __init__(self, feature_dim=300):
                super().__init__()
                self.resnet = resnet101(pretrained=True)
                self.resnet.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
                self.resnet.fc = nn.Linear(self.resnet.fc.in_features, feature_dim)
                self.fc1 = nn.Linear(feature_dim, 128)
                self.fc2 = nn.Linear(128, num_classes)

            def forward(self, x):
                features = self.resnet(x)
                x = F.relu(self.fc1(features))
                return self.fc2(x)

        return ResNetCNN()

    if arch == "resnet_lstm":

        class ResNetLSTM(nn.Module):
            def __init__(self, lstm_hidden=128, lstm_layers=1):
                super().__init__()
                resnet = resnet101(pretrained=True)
                resnet.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
                self.features = nn.Sequential(
                    resnet.conv1,
                    resnet.bn1,
                    resnet.relu,
                    resnet.maxpool,
                    resnet.layer1,
                    resnet.layer2,
                    resnet.layer3,
                    resnet.layer4,
                )
                with torch.no_grad():
                    dummy = torch.zeros(1, 1, *image_shape)
                    dummy_feats = self.features(dummy)
                _, C, _, W = dummy_feats.shape
                self.lstm = nn.LSTM(
                    input_size=W * C,
                    hidden_size=lstm_hidden,
                    num_layers=lstm_layers,
                    batch_first=True,
                )
                self.classifier = nn.Sequential(
                    nn.Linear(lstm_hidden, 128),
                    nn.ReLU(),
                    nn.Linear(128, num_classes),
                )

            def forward(self, x):
                feats = self.features(x)
                feats = feats.permute(0, 2, 1, 3)
                feats = feats.contiguous().view(x.size(0), feats.size(1), -1)
                _, (h_n, _) = self.lstm(feats)
                return self.classifier(h_n[-1])

        return ResNetLSTM()

    raise ValueError("unknown image architecture %r" % arch)


def _run_image(exp, spec, params, seed):
    import copy

    import torch
    import torch.nn as nn
    import torch.optim as optim
    from sklearn.metrics import accuracy_score

    from . import images as _images

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    epochs = params["epochs"]
    dataloaders = exp.dataloaders

    model = _image_model(
        spec["arch"], len(exp.class_names), _images.image_shape(exp.config)
    ).to(device)
    criterion = nn.CrossEntropyLoss(weight=_ce_class_weight(exp, device))
    optimizer = optim.SGD(model.parameters(), lr=params["lr"], momentum=params["momentum"])

    best_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0
    best_epoch = 0
    start = time.perf_counter()
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        train_preds, train_labels = [], []
        for inputs, labels in dataloaders["train"]:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            train_preds.append(preds.cpu().numpy())
            train_labels.append(labels.cpu().numpy())
        train_acc = accuracy_score(
            np.concatenate(train_labels), np.concatenate(train_preds)
        )

        model.eval()
        val_preds, val_labels = [], []
        with torch.no_grad():
            for inputs, labels in dataloaders["val"]:
                outputs = model(inputs.to(device))
                _, preds = torch.max(outputs, 1)
                val_preds.append(preds.cpu().numpy())
                val_labels.append(labels.numpy())
        val_acc = accuracy_score(np.concatenate(val_labels), np.concatenate(val_preds))
        print(
            "Epoch %d/%d - Train Loss: %.4f - Train Acc: %.4f - Val Acc: %.4f"
            % (
                epoch + 1,
                epochs,
                running_loss / len(dataloaders["train"].dataset),
                train_acc,
                val_acc,
            )
        )
        if val_acc > best_acc:
            best_acc = val_acc
            best_epoch = epoch + 1
            best_wts = copy.deepcopy(model.state_dict())
    train_time = time.perf_counter() - start
    model.load_state_dict(best_wts)

    model.eval()
    all_preds, all_probs, all_labels = [], [], []
    with torch.no_grad():
        for inputs, labels in dataloaders["test"]:
            outputs = model(inputs.to(device))
            _, preds = torch.max(outputs, 1)
            all_probs.extend(torch.softmax(outputs, dim=1).cpu().numpy())
            all_preds.append(preds.cpu().numpy())
            all_labels.append(labels.numpy())

    checkpoint_path = _images.checkpoint_path(exp.config, params["checkpoint"])
    torch.save(
        {
            "epoch": best_epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
        },
        str(checkpoint_path),
    )
    print("Model saved to %s" % checkpoint_path)

    timing = eval_metrics.time_inference_torch(
        model, next(iter(dataloaders["val"]))[0].to(device)
    )
    return {
        "model": model,
        "y_pred": np.concatenate(all_preds),
        "y_proba": np.asarray(all_probs),
        "y_true": np.concatenate(all_labels),
        "train_time": train_time,
        "timing": timing,
        "num_epochs": best_epoch,
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

    start = time.perf_counter()
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
        learning_rate=params["ae_learning_rate"],
        early_stopping=params["ae_early_stopping"],
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
    base_time = time.perf_counter() - start

    meta_test = detector.transform_scaled(X_test)
    y_meta = np.asarray(exp.y_train)

    start_meta = time.perf_counter()
    if smote_meta:
        from imblearn.over_sampling import SMOTE

        unique, counts = np.unique(y_meta, return_counts=True)
        majority = unique[np.argmax(counts)]
        strategy = {cls: int(counts.max()) for cls in unique if cls != majority}
        smote = SMOTE(random_state=seed, sampling_strategy=strategy)
        meta_train, y_meta = smote.fit_resample(meta_train, y_meta)
        y_meta = np.asarray(y_meta)
    meta = RandomForestClassifier(random_state=seed, **_rf_params()).fit(meta_train, y_meta)
    train_time = base_time + (time.perf_counter() - start_meta)

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
    if kind == "stacked" and _results.synthetic_info(exp.dataset_name) is not None:
        params.update(spec.get("synthetic_params", {}))
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
    if overrides and append:
        from pathlib import Path

        canonical = results_csv is None or (
            Path(results_csv).resolve() == Path(exp.results_csv).resolve()
        )
        if canonical:
            raise ValueError(
                "an overridden run cannot append to the canonical results CSV; "
                "pass a different results_csv= to record it elsewhere, or change "
                "the spec in gps_ids/training.py"
            )

    if kind == "image" and not hasattr(exp, "dataloaders"):
        raise ValueError(
            "the image models need an ImageExperiment; build it with "
            "gps_ids.images.loaders(config, batch_size=...)"
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

    _seed(exp.seed, use_torch=(kind in ("lstm", "image")))

    if kind == "sklearn":
        out = _run_sklearn(exp, spec, params, exp.seed)
    elif kind == "one_class":
        out = _run_one_class(exp, spec, params, exp.seed)
    elif kind == "lstm":
        out = _run_lstm(exp, spec, params, exp.seed)
    elif kind == "stacked":
        out = _run_stacked(exp, spec, params, exp.seed, smote_meta)
    elif kind == "image":
        out = _run_image(exp, spec, params, exp.seed)
    else:
        raise ValueError("unknown spec kind %r" % kind)

    parameters = out["parameters"]
    if overrides:
        parameters = "%s | overrides=%r" % (parameters, dict(overrides))

    y_true = out.get("y_true")
    if y_true is None:
        y_true = exp.y_test
    kwargs = exp.eval_kwargs()
    kwargs.update(out["eval_overrides"])
    row = eval_metrics.evaluate(
        y_true,
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


def run_seeds(
    models,
    build_exp,
    seeds=None,
    *,
    overrides=None,
    results_csv=None,
    quiet=False,
    append=None,
):
    if isinstance(models, str):
        models = [models]
    seeds = SEEDS if seeds is None else tuple(seeds)
    rows = []
    for seed in seeds:
        exp = build_exp(seed)
        if int(getattr(exp, "seed", seed)) != int(seed):
            raise ValueError(
                "build_exp(%r) returned an experiment with seed %r; the callable "
                "must pass the seed through to the protocol builder"
                % (seed, getattr(exp, "seed", None))
            )
        for model_name in models:
            try:
                result = run(
                    model_name,
                    exp,
                    overrides=overrides,
                    append=append,
                    results_csv=results_csv,
                    quiet=quiet,
                )
            except ExperimentUnusable as error:
                print("Skipping %s at seed %s: %s" % (model_name, seed, error))
                continue
            rows.append(result.row)
        del exp
        gc.collect()
    return rows


def run_synthetic(
    models,
    dataset,
    *,
    protocol_fn=None,
    files=None,
    generators=None,
    results_csv=None,
    quiet=False,
    seeds=None,
):
    if isinstance(models, str):
        models = [models]
    if protocol_fn is None:
        protocol_fn = _protocol.synthetic_vs_full_real
    if files is None:
        files = _results.synthetic_files(dataset, generators=generators)
    seeds = (None,) if seeds is None else tuple(seeds)
    rows = []
    for synth_file in files:
        for seed in seeds:
            try:
                exp = (
                    protocol_fn(dataset, synth_file)
                    if seed is None
                    else protocol_fn(dataset, synth_file, seed=seed)
                )
            except FileNotFoundError:
                print("Skipping %s: file not found" % synth_file)
                break
            print(
                "Training on synthetic: %s%s"
                % (synth_file, "" if seed is None else " (seed %s)" % seed)
            )
            unusable = False
            for model_name in models:
                try:
                    result = run(model_name, exp, results_csv=results_csv, quiet=quiet)
                except ExperimentUnusable as error:
                    print("Skipping %s: %s" % (synth_file, error))
                    unusable = True
                    break
                rows.append(result.row)
            del exp
            gc.collect()
            if unusable:
                break
    return rows
