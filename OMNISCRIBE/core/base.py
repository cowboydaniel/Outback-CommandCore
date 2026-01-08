"""Core data models and runtime for OMNISCRIBE."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from OMNISCRIBE.core.utils import setup_logging


class ScriptLanguage(Enum):
    PYTHON = "python"
    SHELL = "shell"
    JAVASCRIPT = "javascript"


@dataclass
class Script:
    name: str
    language: ScriptLanguage
    code: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)

    def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the script with the given context."""
        # In a real implementation, this would execute the script in the appropriate runtime
        print(f"Executing script: {self.name}")
        print(f"Language: {self.language.value}")
        print(f"Code:\n{self.code}")

        if context:
            print("Context:", json.dumps(context, indent=2))

        # Simulate execution result
        return {
            "success": True,
            "output": f"Script '{self.name}' executed successfully",
            "execution_time": "0.123s",
            "timestamp": datetime.now().isoformat(),
        }


class Omniscribe:
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.scripts: Dict[str, Script] = {}
        self.logger = logger or setup_logging("OMNISCRIBE")

    def create_script(self, name: str, language: ScriptLanguage, code: str, description: str = "") -> Script:
        """Create and store a new script."""
        if name in self.scripts:
            raise ValueError(f"Script with name '{name}' already exists")

        script = Script(
            name=name,
            language=language,
            code=code,
            description=description,
        )
        self.scripts[name] = script
        self.logger.info("Created new script: %s", name)
        return script

    def run_script(self, name: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a stored script by name."""
        if name not in self.scripts:
            raise ValueError(f"No script found with name: {name}")

        script = self.scripts[name]
        self.logger.info("Executing script: %s", name)
        return script.execute(context or {})
