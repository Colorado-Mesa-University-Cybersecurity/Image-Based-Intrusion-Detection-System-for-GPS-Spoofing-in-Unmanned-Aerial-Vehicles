import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

def load_grayscale_image(path):
    img = Image.open(path).convert('L')  # 'L' mode ensures grayscale
    arr = np.array(img)
    return arr

def plot_images_side_by_side(
    img_left, img_right,
    title_left="Normal",
    title_right="GPS Spoofing",
    out_file="UAV_comparison.png",
    dpi=1000,
):
    fig, axes = plt.subplots(1, 2, figsize=(6, 3))  # inches

    for ax, img, title in zip(axes, [img_left, img_right], [title_left, title_right]):
        ax.imshow(img, cmap='nipy_spectral', interpolation='none')
        ax.set_title(title)
        ax.set_xticks(np.arange(0, img.shape[1], 16))
        ax.set_yticks(np.arange(0, img.shape[0], 16))

    plt.tight_layout()

    # Save at 800 dpi
    plt.savefig(out_file, dpi=dpi, bbox_inches="tight")
    plt.show()

if __name__ == "__main__":
    left_img = load_grayscale_image("left.png")
    right_img = load_grayscale_image("right.png")
    plot_images_side_by_side(left_img, right_img)