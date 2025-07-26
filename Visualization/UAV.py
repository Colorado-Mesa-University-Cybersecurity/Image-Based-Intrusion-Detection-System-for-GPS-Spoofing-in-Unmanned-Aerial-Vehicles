import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

def load_grayscale_image(path):
    img = Image.open(path).convert('L')  # 'L' mode ensures grayscale
    arr = np.array(img)
    return arr

def plot_images_side_by_side(img_left, img_right, title_left="Normal", title_right="GPS Spoofing", crop_size=(32, 32), out_file="bw_comparison.png"):
    left_crop = img_left[:crop_size[0], :crop_size[1]]
    right_crop = img_right[:crop_size[0], :crop_size[1]]

    fig, axes = plt.subplots(1, 2, figsize=(6, 3))
    im1 = axes[0].imshow(left_crop, cmap='nipy_spectral', interpolation='none')
    axes[0].set_title(title_left)
    axes[0].axis('on')

    im2 = axes[1].imshow(right_crop, cmap='nipy_spectral', interpolation='none')
    axes[1].set_title(title_right)
    axes[1].axis('on')

    for ax in axes:
        ax.set_xticks(np.arange(0, crop_size[1], 10))
        ax.set_yticks(np.arange(0, crop_size[0], 5))

    plt.tight_layout()
    plt.savefig(out_file)
    plt.show()

if __name__ == "__main__":
    left_img = load_grayscale_image("left.png")
    right_img = load_grayscale_image("right.png")
    plot_images_side_by_side(left_img, right_img)