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

random.seed(RANDOM_STATE)

for d in [TRAIN_DIR, TEST_DIR]:
    os.makedirs(d, exist_ok=True)

manifest = {"random_state": RANDOM_STATE, "train_fraction": TRAIN_FRACTION, "classes": {}}

for label in LABELS:
    src_dir = os.path.join(ROOT_DIR, label)
    if not os.path.isdir(src_dir):
        continue

    files = sorted(f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir, f)))
    random.shuffle(files)
    split_idx = math.ceil(TRAIN_FRACTION * len(files))
    train_files = files[:split_idx]
    test_files = files[split_idx:]

    train_label_dir = os.path.join(TRAIN_DIR, label)
    test_label_dir = os.path.join(TEST_DIR, label)
    os.makedirs(train_label_dir, exist_ok=True)
    os.makedirs(test_label_dir, exist_ok=True)

    for f in train_files:
        shutil.move(os.path.join(src_dir, f), os.path.join(train_label_dir, f))
    for f in test_files:
        shutil.move(os.path.join(src_dir, f), os.path.join(test_label_dir, f))

    manifest["classes"][label] = {"train": train_files, "test": test_files}
    print(f"Label {label}: {len(train_files)} to train, {len(test_files)} to test.")

with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=1)

print(f"Splitting complete. Membership recorded in {MANIFEST}")
