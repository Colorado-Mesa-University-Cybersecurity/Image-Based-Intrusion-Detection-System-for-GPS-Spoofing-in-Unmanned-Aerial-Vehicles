import numpy as np
import pandas as pd

MAX_TOPUP_BATCHES = 24
MAX_BATCH_ROWS = 2_000_000
RATE_SAFETY = 1.3
MIN_RATE = 1e-6
MAX_TRIES_PER_BATCH = 500


class UnbalancedSynthetic(RuntimeError):
    pass


def _rows_for(frame, label_column, value):
    column = frame[label_column]
    if column.dtype == object or str(column.dtype) == "category":
        return frame[column.astype(str) == str(value)]
    return frame[column == value]


def _conditioned(synthesizer, label_column, classes, per_class, max_tries):
    from sdv.sampling import Condition

    conditions = [
        Condition(num_rows=per_class, column_values={label_column: value})
        for value in classes
    ]
    try:
        return synthesizer.sample_from_conditions(
            conditions=conditions, max_tries_per_batch=max_tries
        )
    except TypeError:
        try:
            return synthesizer.sample_from_conditions(conditions=conditions)
        except Exception:
            return None
    except Exception:
        return None


def sample_balanced(
    synthesizer,
    label_column,
    classes,
    total,
    *,
    seed=None,
    max_batches=MAX_TOPUP_BATCHES,
    max_batch_rows=MAX_BATCH_ROWS,
    max_tries=MAX_TRIES_PER_BATCH,
    report=None,
):
    classes = list(classes)
    if not classes:
        raise ValueError("no classes to balance over")
    per_class = total // len(classes)
    if per_class < 1:
        raise ValueError(
            "total=%d cannot be split across %d classes" % (total, len(classes))
        )

    kept = {value: None for value in classes}
    seen = {value: 0 for value in classes}
    drawn = 0

    pooled = _conditioned(synthesizer, label_column, classes, per_class, max_tries)
    if pooled is not None:
        drawn += len(pooled)
        for value in classes:
            rows = _rows_for(pooled, label_column, value)
            seen[value] += len(rows)
            kept[value] = rows.iloc[:per_class]

    def shortfall():
        return {
            value: per_class - (0 if kept[value] is None else len(kept[value]))
            for value in classes
            if kept[value] is None or len(kept[value]) < per_class
        }

    batches = 0
    while shortfall():
        missing = shortfall()
        if batches >= max_batches:
            rates = {
                value: (seen[value] / drawn if drawn else 0.0) for value in missing
            }
            raise UnbalancedSynthetic(
                "could not reach %d rows per class after %d top-up batches "
                "(%d rows drawn). Short classes have/need %s at observed rates %s. "
                "Raise the synthesizer's epochs so it stops collapsing onto the "
                "majority class, raise max_batches, or fit one synthesizer per "
                "class; do not write an unbalanced table."
                % (
                    per_class,
                    batches,
                    drawn,
                    {k: "%d/%d" % (per_class - v, per_class) for k, v in missing.items()},
                    {k: round(v, 5) for k, v in rates.items()},
                )
            )

        worst_rate = min(
            max(seen[value] / drawn if drawn else 0.0, MIN_RATE) for value in missing
        )
        needed = max(missing.values())
        draw = int(min(max(needed / worst_rate * RATE_SAFETY, 1000), max_batch_rows))
        if report:
            report(
                "top-up batch %d: drawing %d rows for %s (worst observed rate %.5f)"
                % (batches + 1, draw, sorted(missing), worst_rate)
            )
        extra = synthesizer.sample(num_rows=draw)
        drawn += len(extra)
        for value in classes:
            rows = _rows_for(extra, label_column, value)
            seen[value] += len(rows)
            if kept[value] is None or len(kept[value]) < per_class:
                current = kept[value]
                if current is None or not len(current):
                    merged = rows
                else:
                    merged = pd.concat([current, rows])
                kept[value] = merged.iloc[:per_class]
        batches += 1

    out = pd.concat([kept[value] for value in classes], ignore_index=True)
    counts = out[label_column].value_counts().to_dict()
    if len(set(counts.values())) != 1 or len(counts) != len(classes):
        raise UnbalancedSynthetic(
            "balancing produced %s, expected %d classes at %d rows each"
            % (counts, len(classes), per_class)
        )
    return out.sample(frac=1, random_state=seed).reset_index(drop=True)


def fit_per_class(synthesizer_factory, frame, label_column, classes=None):
    classes = (
        sorted(frame[label_column].unique().tolist()) if classes is None else list(classes)
    )
    models = {}
    for value in classes:
        subset = frame[frame[label_column] == value]
        if subset.empty:
            raise ValueError("no training rows for class %r" % value)
        model = synthesizer_factory()
        model.fit(subset)
        models[value] = model
    return models


def sample_per_class(models, label_column, total, *, seed=None):
    classes = list(models)
    per_class = total // len(classes)
    if per_class < 1:
        raise ValueError(
            "total=%d cannot be split across %d classes" % (total, len(classes))
        )
    frames = []
    for value, model in models.items():
        rows = model.sample(num_rows=per_class).copy()
        rows[label_column] = value
        frames.append(rows)
    out = pd.concat(frames, ignore_index=True)
    return out.sample(frac=1, random_state=seed).reset_index(drop=True)


def class_balance(frame, label_column):
    counts = frame[label_column].value_counts().sort_index()
    total = int(counts.sum())
    majority = float(counts.max()) / total if total else float("nan")
    ratio = float(counts.max()) / float(counts.min()) if counts.min() else float("inf")
    return {
        "counts": {int(k) if np.isreal(k) else k: int(v) for k, v in counts.items()},
        "n": total,
        "majority_fraction": majority,
        "imbalance_ratio": ratio,
    }
