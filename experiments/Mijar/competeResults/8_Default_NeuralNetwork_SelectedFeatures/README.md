# Summary of 8_Default_NeuralNetwork_SelectedFeatures

[<< Go back](../README.md)


## Neural Network
- **n_jobs**: -1
- **dense_1_size**: 32
- **dense_2_size**: 16
- **learning_rate**: 0.05
- **explain_level**: 1

## Validation
 - **validation_type**: kfold
 - **shuffle**: True
 - **stratify**: True
 - **k_folds**: 10

## Optimized metric
logloss

## Training time

13.5 seconds

## Metric details
|           |     score |     threshold |
|:----------|----------:|--------------:|
| logloss   | 0.0197555 | nan           |
| auc       | 0.999771  | nan           |
| f1        | 0.982544  |   0.00451836  |
| accuracy  | 0.995167  |   0.00451836  |
| precision | 1         |   0.999965    |
| recall    | 1         |   1.31258e-30 |
| mcc       | 0.979776  |   0.00451836  |


## Metric details with threshold from accuracy metric
|           |     score |    threshold |
|:----------|----------:|-------------:|
| logloss   | 0.0197555 | nan          |
| auc       | 0.999771  | nan          |
| f1        | 0.982544  |   0.00451836 |
| accuracy  | 0.995167  |   0.00451836 |
| precision | 0.975248  |   0.00451836 |
| recall    | 0.98995   |   0.00451836 |
| mcc       | 0.979776  |   0.00451836 |


## Confusion matrix (at threshold=0.004518)
|              |   Predicted as 0 |   Predicted as 1 |
|:-------------|-----------------:|-----------------:|
| Labeled as 0 |             2489 |               10 |
| Labeled as 1 |                4 |              394 |

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
