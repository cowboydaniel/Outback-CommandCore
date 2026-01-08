# OMNISCRIBE

OMNISCRIBE is an automation and scripting control suite that enables users to create, schedule, and execute complex task workflows across the CommandCore ecosystem.

## Key Features

- **Versatile Scripting**: Intuitive engine supporting multiple programming languages
- **Task Automation**: Powerful scheduling and batch operation capabilities
- **Ecosystem Integration**: Seamless connection with all CommandCore tools
- **Code Repository**: Extensive library of reusable templates and functions
- **Comprehensive Logging**: Detailed execution tracking and error diagnostics
- **Secure Environment**: Robust permission controls and access management

## Requirements

### Python Version
- Python 3.10 or higher

### Python Dependencies
Install via pip:
```bash
pip install -r requirements.txt
```
- `PySide6>=6.5.0` – Qt6 GUI framework

### Supported Platforms
- Linux (primary)
- macOS
- Windows

No additional OS-level dependencies are required.

## Getting Started

1. Clone the repository and navigate to the OMNISCRIBE directory
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the application

## Usage

### Entry Point
```bash
# Run from repository root
python OMNISCRIBE/omniscribe.py

# Or directly
cd OMNISCRIBE && python omniscribe.py
```

### Module Path
`OMNISCRIBE.omniscribe` (main module: `omniscribe.py`)

### Supported Script Languages
- Python (`.py`)
- Shell/Bash (`.sh`)
- JavaScript (`.js`)

### Examples
```bash
# Launch the OMNISCRIBE GUI
python OMNISCRIBE/omniscribe.py
```

**Creating a new script:**
1. Click "New Script" in the toolbar
2. Enter a script name
3. Select the language (Python, Shell, or JavaScript)
4. Write your script in the editor pane
5. Click "Save" to store the script
6. Click "Run" to execute

**Importing scripts:**
- Use "Import Script" to load existing `.py`, `.sh`, or `.js` files

**Exporting scripts:**
- Select a script and use "Export Script" to save it to a file

## License

Proprietary – Outback Electronics
