# Dataset

This directory has two purposes:

- Local research data may be placed directly in `Dataset/`. Those files are
  ignored by Git and must not be uploaded to GitHub.
- `Dataset/example/` contains a small synthetic dataset that is safe to publish
  and lets the preprocessing scripts and notebooks run after cloning the repo.

The notebooks prefer `Dataset/art_data.xlsx` when it exists. Otherwise they
automatically use `Dataset/example/art_data.xlsx` and print a warning that the
results are demonstrations only.

## Expected local structure

```text
Dataset/
├── art_data.xlsx
├── painting/
├── processed_painting/
└── example/
    ├── art_data.xlsx
    ├── painting/
    └── processed_painting/
```

Image paths in the workbook must be relative to the repository root, for
example `Dataset/painting/painting_1.jpg`. Example paths use
`Dataset/example/painting/...`.

## Data dictionary

| Column | Type | Meaning / current observed range |
|---|---|---|
| `student_id` | text or integer | Unique participant identifier; must not be duplicated |
| `drawing_skills` | integer | Self-rated drawing skill; observed 1–3 |
| `drawing_participation` | integer | Drawing participation; observed 1–3 |
| `enjoy_drawing` | numeric | Enjoyment of drawing; current source contains 1–12, so confirm the intended questionnaire scale before formal analysis |
| `negative_release` | integer | Release of negative emotion; observed 1–10 |
| `write_emotions` | integer | Helpfulness/importance of writing emotions; observed 1–5 |
| `imagine_composition` | integer | Helpfulness/importance of imagining the composition; observed 1–5 |
| `examples` | integer | Helpfulness/importance of example images; observed 1–5 |
| `color_expression` | integer | Helpfulness/importance of expressing emotion with color; observed 1–5 |
| `others` | numeric, optional | Other factor; observed 1–5 |
| `positive_emotion` | integer | Positive-emotion outcome used by the main regression analyses; observed 1–10 |
| `continue_participation` | integer, optional | Intention to participate again; observed 1–3 |
| `level_difficulty` | integer | Perceived activity difficulty; observed 1–10 |
| `painting_path` | text, optional | Repository-relative path to the original drawing |
| `processed_painting_path` | text, optional | Repository-relative path to the processed drawing |
| `text` | text, optional | Participant emotion-writing text associated with the drawing |

The observed ranges above describe the current local workbook; the final scale
definitions should be checked against the original questionnaire. Use blank
cells for missing values. The notebooks also accept legacy `na` strings, but
new datasets should use real empty cells.

## Privacy

Only synthetic example rows and drawings belong in `Dataset/example/`. Never
commit participant-level questionnaires, original drawings, written responses,
API labels, or other identifiable research data.
