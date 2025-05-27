# Summary of 49_ExtraTrees_KMeansFeatures

[<< Go back](../README.md)


## Extra Trees Classifier (Extra Trees)
- **n_jobs**: -1
- **criterion**: entropy
- **max_features**: 0.9
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

22.4 seconds

## Metric details
|           |       score |   threshold |
|:----------|------------:|------------:|
| logloss   | 0.000680048 | nan         |
| auc       | 1           | nan         |
| f1        | 0.992519    |   0.0119984 |
| accuracy  | 0.997929    |   0.0119984 |
| precision | 0.985149    |   0.0119984 |
| recall    | 1           |   0         |
| mcc       | 0.991354    |   0.0119984 |


## Metric details with threshold from accuracy metric
|           |       score |   threshold |
|:----------|------------:|------------:|
| logloss   | 0.000680048 | nan         |
| auc       | 1           | nan         |
| f1        | 0.992519    |   0.0119984 |
| accuracy  | 0.997929    |   0.0119984 |
| precision | 0.985149    |   0.0119984 |
| recall    | 1           |   0.0119984 |
| mcc       | 0.991354    |   0.0119984 |


## Confusion matrix (at threshold=0.011998)
|              |   Predicted as 0 |   Predicted as 1 |
|:-------------|-----------------:|-----------------:|
| Labeled as 0 |             2493 |                6 |
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
