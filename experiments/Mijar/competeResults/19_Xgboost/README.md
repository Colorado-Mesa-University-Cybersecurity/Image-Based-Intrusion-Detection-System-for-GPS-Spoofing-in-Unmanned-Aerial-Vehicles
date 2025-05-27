# Summary of 19_Xgboost

[<< Go back](../README.md)


## Extreme Gradient Boosting (Xgboost)
- **n_jobs**: -1
- **objective**: binary:logistic
- **eta**: 0.075
- **max_depth**: 4
- **min_child_weight**: 5
- **subsample**: 0.6
- **colsample_bytree**: 0.5
- **eval_metric**: logloss
- **explain_level**: 1

## Validation
 - **validation_type**: kfold
 - **shuffle**: True
 - **stratify**: True
 - **k_folds**: 10

## Optimized metric
logloss

## Training time

13.4 seconds

## Metric details
|           |      score |    threshold |
|:----------|-----------:|-------------:|
| logloss   | 0.00808756 | nan          |
| auc       | 0.999992   | nan          |
| f1        | 0.990025   |   0.0264383  |
| accuracy  | 0.997239   |   0.0264383  |
| precision | 1          |   0.970908   |
| recall    | 1          |   0.00132326 |
| mcc       | 0.98846    |   0.0264383  |


## Metric details with threshold from accuracy metric
|           |      score |   threshold |
|:----------|-----------:|------------:|
| logloss   | 0.00808756 | nan         |
| auc       | 0.999992   | nan         |
| f1        | 0.990025   |   0.0264383 |
| accuracy  | 0.997239   |   0.0264383 |
| precision | 0.982673   |   0.0264383 |
| recall    | 0.997487   |   0.0264383 |
| mcc       | 0.98846    |   0.0264383 |


## Confusion matrix (at threshold=0.026438)
|              |   Predicted as 0 |   Predicted as 1 |
|:-------------|-----------------:|-----------------:|
| Labeled as 0 |             2492 |                7 |
| Labeled as 1 |                1 |              397 |

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
