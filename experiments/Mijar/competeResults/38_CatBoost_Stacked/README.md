# Summary of 38_CatBoost_Stacked

[<< Go back](../README.md)


## CatBoost
- **n_jobs**: -1
- **learning_rate**: 0.1
- **depth**: 7
- **rsm**: 0.9
- **loss_function**: Logloss
- **eval_metric**: Logloss
- **explain_level**: 1

## Validation
 - **validation_type**: kfold
 - **shuffle**: True
 - **stratify**: True
 - **k_folds**: 10

## Optimized metric
logloss

## Training time

1044.1 seconds

## Metric details
|           |       score |     threshold |
|:----------|------------:|--------------:|
| logloss   | 0.000724811 | nan           |
| auc       | 1           | nan           |
| f1        | 0.992519    |   0.00127891  |
| accuracy  | 0.997929    |   0.00127891  |
| precision | 1           |   0.997783    |
| recall    | 1           |   2.34124e-06 |
| mcc       | 0.991354    |   0.00127891  |


## Metric details with threshold from accuracy metric
|           |       score |    threshold |
|:----------|------------:|-------------:|
| logloss   | 0.000724811 | nan          |
| auc       | 1           | nan          |
| f1        | 0.992519    |   0.00127891 |
| accuracy  | 0.997929    |   0.00127891 |
| precision | 0.985149    |   0.00127891 |
| recall    | 1           |   0.00127891 |
| mcc       | 0.991354    |   0.00127891 |


## Confusion matrix (at threshold=0.001279)
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
