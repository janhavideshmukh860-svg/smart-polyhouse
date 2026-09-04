"""
Evaluation utilities for the disease classification model: overall and
per-class accuracy/precision/recall/F1, plus a confusion matrix, computed
from arrays of true/predicted label indices (no training-loop coupling,
so this can also be reused by offline evaluation scripts).
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
)


def compute_classification_metrics(y_true: List[int], y_pred: List[int], class_names: List[str]) -> Dict:
    y_true_arr = np.asarray(y_true)
    y_pred_arr = np.asarray(y_pred)

    accuracy = accuracy_score(y_true_arr, y_pred_arr)
    macro_precision = precision_score(y_true_arr, y_pred_arr, average="macro", zero_division=0)
    macro_recall = recall_score(y_true_arr, y_pred_arr, average="macro", zero_division=0)
    macro_f1 = f1_score(y_true_arr, y_pred_arr, average="macro", zero_division=0)
    weighted_precision = precision_score(y_true_arr, y_pred_arr, average="weighted", zero_division=0)
    weighted_recall = recall_score(y_true_arr, y_pred_arr, average="weighted", zero_division=0)
    weighted_f1 = f1_score(y_true_arr, y_pred_arr, average="weighted", zero_division=0)

    per_class_precision, per_class_recall, per_class_f1, per_class_support = precision_recall_fscore_support(
        y_true_arr, y_pred_arr, labels=list(range(len(class_names))), zero_division=0
    )

    per_class = {
        class_names[i]: {
            "precision": round(float(per_class_precision[i]), 4),
            "recall": round(float(per_class_recall[i]), 4),
            "f1": round(float(per_class_f1[i]), 4),
            "support": int(per_class_support[i]),
        }
        for i in range(len(class_names))
    }

    cm = confusion_matrix(y_true_arr, y_pred_arr, labels=list(range(len(class_names))))

    return {
        "accuracy": round(float(accuracy), 4),
        "macro_precision": round(float(macro_precision), 4),
        "macro_recall": round(float(macro_recall), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_precision": round(float(weighted_precision), 4),
        "weighted_recall": round(float(weighted_recall), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "n_samples": int(len(y_true_arr)),
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
    }
