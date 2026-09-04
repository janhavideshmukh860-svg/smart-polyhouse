# SMART POLYHOUSE — MASTER AUTHENTIC ML DATASET GUIDE

## IMPORTANT DATA AUTHENTICITY RULE

This project contains carefully prepared authentic datasets for machine learning model training.

The datasets were collected from real publicly available agricultural datasets and were manually audited, cleaned, structured, deduplicated, and split for safe machine learning training.

DO NOT generate synthetic training samples.

DO NOT replace the provided datasets with sample datasets.

DO NOT download alternative datasets unless explicitly required by project instructions.

DO NOT modify the train, validation, or test assignments.

DO NOT merge the train, validation, and test datasets.

All machine learning models must use the provided authentic datasets.

---

# PROJECT MACHINE LEARNING COMPONENTS

The Smart Polyhouse system contains three primary machine learning components.

## MODEL 1 — PLANT DISEASE DETECTION

Task:

Image classification

Purpose:

Detect plant diseases from uploaded plant leaf images.

Dataset:

Smart Polyhouse Disease Detection Dataset

Total images:

56,501

Total classes:

38

Total crops:

14

Dataset sources:

- PlantVillage
- PlantDoc

Training split:

39,550 images

Validation split:

8,475 images

Test split:

8,476 images

Split strategy:

Stratified by disease class

Duplicate protection:

SHA-256 duplicate detection

Split leakage:

Verified safe

---

# DISEASE DATASET FILES

Main configuration:

05_metadata/disease_dataset_config.json

Dataset documentation:

05_metadata/DISEASE_DATASET_CARD.md

Canonical manifest:

05_metadata/disease_canonical_manifest.csv

Training manifest:

05_metadata/disease_train_manifest.csv

Validation manifest:

05_metadata/disease_validation_manifest.csv

Test manifest:

05_metadata/disease_test_manifest.csv

Class mapping:

05_metadata/disease_class_mapping.csv

Important:

The image files remain in the original dataset directories.

The manifests contain the image paths and final class labels.

The backend training pipeline must load images using the provided manifests.

Do not randomly re-split the dataset.

---

# DISEASE MODEL TRAINING REQUIREMENTS

Recommended workflow:

1. Load training images using disease_train_manifest.csv.
2. Load validation images using disease_validation_manifest.csv.
3. Load test images only for final evaluation.
4. Use final_class as the classification target.
5. Preserve the 38 provided disease classes.
6. Do not remove classes without justification.
7. Use validation data for model selection.
8. Do not use test data during training.
9. Save the trained model.
10. Save the class-to-index mapping.
11. Report final test metrics.

Recommended metrics:

- Accuracy
- Precision
- Recall
- F1 Score
- Confusion Matrix
- Per-class accuracy

---

# MODEL 2 — SOIL MOISTURE CALIBRATION

Task:

Regression

Purpose:

Convert raw low-cost soil sensor readings into calibrated volumetric soil moisture percentage.

Dataset source:

EcoIrrigate

Total records:

21,312

Farms:

2

Sampling interval:

15 minutes

Target variable:

Volumetric_Moisture_Pct

---

# CALIBRATION DATASET FILES

Processed dataset:

03_processed/irrigation/soil_moisture_calibration_dataset.csv

Training split:

05_metadata/irrigation_calibration_train.csv

Validation split:

05_metadata/irrigation_calibration_validation.csv

Test split:

05_metadata/irrigation_calibration_test.csv

Configuration:

05_metadata/irrigation_dataset_config.json

Documentation:

05_metadata/IRRIGATION_DATASET_CARD.md

---

# CALIBRATION MODEL TRAINING REQUIREMENTS

Use the provided chronological splits.

Do not randomly shuffle the dataset before splitting.

Do not merge train, validation, and test datasets.

Use:

Training data:

irrigation_calibration_train.csv

Validation data:

irrigation_calibration_validation.csv

Test data:

irrigation_calibration_test.csv

Target:

Volumetric_Moisture_Pct

Recommended evaluation metrics:

- MAE
- RMSE
- R²

The final model must be evaluated on the untouched test dataset.

---

# MODEL 3 — SOIL MOISTURE FORECASTING

