"""Configuration for PC-X app."""

VERSION = "0.1.0"

COLOR_PALETTE = {
    "primary": "#017E84",
    "primary_dark": "#016169",
    "secondary": "#4CAF50",
    "warning": "#FF9800",
    "danger": "#F44336",
    "background": "#F5F5F5",
    "card_bg": "#FFFFFF",
    "text_primary": "#212121",
    "text_secondary": "#757575",
    "border": "#E0E0E0",
    "highlight": "#E6F7F7",
    "accent": "#00B8D4",
}

CACHE_CONFIG = {
    "enabled": True,
    "ttl": 300,
    "refresh_on_tab_switch": True,
}

SMART_CACHE_MAX_AGE = 600

LIVE_REFRESH_INTERVAL_MS = 1000

DISK_BENCHMARK_FILE_SIZE_BYTES = 100 * 1024 * 1024
DISK_BENCHMARK_BLOCK_SIZE_BYTES = 1024 * 1024

CPU_BENCHMARK_MAX = 100000

SUDOERS_FILE = "/etc/sudoers.d/99-nest-pc-tools"

REQUIRED_TOOLS = {
    "debian": {
        "smartmontools": "smartctl",
        "lm-sensors": "sensors",
        "dmidecode": "dmidecode",
        "lshw": "lshw",
        "pciutils": "lspci",
        "parted": "parted",
        "iw": "iw",
        "ethtool": "ethtool",
        "iputils-ping": "ping",
        "speedtest-cli": "speedtest-cli",
        "sudo": "sudo",
        "libcap2-bin": "setcap",
    },
    "redhat": {
        "smartmontools": "smartctl",
        "lm_sensors": "sensors",
        "dmidecode": "dmidecode",
        "lshw": "lshw",
        "pciutils": "lspci",
        "parted": "parted",
        "iw": "iw",
        "ethtool": "ethtool",
        "iputils": "ping",
        "speedtest-cli": "speedtest-cli",
        "sudo": "sudo",
        "libcap2": "setcap",
    },
}
