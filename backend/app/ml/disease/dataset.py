"""
PyTorch Dataset for the Smart Polyhouse disease detection dataset.

Reads the authoritative manifest CSVs (NOT a folder-per-class layout) and
resolves `relative_image_path` against the configured dataset root. The
manifest is the single source of truth for which image belongs to which
split and class, per DISEASE_DATASET_CARD.md.

IMPORTANT: the manifests ship with Windows-style backslash paths
(e.g. `01_raw\\disease\\PlantVillage\\raw\\color\\...\\file.JPG`). This
module normalizes them to the current OS's path separator so the same
manifest works unmodified on Windows, Linux, or macOS.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import pandas as pd

try:
    from PIL import Image
    from torch.utils.data import Dataset
except ImportError:  # pragma: no cover - torch/Pillow optional in some envs
    Image = None
    Dataset = object  # type: ignore

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

MANIFEST_FILENAMES = {
    "train": "disease_train_manifest.csv",
    "validation": "disease_validation_manifest.csv",
    "test": "disease_test_manifest.csv",
}


def load_manifest(split: str) -> pd.DataFrame:
    if split not in MANIFEST_FILENAMES:
        raise ValueError(f"split must be one of {list(MANIFEST_FILENAMES)}, got {split!r}")
    path = settings.disease_dataset_root_path / MANIFEST_FILENAMES[split]
    if not path.exists():
        raise FileNotFoundError(f"Disease manifest not found: {path}")
    df = pd.read_csv(path)
    # Keep only rows marked valid, as the dataset card documents an
    # `is_valid` integrity flag.
    if "is_valid" in df.columns:
        before = len(df)
        df = df[df["is_valid"].astype(str).str.lower() == "true"].reset_index(drop=True)
        dropped = before - len(df)
        if dropped:
            logger.warning("Dropped %d rows flagged is_valid=False from %s manifest", dropped, split)
    return df


def load_class_mapping() -> pd.DataFrame:
    path = settings.disease_dataset_root_path / "disease_class_mapping.csv"
    if not path.exists():
        raise FileNotFoundError(f"Disease class mapping not found: {path}")
    return pd.read_csv(path)


def build_class_index(class_mapping: pd.DataFrame) -> dict[str, int]:
    """Deterministic class -> index mapping, sorted alphabetically by
    `final_class` so it is stable and reproducible across runs."""
    classes = sorted(class_mapping["final_class"].unique().tolist())
    return {cls: idx for idx, cls in enumerate(classes)}


def resolve_image_path(relative_path: str, dataset_root: Optional[Path] = None) -> Path:
    """Resolve a manifest `relative_image_path` (Windows-style backslashes)
    against the dataset root directory."""
    normalized = relative_path.replace("\\", "/")
    root = dataset_root or settings.dataset_root_path.parent
    return root / normalized


class DiseaseImageDataset(Dataset):  # type: ignore[misc]
    """
    Loads (image, label_index) pairs from a manifest split.

    NOTE: this class requires the actual JPEG/PNG image files referenced
    by `relative_image_path` to exist on disk under the dataset root
    (see DISEASE_DATASET_CARD.md: "The image files remain in the original
    dataset directories"). If those raw image files are not present in
    the current environment (as is the case for the metadata-only package
    supplied for this task), instantiating this dataset will succeed but
    `__getitem__` will raise FileNotFoundError with a clear message,
    rather than silently returning fabricated data.
    """

    def __init__(
        self,
        split: str,
        class_to_idx: dict[str, int],
        transform: Optional[Callable] = None,
        dataset_root: Optional[Path] = None,
    ):
        if Image is None:
            raise ImportError("Pillow and torch are required to use DiseaseImageDataset")
        self.split = split
        self.manifest = load_manifest(split)
        self.class_to_idx = class_to_idx
        self.transform = transform
        # dataset_root is the directory the `relative_image_path` column
        # (e.g. "01_raw\\disease\\PlantVillage\\...") is relative to. This
        # is the parent of the disease/ metadata folder, i.e. the
        # `06_final_dataset/` sibling structure documented in the dataset
        # package README, configurable via DATASET_ROOT.
        self.dataset_root = dataset_root or settings.dataset_root_path.parent

    def __len__(self) -> int:
        return len(self.manifest)

    def __getitem__(self, idx: int):
        row = self.manifest.iloc[idx]
        rel_path = str(row["relative_image_path"]).replace("\\", "/")
        image_path = self.dataset_root / rel_path

        if not image_path.exists():
            raise FileNotFoundError(
                f"Disease image not found on disk: {image_path}. "
                "The manifest/metadata package does not include raw image "
                "bytes - place the actual dataset images under the "
                "configured DATASET_ROOT to enable training."
            )

        image = Image.open(image_path).convert("RGB")
        if self.transform is not None:
            image = self.transform(image)

        label = self.class_to_idx[row["final_class"]]
        return image, label
