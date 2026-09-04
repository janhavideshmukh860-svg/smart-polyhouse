# Smart Polyhouse Irrigation ML Dataset Card

## 1. Dataset Overview

This dataset supports two machine learning tasks for the Smart Polyhouse system:

1. Soil moisture sensor calibration
2. Multi-horizon soil moisture forecasting

The dataset is derived from the authentic EcoIrrigate dataset collected from two real farm environments in Kolkata, India.

The dataset has been processed, validated, split chronologically, and audited for machine learning use.

---

# 2. Source Dataset

Source Dataset: EcoIrrigate

Dataset Type:
Real IoT soil moisture and environmental sensor time-series data.

Farm Locations:
- Kolkata_Farm_1
- Kolkata_Farm_2

Sampling Interval:
15 minutes

Original Records:
21,312

Time Range:
January 5, 2025 to April 25, 2025

---

# 3. Dataset Tasks

## Task A: Soil Moisture Calibration

Objective:

Train a regression model that predicts accurate volumetric soil moisture percentage using raw low-cost sensor readings and environmental conditions.

Target Variable:

Volumetric_Moisture_Pct

Input features include:

- Raw_Capacitive_ADC
- Sensor_Voltage_V
- Sensor_Board_Temperature_C
- Atm_Pressure_inHg
- Atm_Temperature_C
- Soil_Temperature_C
- Hour
- Day
- Month
- DayOfWeek
- DayOfYear
- Hour_sin
- Hour_cos
- Day_sin
- Day_cos

Dataset splits:

- Training: 14,918 records
- Validation: 3,196 records
- Testing: 3,198 records

Total:

21,312 records

---

# 4. Task B: Multi-Horizon Soil Moisture Forecasting

Objective:

Predict future volumetric soil moisture using historical sensor and environmental observations.

Forecast Horizons:

- 1 hour
- 6 hours
- 12 hours
- 24 hours

Target Variables:

- target_moisture_1h
- target_moisture_6h
- target_moisture_12h
- target_moisture_24h

Dataset splits:

- Training: 14,782 records
- Validation: 3,170 records
- Testing: 3,168 records

Total:

21,120 records

---

# 5. Chronological Split Strategy

IMPORTANT:

This dataset uses chronological time-series splitting.

The data must NOT be randomly shuffled.

For each farm:

Training data contains the earliest observations.

Validation data contains observations occurring after the training period.

Test data contains the latest observations.

This prevents future information from leaking into model training.

Split ratio:

- Training: approximately 70%
- Validation: approximately 15%
- Testing: approximately 15%

---

# 6. Data Integrity

The following checks were completed successfully:

- Missing value check: PASSED
- Duplicate row check: PASSED
- Duplicate Farm_ID + Timestamp check: PASSED
- Cross-split leakage check: PASSED
- Chronological order check: PASSED
- Farm coverage check: PASSED
- Forecast target completeness check: PASSED
- Configuration consistency check: PASSED

Final dataset audit result:

ALL FINAL IRRIGATION DATASET AUDIT CHECKS: PASSED

---

# 7. Training Rules

Any machine learning system using this dataset must follow these rules:

1. Use only the provided training split for model fitting.

2. Use the validation split only for hyperparameter tuning and model selection.

3. Use the test split only for final model evaluation.

4. Do not randomly shuffle the complete dataset before splitting.

5. Do not combine training, validation, and test datasets.

6. Do not use future observations to predict past observations.

7. Preserve Farm_ID and chronological ordering during time-series processing.

8. Do not generate synthetic sensor data for model training.

9. Report actual evaluation metrics obtained from the provided test dataset.

---

# 8. Recommended Model Outputs

## Calibration Model

Input:

Raw sensor readings and environmental variables.

Output:

Predicted Volumetric_Moisture_Pct.

Recommended evaluation metrics:

- MAE
- RMSE
- R² Score

---

## Forecasting Model

Input:

Current and historical sensor/environmental observations.

Output:

Predicted soil moisture for:

- 1 hour
- 6 hours
- 12 hours
- 24 hours

Recommended evaluation metrics:

- MAE
- RMSE
- R² Score

Metrics should ideally be reported separately for each forecast horizon.

---

# 9. Authenticity and Reproducibility

This dataset package was created from the EcoIrrigate source dataset and processed through a reproducible dataset preparation pipeline.

The preparation pipeline included:

- Initial integrity inspection
- Time interval verification
- Missing value checks
- Duplicate checks
- Calibration dataset preparation
- Multi-horizon target creation
- Chronological dataset splitting
- Leakage verification
- Configuration validation
- Final reproducibility audit

The original source data was preserved and was not modified during final package assembly.

---

# 10. Intended Usage

This dataset is intended for:

- Smart irrigation systems
- Soil moisture calibration
- Soil moisture forecasting
- IoT agriculture applications
- Precision agriculture research
- Smart polyhouse decision support systems

This dataset should be used only according to the provided train, validation, and test split definitions.