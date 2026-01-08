from __future__ import annotations

import base64
import datetime
import logging
import re
import shutil
from typing import Any

from app import config


def check_ios_tools_installed() -> bool:
    """
    Check if required iOS tools are installed.
    Returns True if all required tools are available, False otherwise.
    """
    missing_tools = [tool for tool in config.REQUIRED_IOS_TOOLS if shutil.which(tool) is None]

    if not missing_tools:
        logging.info("All required iOS tools are installed")
        return True

    logging.warning("Missing iOS tools: %s", ", ".join(missing_tools))
    return False


def decode_base64_if_needed(value: str) -> str:
    """Helper to decode base64 values if they appear to be base64."""
    if not re.match(r"^[A-Za-z0-9+/=]+$", value):
        return value

    try:
        decoded = base64.b64decode(value).decode("utf-8", errors="ignore")
        if len(decoded) > 0 and all(32 <= ord(c) <= 126 for c in decoded):
            return f"{value} (decoded: {decoded})"
    except Exception:
        pass

    return value


def decode_base64(value: str) -> str:
    """Safely decode base64 values."""
    try:
        if not value or not isinstance(value, str):
            return value

        value = value.strip()
        decoded_bytes = base64.b64decode(value)
        decoded = decoded_bytes.decode("utf-8", errors="ignore")

        if len(decoded) < 20 and all(32 <= ord(c) <= 126 for c in decoded):
            return f"{decoded}"

        return f"[Binary data: {len(decoded_bytes)} bytes]"
    except Exception:
        return value


def decode_software_behavior(value: str) -> str:
    """Decode and interpret SoftwareBehavior binary data."""
    try:
        decoded = base64.b64decode(value)
        if not decoded:
            return "No behavior flags set"

        flags = []
        if len(decoded) >= 4:
            byte1 = decoded[0]
            if byte1 & 0x01:
                flags.append("Auto-Lock enabled")
            if byte1 & 0x10:
                flags.append("Unknown flag (0x10)")

            byte2 = decoded[1]
            if byte2 & 0x01:
                flags.append("Unknown flag (0x0100)")

            if any(decoded[1:]):
                hex_str = decoded.hex()
                flags.append(f"Additional data: {hex_str[2:]}")
        else:
            return f"[Raw data: {decoded.hex()}]"

        return ", ".join(flags) if flags else "No behavior flags set"
    except Exception as exc:
        return f"[Error decoding: {exc}]"


def decode_proximity_sensor_data(value: str) -> str:
    """Decode and format proximity sensor calibration data."""
    try:
        if not value.endswith("==") and len(value) % 4 != 0:
            if len(value) > 32:
                return f"[Proximity Sensor Data: {len(value)} bytes]"
            return value

        decoded = base64.b64decode(value)
        if not decoded:
            return "No calibration data"

        hex_str = decoded.hex()
        if len(hex_str) > 40:
            hex_str = f"{hex_str[:40]}..."

        return f"[Calibration Data: {len(decoded)} bytes] {hex_str}"
    except Exception:
        return f"[Sensor Data: {len(value)} bytes]"


def get_color_name(color_code: str) -> str:
    """Convert numeric color code to human-readable name."""
    color_map = {
        "1": "Space Gray",
        "2": "White",
        "3": "Gold",
        "4": "Rose Gold",
        "5": "Silver",
        "6": "Black",
        "7": "Red",
        "8": "Blue",
        "9": "Green",
        "10": "Purple",
        "11": "Midnight Green",
        "12": "Pink",
        "13": "Yellow",
        "14": "Coral",
        "15": "Sierra Blue",
        "16": "Alpine Green",
        "17": "Purple",
        "18": "Deep Purple",
        "19": "Titanium",
        "20": "Natural Titanium",
        "21": "Blue Titanium",
        "22": "White Titanium",
        "23": "Black Titanium",
        "24": "Pink",
        "25": "Yellow",
    }
    return color_map.get(color_code, f"Color #{color_code}")


