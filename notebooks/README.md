# Research notebooks

These notebooks are exploratory research records rather than a sequential production pipeline. Their saved outputs and execution counts have been removed before publication.

## `art_therapy_analysis_hci.ipynb`

- Prefers the local `Dataset/art_data.xlsx` workbook. If it is absent, it uses
  the publishable `Dataset/example/art_data.xlsx` synthetic workbook.
- Validates all 16 required columns before analysis.
- Uses one consistent set of current column names across all sections.
- Runs descriptive statistics, group comparisons, correlation analysis,
  Elastic Net, gradient boosting, hierarchical regression, and cross-fitting.
- Includes participant-level analysis; only publish aggregated, properly anonymized results.
- Execution against the current local dataset has been verified end to end with Python 3.12 and
  the packages in `requirements-analysis.txt`.

## `analyze_images_with_claude.ipynb`

- Uses the same real-data/example-data fallback and resolves the paths stored
  in `processed_painting_path` relative to the repository root.
- Writes resumable labels to the ignored `output/image_labels.csv` file.
- Reads the API key from `ANTHROPIC_API_KEY`; never paste a key into the notebook.
- Sends adolescent drawings and text to an external API. Obtain consent and complete the required ethics/privacy review before use.
- Its local data-loading and path-resolution code is verified. External API
  calls are not exercised without a valid key and model access.

Launch with `jupyter lab notebooks/` from the repository root so relative data paths can be adjusted consistently.

```bash
source .venv/bin/activate
jupyter lab notebooks/
```
