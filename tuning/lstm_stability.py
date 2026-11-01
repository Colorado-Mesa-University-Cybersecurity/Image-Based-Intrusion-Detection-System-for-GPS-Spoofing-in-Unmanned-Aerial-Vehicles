"""Measure LSTM seed stability through the committed harness.

The committed configuration before the tanh head was a coin flip on UAV: one run in
ten collapsed entirely. This reports the spread, the degenerate count, and the best
epochs, so a regression in stability shows up as a number rather than as a surprise.

Each seed builds a fresh protocol.real_heldout, so the spread covers both the split
and the model's own randomness. The original study varied network seeds at a fixed
split; those two spreads are not interchangeable.

    python tuning/lstm_stability.py --dataset uav --seeds 1082 7 42 2024 31337
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gps_ids import protocol, training


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="uav", choices=("uav", "2d"))
    parser.add_argument("--seeds", type=int, nargs="+",
                        default=[1082, 7, 42, 2024, 31337, 5, 13, 97, 404, 777])
    parser.add_argument("--out", default=None, help="CSV to append every run to")
    args = parser.parse_args()

    budget = training.SPECS["LSTM Classifier"]["params"]["epochs"]
    print("committed spec: %s" % training.SPECS["LSTM Classifier"]["params"], flush=True)

    rows = []
    for seed in args.seeds:
        exp = protocol.real_heldout(args.dataset, seed=seed)
        start = time.time()
        result = training.run(
            "LSTM Classifier", exp,
            results_csv=args.out, append=args.out is not None, quiet=True,
        )
        rows.append(result.row)
        print("  seed %-6d MCC %.4f  bal %.4f  min-rec %.4f  degenerate %-5s "
              "best_epoch %-4s (%.0fs)"
              % (seed, float(result.row["mcc"]),
                 float(result.row["balanced_accuracy"]),
                 float(result.row["min_class_recall"]),
                 result.row["is_degenerate"], result.row["num_epochs"],
                 time.time() - start), flush=True)
        del exp

    mcc = np.array([float(r["mcc"]) for r in rows])
    degenerate = sum(1 for r in rows if str(r["is_degenerate"]).lower() == "true")
    epochs = sorted(int(r["num_epochs"]) for r in rows)
    print("\n=== %s, %d seeds ===" % (args.dataset, len(args.seeds)))
    print("  MCC          %.4f +/- %.4f   min %.4f  max %.4f"
          % (mcc.mean(), mcc.std(ddof=1), mcc.min(), mcc.max()))
    print("  degenerate   %d of %d" % (degenerate, len(rows)))
    print("  best epochs  %s  (budget %d)" % (epochs, budget))
    print("  any at the budget: %s" % any(e == budget for e in epochs))


if __name__ == "__main__":
    main()
