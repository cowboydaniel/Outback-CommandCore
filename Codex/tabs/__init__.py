"""Tab builders for the CommandCoreCodex GUI."""

from Codex.tabs.tab_data_prep import setup_data_prep_tab
from Codex.tabs.tab_generation import setup_generation_tab
from Codex.tabs.tab_logs import setup_logs_tab
from Codex.tabs.tab_training import setup_training_tab
from Codex.tabs.tab_validation import setup_validation_tab

__all__ = [
    "setup_data_prep_tab",
    "setup_generation_tab",
    "setup_logs_tab",
    "setup_training_tab",
    "setup_validation_tab",
]
