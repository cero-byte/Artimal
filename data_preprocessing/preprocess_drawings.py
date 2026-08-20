#!/usr/bin/env python3
"""Crop scanned drawings to the bounding box of their visible content."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def detect_drawing_bounds(
    image: np.ndarray,
    *,
    padding: int = 100,
    min_area: float = 20_000,
    trim_top: int = 50,
    trim_bottom: int = 50,
    trim_left: int = 50,
    trim_right: int = 50,
) -> tuple[int, int, int, int] | None:
    """Return ``(x, y, width, height)`` in original-image coordinates."""
    height, width = image.shape[:2]
    if min(trim_top, trim_bottom, trim_left, trim_right, padding) < 0:
        raise ValueError("Trim and padding values must be non-negative.")
    if trim_top + trim_bottom >= height or trim_left + trim_right >= width:
        raise ValueError("Trim values remove the entire image.")

    region = image[
        trim_top : height - trim_bottom,
        trim_left : width - trim_right,
    ]
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        15,
        5,
    )
    kernel = np.ones((5, 5), np.uint8)
    connected = cv2.erode(
        cv2.dilate(binary, kernel, iterations=5), kernel, iterations=3
    )
    edges = cv2.Canny(gray, 20, 80)
    combined = cv2.bitwise_or(connected, edges)
    contours, _ = cv2.findContours(
        combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    valid_contours = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area <= min_area:
            continue
        _, _, contour_width, contour_height = cv2.boundingRect(contour)
        is_sparse_page_frame = (
            contour_width > 4_500
            and contour_height > 3_000
            and area < contour_width * contour_height * 0.2
        )
        if not is_sparse_page_frame:
            valid_contours.append(contour)

    if not valid_contours:
        return None

    x, y, box_width, box_height = cv2.boundingRect(
        np.concatenate(valid_contours)
    )

    # Detection happens in the trimmed region; map the result back to the
    # original image before adding padding. The original scripts omitted this
    # offset, which shifted every crop up and left.
    x += trim_left
    y += trim_top
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(width, x + box_width + padding)
    y2 = min(height, y + box_height + padding)
    return x1, y1, x2 - x1, y2 - y1


def crop_drawing(input_path: Path, output_path: Path, **kwargs) -> bool:
    """Crop one image. Return ``False`` when no drawing region is detected."""
    image = cv2.imread(str(input_path))
    if image is None:
        raise ValueError(f"Could not read image: {input_path}")

    bounds = detect_drawing_bounds(image, **kwargs)
    if bounds is None:
        return False

    x, y, width, height = bounds
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), image[y : y + height, x : x + width]):
        raise OSError(f"Could not write image: {output_path}")
    return True


def process_directory(input_dir: Path, output_dir: Path, **kwargs) -> int:
    """Crop supported images in one directory and return the success count."""
    image_paths = sorted(
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    processed = 0
    for input_path in image_paths:
        output_path = output_dir / input_path.name
        if crop_drawing(input_path, output_path, **kwargs):
            processed += 1
            print(f"Processed: {input_path.name}")
        else:
            print(f"Skipped (no drawing detected): {input_path.name}")
    return processed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Input image or directory")
    parser.add_argument("output", type=Path, help="Output image or directory")
    parser.add_argument("--padding", type=int, default=100)
    parser.add_argument("--min-area", type=float, default=20_000)
    parser.add_argument("--trim-top", type=int, default=50)
    parser.add_argument("--trim-bottom", type=int, default=50)
    parser.add_argument("--trim-left", type=int, default=50)
    parser.add_argument("--trim-right", type=int, default=50)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    options = {
        "padding": args.padding,
        "min_area": args.min_area,
        "trim_top": args.trim_top,
        "trim_bottom": args.trim_bottom,
        "trim_left": args.trim_left,
        "trim_right": args.trim_right,
    }
    if args.input.is_dir():
        count = process_directory(args.input, args.output, **options)
        print(f"Finished: {count} image(s) saved to {args.output}")
        return 0
    if not args.input.is_file():
        raise FileNotFoundError(args.input)
    if crop_drawing(args.input, args.output, **options):
        print(f"Saved: {args.output}")
        return 0
    print("No drawing region detected.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
