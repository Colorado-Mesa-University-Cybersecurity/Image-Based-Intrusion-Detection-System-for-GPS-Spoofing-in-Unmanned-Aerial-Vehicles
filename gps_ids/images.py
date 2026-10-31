import json
import math
import os
import random
import shutil
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import schema as _schema
from .paths import repo_root

RANDOM_STATE = 1082
TRAIN_FRACTION = 0.8
TEST_RATIO = 0.2
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")


@dataclass(frozen=True)
class ImageDataset:
    key: str
    schema_key: str
    folder: str
    class_folders: tuple
    split_style: str
    precision: int = 64
    one: int = 128
    zero: int = 0


UAV_IMAGES = ImageDataset(
    key="uav",
    schema_key="uav",
    folder="binaryImageTransformation/UAVATTACK tubular data",
    class_folders=("benign", "malicious"),
    split_style="train_sample",
)

TWO_D_IMAGES = ImageDataset(
    key="2d",
    schema_key="2d",
    folder="binaryImageTransformation/2d tubular data",
    class_folders=("0", "1", "2", "3"),
    split_style="pool_shuffle",
)

CONFIGS = {c.key: c for c in (UAV_IMAGES, TWO_D_IMAGES)}


def get(key):
    if isinstance(key, ImageDataset):
        return key
    if key not in CONFIGS:
        raise KeyError("unknown image dataset %r; known: %s" % (key, sorted(CONFIGS)))
    return CONFIGS[key]


def image_root(config) -> Path:
    config = get(config)
    return repo_root() / config.folder / "image-results-spoofing"


def data_dir(config) -> Path:
    return image_root(config) / "data"


def train_dir(config) -> Path:
    return data_dir(config) / "Train"


def test_dir(config) -> Path:
    return data_dir(config) / "Test"


def manifest_path(config) -> Path:
    return data_dir(config) / "split_manifest.json"


def checkpoint_path(config, model_key) -> Path:
    config = get(config)
    return repo_root() / config.folder / ("best_%s_model.pth" % model_key)


def image_shape(config):
    config = get(config)
    n_features = len(_schema.feature_columns(config.schema_key))
    return (max(n_features, config.precision), config.precision)


def canonical_class_names(config, folder_names):
    config = get(config)
    schema = _schema.get(config.schema_key)
    index = {name: i for i, name in enumerate(config.class_folders)}
    unknown = [f for f in folder_names if f not in index]
    if unknown:
        raise ValueError(
            "image folders %s are not class folders %s"
            % (unknown, list(config.class_folders))
        )
    return [schema.class_names[index[f]] for f in folder_names]


def _feature_kinds(X):
    kinds = []
    for dtype in X.dtypes:
        if dtype.kind == "f":
            kinds.append("f")
        elif dtype.kind in ("i", "u"):
            kinds.append("i")
        elif dtype.kind == "b":
            kinds.append("b")
        else:
            raise ValueError("unsupported feature dtype %s" % dtype)
    return kinds


def _render_row(values, kinds, name, directory, precision, one, zero):
    import bitstring
    from PIL import Image

    rows = []
    for value, kind in zip(values, kinds):
        if kind == "f":
            bits = bitstring.BitArray(float=float(value), length=precision).bin
            row = [one if b == "1" else zero for b in bits]
        elif kind == "i":
            bits = bitstring.BitArray(int=int(value), length=precision).bin
            row = [one if b == "1" else zero for b in bits]
        else:
            row = [one] * precision if value else [zero] * precision
        rows.append(row)
    n_rows = max(len(rows), precision)
    for _ in range(n_rows - len(rows)):
        rows.append([zero] * precision)
    image = Image.new("L", (precision, len(rows)))
    image.putdata([v for row in rows for v in row])
    image.save(os.path.join(directory, name + ".png"))


def render(config, n_jobs=-1):
    from joblib import Parallel, delayed

    config = get(config)
    X, y = _schema.load_real(config.schema_key)
    kinds = _feature_kinds(X)
    out = image_root(config)
    out.mkdir(parents=True, exist_ok=True)
    counters = {}
    names = []
    for label in y:
        folder = config.class_folders[int(label)]
        counters[folder] = counters.get(folder, 0) + 1
        names.append("%s-%d" % (folder, counters[folder]))
    Parallel(n_jobs=n_jobs)(
        delayed(_render_row)(
            row, kinds, name, str(out), config.precision, config.one, config.zero
        )
        for row, name in zip(X.to_numpy(), names)
    )
    organize(config)
    return out


def organize(config):
    config = get(config)
    root = image_root(config)
    moved = 0
    for cls in config.class_folders:
        (train_dir(config) / cls).mkdir(parents=True, exist_ok=True)
    for entry in os.listdir(root):
        src = root / entry
        if not src.is_file() or not entry.lower().endswith(IMAGE_EXTENSIONS):
            continue
        cls = entry.split("-")[0]
        if cls not in config.class_folders:
            continue
        shutil.move(str(src), str(train_dir(config) / cls / entry))
        moved += 1
    return moved


def _list_images(directory):
    if not os.path.isdir(directory):
        return []
    return sorted(
        f
        for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f))
        and f.lower().endswith(IMAGE_EXTENSIONS)
    )


