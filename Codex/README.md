# CommandCore Codex

CommandCore Codex provides a PySide6 GUI for managing the AI training and code generation pipeline.

## Requirements

- Python 3.10+
- Qt6 GUI dependencies via PySide6
- PyTorch (CPU or CUDA build depending on your environment)

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r Codex/requirements.txt
```

## Run

From the repository root:

```bash
python -m Codex.app.main
```

## Bundled Training Data

CommandCore Codex ships with a built-in Python corpus under `Codex/data/training/python_basics`.
It is a compact, permissively licensed set of small Python examples intended for local CPU training.
Dataset metadata (name, version, license, file count, and size) lives in
`Codex/data/training/manifest.json` for reference. The current UI does not surface the manifest
details directly; it simply expects you to choose a dataset directory in the Data Preparation tab.

If you want to swap to your own data, point the dataset selector at a different folder containing
your training files. The manifest is optional for custom data; if you include one, it is for your
own tracking rather than a required UI input.

## Quickstart (no external downloads)

1. Launch the app (`python -m Codex.app.main`).
2. Open the **Data Preparation** tab and, in **Dataset Selection**, click **Browse...**.
3. Select the bundled dataset directory: `Codex/data/training/python_basics`.
4. Click **Prepare Dataset** and wait for the status to update.
5. Move to the **Training** tab and start training.
6. Go to **Generation** to generate code once training completes.
