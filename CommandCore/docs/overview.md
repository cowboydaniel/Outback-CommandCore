# CommandCore Launcher Overview

A modern, user-friendly launcher application for the CommandCore suite.

## Features

- Modern, responsive UI following the CommandCore design system
- Splash screen with loading animation
- Dashboard with system status and quick access to applications
- Configurable settings and theming

## Requirements

- Python 3.8+
- PySide6

## Installation

1. Clone the repository.
2. Install dependencies:
   ```
   pip install -r requirements.txt --break-system-packages
   ```

## Running the Application

```bash
python -m app.main
```

## Project Structure

```
CommandCore/
├── app/               # Main application package
├── tabs/              # Tab implementations
├── core/              # Core functionality
├── ui/                # UI components and themes
├── tests/             # Test suite
├── docs/              # Documentation
├── requirements.txt   # Python dependencies
└── README.md          # Project README
```

## Style Guide

This project follows the CommandCore UI/UX Style Guide. See `STYLE_GUIDE.md` for details.
