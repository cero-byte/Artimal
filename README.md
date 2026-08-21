# Artimal

[**中文**](README.md) | [English](README.en.md)

Artimal 是一个面向艺术疗愈研究的 HCI 原型，包含中英文交互网站、可选的 AI 引导与图像生成功能，以及绘画和问卷数据分析工具。

> 本项目仅用于研究与教学，不提供医疗诊断，也不能替代专业心理健康支持。

## 项目内容

| 路径 | 作用 |
|---|---|
| `web/` | 中英文网站、本地服务器和共享 3D 模型 |
| `data_preprocessing/` | 绘画裁剪、问卷标准化和 ResNet 特征提取脚本 |
| `notebooks/` | 统计分析与 Claude 图像语义标注 Notebook |
| `Dataset/` | 本地研究数据说明，以及可公开的 `example/` 合成样例 |
| `tests/` | 不调用外部 API 的服务器测试 |
| `config.example.json` | OpenAI API 配置模板 |
| `requirements.txt` | 仅运行网站所需的依赖 |
| `requirements-analysis.txt` | 数据处理和 Notebook 所需的完整依赖 |

## 运行网站

需要 Python 3.10 或更高版本。

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

启动后访问：

- 语言选择：<http://127.0.0.1:8920/>
- 中文版：<http://127.0.0.1:8920/zh/>
- English：<http://127.0.0.1:8920/en/>

macOS 也可以双击 `web/start.command`，Windows 可以双击 `web/start_windows.bat`。

## 下载 3D 模型

由于文件较大，仓库不包含 `web/assets/` 下的 GLB 模型。缺少模型时，身体部位的 3D 预览不能显示，网站的其他功能仍可使用。

