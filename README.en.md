# Artimal

[中文](README.md) | [**English**](README.en.md)

Artimal investigates how generative AI can support adolescents in developing, elaborating, and externalizing their mental imagery from vague emotional experiences to therapeutic art-making, while preserving their imagination and agency throughout the creative process.

> This project is for research only. It does not provide medical diagnosis or replace professional mental-health support.

## Repository contents

| Path | Purpose |
|---|---|
| `web/` | Chinese and English websites, local server, and the 3D asset directory |
| `data_preprocessing/` | Drawing crop, questionnaire standardization, and ResNet feature scripts |
| `notebooks/` | Statistical analysis and Claude semantic-labeling notebooks |
| `Dataset/` | Local research-data guidance and publishable synthetic examples under `example/` |
| `tests/` | Server tests that do not call external APIs |
| `config.example.json` | OpenAI API configuration template |
| `requirements.txt` | Minimal dependencies for the website |
| `requirements-analysis.txt` | Full dependencies for preprocessing and notebooks |

## Run the website

Python 3.10 or newer is required.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp config.example.json config.json
python web/server.py
```

### Windows

```bat
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
copy config.example.json config.json
py web\server.py
```

Open one of these URLs:

- Language selector: <http://127.0.0.1:8920/>
- Chinese: <http://127.0.0.1:8920/zh/>
- English: <http://127.0.0.1:8920/en/>

On macOS you may also double-click `web/start.command`. On Windows, double-click `web/start_windows.bat`.

## Download the 3D models

The GLB files under `web/assets/` are not included in the repository because of their size. Without them, the body-part 3D previews will not appear, but the rest of the website remains usable.

| Save as | Model source |
|---|---|
| `brain.glb` | [Human Brain](https://sketchfab.com/3d-models/human-brain-c9c9d4d671b94345952d012cc2ea7a24) |
| `face.glb` | [Human Face Sculpting Practice](https://sketchfab.com/3d-models/human-face-sculpting-practice-d3920e30164844adb0f0ff2b936c9017) |
| `heart.glb` | [Human Heart](https://sketchfab.com/3d-models/human-heart-30f93d9dae4948fe85cd4d60ac40c23f) |
| `limbs.glb` | [Arms, hands, head, legs and feet](https://sketchfab.com/3d-models/arms-hands-head-legs-and-feet-low-poly-female-9ba2de9a0e4941da9ac55d43b8652a4b) |
| `lungs.glb` | [Realistic Human Lungs](https://sketchfab.com/3d-models/realistic-human-lungs-ce09f4099a68467880f46e61eb9a3531) |
| `stomach.glb` | [Stomach](https://sketchfab.com/3d-models/stomach-29b78b9373c943a8bb6c5c2cf4592967) |

Installation:

1. Sign in to Sketchfab and download each model.
2. Use glTF 2.0 Binary (`.glb`) format and rename each file exactly as shown above.
3. Put all six files in `web/assets/`:

```text
web/assets/
├── brain.glb
├── face.glb
├── heart.glb
├── limbs.glb
├── lungs.glb
└── stomach.glb
```

If the download is a ZIP containing `scene.gltf`, `scene.bin`, and textures, import `scene.gltf` into Blender and export it as **glTF Binary (.glb)**. Renaming a `.gltf` file to `.glb` is not sufficient.

The project does not download models automatically because Sketchfab downloads require user authorization and use temporary URLs. All `web/assets/*.glb` files are ignored by Git. See `ATTRIBUTIONS.md` for creators and licenses.

## Configure the OpenAI API

The website opens without an API key, but AI guidance, reference images, and final image generation require the OpenAI API.

Copy `config.example.json` to `config.json` and fill in:

```json
{
  "openai": {
    "api_base_url": "https://api.openai.com/v1",
    "api_key": ""
  }
}
```

`config.json` is ignored by Git. Never place a real key in `config.example.json`. The server also supports `OPENAI_API_KEY`, `OPENAI_API_BASE_URL`, `ARTIMAL_PORT`, and `ARTIMAL_BIND` environment variables.

## Data preprocessing

Install the full analysis dependencies:

```bash
python -m pip install -r requirements-analysis.txt
```

### 1. Crop drawing regions

```bash
python data_preprocessing/preprocess_drawings.py INPUT_DIR OUTPUT_DIR
```

Detects visible drawing content, removes excess scan margins and whitespace, and writes cropped images to the output directory.

### 2. Standardize questionnaire scores

```bash
python data_preprocessing/preprocess_questionnaire_scores.py INPUT.xlsx OUTPUT.csv
```

Reads selected questionnaire columns and applies Z-score standardization. It does not calculate a questionnaire total or diagnosis.

### 3. Extract drawing features

```bash
python data_preprocessing/extract_image_features.py INPUT_DIR OUTPUT_DIR
```

Uses a pretrained ResNet-50 to create one 2,048-dimensional feature vector per image:

- `features.npy`: feature matrix.
- `filenames.npy`: image filename corresponding to each row.

These features are not yet connected to the main statistics notebook. They can support later similarity, clustering, or prediction analyses.

## Sample data

`Dataset/example/` contains synthetic data only. The following commands write generated outputs to the ignored `output/` directory:

```bash
python data_preprocessing/preprocess_drawings.py \
  Dataset/example/painting output/example_processed_painting \
  --min-area 1000 --padding 30

python data_preprocessing/preprocess_questionnaire_scores.py \
  Dataset/example/art_data.xlsx output/example_scores.csv

python data_preprocessing/extract_image_features.py \
  Dataset/example/processed_painting output/example_features --no-pretrained
```

`--no-pretrained` only checks whether the code runs. Its random-network features must not be used for research. Remove this option for real feature extraction.

## Notebooks

```bash
jupyter lab notebooks/
```

### `art_therapy_analysis_hci.ipynb`

Prefers the local `Dataset/art_data.xlsx`; if it is absent, the notebook automatically uses the publishable `Dataset/example/art_data.xlsx`. It validates all 16 required columns before running descriptive statistics, correlation analysis, Elastic Net, gradient boosting, hierarchical regression, and cross-fitting.

### `analyze_images_with_claude.ipynb`

Sends a drawing and its accompanying text to Claude to label depicted imagery, image-versus-text intensity, metaphor specificity, and visible body parts.

Set a separate Anthropic API key before running:

```bash
export ANTHROPIC_API_KEY="your-key"
```

The notebook uses the same real-data/example-data selection rule and resolves the image paths stored in the workbook. Results are written to the ignored `output/image_labels.csv`. These labels are not yet merged into the main statistics notebook.

## Data and outputs

- Chinese-site session data is saved to `data/collected/<participant_id>/` by default.
- Preprocessing results are written to the output paths supplied in each command.
- Real research data, local API configuration, and generated analysis outputs are ignored by Git.
- Files placed directly under `Dataset/` are local research data and are not committed.
- `Dataset/example/` contains only synthetic data and drawings that are safe to publish.
- See `Dataset/README.md` for the 16-column data dictionary and observed ranges.

## Tests

```bash
python -m unittest discover -s tests -v
python -m compileall -q data_preprocessing web tests
```

## Privacy

Do not commit API keys, real questionnaires, original participant drawings, or identifiable participant information. Obtain appropriate consent and follow institutional ethics and data-protection requirements before sending drawings or text to third-party AI services.

See `ATTRIBUTIONS.md` for 3D model credits and licenses. The project source code does not currently specify a license.
