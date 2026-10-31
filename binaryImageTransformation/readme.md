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
│   ├── CNN.ipynb
│   ├── CnnLstm.ipynb
│   ├── ResnetCnn.ipynb
│   ├── ResnetLstm.ipynb
│   ├── tabToImage.ipynb
│   ├── split-Images.py
│   └── image-results-spoofing/      <- generated images and .pth files, gitignored
├── UAVATTACK tubular data/
│   ├── CNN.ipynb
│   ├── CnnLstm.ipynb
│   ├── ResnetCnn.ipynb
│   ├── ResnetLstm.ipynb
│   ├── tabToImage.ipynb
│   ├── split images.py
│   └── image-results-spoofing/      <- generated images and .pth files, gitignored
└── readme.md
```

The pipeline itself lives in `gps_ids/images.py`: one module configured per
dataset (`UAV_IMAGES`, `TWO_D_IMAGES`) that renders the images, organizes them
into `data/Train/<class>`, splits idempotently under one manifest format, and
builds the train/val/test loaders with the image shape derived from the
dataset schema. The notebooks and split scripts are thin callers.

Each notebook's filename matches the `MODEL_NAME` it records:

| notebook | `MODEL_NAME` | backbone | head |
|---|---|---|---|
| `CNN.ipynb` | `CNN` | custom 4-block CNN | dense |
| `CnnLstm.ipynb` | `CNN-LSTM` | custom 4-block CNN | LSTM |
| `ResnetCnn.ipynb` | `ResNet-CNN` | ResNet-101 (pretrained) | dense |
| `ResnetLstm.ipynb` | `ResNet-LSTM` | ResNet-101 (pretrained) | LSTM |

`tabToImage.ipynb` is the encoder, not a model: it turns a tabular row into one
binary image whose rows are features and whose columns are bits.

### Notes

- The `image-results-spoofing` folders contain the images used by the CNN models. If you want to generate your own images, you can run the `tabToImage.ipynb` notebook. Make sure you have downloaded the datasets and placed them in the `Datasets` directory before doing this.
- After generating images, run `split-Images.py` (2d data) or `split images.py` (UAVATTACK) to carve the test split out of `data/Train`. Both call `gps_ids.images.split`, which is idempotent: it adopts a pre-split archive (the UAVATTACK download ships split), completes legacy manifests, and refuses to double-split. Loose images in `image-results-spoofing/` are picked up by `gps_ids.images.organize`.
- Be sure to keep all file and folder names exactly as shown above. This helps keep everything organized and avoids errors with file paths in the scripts.