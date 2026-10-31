import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")

from sdv.single_table import (
    CTGANSynthesizer,
    GaussianCopulaSynthesizer,
    TVAESynthesizer,
)

if len(sys.argv) < 3:
    sys.exit("usage: gen_synth.py <repo_root> <size> [<size> ...]")

ROOT = sys.argv[1]
SIZES = [int(s) for s in sys.argv[2:]]

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from gps_ids import schema as gps_schema

JOBS = [
    (
        os.path.join(ROOT, "Synthetic_Data_Generation", "UAV Synthetic Data Generation", "SDV"),
        os.path.join(ROOT, "Datasets", "csv", "UAVATTACK"),
        "uav",
    ),
    (
        os.path.join(ROOT, "Synthetic_Data_Generation", "2D Synthetic Data Generation", "SDV"),
        os.path.join(ROOT, "Datasets", "excel", "2dSpoofingDataset"),
        "2d",
    ),
]

CLASSES = {
    "gc": ("GaussianCopula", GaussianCopulaSynthesizer),
    "ctgan": ("CTGAN", CTGANSynthesizer),
    "tvae": ("TVAE", TVAESynthesizer),
}

for synth_dir, out_dir, tag in JOBS:
    os.makedirs(out_dir, exist_ok=True)
    for key, (pkl_name, cls) in CLASSES.items():
        pkl = os.path.join(synth_dir, f"spoofing-{pkl_name}-synthesizer.pkl")
        if not os.path.isfile(pkl):
            print(f"[{tag}] MISSING {pkl}", flush=True)
            continue
        synth = None
        for n in SIZES:
            out = os.path.join(out_dir, f"spoofing_{key}_{n}.csv")
            if os.path.isfile(out):
                print(f"[{tag}] skip (exists) {os.path.basename(out)}", flush=True)
                continue
            if synth is None:
                synth = cls.load(pkl)
            t = time.time()
            synth.reset_sampling()
            df = synth.sample(n)
            label_col = gps_schema.get(tag).label_column
            df = gps_schema.to_canonical_frame(
                df.drop(columns=[label_col]), df[label_col], tag
            )
            tmp = out + ".partial"
            df.to_csv(tmp, index=False)
            os.replace(tmp, out)
            mb = os.path.getsize(out) / 1e6
            print(
                f"[{tag}] {os.path.basename(out):32s} {df.shape}  "
                f"{time.time() - t:7.1f}s  {mb:8.1f} MB",
                flush=True,
            )

print("DONE", flush=True)
