import json
import os
import random
import shutil

RANDOM_STATE = 1082
SPLIT_RATIO = 0.2

base_dir = os.path.join("image-results-spoofing", "data")
train_dir = os.path.join(base_dir, "Train")
test_dir = os.path.join(base_dir, "Test")
MANIFEST = os.path.join(base_dir, "split_manifest.json")
classes = ["benign", "malicious"]

if os.path.isfile(MANIFEST):
    raise SystemExit(
        "%s already exists, so the split has been made.\n"
        "This script moves images out of Train, so re-running it would split an\n"
        "already-split pool and leave roughly 64/36 instead of 80/20.\n"
        "Delete the manifest and move Test back into Train to redo it." % MANIFEST
    )

random.seed(RANDOM_STATE)

os.makedirs(test_dir, exist_ok=True)

manifest = {"random_state": RANDOM_STATE, "test_ratio": SPLIT_RATIO, "classes": {}}

for cls in classes:
    train_cls_dir = os.path.join(train_dir, cls)
    test_cls_dir = os.path.join(test_dir, cls)
    os.makedirs(test_cls_dir, exist_ok=True)

    images = sorted(
        img for img in os.listdir(train_cls_dir)
        if img.lower().endswith((".png", ".jpg", ".jpeg"))
    )
    n_test = int(len(images) * SPLIT_RATIO)
    test_images = sorted(random.sample(images, n_test))

    for img in test_images:
        shutil.move(os.path.join(train_cls_dir, img), os.path.join(test_cls_dir, img))

    manifest["classes"][cls] = {"test": test_images, "n_train_remaining": len(images) - n_test}
    print(f"Moved {n_test} images from {train_cls_dir} to {test_cls_dir}")

with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=1)

print(f"Splitting complete. Membership recorded in {MANIFEST}")
