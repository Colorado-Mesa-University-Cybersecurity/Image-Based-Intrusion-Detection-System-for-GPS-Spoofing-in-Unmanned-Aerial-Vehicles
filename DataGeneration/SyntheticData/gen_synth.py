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

from gps_ids import schema
from gps_ids.paths import repo_root

if len(sys.argv) < 2:
    sys.exit("usage: gen_synth.py <size> [<size> ...]")

SIZES = [int(s) for s in sys.argv[1:]]
SYNTH_ROOT = repo_root() / "DataGeneration" / "SyntheticData"

JOBS = [
    (SYNTH_ROOT / "UAVATTACK" / "SDV", "uav"),
    (SYNTH_ROOT / "2D" / "SDV", "2d"),
]

CLASSES = {
    "gc": ("GaussianCopula", GaussianCopulaSynthesizer),
    "ctgan": ("CTGAN", CTGANSynthesizer),
    "tvae": ("TVAE", TVAESynthesizer),
}

for synth_dir, dataset in JOBS:
    out_dir = repo_root() / schema.get(dataset).data_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    for key, (pkl_name, cls) in CLASSES.items():
        pkl = synth_dir / f"spoofing-{pkl_name}-synthesizer.pkl"
        if not pkl.is_file():
            print(f"[{dataset}] MISSING {pkl}", flush=True)
            continue
        synth = None
        for n in SIZES:
            out = out_dir / f"spoofing_{key}_{n}.csv"
            if out.is_file():
                print(f"[{dataset}] skip (exists) {out.name}", flush=True)
                continue
            if synth is None:
                synth = cls.load(str(pkl))
            t = time.time()
            synth.reset_sampling()
            df = synth.sample(n)
            label_col = schema.get(dataset).label_column
            df = schema.to_canonical_frame(
                df.drop(columns=[label_col]), df[label_col], dataset
            )
            tmp = out.with_suffix(out.suffix + ".partial")
            df.to_csv(tmp, index=False)
            os.replace(tmp, out)
            mb = out.stat().st_size / 1e6
            print(
                f"[{dataset}] {out.name:32s} {df.shape}  "
                f"{time.time() - t:7.1f}s  {mb:8.1f} MB",
                flush=True,
            )

print("DONE", flush=True)
