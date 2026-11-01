import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

def load_grayscale_image(path):
    img = Image.open(path).convert('L')  # Convert to grayscale
    arr = np.array(img)
    return arr

def plot_images_4_classes(img_files, titles, out_file="2D_comparison.png"):
    images = [load_grayscale_image(f) for f in img_files]

    fig, axes = plt.subplots(1, 4, figsize=(12, 3))
    for ax, img, title in zip(axes, images, titles):
        ax.imshow(img, cmap='nipy_spectral', interpolation='none')
        ax.set_title(title)
        ax.axis('on')

    plt.tight_layout()
    plt.savefig(out_file, dpi=1000, bbox_inches="tight")
    plt.show()

if __name__ == "__main__":
    img_files = ["1.png", "2.png", "3.png", "4.png"]
    titles = [
        "Normal",
        "Simplistic Attack",
        "Intermediate Attack",
        "Sophisticated Attack"
    ]
    plot_images_4_classes(img_files, titles)