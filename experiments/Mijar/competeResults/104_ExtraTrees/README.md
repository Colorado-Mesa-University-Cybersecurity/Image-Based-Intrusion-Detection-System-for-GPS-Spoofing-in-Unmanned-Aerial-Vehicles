# Summary of 104_ExtraTrees

[<< Go back](../README.md)


## Extra Trees Classifier (Extra Trees)
- **n_jobs**: -1
- **criterion**: gini
- **max_features**: 0.6
- **min_samples_split**: 40
- **max_depth**: 6
- **eval_metric_name**: logloss
- **explain_level**: 1

## Validation
 - **validation_type**: kfold
 - **shuffle**: True
 - **stratify**: True
 - **k_folds**: 10

## Optimized metric
logloss

## Training time

24.0 seconds

## Metric details
|           |       score |   threshold |
|:----------|------------:|------------:|
| logloss   | 0.000575971 | nan         |
| auc       | 1           | nan         |
| f1        | 0.993758    |   0.0322581 |
| accuracy  | 0.998274    |   0.0322581 |
| precision | 0.987593    |   0.0322581 |
| recall    | 1           |   0         |
| mcc       | 0.992782    |   0.0322581 |


## Metric details with threshold from accuracy metric
|           |       score |   threshold |
|:----------|------------:|------------:|
| logloss   | 0.000575971 | nan         |
| auc       | 1           | nan         |
| f1        | 0.993758    |   0.0322581 |
| accuracy  | 0.998274    |   0.0322581 |
| precision | 0.987593    |   0.0322581 |
| recall    | 1           |   0.0322581 |
| mcc       | 0.992782    |   0.0322581 |


## Confusion matrix (at threshold=0.032258)
|              |   Predicted as 0 |   Predicted as 1 |
|:-------------|-----------------:|-----------------:|
| Labeled as 0 |             2494 |                5 |
| Labeled as 1 |                0 |              398 |

## Learning curves
![Learning curves](learning_curves.png)

## Permutation-based Importance
![Permutation-based Importance](permutation_importance.png)
## Confusion Matrix

![Confusion Matrix](confusion_matrix.png)


## Normalized Confusion Matrix

![Normalized Confusion Matrix](confusion_matrix_normalized.png)


## ROC Curve

![ROC Curve](roc_curve.png)


## Kolmogorov-Smirnov Statistic

![Kolmogorov-Smirnov Statistic](ks_statistic.png)


## Precision-Recall Curve

![Precision-Recall Curve](precision_recall_curve.png)


## Calibration Curve

![Calibration Curve](calibration_curve_curve.png)


## Cumulative Gains Curve

![Cumulative Gains Curve](cumulative_gains_curve.png)


## Lift Curve

![Lift Curve](lift_curve.png)



[<< Go back](../README.md)
