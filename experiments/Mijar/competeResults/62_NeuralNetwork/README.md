# Summary of 62_NeuralNetwork

[<< Go back](../README.md)


## Neural Network
- **n_jobs**: -1
- **dense_1_size**: 64
- **dense_2_size**: 8
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

12.6 seconds

## Metric details
|           |     score |     threshold |
|:----------|----------:|--------------:|
| logloss   | 0.0126502 | nan           |
| auc       | 0.999881  | nan           |
| f1        | 0.987531  |   0.00142514  |
| accuracy  | 0.996548  |   0.00142514  |
| precision | 0.980198  |   0.00142514  |
| recall    | 1         |   2.53921e-68 |
| mcc       | 0.985565  |   0.00142514  |


## Metric details with threshold from accuracy metric
|           |     score |    threshold |
|:----------|----------:|-------------:|
| logloss   | 0.0126502 | nan          |
| auc       | 0.999881  | nan          |
| f1        | 0.987531  |   0.00142514 |
| accuracy  | 0.996548  |   0.00142514 |
| precision | 0.980198  |   0.00142514 |
| recall    | 0.994975  |   0.00142514 |
| mcc       | 0.985565  |   0.00142514 |


## Confusion matrix (at threshold=0.001425)
|              |   Predicted as 0 |   Predicted as 1 |
|:-------------|-----------------:|-----------------:|
| Labeled as 0 |             2491 |                8 |
| Labeled as 1 |                2 |              396 |

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
