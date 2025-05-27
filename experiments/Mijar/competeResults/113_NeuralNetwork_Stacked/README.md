# Summary of 113_NeuralNetwork_Stacked

[<< Go back](../README.md)


## Neural Network
- **n_jobs**: -1
- **dense_1_size**: 32
- **dense_2_size**: 16
- **learning_rate**: 0.08
- **explain_level**: 1

## Validation
 - **validation_type**: kfold
 - **shuffle**: True
 - **stratify**: True
 - **k_folds**: 10

## Optimized metric
logloss

## Training time

26.1 seconds

## Metric details
|           |       score |     threshold |
|:----------|------------:|--------------:|
| logloss   | 7.48647e-06 | nan           |
| auc       | 1           | nan           |
| f1        | 0.992519    |   0.00119856  |
| accuracy  | 0.997929    |   0.00119856  |
| precision | 0.985149    |   0.00119856  |
| recall    | 1           |   1.12853e-45 |
| mcc       | 0.991354    |   0.00119856  |


## Metric details with threshold from accuracy metric
|           |       score |    threshold |
|:----------|------------:|-------------:|
| logloss   | 7.48647e-06 | nan          |
| auc       | 1           | nan          |
| f1        | 0.992519    |   0.00119856 |
| accuracy  | 0.997929    |   0.00119856 |
| precision | 0.985149    |   0.00119856 |
| recall    | 1           |   0.00119856 |
| mcc       | 0.991354    |   0.00119856 |


## Confusion matrix (at threshold=0.001199)
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
