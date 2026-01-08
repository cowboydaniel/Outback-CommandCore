"""Configuration values for the NIGHTFIRE application."""
import logging
from typing import Dict, List, Tuple

APP_NAME = "NIGHTFIRE"
WINDOW_TITLE = "NIGHTFIRE - Active Defense System"
MIN_WINDOW_SIZE: Tuple[int, int] = (900, 600)

ALERT_THRESHOLDS: Dict[str, int] = {
    "network_scan": 10,  # alerts after 10 scan attempts
    "failed_auth": 5,    # alerts after 5 failed auth attempts
}

CHECK_INTERVAL_MS = 2000
DEMO_THREATS_DELAY_MS = 5000

THREAT_TYPES: List[str] = [
    "network_scan",
    "failed_auth",
    "intrusion_attempt",
    "malware_detected",
]

DEMO_THREAT_TYPES: List[str] = [
    "network_scan",
    "failed_auth",
    "intrusion_attempt",
]

LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
