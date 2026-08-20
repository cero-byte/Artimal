# Sample research data

This directory contains synthetic, non-participant fixtures for testing the
data-preprocessing scripts. The values and drawings are illustrative only and
must not be used as research findings.

## Files

- `art_data.xlsx` and `art_data.csv`: 30 synthetic rows containing the column
  names referenced across the exploratory notebooks and questionnaire script.
- `drawings/raw/`: three generated example drawings.
- `drawings/processed/`: created by `preprocess_drawings.py`.
- `features/`: created by `extract_image_features.py`.
- `processed_scores.csv`: created by
  `preprocess_questionnaire_scores.py`.

## Commands

Run from the repository root after installing `requirements-analysis.txt`:

```bash
python data_preprocessing/preprocess_drawings.py \
  sample_data/drawings/raw sample_data/drawings/processed \
  --min-area 1000 --padding 30

python data_preprocessing/preprocess_questionnaire_scores.py \
  sample_data/art_data.xlsx sample_data/processed_scores.csv

python data_preprocessing/extract_image_features.py \
  sample_data/drawings/processed sample_data/features --no-pretrained
```

Remove `--no-pretrained` for research use. The first pretrained run may
download ResNet-50 weights.

The notebooks are exploratory rather than one sequential pipeline. See
`notebooks/README.md` before executing them. The Claude image-analysis
notebook also requires `ANTHROPIC_API_KEY`, external API access, and appropriate
research consent.
