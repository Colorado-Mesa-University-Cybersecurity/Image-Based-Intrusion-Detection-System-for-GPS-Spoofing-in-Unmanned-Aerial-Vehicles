import os
import shutil
import random

# Set paths
base_dir = "image-results-spoofing/data"
train_dir = os.path.join(base_dir, "Train")
test_dir = os.path.join(base_dir, "Test")
classes = ["benign", "malicious"]

split_ratio = 0.2  # 20% for testing

os.makedirs(test_dir, exist_ok=True)

for cls in classes:
    train_cls_dir = os.path.join(train_dir, cls)
    test_cls_dir = os.path.join(test_dir, cls)
    os.makedirs(test_cls_dir, exist_ok=True)

    images = os.listdir(train_cls_dir)
    images = [img for img in images if img.lower().endswith(('.png', '.jpg', '.jpeg'))]
    n_test = int(len(images) * split_ratio)
    test_images = random.sample(images, n_test)

    for img in test_images:
        src = os.path.join(train_cls_dir, img)
        dst = os.path.join(test_cls_dir, img)
        shutil.move(src, dst)

    print(f"Moved {n_test} images from {train_cls_dir} to {test_cls_dir}")