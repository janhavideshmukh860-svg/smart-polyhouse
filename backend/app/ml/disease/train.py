"""
Disease classification training script.

Pipeline: manifest -> image loading -> preprocessing -> train -> validate
-> evaluate (test, once) -> save artifacts -> (inference is served by
app.ml.disease.inference / app.services.disease_service).

Usage:
    python -m app.ml.disease.train --epochs 15 --batch-size 32

This script performs an early "smoke check": it verifies that at least
one image referenced by the training manifest actually exists on disk
before attempting a full run, and exits with a clear, honest error
message (NOT a fabricated result) if the raw image files are not present
in the current environment. This project's supplied dataset package for
this task is metadata/manifests-only (see MASTER_DATASET_GUIDE.md) - the
56,501 source images themselves were not included, so this script is
expected to stop at the smoke check until the images are made available
under DATASET_ROOT and training is re-run in an environment with a
PyTorch/GPU (or CPU) runtime.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.ml.disease.dataset import build_class_index, load_class_mapping, load_manifest, resolve_image_path

logger = get_logger(__name__)

MODEL_VERSION = "1.0.0"
RANDOM_SEED = 42


def set_seed(seed: int = RANDOM_SEED):
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def smoke_check_images_available(sample_size: int = 20) -> bool:
    """Checks whether a sample of manifest-referenced images actually
    exist on disk. Returns True only if ALL sampled images are found."""
    manifest = load_manifest("train")
    sample = manifest.sample(n=min(sample_size, len(manifest)), random_state=RANDOM_SEED)
    missing = 0
    for _, row in sample.iterrows():
        img_path = resolve_image_path(row["relative_image_path"])
        if not img_path.exists():
            missing += 1
    found = sample_size - missing
    logger.info("Image availability smoke check: %d/%d sampled images found on disk", found, len(sample))
    return missing == 0


def train(
    epochs: int = 15,
    batch_size: int = 32,
    image_size: int = 224,
    learning_rate: float = 3e-4,
    num_workers: int = 2,
    architecture: str = "mobilenet_v3_large",
) -> dict:
    try:
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader
    except ImportError:
        logger.error("PyTorch is not installed in this environment. Install torch/torchvision "
                     "(see requirements.txt) to run disease model training.")
        return {"status": "FAILED", "reason": "PyTorch not installed"}

    from app.ml.disease.dataset import DiseaseImageDataset
    from app.ml.disease.evaluate import compute_classification_metrics
    from app.ml.disease.model import build_model, get_device, get_transforms

    set_seed(RANDOM_SEED)

    class_mapping = load_class_mapping()
    class_to_idx = build_class_index(class_mapping)
    idx_to_class = {v: k for k, v in class_to_idx.items()}
    class_names = [idx_to_class[i] for i in range(len(idx_to_class))]
    logger.info("Loaded %d canonical classes", len(class_names))

    if not smoke_check_images_available():
        msg = (
            "Disease training ABORTED: raw image files referenced by the manifest "
            f"were not found under DATASET_ROOT={settings.dataset_root_path}. "
            "This environment only has the dataset METADATA package "
            "(manifests/configs/cards), not the 56,501 source images. "
            "Place the actual image dataset on disk (matching the "
            "relative_image_path values in the manifests) and re-run this "
            "script to train the model. NOT YET TRAINED."
        )
        logger.error(msg)
        result = {
            "status": "NOT_YET_TRAINED",
            "reason": "REQUIRES_IMAGE_DATASET",
            "detail": msg,
            "dataset_root_checked": str(settings.dataset_root_path),
        }
        out_dir = settings.model_artifact_root_path / "disease"
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / "training_status.json", "w") as f:
            json.dump(result, f, indent=2)
        return result

    device = get_device()
    logger.info("Training on device: %s", device)

    train_transform = get_transforms(image_size, train=True)
    eval_transform = get_transforms(image_size, train=False)

    train_ds = DiseaseImageDataset("train", class_to_idx, transform=train_transform)
    val_ds = DiseaseImageDataset("validation", class_to_idx, transform=eval_transform)
    test_ds = DiseaseImageDataset("test", class_to_idx, transform=eval_transform)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=(device.type == "cuda"))
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    model = build_model(num_classes=len(class_names), architecture=architecture, pretrained=True).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    out_dir = settings.model_artifact_root_path / "disease"
    out_dir.mkdir(parents=True, exist_ok=True)

    best_val_acc = -1.0
    history = []

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss, correct, total = 0.0, 0, 0
        t0 = time.time()
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            preds = outputs.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

        train_loss = running_loss / max(total, 1)
        train_acc = correct / max(total, 1)
        scheduler.step()

        model.eval()
        val_correct, val_total, val_loss_sum = 0, 0, 0.0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss_sum += loss.item() * images.size(0)
                preds = outputs.argmax(dim=1)
                val_correct += (preds == labels).sum().item()
                val_total += labels.size(0)

        val_loss = val_loss_sum / max(val_total, 1)
        val_acc = val_correct / max(val_total, 1)
        elapsed = time.time() - t0

        logger.info(
            "Epoch %d/%d | train_loss=%.4f train_acc=%.4f | val_loss=%.4f val_acc=%.4f | %.1fs",
            epoch, epochs, train_loss, train_acc, val_loss, val_acc, elapsed,
        )
        history.append({
            "epoch": epoch, "train_loss": train_loss, "train_acc": train_acc,
            "val_loss": val_loss, "val_acc": val_acc, "seconds": elapsed,
        })

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), out_dir / "best_model.pt")
            logger.info("New best model saved (val_acc=%.4f)", val_acc)

    # Final test evaluation using the BEST checkpoint (test used only once).
    model.load_state_dict(torch.load(out_dir / "best_model.pt", map_location=device))
    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            preds = outputs.argmax(dim=1).cpu().numpy().tolist()
            all_preds.extend(preds)
            all_labels.extend(labels.numpy().tolist())

    test_metrics = compute_classification_metrics(all_labels, all_preds, class_names)
    logger.info("Final TEST metrics: accuracy=%.4f macro_f1=%.4f", test_metrics["accuracy"], test_metrics["macro_f1"])

    with open(out_dir / "class_mapping.json", "w") as f:
        json.dump({"class_to_idx": class_to_idx, "idx_to_class": idx_to_class}, f, indent=2)
    with open(out_dir / "training_history.json", "w") as f:
        json.dump(history, f, indent=2)
    with open(out_dir / "test_metrics.json", "w") as f:
        json.dump(test_metrics, f, indent=2)

    metadata = {
        "model_name": "disease_detection",
        "model_type": architecture,
        "version": MODEL_VERSION,
        "task": "disease_classification",
        "num_classes": len(class_names),
        "training_dataset": "06_final_dataset/disease/disease_{train,validation,test}_manifest.csv",
        "training_date": datetime.now(timezone.utc).isoformat(),
        "random_seed": RANDOM_SEED,
        "hyperparameters": {
            "epochs": epochs, "batch_size": batch_size, "image_size": image_size,
            "learning_rate": learning_rate, "architecture": architecture,
        },
        "best_val_accuracy": best_val_acc,
        "test_metrics_summary": {
            "accuracy": test_metrics["accuracy"],
            "macro_f1": test_metrics["macro_f1"],
            "weighted_f1": test_metrics["weighted_f1"],
        },
        "status": "trained",
    }
    with open(out_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Disease model artifacts saved to %s", out_dir)
    return metadata


def main():
    parser = argparse.ArgumentParser(description="Train the Smart Polyhouse disease classification model")
    parser.add_argument("--epochs", type=int, default=settings.DISEASE_EPOCHS)
    parser.add_argument("--batch-size", type=int, default=settings.DISEASE_BATCH_SIZE)
    parser.add_argument("--image-size", type=int, default=settings.DISEASE_IMAGE_SIZE)
    parser.add_argument("--lr", type=float, default=settings.DISEASE_LEARNING_RATE)
    parser.add_argument("--workers", type=int, default=settings.DISEASE_NUM_WORKERS)
    parser.add_argument("--architecture", type=str, default="mobilenet_v3_large",
                         choices=["mobilenet_v3_large", "resnet50", "efficientnet_b0"])
    args = parser.parse_args()

    result = train(
        epochs=args.epochs,
        batch_size=args.batch_size,
        image_size=args.image_size,
        learning_rate=args.lr,
        num_workers=args.workers,
        architecture=args.architecture,
    )
    print(json.dumps(result, indent=2, default=str))
    if result.get("status") == "NOT_YET_TRAINED":
        sys.exit(2)


if __name__ == "__main__":
    main()
