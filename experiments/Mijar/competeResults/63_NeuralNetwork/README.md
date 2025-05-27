# Summary of 63_NeuralNetwork

[<< Go back](../README.md)


## Neural Network
- **n_jobs**: -1
- **dense_1_size**: 64
- **dense_2_size**: 16
- **learning_rate**: 0.1
- **explain_level**: 1

## Validation
 - **validation_type**: kfold
 - **shuffle**: True
 - **stratify**: True
 - **k_folds**: 10

## Optimized metric
logloss

## Training time

13.3 seconds

## Metric details
|           |     score |     threshold |
|:----------|----------:|--------------:|
| logloss   | 0.0125732 | nan           |
| auc       | 0.999707  | nan           |
| f1        | 0.985037  |   0.0381082   |
| accuracy  | 0.995858  |   0.0381082   |
| precision | 0.977723  |   0.0381082   |
| recall    | 1         |   1.18067e-93 |
| mcc       | 0.982671  |   0.0381082   |


## Metric details with threshold from accuracy metric
|           |     score |   threshold |
|:----------|----------:|------------:|
| logloss   | 0.0125732 | nan         |
| auc       | 0.999707  | nan         |
| f1        | 0.985037  |   0.0381082 |
| accuracy  | 0.995858  |   0.0381082 |
| precision | 0.977723  |   0.0381082 |
| recall    | 0.992462  |   0.0381082 |
| mcc       | 0.982671  |   0.0381082 |


## Confusion matrix (at threshold=0.038108)
|              |   Predicted as 0 |   Predicted as 1 |
|:-------------|-----------------:|-----------------:|
| Labeled as 0 |             2490 |                9 |
| Labeled as 1 |                3 |              395 |

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