def _read_manifest(config):
    path = manifest_path(config)
    with open(path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    for cls, entry in manifest.get("classes", {}).items():
        if "train" not in entry:
            entry["train"] = _list_images(train_dir(config) / cls)
    return manifest


def _write_manifest(config, manifest):
    manifest_path(config).parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path(config), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)


def _adopted_manifest(config):
    manifest = {
        "random_state": None,
        "train_fraction": None,
        "adopted_pre_split": True,
        "classes": {},
    }
    for cls in config.class_folders:
        manifest["classes"][cls] = {
            "train": _list_images(train_dir(config) / cls),
            "test": _list_images(test_dir(config) / cls),
        }
    return manifest


def split(config):
    config = get(config)
    if manifest_path(config).is_file():
        return _read_manifest(config)

    test_counts = {
        cls: len(_list_images(test_dir(config) / cls)) for cls in config.class_folders
    }
    if any(test_counts.values()):
        manifest = _adopted_manifest(config)
        _write_manifest(config, manifest)
        return manifest

    rng = random.Random(RANDOM_STATE)
    manifest = {
        "random_state": RANDOM_STATE,
        "train_fraction": TRAIN_FRACTION,
        "classes": {},
    }
    total = 0

    if config.split_style == "train_sample":
        for cls in config.class_folders:
            src = train_dir(config) / cls
            images = _list_images(src)
            if not images:
                continue
            n_test = int(len(images) * TEST_RATIO)
            test_images = sorted(rng.sample(images, n_test))
            dst = test_dir(config) / cls
            dst.mkdir(parents=True, exist_ok=True)
            for img in test_images:
                shutil.move(str(src / img), str(dst / img))
            manifest["classes"][cls] = {
                "train": _list_images(src),
                "test": test_images,
            }
            total += len(images)
    elif config.split_style == "pool_shuffle":
        for cls in config.class_folders:
            staged = train_dir(config) / cls
            pooled = image_root(config) / cls
            src = staged if _list_images(staged) else pooled
            files = _list_images(src)
            if not files:
                continue
            rng.shuffle(files)
            split_idx = math.ceil(TRAIN_FRACTION * len(files))
            train_files, test_files = files[:split_idx], files[split_idx:]
            staged.mkdir(parents=True, exist_ok=True)
            dst = test_dir(config) / cls
            dst.mkdir(parents=True, exist_ok=True)
            if src.resolve() != staged.resolve():
                for f in train_files:
                    shutil.move(str(src / f), str(staged / f))
            for f in test_files:
                shutil.move(str(src / f), str(dst / f))
            manifest["classes"][cls] = {
                "train": sorted(train_files),
                "test": sorted(test_files),
            }
            total += len(files)
    else:
        raise ValueError("unknown split_style %r" % config.split_style)

    if total == 0:
        raise FileNotFoundError(
            "no images under %s; run render() first" % image_root(config)
        )
    _write_manifest(config, manifest)
    return manifest


class ImageExperiment:
    def __init__(self, config, dataloaders, folder_classes, train_targets, train_idx):
        self.config = get(config)
        self.schema = _schema.get(self.config.schema_key)
        self.dataloaders = dataloaders
        self.folder_classes = list(folder_classes)
        self.class_names = canonical_class_names(self.config, folder_classes)
        self.train_targets = train_targets
        self.train_idx = train_idx
        self.seed = RANDOM_STATE

    @property
    def labels(self):
        return list(range(len(self.folder_classes)))

    @property
    def dataset_name(self):
        return self.schema.real_file

    @property
    def test_set(self):
        return "real_heldout_20pct"

    @property
    def n_train(self):
        return len(self.train_idx)

    @property
    def n_features(self):
        return int(np.prod(image_shape(self.config)))

    @property
    def y_train(self):
        return np.asarray(self.train_targets)[self.train_idx]

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


def loaders(config, batch_size, test_batch_size=1, num_workers=0):
    import torch
    from sklearn.model_selection import train_test_split
    from torch.utils.data import DataLoader, Subset
    from torchvision import datasets, transforms

    config = get(config)
    shape = image_shape(config)
    transform = transforms.Compose(
        [
            transforms.Grayscale(num_output_channels=1),
            transforms.Resize(shape),
            transforms.ToTensor(),
            transforms.Normalize((0.5,), (0.5,)),
        ]
    )
    train_full = datasets.ImageFolder(root=str(train_dir(config)), transform=transform)
    val_full = datasets.ImageFolder(root=str(train_dir(config)), transform=transform)
    test_dataset = datasets.ImageFolder(root=str(test_dir(config)), transform=transform)

    targets = np.array(train_full.targets)
    train_idx, val_idx = train_test_split(
        np.arange(len(train_full)),
        train_size=TRAIN_FRACTION,
        random_state=RANDOM_STATE,
        stratify=targets,
    )
    dataloaders = {
        "train": DataLoader(
            Subset(train_full, train_idx),
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
        ),
        "val": DataLoader(
            Subset(val_full, val_idx),
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
        ),
        "test": DataLoader(
            test_dataset,
            batch_size=test_batch_size,
            shuffle=False,
            num_workers=num_workers,
        ),
    }
    return ImageExperiment(config, dataloaders, train_full.classes, targets, train_idx)