def format_system_value(key: str, value: Any) -> str | None:
    """Format system information values for better readability."""
    if not value or value == "(null)" or (isinstance(key, str) and re.match(r"^\d+$", key)):
        return None

    if isinstance(value, list):
        cleaned = [str(v).strip() for v in value if str(v).strip()]
        if not cleaned:
            return None

        if "DeviceFamilies" in key:
            family_map = {
                "1": "iPhone/iPod Touch",
                "2": "iPad",
                "3": "Apple TV",
                "4": "Apple Watch",
                "5": "HomePod",
                "6": "iPod Touch",
                "7": "Apple Vision Pro",
            }
            families = [family_map.get(v, f"Unknown ({v})") for v in cleaned if v in family_map or v.isdigit()]
            return ", ".join(families) if families else None

        return ", ".join(cleaned)

    if key in [
        "ActivationStateAcknowledged",
        "ProductionSOC",
        "TrustedHostAttached",
        "TelephonyCapability",
        "UseRaptorCerts",
        "HasSiDP",
        "HostAttached",
    ]:
        return "✅ Yes" if str(value).lower() == "true" else "❌ No"
    if key == "BrickState":
        return "❌ Bricked" if str(value).lower() == "true" else "✅ Not Bricked"
    if key == "PasswordProtected":
        return "🔒 Yes" if str(value).lower() == "true" else "🔓 No"

    field_handlers = {
        "SoftwareBehavior": lambda v: decode_software_behavior(v) if isinstance(v, str) else f"[Unhandled type: {type(v).__name__}]",
        "ProximitySensorCalibration": lambda v: decode_proximity_sensor_data(v)
        if isinstance(v, str)
        else f"[Unhandled type: {type(v).__name__}]",
        "SupportedDeviceFamilies": lambda v: f"Supports: {v}" if v else None,
        "RegionInfo": lambda v: v if v != "LL/A" else "Australia",
        "fm-activation-locked": lambda v: "🔒 Locked" if v == "Tk8=" else "🔓 Unlocked",
        "bootdelay": lambda v: "0 (immediate)" if v == "MA==" else v,
        "auto-boot": lambda v: "✅ Enabled" if v == "dHJ1ZQ==" else "⏹ Disabled",
        "fm-spstatus": lambda v: "📶 "
        + {
            "WUVT": "Wi-Fi and Cellular",
            "WUVTQ0Y=": "Wi-Fi, Cell, GPS",
            "WQ==": "Wi-Fi only",
            "UQ==": "Cellular only",
        }.get(v, v),
        "usbcfwflasherResult": lambda v: "✅ Success" if v == "Tm8gZXJyb3Jz" else f"❌ {v}",
        "DeviceColor": lambda v: get_color_name(v),
        "Uses24HourClock": lambda v: "🕒 24-hour" if str(v).lower() == "true" else "🕒 12-hour",
        "TimeZoneOffsetFromUTC": lambda v: f"UTC{int(v) / 3600:+.1f} hours",
    }

    if key in field_handlers:
        return field_handlers[key](value)

    if any(x in key.lower() for x in ["hash", "key", "token", "cert", "calibration", "serial"]) or any(
        key.lower().endswith(x) for x in ["status", "state", "result", "locked", "level", "args", "delay"]
    ):
        if isinstance(value, str) and value.endswith("=="):
            return decode_base64(value)

    if isinstance(value, str) and all(c in "0123456789abcdefABCDEF" for c in value) and len(value) > 8:
        return f"0x{value} (hex, {len(value) // 2} bytes)"

    if isinstance(value, str) and any(c in "+/=" for c in value) and len(value) % 4 == 0:
        if len(value) < 50:
            return decode_base64(value)
        return f"{value[:20]}... (binary data, {len(value)} chars)"

    if isinstance(value, str):
        if value.lower() in ("true", "yes", "1"):
            return "✅ Yes"
        if value.lower() in ("false", "no", "0", "none", "null"):
            return "❌ No"

    if key.endswith("Since1970") and str(value).replace(".", "").isdigit():
        try:
            timestamp = float(value)
            dt = datetime.datetime.fromtimestamp(timestamp)
            return f"{dt.strftime('%Y-%m-%d %H:%M:%S')}"
        except (ValueError, OSError):
            pass

    return value
