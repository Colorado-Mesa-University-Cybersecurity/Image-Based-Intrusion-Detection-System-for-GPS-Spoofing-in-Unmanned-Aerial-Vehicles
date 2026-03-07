import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

def load_grayscale_image(path):
    return np.array(Image.open(path).convert("L"))

def plot_four_side_by_side(
    paths=("1.png", "2.png", "3.png", "4.png"),
    titles=("Normal", "Simplistic", "Intermediate", "Sophisticated"),
    out_file="comparison_4.png",
    dpi=800,
):
    imgs = [load_grayscale_image(p) for p in paths]

    fig, axes = plt.subplots(1, 4, figsize=(12, 3))  # same 1-row layout, wider

    for ax, img, title in zip(axes, imgs, titles):
        ax.imshow(img, cmap="nipy_spectral", interpolation="none")
        ax.set_title(title)
        ax.set_xticks(np.arange(0, img.shape[1], 16))
        ax.set_yticks(np.arange(0, img.shape[0], 16))
        ax.axis("on")

    plt.tight_layout()
    plt.savefig(out_file, dpi=dpi, bbox_inches="tight")
    plt.show()

if __name__ == "__main__":
    plot_four_side_by_side()