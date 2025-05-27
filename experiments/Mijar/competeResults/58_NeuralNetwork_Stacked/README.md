# Summary of 58_NeuralNetwork_Stacked

[<< Go back](../README.md)


## Neural Network
- **n_jobs**: -1
- **dense_1_size**: 64
- **dense_2_size**: 4
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

26.6 seconds

## Metric details
|           |      score |     threshold |
|:----------|-----------:|--------------:|
| logloss   | 0.00550319 | nan           |
| auc       | 1          | nan           |
| f1        | 0.992519   |   4.18543e-12 |
| accuracy  | 0.997929   |   4.18543e-12 |
| precision | 0.985149   |   4.18543e-12 |
| recall    | 1          |   5.01252e-41 |
| mcc       | 0.991354   |   4.18543e-12 |


## Metric details with threshold from accuracy metric
|           |      score |     threshold |
|:----------|-----------:|--------------:|
| logloss   | 0.00550319 | nan           |
| auc       | 1          | nan           |
| f1        | 0.992519   |   4.18543e-12 |
| accuracy  | 0.997929   |   4.18543e-12 |
| precision | 0.985149   |   4.18543e-12 |
| recall    | 1          |   4.18543e-12 |
| mcc       | 0.991354   |   4.18543e-12 |


## Confusion matrix (at threshold=0.0)
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
