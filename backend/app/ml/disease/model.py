"""
Disease classification model definition.

Model choice: MobileNetV3-Large (torchvision), pretrained on ImageNet,
with a replaced classifier head for the 38 canonical disease classes.

Rationale (balancing accuracy / training time / inference speed / size,
per project requirements):
  - MobileNetV3-Large is ~5.4M parameters (~21MB fp32) vs. ~25M+ for
    ResNet50 or ~11M+ for EfficientNet-B3 at similar input resolution.
  - It was designed explicitly for fast CPU/mobile inference, which
    matters here since the target deployment is "a normal laptop" and a
    JSON prediction API, not a GPU inference cluster.
  - Transfer learning from ImageNet features works well for leaf-disease
    texture/color patterns and converges quickly even on a CPU for a
    reasonable number of epochs.
  - EfficientNet/ResNet remain easy drop-in alternatives (see
    `build_model(architecture=...)`) if more accuracy is later needed and
    training-time budget allows it.
"""
from __future__ import annotations

from typing import Literal

try:
    import torch
    import torch.nn as nn
    from torchvision import models
except ImportError:  # pragma: no cover
    torch = None
    nn = None
    models = None

Architecture = Literal["mobilenet_v3_large", "resnet50", "efficientnet_b0"]


def get_device() -> "torch.device":
    if torch is None:
        raise ImportError("PyTorch is required for disease model training/inference")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def build_model(num_classes: int, architecture: Architecture = "mobilenet_v3_large", pretrained: bool = True) -> "nn.Module":
    if torch is None:
        raise ImportError("PyTorch/torchvision are required to build the disease model")

    if architecture == "mobilenet_v3_large":
        weights = models.MobileNet_V3_Large_Weights.DEFAULT if pretrained else None
        model = models.mobilenet_v3_large(weights=weights)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, num_classes)
    elif architecture == "resnet50":
        weights = models.ResNet50_Weights.DEFAULT if pretrained else None
        model = models.resnet50(weights=weights)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    elif architecture == "efficientnet_b0":
        weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
        model = models.efficientnet_b0(weights=weights)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, num_classes)
    else:
        raise ValueError(f"Unsupported architecture: {architecture}")

    return model


def get_transforms(image_size: int = 224, train: bool = True):
    if torch is None:
        raise ImportError("torchvision is required for image transforms")
    from torchvision import transforms

    imagenet_mean = [0.485, 0.456, 0.406]
    imagenet_std = [0.229, 0.224, 0.225]

    if train:
        return transforms.Compose([
            transforms.RandomResizedCrop(image_size, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=imagenet_mean, std=imagenet_std),
        ])
    else:
        return transforms.Compose([
            transforms.Resize(int(image_size * 1.14)),
            transforms.CenterCrop(image_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=imagenet_mean, std=imagenet_std),
        ])
