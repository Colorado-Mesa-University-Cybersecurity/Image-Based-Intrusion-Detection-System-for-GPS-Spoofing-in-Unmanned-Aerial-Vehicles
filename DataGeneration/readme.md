## Data Generation

Everything derived from the two original datasets is produced here. Nothing in
this tree trains a detector; the models that consume these outputs live in
`Models/<dataset>/`.

```plaintext
DataGeneration/
├── BinaryImages/
│   ├── 2D/
│   │   ├── tabToImage.ipynb          renders every row to a binary image
│   │   ├── split_images.py           carves the test split, idempotently
│   │   └── image-results-spoofing/   generated images and checkpoints, gitignored
│   └── UAVATTACK/
│       ├── tabToImage.ipynb
│       ├── split_images.py
│       └── image-results-spoofing/
└── SyntheticData/
    ├── gen_synth.py                  samples the committed synthesizers
    ├── 2D/SDV/                       synthesizer fit notebook + 3 .pkl + metadata
    └── UAVATTACK/
        ├── SDV/                      synthesizer fit notebook + 3 .pkl + metadata
        ├── GAN/GAN.ipynb
        └── CGAN/CGAN.ipynb
```

### Synthetic tables

`SDV_Synthetic.ipynb` fits GaussianCopula, CTGAN, and TVAE on the real dataset
and saves each synthesizer as a `.pkl` beside the notebook (committed, so the
fit does not have to be repeated). `gen_synth.py` then samples those
synthesizers at 10k / 100k / 1M rows:

```bash
.venv/Scripts/python -I DataGeneration/SyntheticData/gen_synth.py 10000 100000 1000000
```

It writes into each dataset's folder under `Datasets/`, skips files that already
exist, and is resumable. SDV must stay on 1.x — see `SETUP.md`.

GAN and CGAN are UAV-ATTACK only. Both write their samples through the canonical
dataset schema, so a generated table is indistinguishable from the real data in
column names, column order, and label encoding.

### Binary images

`tabToImage.ipynb` renders one image per row: each feature becomes a row of bit
pixels, padded to at least `precision` rows. UAV-ATTACK yields 82x64 images
(82 features, 64-bit encoding) and 2D yields 64x64. Images land in
`image-results-spoofing/data/Train/<class>/`.

`split_images.py` then moves the test split into `.../data/Test/<class>/` and
records membership in `split_manifest.json`. It is safe to re-run: it adopts a
pre-split archive (the UAV-ATTACK download ships split 2,899/723), completes a
legacy manifest, and refuses to split an already-split pool.

The downloadable image archives are linked from `Datasets/readme.md`. Extract
each into its dataset's `image-results-spoofing/` folder if you would rather not
render 510,530 images locally.

### Where the behaviour lives

Both halves are thin callers of `gps_ids/`:

- `gps_ids/schema.py` — the canonical columns and label vocabulary every
  generated table is normalized to.
- `gps_ids/images.py` — rendering, folder organization, the idempotent split,
  the image shape derived from the schema, and the loaders the image models use.

Change the bit precision, the split ratio, or the class folders there, not in
these notebooks.
