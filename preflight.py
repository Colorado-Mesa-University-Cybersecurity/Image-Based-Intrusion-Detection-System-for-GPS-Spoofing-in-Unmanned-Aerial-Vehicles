"""Run this before the regeneration campaign. Exits non-zero if anything is wrong.

Checks the environment, that the repository is a clean slate, and that the GPU
backends resolve and actually fit. The cuML stacking check matters most: on Linux the
StackingClassifier's SVC runs on cuML for the first time, and the alternative to
proving it here is discovering it hours into the 2D stacking run.

    python preflight.py
    python preflight.py --skip-fit     # environment and slate only
"""
import argparse
import glob
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

PASS, FAIL, SKIP = [], [], []


def check(label, ok, info=""):
    (PASS if ok else FAIL).append(label)
    print("%s %-46s %s" % ("PASS" if ok else "FAIL", label, info), flush=True)
    return ok


def skip(label, info=""):
    SKIP.append(label)
    print("SKIP %-46s %s" % (label, info), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-fit", action="store_true",
                        help="skip the cuML stacking fit")
    parser.add_argument("--rows", type=int, default=4000,
                        help="subsample size for the stacking fit")
    args = parser.parse_args()

    is_linux = sys.platform.startswith("linux")
    print("=== environment ===")
    print("     %s | python %s" % (platform.platform(), platform.python_version()))
    check("python is 3.11-3.13 (cuML has no 3.14 wheel)",
          (3, 11) <= sys.version_info[:2] <= (3, 13),
          ".".join(map(str, sys.version_info[:3])))

    try:
        import torch
        cuda = torch.cuda.is_available()
        check("torch sees CUDA", cuda,
              torch.cuda.get_device_name(0) if cuda else "no device")
    except Exception as error:
        check("torch imports", False, repr(error))

    print("\n=== cuML backend ===")
    from gps_ids import accel

    try:
        backend, _ = accel.resolve_svc("auto")
    except Exception as error:
        backend = "error: %r" % error
    if is_linux:
        check("auto resolves to cuML", backend == "cuml", backend)
    elif backend == "cuml":
        check("auto resolves to cuML", True, backend)
    else:
        skip("auto resolves to cuML",
             "%s - expected off Linux, where cuML has no wheel" % backend)

    print("\n=== source data ===")
    from gps_ids import images, protocol, results, schema, training

    for key in ("uav", "2d"):
        try:
            X, y = schema.load_real(schema.get(key))
            check("%s source data loads" % key, len(X) > 0,
                  "%d rows x %d features" % (len(X), X.shape[1]))
        except Exception as error:
            check("%s source data loads" % key, False, repr(error))

    print("\n=== clean slate ===")
    for key in ("uav", "2d"):
        present = [f for f in results.synthetic_files(key)
                   if schema.synthetic_path(schema.get(key), f).exists()]
        check("%s synthetic tables absent" % key, not present,
              "%d of 11 present" % len(present))
        config = images.get(key)
        check("%s renders absent" % key, not images.data_dir(config).exists())
        check("%s tensor cache absent" % key, not images.cache_dir(config).exists())
    for name in ("UAVATTACK_Results.csv", "2D_Results.csv"):
        check("%s absent" % name, not (ROOT / name).is_file())
    check("no synthesizer pickles",
          not glob.glob(str(ROOT / "DataGeneration/**/*.pkl"), recursive=True))
    check("no model checkpoints",
          not glob.glob(str(ROOT / "DataGeneration/**/*.pth"), recursive=True))

    print("\n=== configuration ===")
    check("SEEDS has 5 entries", len(training.SEEDS) == 5, str(training.SEEDS))
    check("SYNTHETIC_SEEDS has 3 entries", len(training.SYNTHETIC_SEEDS) == 3,
          str(training.SYNTHETIC_SEEDS))
    check("both image configs use tabular_index",
          all(images.get(k).split_style == "tabular_index" for k in ("uav", "2d")))
    check("MLP is the only unweighted model",
          [n for n, s in training.SPECS.items()
           if s["kind"] == "sklearn" and "class_weight" not in s["params"]
           and not s.get("balanced_sample_weight")] == ["MLP Classifier"])

    if args.skip_fit:
        skip("stacking fit through the resolved backend", "--skip-fit")
    else:
        print("\n=== stacking fit through the resolved backend ===")
        import numpy as np
        from sklearn.model_selection import train_test_split

        real = schema.load_real

        def subsample(sch):
            X, y = real(sch)
            y = np.asarray(y)
            if len(X) <= args.rows:
                return X, y
            Xs, _, ys, _ = train_test_split(
                X, y, train_size=args.rows, random_state=1082, stratify=y)
            return Xs, ys

        schema.load_real = subsample
        try:
            exp = protocol.real_heldout("2d")
            start = time.time()
            result = training.run(training.STACK_NAME, exp, quiet=True,
                                  results_csv=str(ROOT / ".preflight_results.csv"))
            recorded = str(result.row["parameters"])
            resolved = "cuml" if "'svc_backend': 'cuml'" in recorded else (
                "sklearn" if "'svc_backend': 'sklearn'" in recorded else "unrecorded")
            check("stack fits on %d rows" % args.rows, True,
                  "MCC %.4f in %.0fs" % (float(result.row["mcc"]), time.time() - start))
            check("the row records which backend ran", resolved != "unrecorded", resolved)
            if is_linux:
                check("the stack actually used cuML", resolved == "cuml", resolved)
            else:
                skip("the stack actually used cuML", resolved)
        except Exception as error:
            check("stack fits on %d rows" % args.rows, False, repr(error))
        finally:
            schema.load_real = real
            (ROOT / ".preflight_results.csv").unlink(missing_ok=True)

    print("\n=== %d passed, %d failed, %d skipped ===" % (len(PASS), len(FAIL), len(SKIP)))
    for label in FAIL:
        print("  FAILED: %s" % label)
    if FAIL:
        print("\nDo not start the campaign until these are fixed.")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
