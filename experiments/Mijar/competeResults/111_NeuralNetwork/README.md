# Summary of 111_NeuralNetwork

[<< Go back](../README.md)


## Neural Network
- **n_jobs**: -1
- **dense_1_size**: 64
- **dense_2_size**: 16
- **learning_rate**: 0.01
- **explain_level**: 1

## Validation
 - **validation_type**: kfold
 - **shuffle**: True
 - **stratify**: True
 - **k_folds**: 10

## Optimized metric
logloss

## Training time

17.3 seconds

## Metric details
|           |      score |     threshold |
|:----------|-----------:|--------------:|
| logloss   | 0.00582897 | nan           |
| auc       | 0.999865   | nan           |
| f1        | 0.987531   |   0.0459464   |
| accuracy  | 0.996548   |   0.0459464   |
| precision | 1          |   0.999664    |
| recall    | 1          |   7.27404e-09 |
| mcc       | 0.985565   |   0.0459464   |


## Metric details with threshold from accuracy metric
|           |      score |   threshold |
|:----------|-----------:|------------:|
| logloss   | 0.00582897 | nan         |
| auc       | 0.999865   | nan         |
| f1        | 0.987531   |   0.0459464 |
| accuracy  | 0.996548   |   0.0459464 |
| precision | 0.980198   |   0.0459464 |
| recall    | 0.994975   |   0.0459464 |
| mcc       | 0.985565   |   0.0459464 |


## Confusion matrix (at threshold=0.045946)
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
