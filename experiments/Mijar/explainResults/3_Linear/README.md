# Summary of 3_Linear

[<< Go back](../README.md)


## Logistic Regression (Linear)
- **n_jobs**: -1
- **explain_level**: 2

## Validation
 - **validation_type**: split
 - **train_ratio**: 0.75
 - **shuffle**: True
 - **stratify**: True

## Optimized metric
logloss

## Training time

4.9 seconds

## Metric details
|           |      score |     threshold |
|:----------|-----------:|--------------:|
| logloss   | 0.00506247 | nan           |
| auc       | 1          | nan           |
| f1        | 0.987854   |   0.872702    |
| accuracy  | 0.996689   |   0.872702    |
| precision | 1          |   0.872702    |
| recall    | 1          |   6.07993e-06 |
| mcc       | 0.986035   |   0.872702    |


## Metric details with threshold from accuracy metric
|           |      score |   threshold |
|:----------|-----------:|------------:|
| logloss   | 0.00506247 |  nan        |
| auc       | 1          |  nan        |
| f1        | 0.987854   |    0.872702 |
| accuracy  | 0.996689   |    0.872702 |
| precision | 1          |    0.872702 |
| recall    | 0.976      |    0.872702 |
| mcc       | 0.986035   |    0.872702 |


## Confusion matrix (at threshold=0.872702)
|              |   Predicted as 0 |   Predicted as 1 |
|:-------------|-----------------:|-----------------:|
| Labeled as 0 |              781 |                0 |
| Labeled as 1 |                3 |              122 |

## Learning curves
![Learning curves](learning_curves.png)

## Coefficients
| feature           |   Learner_1 |
|:------------------|------------:|
| vdop              |  1.69925    |
| hdop              |  1.2268     |
| lat_y             |  1.15153    |
| lat_x             |  0.928524   |
| x                 |  0.928331   |
| jamming_indicator |  0.900153   |
| s_variance_m_s    |  0.81073    |
| vel_n_m_s         |  0.786786   |
| q_0_              |  0.746068   |
| vel_m_s           |  0.610793   |
| alt_y             |  0.566766   |
| alt_ellipsoid_y   |  0.566476   |
| eph_x             |  0.514049   |
| dist_bottom       |  0.326042   |
| ay                |  0.301269   |
| alt_x             |  0.285956   |
| heading_y         |  0.251552   |
| eph               |  0.224376   |
| epv_x             |  0.181068   |
| z                 |  0.16591    |
| noise_per_ms      |  0.155376   |
| eph_y             |  0.0749973  |
| vy                |  0.063827   |
| alt_ellipsoid_x   |  0.0505181  |
| terrain_alt       |  0.0160511  |
| q_1_              |  0.00257944 |
| q_2_              | -0.00897288 |
| vx                | -0.00919371 |
| epv_y             | -0.047426   |
| lon_x             | -0.0494589  |
| vel_d_m_s         | -0.0974719  |
| terrain_alt_valid | -0.0982608  |
| dist_bottom_valid | -0.0992946  |
| xy_valid          | -0.122941   |
| v_xy_valid        | -0.122941   |
| z_deriv           | -0.147946   |
| evv               | -0.175863   |
| vel_e_m_s         | -0.321394   |
| lon_y             | -0.324409   |
| evh               | -0.369321   |
| az                | -0.371633   |
| vz                | -0.407474   |
| ax                | -0.666298   |
| q_3_              | -0.688316   |
| y                 | -0.709508   |
| cog_rad           | -0.7907     |
| epv               | -0.809123   |
| c_variance_rad    | -0.888094   |
| satellites_used   | -1.83019    |
| intercept         | -3.30977    |


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



## SHAP Importance
![SHAP Importance](shap_importance.png)

## SHAP Dependence plots

### Dependence (Fold 1)
![SHAP Dependence from Fold 1](learner_fold_0_shap_dependence.png)

## SHAP Decision plots

### Top-10 Worst decisions for class 0 (Fold 1)
![SHAP worst decisions class 0 from Fold 1](learner_fold_0_shap_class_0_worst_decisions.png)
### Top-10 Best decisions for class 0 (Fold 1)
![SHAP best decisions class 0 from Fold 1](learner_fold_0_shap_class_0_best_decisions.png)
### Top-10 Worst decisions for class 1 (Fold 1)
![SHAP worst decisions class 1 from Fold 1](learner_fold_0_shap_class_1_worst_decisions.png)
### Top-10 Best decisions for class 1 (Fold 1)
![SHAP best decisions class 1 from Fold 1](learner_fold_0_shap_class_1_best_decisions.png)

[<< Go back](../README.md)
