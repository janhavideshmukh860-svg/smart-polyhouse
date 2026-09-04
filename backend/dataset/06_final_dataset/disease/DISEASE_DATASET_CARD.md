# Disease Detection Dataset Card

## Dataset Purpose

This dataset is prepared for training and evaluating a plant disease image classification model for a Smart Polyhouse system.

The dataset must be treated as the authoritative dataset for disease detection model development.

Only the image files and manifests included in this dataset package should be used for training, validation, and testing unless explicitly approved later.

---

# Dataset Sources

The dataset combines two authentic public plant disease image datasets:

1. PlantVillage Color Dataset
2. PlantDoc Dataset

The datasets were consolidated into a unified canonical label structure.

No synthetic images were generated during dataset preparation.

---

# Dataset Statistics

Total valid images: 56,501

Total disease/health classes: 38

Total crop categories: 14

Dataset sources:

- PlantVillage Color: 54,238 original records before duplicate cleanup
- PlantDoc: 2,296 original records before duplicate cleanup

Duplicate images were identified using SHA-256 hashes and removed before the final split generation.

---

# Final Dataset Split

The dataset uses a leakage-safe stratified split.

| Split | Images | Percentage |
|---|---:|---:|
| Train | 39,550 | 70% |
| Validation | 8,475 | 15% |
| Test | 8,476 | 15% |
| Total | 56,501 | 100% |

Random seed: 42

Split strategy: Stratified by `final_class`.

Duplicate SHA-256 hashes do not overlap across train, validation, or test sets.

---

# Important Training Rules

The following rules are mandatory:

1. Train the model only using the images listed in `disease_train_manifest.csv`.

2. Use `disease_validation_manifest.csv` only for validation, hyperparameter tuning, and model selection.

3. Never use test images during model training or hyperparameter tuning.

4. Use `disease_test_manifest.csv` only for final unbiased model evaluation.

5. Do not randomly regenerate dataset splits.

6. Do not create synthetic images or replace authentic images with generated data.

7. Do not silently add external datasets.

8. Preserve the provided `final_class` labels exactly.

9. Use the provided canonical manifests as the source of truth for image paths and labels.

---

# Main Manifest Files

## Canonical Manifest

`disease_canonical_manifest.csv`

Contains the unified canonical dataset before final duplicate cleanup and splitting.

Important fields include:

- source_dataset
- original_class
- relative_image_path
- sha256
- is_valid
- final_class

---

## Train Manifest

`disease_train_manifest.csv`

Contains the records approved for model training.

Total records: 39,550

---

## Validation Manifest

`disease_validation_manifest.csv`

Contains the records approved for validation.

Total records: 8,475

---

## Test Manifest

`disease_test_manifest.csv`

Contains the records reserved for final model evaluation.

Total records: 8,476

---

# Target Label

The primary classification target is:

`final_class`

The model must predict one of the 38 canonical classes.

---

# Canonical Classes

1. Apple___Apple_scab
2. Apple___Black_rot
3. Apple___Cedar_apple_rust
4. Apple___healthy
5. Bell_pepper___Bacterial_spot
6. Bell_pepper___healthy
7. Blueberry___healthy
8. Cherry___Powdery_mildew
9. Cherry___healthy
10. Corn___Common_rust
11. Corn___Gray_leaf_spot
12. Corn___Northern_Leaf_Blight
13. Corn___healthy
14. Grape___Black_rot
15. Grape___Esca_Black_Measles
16. Grape___Leaf_blight
17. Grape___healthy
18. Orange___Citrus_greening
19. Peach___Bacterial_spot
20. Peach___healthy
21. Potato___Early_blight
22. Potato___Late_blight
23. Potato___healthy
24. Raspberry___healthy
25. Soybean___healthy
26. Squash___Powdery_mildew
27. Strawberry___Leaf_scorch
28. Strawberry___healthy
29. Tomato___Bacterial_spot
30. Tomato___Early_blight
31. Tomato___Late_blight
32. Tomato___Leaf_Mold
33. Tomato___Septoria_leaf_spot
34. Tomato___Target_Spot
35. Tomato___Tomato_Yellow_Leaf_Curl_Virus
36. Tomato___Tomato_mosaic_virus
37. Tomato___Two_spotted_spider_mite
38. Tomato___healthy

---

# File Integrity Status

All manifest records were verified against the physical dataset files.

Results:

- Total records checked: 56,501
- Missing files: 0
- File integrity: PASSED

Every image referenced in the train, validation, and test manifests exists in the dataset directory.

---

# Data Authenticity Policy

The dataset preparation pipeline was designed to preserve source provenance and dataset reproducibility.

Each image record includes metadata such as:

- source dataset
- original source class
- canonical class
- relative image path
- SHA-256 file hash
- file size
- validity status

The training system must preserve this provenance information.

---

# Recommended Model Training Workflow

1. Read the train, validation, and test manifests.
2. Resolve image paths relative to the dataset package root.
3. Load images according to the provided manifest.
4. Apply image preprocessing only during the data loading pipeline.
5. Apply training augmentation only to training images.
6. Do not augment validation or test images.
7. Train the classification model using only the training split.
8. Select the best model using validation performance.
9. Evaluate the final selected model exactly once on the test split.
10. Save:
   - trained model
   - class mapping
   - preprocessing configuration
   - training configuration
   - evaluation metrics
   - confusion matrix
   - per-class performance metrics

---

# Reproducibility Requirements

The backend training pipeline should:

- use fixed random seeds
- save model configuration
- save training hyperparameters
- save dataset manifest references
- record dataset sizes
- record model evaluation metrics
- preserve the canonical class ordering

The resulting trained model should be reproducible from the provided dataset package.

---

# Final Instruction

This dataset is the authoritative disease detection dataset for this Smart Polyhouse project.

Do not substitute, silently modify, fabricate, or supplement the dataset.

Train only on the provided training split.

Validate only on the provided validation split.

Test only on the provided test split.

Preserve the canonical 38-class label structure.