# CommandCore Codex

CommandCore Codex provides a PySide6 GUI for managing the AI training and code generation pipeline.

## Requirements

- Python 3.10+
- Qt6 GUI dependencies via PySide6
- PyTorch (CPU or CUDA build depending on your environment)

## Install

```bash
cd Codex
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python app/gui.py
```

If you want to run Codex from the repository root, use:

```bash
python Codex/app/gui.py
```
