#!/usr/bin/env python3
"""Extract 2,048-dimensional ResNet-50 features from drawing images."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps
import torch
from torch import nn
from torchvision import transforms
from torchvision.models import ResNet50_Weights, resnet50
from tqdm import tqdm


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


class ImageFeatureExtractor(nn.Module):
    """ResNet-50 convolutional backbone followed by global average pooling."""

    def __init__(self, *, pretrained: bool = True, device: str = "cpu") -> None:
        super().__init__()
        weights = ResNet50_Weights.DEFAULT if pretrained else None
        model = resnet50(weights=weights)
        self.feature_extractor = nn.Sequential(*list(model.children())[:-2])
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.device = torch.device(device)
        self.to(self.device)
        self.eval()

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        with torch.inference_mode():
            features = self.feature_extractor(inputs)
            return self.pool(features).flatten(start_dim=1)

    def extract_from_pil(self, image: Image.Image) -> torch.Tensor:
        tensor = self.preprocess(image).unsqueeze(0).to(self.device)
        return self(tensor)

    @staticmethod
    def preprocess(image: Image.Image, target_size: int = 224) -> torch.Tensor:
        image = ImageOps.autocontrast(image.convert("RGB"))
        image = image.filter(ImageFilter.SHARPEN)

        old_width, old_height = image.size
        ratio = target_size / max(old_width, old_height)
        new_size = (
            max(1, round(old_width * ratio)),
            max(1, round(old_height * ratio)),
        )
        image = image.resize(new_size, Image.Resampling.LANCZOS)

        canvas = Image.new("RGB", (target_size, target_size), (255, 255, 255))
        canvas.paste(
            image,
            ((target_size - new_size[0]) // 2, (target_size - new_size[1]) // 2),
        )
        transform = transforms.Compose(
            [
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )
        return transform(canvas)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda", "mps"),
        default="auto",
    )
    parser.add_argument(
        "--no-pretrained",
        action="store_true",
        help="Do not download or use ImageNet weights.",
    )
    return parser.parse_args()


def resolve_device(requested: str) -> str:
    if requested != "auto":
        return requested
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def main() -> int:
    args = parse_args()
    if not args.input_dir.is_dir():
        raise NotADirectoryError(args.input_dir)

    files = sorted(
        path
        for path in args.input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )
    if not files:
        raise ValueError(f"No supported images found in {args.input_dir}")

    device = resolve_device(args.device)
    extractor = ImageFeatureExtractor(
        pretrained=not args.no_pretrained,
        device=device,
    )
    features: list[np.ndarray] = []
    filenames: list[str] = []

    for image_path in tqdm(files, desc="Extracting image features"):
        try:
            with Image.open(image_path) as image:
                feature = extractor.extract_from_pil(image).cpu().numpy().ravel()
            features.append(feature)
            filenames.append(image_path.name)
        except (OSError, ValueError) as exc:
            print(f"Skipped {image_path.name}: {exc}")

    if not features:
        raise RuntimeError("All image files failed to process.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    np.save(args.output_dir / "features.npy", np.stack(features))
    np.save(args.output_dir / "filenames.npy", np.asarray(filenames))
    print(f"Saved {len(features)} feature vectors to {args.output_dir} ({device=})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
