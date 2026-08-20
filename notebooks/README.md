# Research notebooks

These notebooks are exploratory research records rather than a sequential production pipeline. Their saved outputs and execution counts have been removed before publication.

## `art_therapy_analysis_hci.ipynb`

- Uses `sample_data/art_data.xlsx` by default. The committed file contains 30
  synthetic rows and is only a runnable schema example.
- For real analysis, replace the sample workbook locally with an anonymized
  dataset using the same columns. Do not publish participant-level data.
- Contains several iterations of column naming and statistical models. Confirm the schema used by each section before running it.
- Includes participant-level analysis; only publish aggregated, properly anonymized results.
- The sample-data execution has been verified end to end with Python 3.12 and
  the packages in `requirements-analysis.txt`.

## `analyze_images_with_claude.ipynb`

- Uses `sample_data/art_data.csv` and the image paths stored in that CSV.
- `sample_data/processed_painting.zip` is optional. If it is absent, the
  notebook uses the existing image paths directly.
- Reads the API key from `ANTHROPIC_API_KEY`; never paste a key into the notebook.
- Sends adolescent drawings and text to an external API. Obtain consent and complete the required ethics/privacy review before use.
- Its imports, code syntax, sample CSV schema, and sample image paths have been
  verified. External API calls are not exercised without a valid key and model
  access.

Launch with `jupyter lab notebooks/` from the repository root so relative data paths can be adjusted consistently.

```bash
source .venv/bin/activate
jupyter lab notebooks/
```
