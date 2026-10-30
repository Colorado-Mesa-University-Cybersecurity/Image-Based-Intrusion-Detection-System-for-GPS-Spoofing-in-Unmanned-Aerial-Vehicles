import json
import math
import os
import random
import shutil

RANDOM_STATE = 1082
TRAIN_FRACTION = 0.8

ROOT_DIR = "image-results-spoofing"
DATA_DIR = os.path.join(ROOT_DIR, "data")
TRAIN_DIR = os.path.join(DATA_DIR, "Train")
TEST_DIR = os.path.join(DATA_DIR, "Test")
MANIFEST = os.path.join(DATA_DIR, "split_manifest.json")

LABELS = ["0", "1", "2", "3"]

if os.path.isfile(MANIFEST):
    raise SystemExit(
        "%s already exists, so the split has been made.\n"
        "Re-running would move an already-split pool and produce a 64/36 split.\n"
        "Delete the manifest and the Train/Test folders to redo it." % MANIFEST
    )


def list_images(directory):
    if not os.path.isdir(directory):
        return []
    return sorted(
        f for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f))
        and f.lower().endswith((".png", ".jpg", ".jpeg"))
    )


def source_for(label):
    staged = os.path.join(TRAIN_DIR, label)
    if list_images(staged):
        return staged, list_images(staged)
    pooled = os.path.join(ROOT_DIR, label)
    return pooled, list_images(pooled)


random.seed(RANDOM_STATE)

manifest = {"random_state": RANDOM_STATE, "train_fraction": TRAIN_FRACTION, "classes": {}}
total_moved = 0

for label in LABELS:
    src_dir, files = source_for(label)
    if not files:
        print(f"Label {label}: no images found under {src_dir}, skipping.")
        continue

    random.shuffle(files)
    split_idx = math.ceil(TRAIN_FRACTION * len(files))
    train_files = files[:split_idx]
    test_files = files[split_idx:]

    train_label_dir = os.path.join(TRAIN_DIR, label)
    test_label_dir = os.path.join(TEST_DIR, label)
    os.makedirs(train_label_dir, exist_ok=True)
    os.makedirs(test_label_dir, exist_ok=True)

    if os.path.abspath(src_dir) != os.path.abspath(train_label_dir):
        for f in train_files:
            shutil.move(os.path.join(src_dir, f), os.path.join(train_label_dir, f))
    for f in test_files:
        shutil.move(os.path.join(src_dir, f), os.path.join(test_label_dir, f))

    manifest["classes"][label] = {"train": train_files, "test": test_files}
    total_moved += len(files)
    print(f"Label {label}: {len(train_files)} to train, {len(test_files)} to test.")

if total_moved == 0:
    raise SystemExit(
        "No images found under %s or %s/<label>.\n"
        "Run tabToImage.ipynb first. Nothing was written." % (TRAIN_DIR, ROOT_DIR)
    )

with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=1)

print(f"Splitting complete. Membership recorded in {MANIFEST}")
