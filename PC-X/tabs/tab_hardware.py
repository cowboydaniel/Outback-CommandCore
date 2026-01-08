"""Hardware tab layout for PC-X."""

import os

import psutil
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QFont


def setup_hardware_tab(module) -> None:
    """Set up the Hardware tab with CPU, RAM, and GPU information."""
    hardware_tab = module.device_tabs["hardware"]

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)

    content_widget = QWidget()
    content_layout = QVBoxLayout(content_widget)
    content_layout.setContentsMargins(10, 10, 10, 10)

    header = QLabel("Hardware Information")
    header.setFont(QFont("Arial", 12, QFont.Bold))
    header.setStyleSheet(f"color: {module.colors['primary']};")
    content_layout.addWidget(header)

    cpu_group = QGroupBox("CPU Information")
    cpu_layout = QGridLayout(cpu_group)

    cpu_model = "Unknown"
    cpu_cores = str(os.cpu_count()) if os.cpu_count() else "Unknown"
    cpu_freq = "Unknown"
    cpu_cache = "Unknown"

    try:
        if os.path.exists("/proc/cpuinfo"):
            with open("/proc/cpuinfo", "r", encoding="utf-8") as cpu_file:
                cpuinfo = cpu_file.read()
                for line in cpuinfo.split("\n"):
                    if line.startswith("model name"):
                        cpu_model = line.split(":", 1)[1].strip()
                    elif line.startswith("cpu MHz"):
                        freq = float(line.split(":")[1].strip())
                        cpu_freq = f"{freq:.2f} MHz"

                cache_match = None
                for line in cpuinfo.split("\n"):
                    if line.startswith("cache size"):
                        cache_match = line
                        break
                if cache_match:
                    cache_kb = int(cache_match.split(":", 1)[1].strip().split()[0])
                    cpu_cache = f"{cache_kb / 1024:.1f} MB" if cache_kb >= 1024 else f"{cache_kb} KB"
    except Exception:
        pass

    cpu_info = [
        ("CPU Model", cpu_model),
        ("CPU Cores", cpu_cores),
        ("CPU Cache", cpu_cache),
        ("CPU Frequency", cpu_freq),
        ("CPU Usage", f"{psutil.cpu_percent(interval=0.1)}%"),
        (
            "CPU Temperature",
            f"{module.get_cpu_temp():.1f}°C" if module.get_cpu_temp() else "N/A",
        ),
    ]

    for row, (label, value) in enumerate(cpu_info):
        label_widget = QLabel(f"{label}:")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        cpu_layout.addWidget(label_widget, row, 0)

        value_label = QLabel(str(value))
        value_label.setFont(QFont("Arial", 10))
        cpu_layout.addWidget(value_label, row, 1)
        module.hardware_info_labels[label] = value_label

    content_layout.addWidget(cpu_group)

    memory_group = QGroupBox("Memory Information")
    memory_layout = QGridLayout(memory_group)

    try:
        mem = psutil.virtual_memory()
        total_ram = f"{mem.total / (1024**3):.2f} GB"
        available_ram = f"{mem.available / (1024**3):.2f} GB"
        used_ram = f"{mem.used / (1024**3):.2f} GB ({mem.percent}%)"
        ram_speed = module.get_ram_speed()
    except Exception:
        total_ram = available_ram = used_ram = ram_speed = "Unknown"

    memory_info = [
        ("Total Memory", total_ram),
        ("Available Memory", available_ram),
        ("Used Memory", used_ram),
        ("Memory Speed", ram_speed),
    ]

    for row, (label, value) in enumerate(memory_info):
        label_widget = QLabel(f"{label}:")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        memory_layout.addWidget(label_widget, row, 0)

        value_label = QLabel(str(value))
        value_label.setFont(QFont("Arial", 10))
        memory_layout.addWidget(value_label, row, 1)
        if label in ["Used Memory", "Available Memory"]:
            module.hardware_info_labels[label] = value_label

    content_layout.addWidget(memory_group)

    gpu_group = QGroupBox("Graphics Information")
    gpu_layout = QGridLayout(gpu_group)

    gpu_info = module.get_gpu_info()
    gpu_temp = module.get_gpu_temp()
    gpu_freq = module.get_gpu_freq()

    row = 0
    for i, gpu in enumerate(gpu_info):
        label_widget = QLabel(f"GPU {i + 1}:")
        label_widget.setFont(QFont("Arial", 10, QFont.Bold))
        gpu_layout.addWidget(label_widget, row, 0)

        value_label = QLabel(gpu)
        value_label.setFont(QFont("Arial", 10))
        gpu_layout.addWidget(value_label, row, 1)
        row += 1

    temp_label = QLabel("GPU Temperature:")
    temp_label.setFont(QFont("Arial", 10, QFont.Bold))
    gpu_layout.addWidget(temp_label, row, 0)

    gpu_temp_value = QLabel(f"{gpu_temp:.1f}°C" if gpu_temp else "N/A")
    gpu_layout.addWidget(gpu_temp_value, row, 1)
    module.hardware_info_labels["GPU Temperature"] = gpu_temp_value
    row += 1

    freq_label = QLabel("GPU Frequency:")
    freq_label.setFont(QFont("Arial", 10, QFont.Bold))
    gpu_layout.addWidget(freq_label, row, 0)

    gpu_freq_value = QLabel(f"{gpu_freq:.0f} MHz" if gpu_freq else "N/A")
    gpu_layout.addWidget(gpu_freq_value, row, 1)
    module.hardware_info_labels["GPU Frequency"] = gpu_freq_value

    content_layout.addWidget(gpu_group)

    battery_group = QGroupBox("Battery Information")
    battery_layout = QGridLayout(battery_group)

    battery_info = module.get_battery_info()

    if battery_info["present"]:
        battery_data = [
            ("Battery Device", battery_info["device"]),
            ("Model/Manufacturer", battery_info["model"]),
            ("Serial Number", battery_info["serial"]),
            ("Charge Level", f"{battery_info['capacity']}%"),
            ("Status", battery_info["status"]),
            ("Health", battery_info["health"]),
            ("Recommendation", battery_info["recommendation"]),
        ]

        for row, (label, value) in enumerate(battery_data):
            label_widget = QLabel(f"{label}:")
            label_widget.setFont(QFont("Arial", 10, QFont.Bold))
            battery_layout.addWidget(label_widget, row, 0)

            value_label = QLabel(str(value))
            value_label.setFont(QFont("Arial", 10))
            battery_layout.addWidget(value_label, row, 1)

            if label == "Charge Level":
                module.battery_charge_label = value_label
            elif label == "Status":
                module.battery_status_label = value_label
            elif label == "Health":
                module.battery_health_label = value_label
    else:
        no_battery = QLabel("No battery detected on this system")
        no_battery.setFont(QFont("Arial", 10, QFont.Italic))
        battery_layout.addWidget(no_battery, 0, 0, 1, 2)

    content_layout.addWidget(battery_group)

    content_layout.addStretch()
    scroll.setWidget(content_widget)

    tab_layout = QVBoxLayout(hardware_tab)
    tab_layout.setContentsMargins(0, 0, 0, 0)
    tab_layout.addWidget(scroll)
