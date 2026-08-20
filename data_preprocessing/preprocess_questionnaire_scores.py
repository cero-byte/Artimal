#!/usr/bin/env python3
"""Select and standardize questionnaire score columns from an Excel workbook."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.preprocessing import StandardScaler


DEFAULT_SCORE_COLUMNS = [
    "绘画基础2",
    "参与程度3",
    "是否喜欢绘画4",
    "持续参加8",
    "活动难度9",
]


def standardize_scores(
    input_path: Path,
    output_path: Path,
    columns: list[str],
    *,
    fill_value: float = 0,
) -> None:
    frame = pd.read_excel(input_path, engine="openpyxl")
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing columns: {', '.join(missing)}")

    scores = frame[columns].apply(pd.to_numeric, errors="coerce").fillna(fill_value)
    scaled = StandardScaler().fit_transform(scores)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(scaled, columns=columns).to_csv(output_path, index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Source .xlsx file")
    parser.add_argument("output", type=Path, help="Destination .csv file")
    parser.add_argument(
        "--columns",
        nargs="+",
        default=DEFAULT_SCORE_COLUMNS,
        help="Workbook columns to standardize.",
    )
    parser.add_argument(
        "--fill-value",
        type=float,
        default=0,
        help="Value used for missing or non-numeric cells (default: 0).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    standardize_scores(
        args.input,
        args.output,
        args.columns,
        fill_value=args.fill_value,
    )
    print(f"Saved standardized scores to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
