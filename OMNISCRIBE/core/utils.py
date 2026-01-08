"""Shared helpers for OMNISCRIBE."""
from __future__ import annotations

import logging

from OMNISCRIBE.app.config import LOG_FORMAT, LOG_LEVEL


def setup_logging(name: str) -> logging.Logger:
    """Configure logging for OMNISCRIBE."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format=LOG_FORMAT,
    )
    return logging.getLogger(name)


def create_sample_scripts(omni, ui=None) -> None:
    """Create sample scripts if none exist."""
    if omni.scripts:
        return

    from OMNISCRIBE.core.base import ScriptLanguage

    try:
        omni.create_script(
            name="hello_world",
            language=ScriptLanguage.PYTHON,
            code=(
                "# Simple Python script\n"
                "print('Hello from OMNISCRIBE!')\n"
                "print('Context:', context)\n"
            ),
            description="A simple hello world script in Python",
        )

        omni.create_script(
            name="system_info",
            language=ScriptLanguage.SHELL,
            code=(
                "#!/bin/bash\n"
                "# Simple system info script\n"
                "echo \"Hostname: $(hostname)\"\n"
                "echo \"Uptime: $(uptime)\"\n"
            ),
            description="Display basic system information",
        )

        omni.create_script(
            name="array_ops",
            language=ScriptLanguage.JAVASCRIPT,
            code=(
                "// Simple array operations\n"
                "const numbers = [1, 2, 3, 4, 5];\n"
                "const doubled = numbers.map(n => n * 2);\n"
                "console.log('Original:', numbers);\n"
                "console.log('Doubled:', doubled);\n"
            ),
            description="JavaScript array operations example",
        )

        if ui is not None:
            ui.update_script_list()
    except Exception as exc:
        print(f"Error creating sample scripts: {exc}")
