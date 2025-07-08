import os
import shutil
import random
import math

# Root directory where your folders 0, 1, 2, 3 are located
ROOT_DIR = "image-results-spoofing"
TRAIN_DIR = os.path.join(ROOT_DIR, "train")
TEST_DIR = os.path.join(ROOT_DIR, "test")

# Make sure train/ and test/ directories exist
for d in [TRAIN_DIR, TEST_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# For each class folder (0, 1, 2, 3)
for label in ["0", "1", "2", "3"]:
    src_dir = os.path.join(ROOT_DIR, label)
    if not os.path.isdir(src_dir):
        continue

    files = [f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir, f))]
    random.shuffle(files)
    split_idx = math.ceil(0.2 * len(files))
    train_files = files[:split_idx]
    test_files = files[split_idx:]

    # Create destination folders
    train_label_dir = os.path.join(TRAIN_DIR, label)
    test_label_dir = os.path.join(TEST_DIR, label)
    os.makedirs(train_label_dir, exist_ok=True)
    os.makedirs(test_label_dir, exist_ok=True)

    # Move files
    for f in train_files:
        shutil.move(os.path.join(src_dir, f), os.path.join(train_label_dir, f))
    for f in test_files:
        shutil.move(os.path.join(src_dir, f), os.path.join(test_label_dir, f))

    print(f"Label {label}: {len(train_files)} to train, {len(test_files)} to test.")

print("Splitting complete.")