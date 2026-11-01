import numpy as np
import pandas as pd

MAX_TOPUP_BATCHES = 24
TOPUP_BATCH_MULTIPLIER = 4


class UnbalancedSynthetic(RuntimeError):
    pass


def _rows_for(frame, label_column, value):
    column = frame[label_column]
    if column.dtype == object or str(column.dtype) == "category":
        return frame[column.astype(str) == str(value)]
    return frame[column == value]


def _conditioned(synthesizer, label_column, classes, per_class):
    from sdv.sampling import Condition

    conditions = [
        Condition(num_rows=per_class, column_values={label_column: value})
        for value in classes
    ]
    try:
        return synthesizer.sample_from_conditions(conditions=conditions)
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
    batch_multiplier=TOPUP_BATCH_MULTIPLIER,
):
    classes = list(classes)
    if not classes:
        raise ValueError("no classes to balance over")
    per_class = total // len(classes)
    if per_class < 1:
        raise ValueError(
            "total=%d cannot be split across %d classes" % (total, len(classes))
        )

    kept = {}
    pooled = _conditioned(synthesizer, label_column, classes, per_class)
    for value in classes:
        rows = _rows_for(pooled, label_column, value) if pooled is not None else None
        kept[value] = (
            rows.iloc[:per_class] if rows is not None else pd.DataFrame(columns=None)
        )

    batches = 0
    while any(len(kept[value]) < per_class for value in classes):
        if batches >= max_batches:
            short = {
                value: len(kept[value])
                for value in classes
                if len(kept[value]) < per_class
            }
            raise UnbalancedSynthetic(
                "could not reach %d rows per class after %d top-up batches; "
                "short classes (have/need): %s. The generator does not produce "
                "these classes often enough to balance by sampling."
                % (per_class, batches, {k: "%d/%d" % (v, per_class) for k, v in short.items()})
            )
        extra = synthesizer.sample(num_rows=per_class * batch_multiplier)
        for value in classes:
            if len(kept[value]) < per_class:
                rows = _rows_for(extra, label_column, value)
                if len(rows):
                    current = kept[value]
                    merged = rows if not len(current) else pd.concat([current, rows])
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
