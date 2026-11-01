"""Compare Random Forest max_features=None against 'sqrt' through the committed harness.

Reproduces the margin reported in the tuning appendix. Everything else, including
class_weight, is taken from SPECS["Random Forest"], so the comparison tracks whatever
is committed rather than a configuration frozen into this script.

    python tuning/rf_max_features.py --dataset 2d --seeds 1082 7 42
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gps_ids import protocol, training

ARMS = (("None (committed)", None), ("sqrt", "sqrt"))
METRICS = ("mcc", "balanced_accuracy", "min_class_recall")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="2d", choices=("uav", "2d"))
    parser.add_argument("--seeds", type=int, nargs="+", default=[1082, 7, 42])
    parser.add_argument("--out", default=None, help="CSV to append every run to")
    args = parser.parse_args()

    print("committed spec: %s" % training.SPECS["Random Forest"]["params"], flush=True)
    rows = {}
    for seed in args.seeds:
        exp = protocol.real_heldout(args.dataset, seed=seed)
        print("\n=== %s seed %d | train %d / test %d ==="
              % (args.dataset, seed, exp.n_train, len(exp.y_test)), flush=True)
        for label, max_features in ARMS:
            start = time.time()
            result = training.run(
                "Random Forest", exp,
                overrides={"max_features": max_features},
                results_csv=args.out, append=args.out is not None, quiet=True,
            )
            rows[(seed, label)] = result.row
            print("  %-17s MCC %.4f  bal %.4f  min-rec %.4f  fit %7.1fs"
                  % (label, float(result.row["mcc"]),
                     float(result.row["balanced_accuracy"]),
                     float(result.row["min_class_recall"]),
                     float(result.row["train_time_sec"])), flush=True)
        del exp

    print("\n=== %s, %d seeds: None minus sqrt ===" % (args.dataset, len(args.seeds)))
    for metric in METRICS:
        deltas = [float(rows[(s, "None (committed)")][metric])
                  - float(rows[(s, "sqrt")][metric]) for s in args.seeds]
        print("  %-18s %+.4f +/- %.4f   per seed %s"
              % (metric, np.mean(deltas), np.std(deltas, ddof=1),
                 [round(v, 4) for v in deltas]))
    times = {
        label: np.mean([float(rows[(s, label)]["train_time_sec"]) for s in args.seeds])
        for label, _ in ARMS
    }
    print("  %-18s None is %.2fx sqrt (%.0fs vs %.0fs mean)"
          % ("train time", times["None (committed)"] / times["sqrt"],
             times["None (committed)"], times["sqrt"]))


if __name__ == "__main__":
    main()
