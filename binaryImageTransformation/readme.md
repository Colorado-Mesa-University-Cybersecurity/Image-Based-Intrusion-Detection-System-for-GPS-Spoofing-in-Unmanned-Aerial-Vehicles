## Instructions for Setting Up `binaryImageTransformation`

This directory contains code and results for binary image transformation experiments on two datasets: "2d tubular data" and "UAVATTACK tubular data." Each dataset folder includes an `image-results-spoofing` subfolder with necessary images.

### How to Download and Organize Results

For every dataset folder listed below, make sure you have the corresponding `image-results-spoofing` folder. If any of these folders are missing, please download them from the following link and rename them to `image-results-spoofing` after extraction:

[Download image-results folders from Google Drive](https://drive.google.com/drive/folders/1l2LfGwJ8FRzE115wkMUHQRaGiru-SwGv?usp=sharing)

Place each `image-results-spoofing` folder inside its respective dataset directory as shown below.

---

### Directory Structure

Your directory should look like this:

```plaintext
binaryImageTransformation/
├── 2d tubular data/
│   └── image-results-spoofing/
│       ├── CNN.ipynb
│       ├── helper_functions.py
│       ├── LSTM.ipynb
│       ├── organize.py
│       ├── ResNet.ipynb
│       ├── split-Images.py
│       └── tabToImage.ipynb
├── UAVATTACK tubular data/
│   └── image-results-spoofing/
│       ├── best_cnn_lstm_model.pth
│       ├── best_cnn_model.pth
│       ├── best_resnet_model.pth
│       ├── CNN.ipynb
│       ├── helper_functions.py
│       ├── LSTM.ipynb
│       ├── ResNet.ipynb
│       ├── split images.py
│       └── tabToImage.ipynb
└── readme.md
```

### Notes

- The `image-results-spoofing` folders contain the images used by the CNN models. If you want to generate your own images, you can run the `tabToImage.ipynb` notebook. Make sure you have downloaded the datasets and placed them in the `Datasets` directory before doing this.
- After generating images, use `organize.py` (for 2d data) or just proceed to `split-Images.py` to sort the images into the correct folders.
- Be sure to keep all file and folder names exactly as shown above. This helps keep everything organized and avoids errors with file paths in the scripts.