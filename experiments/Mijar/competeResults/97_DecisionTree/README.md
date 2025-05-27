# Summary of 97_DecisionTree

[<< Go back](../README.md)


## Decision Tree
- **n_jobs**: -1
- **criterion**: gini
- **max_depth**: 3
- **explain_level**: 1

## Validation
 - **validation_type**: kfold
 - **shuffle**: True
 - **stratify**: True
 - **k_folds**: 10

## Optimized metric
logloss

## Training time

20.0 seconds

## Metric details
|           |      score |   threshold |
|:----------|-----------:|------------:|
| logloss   | 0.00550319 |         nan |
| auc       | 0.998744   |         nan |
| f1        | 0.998742   |           0 |
| accuracy  | 0.999655   |           0 |
| precision | 1          |           0 |
| recall    | 0.997487   |           0 |
| mcc       | 0.998543   |           0 |


## Metric details with threshold from accuracy metric
|           |      score |   threshold |
|:----------|-----------:|------------:|
| logloss   | 0.00550319 |         nan |
| auc       | 0.998744   |         nan |
| f1        | 0.998742   |           0 |
| accuracy  | 0.999655   |           0 |
| precision | 1          |           0 |
| recall    | 0.997487   |           0 |
| mcc       | 0.998543   |           0 |


## Confusion matrix (at threshold=0.0)
|              |   Predicted as 0 |   Predicted as 1 |
|:-------------|-----------------:|-----------------:|
| Labeled as 0 |             2499 |                0 |
| Labeled as 1 |                1 |              397 |

## Learning curves
![Learning curves](learning_curves.png)

## Decision Tree 

### Tree #1
![Tree 1](learner_fold_0_tree.svg)

### Rules

if (lat_y <= 362048272.0) and (c_variance_rad > 0.636) then class: 0 (proba: 100.0%) | based on 2,249 samples

if (lat_y > 362048272.0) then class: 1 (proba: 100.0%) | based on 347 samples

if (lat_y <= 362048272.0) and (c_variance_rad <= 0.636) then class: 1 (proba: 100.0%) | based on 11 samples




### Tree #2
![Tree 2](learner_fold_1_tree.svg)

### Rules

if (lat_y <= 362048272.0) and (c_variance_rad > 0.636) then class: 0 (proba: 100.0%) | based on 2,249 samples

if (lat_y > 362048272.0) then class: 1 (proba: 100.0%) | based on 348 samples

if (lat_y <= 362048272.0) and (c_variance_rad <= 0.636) then class: 1 (proba: 100.0%) | based on 10 samples




### Tree #3
![Tree 3](learner_fold_2_tree.svg)

### Rules

if (lat_y <= 362048272.0) and (c_variance_rad > 0.636) then class: 0 (proba: 100.0%) | based on 2,249 samples

if (lat_y > 362048272.0) then class: 1 (proba: 100.0%) | based on 347 samples

if (lat_y <= 362048272.0) and (c_variance_rad <= 0.636) then class: 1 (proba: 100.0%) | based on 11 samples




### Tree #4
![Tree 4](learner_fold_3_tree.svg)

### Rules

if (lat_y <= 362048272.0) and (c_variance_rad > 0.636) then class: 0 (proba: 100.0%) | based on 2,249 samples

if (lat_y > 362048272.0) then class: 1 (proba: 100.0%) | based on 348 samples

if (lat_y <= 362048272.0) and (c_variance_rad <= 0.636) then class: 1 (proba: 100.0%) | based on 10 samples




### Tree #5
![Tree 5](learner_fold_4_tree.svg)

### Rules

if (lat_y <= 362048272.0) and (c_variance_rad > 0.636) then class: 0 (proba: 100.0%) | based on 2,249 samples

if (lat_y > 362048272.0) then class: 1 (proba: 100.0%) | based on 349 samples

if (lat_y <= 362048272.0) and (c_variance_rad <= 0.636) then class: 1 (proba: 100.0%) | based on 9 samples




### Tree #6
![Tree 6](learner_fold_5_tree.svg)

### Rules

if (lat_y <= 362048272.0) and (c_variance_rad > 0.636) then class: 0 (proba: 100.0%) | based on 2,249 samples

if (lat_y > 362048272.0) then class: 1 (proba: 100.0%) | based on 346 samples

if (lat_y <= 362048272.0) and (c_variance_rad <= 0.636) then class: 1 (proba: 100.0%) | based on 12 samples




### Tree #7
![Tree 7](learner_fold_6_tree.svg)

### Rules

if (lat_y <= 362048272.0) and (hdop <= 0.876) then class: 0 (proba: 100.0%) | based on 2,249 samples

if (lat_y > 362048272.0) then class: 1 (proba: 100.0%) | based on 347 samples

if (lat_y <= 362048272.0) and (hdop > 0.876) then class: 1 (proba: 100.0%) | based on 11 samples




### Tree #8
![Tree 8](learner_fold_7_tree.svg)

### Rules

if (lat_y <= 362048272.0) and (c_variance_rad > 0.636) then class: 0 (proba: 100.0%) | based on 2,249 samples

if (lat_y > 362048272.0) then class: 1 (proba: 100.0%) | based on 349 samples

if (lat_y <= 362048272.0) and (c_variance_rad <= 0.636) then class: 1 (proba: 100.0%) | based on 10 samples




### Tree #9
![Tree 9](learner_fold_8_tree.svg)

### Rules

if (lat_y <= 362048272.0) and (c_variance_rad > 0.636) then class: 0 (proba: 100.0%) | based on 2,249 samples

if (lat_y > 362048272.0) then class: 1 (proba: 100.0%) | based on 347 samples

if (lat_y <= 362048272.0) and (c_variance_rad <= 0.636) then class: 1 (proba: 100.0%) | based on 12 samples




### Tree #10
![Tree 10](learner_fold_9_tree.svg)

### Rules

if (lat_y <= 362048272.0) and (c_variance_rad > 0.636) then class: 0 (proba: 100.0%) | based on 2,250 samples

if (lat_y > 362048272.0) then class: 1 (proba: 100.0%) | based on 346 samples

if (lat_y <= 362048272.0) and (c_variance_rad <= 0.636) then class: 1 (proba: 100.0%) | based on 12 samples





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