Task:

Multi-horizon time-series forecasting

Purpose:

Predict future soil moisture levels.

Dataset source:

EcoIrrigate

Total records:

21,120

Sampling interval:

15 minutes

Farms:

2

Forecast horizons:

- 1 hour
- 6 hours
- 12 hours
- 24 hours

---

# FORECASTING DATASET FILES

Processed dataset:

03_processed/irrigation/soil_moisture_forecasting_dataset.csv

Training split:

05_metadata/irrigation_forecasting_train.csv

Validation split:

05_metadata/irrigation_forecasting_validation.csv

Test split:

05_metadata/irrigation_forecasting_test.csv

Configuration:

05_metadata/irrigation_dataset_config.json

Documentation:

05_metadata/IRRIGATION_DATASET_CARD.md

---

# FORECASTING TARGET VARIABLES

The forecasting model must predict:

target_moisture_1h

target_moisture_6h

target_moisture_12h

target_moisture_24h

The dataset was prepared using:

1 hour = 4 time steps

6 hours = 24 time steps

12 hours = 48 time steps

24 hours = 96 time steps

Sampling interval:

15 minutes

---

# FORECASTING MODEL TRAINING REQUIREMENTS

The model must preserve chronological ordering.

Random shuffling must not be used across time.

The training pipeline should create historical sequences only within the boundaries of each split.

Sequences must not accidentally use future observations.

Sequences must not cross farm boundaries.

Recommended sequence length:

24 hours of history

At 15-minute intervals:

96 historical time steps

Recommended evaluation metrics:

- MAE
- RMSE
- R²

Metrics should be reported separately for:

- 1 hour
- 6 hours
- 12 hours
- 24 hours

---

# STRICT DATA LEAKAGE RULES

The following are prohibited:

- Training on test data
- Using future observations to predict past observations
- Mixing records from train and test splits
- Randomly shuffling time-series data before splitting
- Creating sequences that cross farm boundaries
- Using future timestamps as model inputs
- Fitting scalers on validation or test datasets

Feature scaling must be performed as follows:

1. Fit scaler only on training data.
2. Transform validation data using the training scaler.
3. Transform test data using the training scaler.

---

# DATA AUTHENTICITY REQUIREMENTS

The provided datasets are the authoritative datasets for this project.

The backend must not:

- Generate synthetic sensor data for model training.
- Generate fake disease images for model training.
- Replace missing classes with generated examples.
- Download unrelated datasets.
- Silently modify labels.
- Randomly reshuffle the prepared splits.

Data augmentation may be used only during disease model training and only on training images.

Validation and test images must not be augmented.

---

# REQUIRED TRAINING OUTPUTS

After training, save:

## Disease Model

- Trained model file
- Class mapping
- Training history
- Test metrics
- Confusion matrix

## Calibration Model

- Trained model file
- Feature list
- Scaler
- Validation metrics
- Final test metrics

## Forecasting Model

- Trained model file
- Feature list
- Sequence configuration
- Scaler
- Validation metrics
- Final test metrics for each forecast horizon

---

# MODEL REPRODUCIBILITY

All training scripts should:

- Set random seeds
- Save configuration files
- Log training parameters
- Save model versions
- Record dataset file paths
- Record evaluation metrics

---

# FINAL PROJECT RULE

This Smart Polyhouse backend must be built around the authentic datasets contained in this repository.

The datasets must be treated as the source of truth.

Demo data may be used only for frontend demonstration when no real sensor input is available.

Demo data must never be mixed with model training data.

All production machine learning models must be trained using the provided authentic datasets.

---

# DATASET STATUS

Plant Disease Detection Dataset:

READY FOR ML TRAINING

Soil Moisture Calibration Dataset:

READY FOR ML TRAINING

Soil Moisture Forecasting Dataset:

READY FOR ML TRAINING

All datasets have passed:

- Integrity checks
- Duplicate checks
- Leakage checks
- Split consistency checks
- Chronological consistency checks
- Missing value checks
- Configuration validation
- Final reproducibility audits

FINAL STATUS:

AUTHENTIC ML DATA PACKAGE READY FOR BACKEND DEVELOPMENT