# CommandCore Launcher

A modern, user-friendly launcher for Outback Electronics software suite.

## Features

- Clean, dark-themed interface
- Automatic discovery of installed applications
- Support for both Python and native applications
- Privilege escalation when needed
- Responsive grid layout

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt --break-system-packages
   ```

2. Install the package in development mode:
   ```bash
   pip install -e . --break-system-packages
   ```

## Usage

Run the launcher with:
```bash
python -m CommandCore
```

Or use the desktop launcher if installed.

## Development

### Project Structure

- `app/` - Main application package
- `core/` - Core functionality
- `tabs/` - Tab implementations
- `ui/` - UI components and themes
- `tests/` - Test suite

### Style Guide

Please refer to `STYLE_GUIDE.md` for coding and UI/UX standards.

## License

Proprietary - Outback Electronics
