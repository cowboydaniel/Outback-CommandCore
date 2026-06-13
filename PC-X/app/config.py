"""Configuration for PC-X app."""

VERSION = "0.1.0"

COLOR_PALETTE = {
    "primary": "#00a8ff",
    "primary_dark": "#0090d8",
    "secondary": "#00d2d3",
    "warning": "#ffbe0b",
    "danger": "#ff6b6b",
    "background": "#2A2D2E",
    "card_bg": "#3A3A3A",
    "text_primary": "#ECF0F1",
    "text_secondary": "#B0B0B0",
    "border": "#3E3E3E",
    "highlight": "#252729",
    "accent": "#00d4aa",
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