| 保存文件名 | 模型来源 |
|---|---|
| `brain.glb` | [Human Brain](https://sketchfab.com/3d-models/human-brain-c9c9d4d671b94345952d012cc2ea7a24) |
| `face.glb` | [Human Face Sculpting Practice](https://sketchfab.com/3d-models/human-face-sculpting-practice-d3920e30164844adb0f0ff2b936c9017) |
| `heart.glb` | [Human Heart](https://sketchfab.com/3d-models/human-heart-30f93d9dae4948fe85cd4d60ac40c23f) |
| `limbs.glb` | [Arms, hands, head, legs and feet](https://sketchfab.com/3d-models/arms-hands-head-legs-and-feet-low-poly-female-9ba2de9a0e4941da9ac55d43b8652a4b) |
| `lungs.glb` | [Realistic Human Lungs](https://sketchfab.com/3d-models/realistic-human-lungs-ce09f4099a68467880f46e61eb9a3531) |
| `stomach.glb` | [Stomach](https://sketchfab.com/3d-models/stomach-29b78b9373c943a8bb6c5c2cf4592967) |

安装步骤：

1. 登录 Sketchfab，从对应页面下载模型。
2. 使用 glTF 2.0 Binary（`.glb`）格式，并重命名为表格中的文件名。
3. 把六个文件放入 `web/assets/`：

```text
web/assets/
├── brain.glb
├── face.glb
├── heart.glb
├── limbs.glb
├── lungs.glb
└── stomach.glb
```

如果下载的是包含 `scene.gltf`、`scene.bin` 和纹理的 ZIP，请在 Blender 中导入 `scene.gltf`，再以 **glTF Binary (.glb)** 格式导出。不能只修改扩展名。

项目不会在启动时自动下载模型，因为 Sketchfab 下载需要用户授权，下载地址也是临时链接。所有 `web/assets/*.glb` 均已被 Git 忽略；作者和许可证信息见 `ATTRIBUTIONS.md`。

## 配置 OpenAI API

网站本身可以在没有 API Key 的情况下打开，但 AI 引导、参考图和最终图像生成功能需要 OpenAI API。

复制 `config.example.json` 为 `config.json`，然后填写：

```json
{
  "openai": {
    "api_base_url": "https://api.openai.com/v1",
    "api_key": ""
  }
}
```

`config.json` 已被 Git 忽略，不要把真实 API Key 写入 `config.example.json`。服务器也支持 `OPENAI_API_KEY`、`OPENAI_API_BASE_URL`、`ARTIMAL_PORT` 和 `ARTIMAL_BIND` 环境变量。

## 数据预处理

先安装完整依赖：

```bash
python -m pip install -r requirements-analysis.txt
```

### 1. 裁剪绘画区域

```bash
python data_preprocessing/preprocess_drawings.py INPUT_DIR OUTPUT_DIR
```

脚本会检测图片中的绘画区域，裁去多余的扫描边缘和白边，并把处理后的图片写入输出目录。

### 2. 标准化问卷分数

```bash
python data_preprocessing/preprocess_questionnaire_scores.py INPUT.xlsx OUTPUT.csv
```

脚本读取指定问卷列并进行 Z-score 标准化。它不会自动计算问卷总分或诊断结果。

### 3. 提取绘画特征

```bash
python data_preprocessing/extract_image_features.py INPUT_DIR OUTPUT_DIR
```

脚本使用预训练 ResNet-50 为每张图片生成一个 2048 维视觉特征向量，输出：

- `features.npy`：视觉特征矩阵。
- `filenames.npy`：每行特征对应的图片文件名。

这组特征目前尚未接入主要统计 Notebook，可用于后续相似度、聚类或预测分析。

## 使用示例数据

仓库中的 `Dataset/example/` 全部是合成数据，可以直接测试三个预处理脚本。生成结果写入已被 Git 忽略的 `output/`：

```bash
python data_preprocessing/preprocess_drawings.py \
  Dataset/example/painting output/example_processed_painting \
  --min-area 1000 --padding 30

python data_preprocessing/preprocess_questionnaire_scores.py \
  Dataset/example/art_data.xlsx output/example_scores.csv

python data_preprocessing/extract_image_features.py \
  Dataset/example/processed_painting output/example_features --no-pretrained
```

`--no-pretrained` 只用于快速检查程序能否运行，生成的随机网络特征不能用于正式研究。正式提取特征时请移除该参数。

## Notebook

启动 Jupyter：

```bash
jupyter lab notebooks/
```

### `art_therapy_analysis_hci.ipynb`

优先读取本地 `Dataset/art_data.xlsx`；如果不存在，则自动读取可公开的 `Dataset/example/art_data.xlsx`。Notebook 会先检查16个必需字段，再进行描述统计、相关分析、Elastic Net、梯度提升、分层回归和 Cross-fitting。

### `analyze_images_with_claude.ipynb`

把参与者的绘画和文字一起发送给 Claude，生成以下语义标签：

- 画面描绘的内容。
- 绘画相对文字是强化、匹配、弱化还是矛盾。
- 绘画是否具体呈现了文字中的隐喻。
- 画面中出现的身体部位。

运行前需要单独设置 Anthropic API Key：

```bash
export ANTHROPIC_API_KEY="your-key"
```

Notebook 使用与统计 Notebook 相同的数据选择规则，并读取其中的图片路径。结果写入已被 Git 忽略的 `output/image_labels.csv`。这些标签目前尚未合并进主要统计 Notebook。

## 数据与输出

- 中文网站收集的数据默认保存在 `data/collected/<participant_id>/`。
- 预处理结果保存在命令指定的输出路径。
- `data/`、真实研究数据、API 配置和生成结果默认被 Git 忽略。
- `Dataset/` 根目录用于本地真实研究数据，这些文件不会提交到 GitHub。
- `Dataset/example/` 只包含合成示例数据和示例图片，可以安全提交。
- 16个字段的含义和当前观察范围见 `Dataset/README.md`。

## 测试

```bash
python -m unittest discover -s tests -v
python -m compileall -q data_preprocessing web tests
```

## 隐私说明

不要向 GitHub 提交 API Key、真实问卷、原始绘画或可识别参与者的信息。向第三方 AI API 发送绘画和文字前，应取得适当同意，并遵守所在机构的伦理与数据保护要求。

3D 模型的来源与许可信息见 `ATTRIBUTIONS.md`。项目源代码目前尚未指定许可证。
