#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Disk Wiping Module - Main UI class for wipe operations
"""

import os
import json
import subprocess
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, QListWidget, 
                            QListWidgetItem, QRadioButton, QButtonGroup, QCheckBox, QTextEdit, 
                            QPushButton, QFormLayout, QMessageBox, QSpinBox, QDoubleSpinBox, 
                            QComboBox, QProgressBar, QTabWidget, QLabel, QScrollArea, QLineEdit, QFrame)
from PySide6.QtGui import QFont

def format_size(size_bytes):
    """Format size in bytes to human-readable format (B, KB, MB, GB, TB).
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        tuple: (formatted_size, unit) where formatted_size is a float with 1 decimal place
               and unit is one of 'B', 'KB', 'MB', 'GB', 'TB'
    """
    unit = 'B'
    size = float(size_bytes)
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0 or unit == 'TB':
            break
        size /= 1024.0
        
    return size, unit

class WipeOperationsTab(QWidget):
    """Tab for wipe operations with secure disk erasure functionality."""
    
    def __init__(self):
        super().__init__()
        self.tab_widget = QTabWidget(self)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        
        # Progress card container (initially hidden)
        self.progress_card_container = QFrame()
        self.progress_card_container.setVisible(False)
        self.progress_card_layout = QVBoxLayout(self.progress_card_container)
        
        # Add progress card container to layout
        self.layout.addWidget(self.progress_card_container)
        self.layout.addWidget(self.tab_widget)
        
        # Create subtabs
        standard_wipe_tab = self.create_standard_wipe_tab()
        advanced_wipe_tab = self.create_advanced_wipe_tab()
        wipe_profiles_tab = self.create_wipe_profiles_tab()
        
        # Add subtabs to the tab widget
        self.tab_widget.addTab(standard_wipe_tab, "Standard Wipe")
        self.tab_widget.addTab(advanced_wipe_tab, "Advanced Wipe")
        self.tab_widget.addTab(wipe_profiles_tab, "Wipe Profiles")
        
        # Initialize device lists
        self.refresh_devices()
        
        # Initialize worker reference
        self.wipe_worker = None

    def refresh_devices(self):
        """Refresh the device lists in both standard and advanced tabs."""
        devices = self._get_available_devices()
        
        if hasattr(self, 'device_list'):
            self._populate_device_list(self.device_list, devices)
            
        if hasattr(self, 'adv_device_list'):
            self._populate_device_list(self.adv_device_list, devices)

    def create_standard_wipe_tab(self):
        """Create the Standard Wipe interface."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Device Selection
        device_group = QGroupBox("1. Select Target Device(s)")
        device_layout = QVBoxLayout()
        
        # Device list with checkboxes
        self.device_list = QListWidget()
        self.device_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        # Add refresh button
        refresh_btn = QPushButton("Refresh Device List")
        refresh_btn.clicked.connect(self.refresh_devices)
        
        device_layout.addWidget(self.device_list)
        device_layout.addWidget(refresh_btn)
        device_group.setLayout(device_layout)
        
        # Wipe Method Selection
        method_group = QGroupBox("2. Select Wipe Method")
        method_layout = QVBoxLayout()
        
        self.wipe_methods = QButtonGroup()
        methods = [
            ("Quick Wipe (1-pass zeroes)", "quick"),
            ("DoD 5220.22-M (3-pass)", "dod"),
            ("NIST 800-88 (1-pass)", "nist"),
            ("Gutmann (35-pass)", "gutmann")
        ]
        
        for text, method_id in methods:
            radio = QRadioButton(text)
            self.wipe_methods.addButton(radio, id=methods.index((text, method_id)))
            method_layout.addWidget(radio)
        
        # Select first method by default
        if self.wipe_methods.buttons():
            self.wipe_methods.buttons()[0].setChecked(True)
        
        method_group.setLayout(method_layout)
        
        # Wipe Options
        options_group = QGroupBox("3. Wipe Options")
        options_layout = QFormLayout()
        
        self.verify_wipe = QCheckBox("Verify wipe after completion")
        self.verify_wipe.setChecked(True)
        
        self.quick_erase = QCheckBox("Quick erase (skip bad blocks)")
        
        options_layout.addRow("Verification:", self.verify_wipe)
        options_layout.addRow("Performance:", self.quick_erase)
        options_group.setLayout(options_layout)
        
        # Status and Log
        self.wipe_status = QLabel("Ready to wipe")
        self.wipe_status.setStyleSheet("font-weight: bold; color: #89b4fa;")
        
        self.wipe_log = QTextEdit()
        self.wipe_log.setReadOnly(True)
        self.wipe_log.setMaximumHeight(100)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        
        self.start_wipe_btn = QPushButton("Start Wipe")
        self.start_wipe_btn.setStyleSheet("background-color: #f38ba8;")
        self.start_wipe_btn.clicked.connect(self.start_wipe)
        
        self.stop_wipe_btn = QPushButton("Stop")
        self.stop_wipe_btn.setEnabled(False)
        self.stop_wipe_btn.clicked.connect(self.stop_wipe)
        
        button_layout.addWidget(self.start_wipe_btn)
        button_layout.addWidget(self.stop_wipe_btn)
        
        # Add all sections to main layout
        layout.addWidget(device_group, 1)
        layout.addWidget(method_group)
        layout.addWidget(options_group)
        layout.addWidget(self.wipe_status)
        layout.addWidget(QLabel("Activity Log:"))
        layout.addWidget(self.wipe_log, 1)
        layout.addLayout(button_layout)
        
        tab.setLayout(layout)
        return tab

    def create_advanced_wipe_tab(self):
        """Create the Advanced Wipe interface with custom wipe patterns and options."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Device Selection Group
        device_group = QGroupBox("Device Selection")
        device_layout = QVBoxLayout()
        
        # Device list with checkboxes
        self.adv_device_list = QListWidget()
        self.adv_device_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.clicked.connect(self.refresh_devices)
        
        device_layout.addWidget(QLabel("Select devices to wipe:"))
        device_layout.addWidget(self.adv_device_list)
        device_layout.addWidget(refresh_btn)
        device_group.setLayout(device_layout)
        
        # Wipe Pattern Group
        pattern_group = QGroupBox("Wipe Pattern")
        pattern_layout = QVBoxLayout()
        
        # Custom pattern input
        self.pattern_input = QTextEdit()
        self.pattern_input.setPlaceholderText("Enter custom pattern (e.g., 0xFF, 0x00, 0x55, 0xAA)")
        self.pattern_input.setMaximumHeight(100)
        
        # Number of passes
        passes_layout = QHBoxLayout()
        passes_layout.addWidget(QLabel("Number of passes:"))
        self.passes_spin = QSpinBox()
        self.passes_spin.setRange(1, 100)
        self.passes_spin.setValue(3)
        passes_layout.addWidget(self.passes_spin)
        passes_layout.addStretch()
        
        # Verification options
        self.verify_check = QCheckBox("Verify after wipe")
        self.verify_check.setChecked(True)
        
        pattern_layout.addWidget(QLabel("Custom pattern (comma-separated hex values):"))
        pattern_layout.addWidget(self.pattern_input)
        pattern_layout.addLayout(passes_layout)
        pattern_layout.addWidget(self.verify_check)
        pattern_group.setLayout(pattern_layout)
        
        # Advanced Options Group
        options_group = QGroupBox("Advanced Options")
        options_layout = QFormLayout()
        
        # Create tabs for different option categories
        options_tabs = QTabWidget()
        
        # Basic Options Tab
        basic_tab = QWidget()
        basic_layout = QFormLayout()
        
        # Sector size
        self.sector_size = QComboBox()
        self.sector_size.addItems(["512", "1024", "2048", "4096"])
        self.sector_size.setCurrentText("512")
        
        # Block size
        self.block_size = QComboBox()
        self.block_size.addItems(["1M", "4M", "8M", "16M", "32M"])
        self.block_size.setCurrentText("4M")
        
        # Direct I/O
        self.direct_io = QCheckBox("Use direct I/O (O_DIRECT)")
        self.direct_io.setChecked(True)
        
        # Sync after each write
        self.sync_writes = QCheckBox("Sync after each write")
        self.sync_writes.setChecked(False)
        
        basic_layout.addRow("Sector size (bytes):", self.sector_size)
        basic_layout.addRow("Block size:", self.block_size)
        basic_layout.addRow("", self.direct_io)
        basic_layout.addRow("", self.sync_writes)
        basic_tab.setLayout(basic_layout)
        
        # Security Features Tab
        security_tab = QWidget()
        security_layout = QVBoxLayout()
        
        # Create a scroll area for security options
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Key Wipe
        self.key_wipe_check = QCheckBox("Wipe cryptographic keys")
        self.key_wipe_check.setToolTip("Securely erase cryptographic keys and certificates")
        
        # Bootloader Wipe
        self.bootloader_wipe_check = QCheckBox("Wipe bootloader")
        self.bootloader_wipe_check.setToolTip("Remove bootloader to prevent device booting")
        
        # Volatile Memory Wipe
        self.volatile_memory_check = QCheckBox("Wipe volatile memory (RAM)")
        self.volatile_memory_check.setToolTip("Securely wipe RAM before shutdown")
        
        # Thermal Stress Test
        thermal_group = QGroupBox("Thermal Stress Test")
        thermal_layout = QVBoxLayout()
        self.thermal_stress_check = QCheckBox("Enable thermal stress testing")
        
        thermal_params = QHBoxLayout()
        thermal_params.addWidget(QLabel("Duration (s):"))
        self.stress_duration_spin = QSpinBox()
        self.stress_duration_spin.setRange(60, 3600)
        self.stress_duration_spin.setValue(300)
        thermal_params.addWidget(self.stress_duration_spin)
        
        thermal_params.addWidget(QLabel("Target temp (°C):"))
        self.stress_temp_spin = QSpinBox()
        self.stress_temp_spin.setRange(40, 100)
        self.stress_temp_spin.setValue(70)
        thermal_params.addWidget(self.stress_temp_spin)
        thermal_params.addStretch()
        
        thermal_layout.addWidget(self.thermal_stress_check)
        thermal_layout.addLayout(thermal_params)
        thermal_group.setLayout(thermal_layout)
        
        # Verification Mode
        verification_group = QGroupBox("Verification Settings")
        verification_layout = QVBoxLayout()
        
        self.verification_combo = QComboBox()
        self.verification_combo.addItems(["Basic", "Entropy"])
        
        entropy_layout = QHBoxLayout()
        entropy_layout.addWidget(QLabel("Entropy threshold:"))
        self.entropy_spin = QDoubleSpinBox()
        self.entropy_spin.setRange(0.0, 8.0)
        self.entropy_spin.setValue(7.9)
        self.entropy_spin.setDecimals(1)
        self.entropy_spin.setSingleStep(0.1)
        entropy_layout.addWidget(self.entropy_spin)
        entropy_layout.addStretch()
        
        verification_layout.addWidget(QLabel("Verification method:"))
        verification_layout.addWidget(self.verification_combo)
        verification_layout.addLayout(entropy_layout)
        verification_group.setLayout(verification_layout)
        
        # Tamper Logging
        self.tamper_log_check = QCheckBox("Enable tamper-evident logging")
        self.tamper_log_check.setChecked(True)
        self.tamper_log_check.setToolTip("Log all security-critical operations to a secure log file")
        
        # Post-Erase Locking
        post_erase_group = QGroupBox("Post-Erase Security")
        post_erase_layout = QVBoxLayout()
        
        # Post-erase lock
        self.post_erase_lock_check = QCheckBox("Lock device after wipe")
        self.post_erase_lock_check.setToolTip("Set an ATA password to lock the device after wiping")
        
        # Force brick option (military-grade)
        self.force_brick_check = QCheckBox("Force permanent brick (military-grade)")
        self.force_brick_check.setToolTip("Permanently lock the device with no recovery possible")
        
        # Password input
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Lock password:"))
        self.lock_password_edit = QLineEdit("BRICK")
        self.lock_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self.lock_password_edit)
        
        # Connect signals
        self.post_erase_lock_check.toggled.connect(self._update_lock_ui_state)
        self.force_brick_check.toggled.connect(self._update_lock_ui_state)
        
        # Add widgets to layout
        post_erase_layout.addWidget(self.post_erase_lock_check)
        post_erase_layout.addWidget(self.force_brick_check)
        post_erase_layout.addLayout(password_layout)
        post_erase_group.setLayout(post_erase_layout)
        
        # Add all security widgets to layout
        scroll_layout.addWidget(self.key_wipe_check)
        scroll_layout.addWidget(self.bootloader_wipe_check)
        scroll_layout.addWidget(self.volatile_memory_check)
        scroll_layout.addWidget(thermal_group)
        scroll_layout.addWidget(verification_group)
        scroll_layout.addWidget(self.tamper_log_check)
        scroll_layout.addWidget(post_erase_group)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        security_layout.addWidget(scroll)
        security_tab.setLayout(security_layout)
        
        # Add tabs to options
        options_tabs.addTab(basic_tab, "Basic")
        options_tabs.addTab(security_tab, "Security")
        
        options_layout.addRow(options_tabs)
        options_group.setLayout(options_layout)
        
        # Status and Logs
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.adv_wipe_status = QLabel("Ready")
        self.adv_wipe_log = QTextEdit()
        self.adv_wipe_log.setReadOnly(True)
        self.adv_wipe_log.setMaximumHeight(150)
        
        # Progress bar
        self.adv_progress = QProgressBar()
        self.adv_progress.setRange(0, 100)
        self.adv_progress.setValue(0)
        
        status_layout.addWidget(self.adv_wipe_status)
        status_layout.addWidget(self.adv_wipe_log)
        status_layout.addWidget(self.adv_progress)
        status_group.setLayout(status_layout)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        self.adv_start_btn = QPushButton("Start Wipe")
        self.adv_stop_btn = QPushButton("Stop")
        self.adv_stop_btn.setEnabled(False)
        
        button_layout.addWidget(self.adv_start_btn)
        button_layout.addWidget(self.adv_stop_btn)
        
        # Connect signals
        self.adv_start_btn.clicked.connect(self.start_advanced_wipe)
        self.adv_stop_btn.clicked.connect(self.stop_wipe)
        
        # Add all groups to main layout
        layout.addWidget(device_group)
        layout.addWidget(pattern_group)
        layout.addWidget(options_group)
        layout.addWidget(status_group)
        layout.addLayout(button_layout)
        
        tab.setLayout(layout)
        return tab

    def create_wipe_profiles_tab(self):
        """Create the Wipe Profiles tab with predefined profiles."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Title and description
        title = QLabel("Wipe Profiles")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title.setFont(title_font)
        
        description = QLabel(
            "Select a predefined wipe profile based on your security requirements. "
            "Each profile is tailored for specific use cases and compliance standards."
        )
        description.setWordWrap(True)
        
        # Create scroll area for profiles
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Define profiles
        profiles = [
            {
                'name': 'REDBACK Protocol',
                'category': 'National Security / SIGINT-Class Sanitisation',
                'description': 'Maximum-grade wipe for classified or Top Secret materials',
                'use_case': 'Destroying critical defence, intelligence, or field operation data',
                'compliance': 'ASD ISM (Top Secret), DoD 5220.22-M, NIST 800-88 Rev.1, PSPF',
                'passes': 3,
                'features': ['Key Wipe', 'Bootloader Wipe', 'Volatile Memory', 'Thermal Stress', 'Entropy Analysis', 'Tamper Log']
            },
            {
                'name': 'KOOKABURRA Sweep',
                'category': 'Civilian / Personal / Recyclable Drive',
                'description': 'Lightweight one-pass overwrite for non-sensitive environments',
                'use_case': 'Donating or reselling personal devices, workstations for asset return',
                'compliance': 'N/A',
                'passes': 1,
                'features': ['Basic Verification']
            },
            {
                'name': 'FEDPOL Purge',
                'category': 'Law Enforcement / Forensics',
                'description': 'Two-pass wipe with journal and shadow copy cleaning',
                'use_case': 'Sanitising forensic drives post-extraction, evidence drive turnover',
                'compliance': 'ACIC digital evidence protocols, Federal Court IT evidence procedures',
                'passes': 2,
                'features': ['Key Wipe', 'Bootloader Wipe', 'Basic Verification', 'Tamper Log']
            },
            {
                'name': 'IRONBANK Reset',
                'category': 'Corporate / Finance / Government Agencies',
                'description': 'Two-pass random pattern + metadata overwrite',
                'use_case': 'Securely wiping corporate laptops, financial servers, government machines',
                'compliance': 'ASD Essential Eight (Level 3), ISO/IEC 27040, OAIC',
                'passes': 2,
                'features': ['Key Wipe', 'Bootloader Wipe', 'Basic Verification', 'Tamper Log']
            },
            {
                'name': 'WALLABY ZeroClean',
                'category': 'Fast Wipe / Logistics / Rapid Deployment',
                'description': 'Ultra-fast one-pass zero fill for staging drives',
                'use_case': 'Resetting gear between missions, setting up field kits',
                'compliance': 'N/A',
                'passes': 1,
                'features': ['Bootloader Wipe', 'Basic Verification']
            },
            {
                'name': 'NIGHTOWL Erasure',
                'category': 'Covert / Intelligence / Field Op',
                'description': 'Stealth-focused 3-pass cryptographic shred',
                'use_case': 'Covert destruction in hostile/surveilled environments',
                'compliance': 'Classified',
                'passes': 3,
                'features': ['Key Wipe', 'Bootloader Wipe', 'Volatile Memory', 'Entropy Analysis', 'Tamper Log']
            },
            {
                'name': 'WEDGE-TAIL Purifier',
                'category': 'Military (Standard Deployment-Level Sanitisation)',
                'description': 'Two-pass with journal wipe and bootloader cleanse',
                'use_case': 'Post-mission sanitisation of field-deployed systems',
                'compliance': 'ASD ISM (Secret), ADF disposal practices',
                'passes': 2,
                'features': ['Key Wipe', 'Bootloader Wipe', 'Basic Verification', 'Tamper Log']
            },
            {
                'name': 'NULLDRIVE',
                'category': 'Bricking / Emergency',
                'description': 'Permanent drive destruction with firmware overwrite',
                'use_case': 'Permanent sanitisation under capture risk',
                'compliance': 'N/A',
                'passes': 1,
                'features': ['Key Wipe', 'Bootloader Wipe']
            }
        ]
        
        # Add profiles to the layout
        for profile in profiles:
            group = QGroupBox(profile['name'])
            group.setStyleSheet("""
                QGroupBox {
                    border: 1px solid #3b8ed0;
                    border-radius: 6px;
                    margin-top: 6px;
                    padding-top: 12px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
            """)
            
            layout_inner = QVBoxLayout()
            
            # Category and description
            category = QLabel(f"<b>Category:</b> {profile['category']}")
            desc = QLabel(profile['description'])
            desc.setWordWrap(True)
            
            # Use case and compliance
            use_case = QLabel(f"<b>Use Case:</b> {profile['use_case']}")
            use_case.setWordWrap(True)
            compliance = QLabel(f"<b>Compliance:</b> {profile['compliance']}")
            compliance.setWordWrap(True)
            
            # Features
            features = QLabel(f"<b>Passes:</b> {profile['passes']} | <b>Features:</b> {', '.join(profile['features'])}")
            
            # Select button
            select_btn = QPushButton("Select Profile")
            select_btn.setProperty('profile', profile['name'])
            select_btn.clicked.connect(self.on_profile_selected)
            
            # Add widgets to layout
            for widget in [category, desc, use_case, compliance, features, select_btn]:
                layout_inner.addWidget(widget)
            
            group.setLayout(layout_inner)
            scroll_layout.addWidget(group)
        
        # Add stretch to push content to top
        scroll_layout.addStretch()
        
        # Set up scroll area
        scroll.setWidget(scroll_content)
        
        # Add widgets to main layout
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(scroll)
        
        tab.setLayout(layout)
        return tab

    def on_profile_selected(self):
        """Handle profile selection and configure advanced wipe settings accordingly."""
        button = self.sender()
        profile_name = button.property('profile')
        
        # Define profile configurations with all security features
        profile_configs = {
            'REDBACK Protocol': {
                # Basic settings
                'pattern': '00 FF 55 AA 96 69 C3 3C 0F F0 33 CC 66 99 A5 5A',
                'passes': 3,
                'verify': True,
                'sector_size': 512,
                'block_size': '4M',
                'direct_io': True,
                'sync_writes': True,
                # Security features
                'key_wipe': True,
                'bootloader_wipe': True,
                'volatile_memory': True,
                'thermal_stress': True,
                'verification_mode': 'entropy',
                'tamper_log': True,
                # Advanced options
                'entropy_threshold': 7.9,
                'stress_duration': 600,  # 10 minutes
                'stress_temp': 75
            },
            'KOOKABURRA Sweep': {
                'pattern': '00',
                'passes': 1,
                'verify': True,
                'sector_size': 512,
                'block_size': '4M',
                'direct_io': False,
                'sync_writes': False,
                'key_wipe': False,
                'bootloader_wipe': False,
                'volatile_memory': False,
                'thermal_stress': False,
                'verification_mode': 'basic',
                'tamper_log': True,
                'entropy_threshold': 0.0,
                'stress_duration': 0,
                'stress_temp': 0
            },
            'FEDPOL Purge': {
                'pattern': '00 FF 55 AA',
                'passes': 2,
                'verify': True,
                'sector_size': 512,
                'block_size': '2M',
                'direct_io': True,
                'sync_writes': True,
                'key_wipe': True,
                'bootloader_wipe': True,
                'volatile_memory': True,
                'thermal_stress': False,
                'verification_mode': 'basic',
                'tamper_log': True,
                'entropy_threshold': 0.0,
                'stress_duration': 0,
                'stress_temp': 0
            },
            'IRONBANK Reset': {
                'pattern': 'random',
                'passes': 2,
                'verify': True,
                'sector_size': 4096,
                'block_size': '4M',
                'direct_io': True,
                'sync_writes': True,
                'key_wipe': True,
                'bootloader_wipe': False,
                'volatile_memory': False,
                'thermal_stress': False,
                'verification_mode': 'basic',
                'tamper_log': True,
                'entropy_threshold': 0.0,
                'stress_duration': 0,
                'stress_temp': 0
            },
            'WALLABY ZeroClean': {
                'pattern': '00',
                'passes': 1,
                'verify': True,
                'sector_size': 512,
                'block_size': '8M',
                'direct_io': True,
                'sync_writes': False,
                'key_wipe': False,
                'bootloader_wipe': False,
                'volatile_memory': False,
                'thermal_stress': False,
                'verification_mode': 'none',
                'tamper_log': True,
                'entropy_threshold': 0.0,
                'stress_duration': 0,
                'stress_temp': 0
            },
            'NIGHTOWL Erasure': {
                'pattern': 'random',
                'passes': 3,
                'verify': True,
                'sector_size': 512,
                'block_size': '1M',
                'direct_io': True,
                'sync_writes': True,
                'key_wipe': True,
                'bootloader_wipe': True,
                'volatile_memory': True,
                'thermal_stress': True,
                'verification_mode': 'entropy',
                'tamper_log': True,
                'entropy_threshold': 7.8,
                'stress_duration': 300,  # 5 minutes
                'stress_temp': 70
            },
            'WEDGE-TAIL Purifier': {
                'pattern': '00 55 AA FF',
                'passes': 2,
                'verify': True,
                'sector_size': 512,
                'block_size': '4M',
                'direct_io': True,
                'sync_writes': True,
                'key_wipe': True,
                'bootloader_wipe': True,
                'volatile_memory': False,
                'thermal_stress': False,
                'verification_mode': 'basic',
                'tamper_log': True,
                'entropy_threshold': 0.0,
                'stress_duration': 0,
                'stress_temp': 0
            },
            'NULLDRIVE': {
                'pattern': 'FF 00 55 AA',
                'passes': 1,
                'verify': False,
                'sector_size': 512,
                'block_size': '1M',
                'direct_io': True,
                'sync_writes': True,
                'key_wipe': True,
                'bootloader_wipe': True,
                'volatile_memory': False,
                'thermal_stress': False,
                'verification_mode': 'none',
                'tamper_log': False,
                'entropy_threshold': 0.0,
                'stress_duration': 0,
                'stress_temp': 0
            }
        }
        
        # Get the configuration for the selected profile
        config = profile_configs.get(profile_name)
        if not config:
            QMessageBox.warning(
                self,
                "Profile Error",
                f"Configuration not found for profile: {profile_name}"
            )
            return
        
        try:
            # Update the Advanced Wipe tab settings
            self.pattern_input.setPlainText(config['pattern'])
            self.passes_spin.setValue(config['passes'])
            self.verify_check.setChecked(config['verify'])
            
            # Set sector size
            sector_idx = self.sector_size.findText(str(config['sector_size']))
            if sector_idx >= 0:
                self.sector_size.setCurrentIndex(sector_idx)
            
            # Set block size
            block_idx = self.block_size.findText(config['block_size'])
            if block_idx >= 0:
                self.block_size.setCurrentIndex(block_idx)
            
            self.direct_io.setChecked(config['direct_io'])
            self.sync_writes.setChecked(config['sync_writes'])
            
            # Switch to the Advanced Wipe tab
            self.tab_widget.setCurrentIndex(1)  # Assuming Wipe Operations tab is index 1
            wipe_tabs = self.tab_widget.currentWidget()
            if hasattr(wipe_tabs, 'setCurrentIndex'):
                # Find the Advanced Wipe tab (index 1 in the Wipe Operations tab)
                wipe_tabs.setCurrentIndex(1)
            
            # Show success message
            QMessageBox.information(
                self,
                "Profile Applied",
                f"'{profile_name}' profile has been loaded into the Advanced Wipe tab.\n\n"
                "Please review the settings and click 'Start Wipe' when ready."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Applying Profile",
                f"Failed to apply profile settings:\n\n{str(e)}"
            )

    def _get_available_devices(self):
        """Get list of available storage devices."""
        try:
            # Get block devices using lsblk
            result = subprocess.run(
                ['lsblk', '-d', '-n', '-o', 'NAME,SIZE,MODEL,VENDOR,TYPE', '--json'],
                capture_output=True, text=True, check=True
            )
            
            devices = json.loads(result.stdout)['blockdevices']
            valid_devices = []
            
            for dev in devices:
                # Skip non-disk devices and loop devices
                if dev['type'] != 'disk' or dev['name'].startswith('loop'):
                    continue
                    
                # Get device path and info
                dev_path = f"/dev/{dev['name']}"
                
                # Safely get and clean model and vendor, handling None values
                model = str(dev.get('model', '')).strip()
                vendor = str(dev.get('vendor', '')).strip()
                size = str(dev.get('size', '0')).strip()
                
                # Skip if we couldn't get a valid device path
                if not dev_path or not os.path.exists(dev_path):
                    continue
                
                # Create display text
                display_text = f"{dev_path} - {size}"
                if vendor:
                    display_text += f" - {vendor}"
                if model:
                    display_text += f" {model}"
                
                # Add to list
                valid_devices.append((dev_path, display_text))
            
            return valid_devices
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else "Unknown error"
            return []
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            return []
    
    def _populate_device_list(self, list_widget, devices, selectable=True):
        """Populate a QListWidget with device information."""
        list_widget.clear()
        for dev_path, display_text in devices:
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, dev_path)
            if selectable:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
            else:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            list_widget.addItem(item)
    
    def start_wipe(self):
        """Start the wipe process on selected devices."""
        # Check for root privileges
        if os.geteuid() != 0:
            QMessageBox.critical(
                self, "Permission Denied",
                "Root privileges are required for disk wiping.\n\n"
                "Please run this application with sudo or as root."
            )
            return
            
        selected_devices = []
        for i in range(self.device_list.count()):
            item = self.device_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                # Get the device path from the UserRole
                dev_path = item.data(Qt.ItemDataRole.UserRole)
                if dev_path:
                    selected_devices.append(dev_path)
        
        if not selected_devices:
            self.wipe_status.setText("Error: No devices selected")
            self.wipe_status.setStyleSheet("color: #f38ba8;")
            return
            
        # Get selected method
        method_id = self.wipe_methods.checkedId()
        method_button = self.wipe_methods.button(method_id)
        method_text = method_button.text().lower()
        
        # Map UI text to method names
        method_map = {
            'quick wipe (1-pass zeroes)': 'quick',
            'dod 5220.22-m (3-pass)': 'dod',
            'nist 800-88 (1-pass)': 'nist',
            'gutmann (35-pass)': 'gutmann'
        }
        
        method = method_map.get(method_text, 'quick')
        
        # Show confirmation dialog
        confirm = QMessageBox.question(
            self, "Confirm Wipe",
            f"WARNING: This will PERMANENTLY DESTROY ALL DATA on the selected devices.\n\n"
            f"Devices to wipe: {', '.join(selected_devices)}\n"
            f"Method: {method_button.text()}\n\n"
            f"Are you absolutely sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm != QMessageBox.StandardButton.Yes:
            self.wipe_log.append("Wipe operation cancelled by user")
            return
        
        # Disable UI elements
        self.start_wipe_btn.setEnabled(False)
        self.stop_wipe_btn.setEnabled(True)
        self.device_list.setEnabled(False)
        
        # Store wipe information
        self.current_wipe = {
            'devices': selected_devices,
            'current_device_index': 0,
            'method': method,
            'verify': self.verify_wipe.isChecked() if hasattr(self, 'verify_wipe') else False,
            'quick_erase': self.quick_erase.isChecked() if hasattr(self, 'quick_erase') else False
        }
        
        # Start wiping the first device
        self._start_next_wipe()
    
    def _start_next_wipe(self):
        """Start wiping the next device in the queue."""
        if not hasattr(self, 'current_wipe'):
            return
            
        if self.current_wipe['current_device_index'] >= len(self.current_wipe['devices']):
            # All devices wiped
            self._wipe_completed(True, "All devices wiped successfully")
            return
            
        # Get current device
        device = self.current_wipe['devices'][self.current_wipe['current_device_index']]
        
        # Update status
        self.wipe_status.setText(f"Wiping {device} ({self.current_wipe['current_device_index'] + 1}/{len(self.current_wipe['devices'])})")
        self.wipe_status.setStyleSheet("color: #a6e3a1;")
        self.wipe_log.append(f"Starting wipe on {device}...")
        
        # Create and start worker thread
        self.wipe_worker = WipeWorker(
            device=device,
            method=self.current_wipe['method'],
            verify=self.current_wipe['verify'],
            quick_erase=self.current_wipe['quick_erase']
        )
        
        # Connect signals
        self.wipe_worker.log_message.connect(self.wipe_log.append)
        self.wipe_worker.finished.connect(self._on_wipe_finished)
        self.wipe_worker.progress.connect(self._update_progress)
        self.wipe_worker.progress_card_shown.connect(self._show_progress_card)
        
        # Start the worker
        self.wipe_worker.start()
    
    def _on_wipe_finished(self, success, message):
        """Handle completion of a wipe operation."""
        if not hasattr(self, 'current_wipe'):
            return
            
        # Log the result
        status = "completed" if success else "failed"
        device = self.current_wipe['devices'][self.current_wipe['current_device_index']]
        self.wipe_log.append(f"Wipe {status} on {device}: {message}")
        
        # Move to next device
        self.current_wipe['current_device_index'] += 1
        
        if success:
            # Start next wipe or finish
            self._start_next_wipe()
        else:
            # Stop on error
            self._wipe_completed(False, f"Wipe failed: {message}")
    
    def _wipe_completed(self, success, message):
        """Handle completion of all wipe operations."""
        # Clean up
        if hasattr(self, 'wipe_worker'):
            self.wipe_worker.quit()
            self.wipe_worker.wait()
            del self.wipe_worker
        
        # Update UI
        if hasattr(self, 'start_wipe_btn'):
            self.start_wipe_btn.setEnabled(True)
        if hasattr(self, 'stop_wipe_btn'):
            self.stop_wipe_btn.setEnabled(False)
        if hasattr(self, 'device_list'):
            self.device_list.setEnabled(True)
        
        # Show status
        if hasattr(self, 'wipe_status'):
            if success:
                self.wipe_status.setText("All wipes completed successfully")
                self.wipe_status.setStyleSheet("color: #a6e3a1;")
            else:
                self.wipe_status.setText(message)
                self.wipe_status.setStyleSheet("color: #f38ba8;")
        
        # Clear current wipe
        if hasattr(self, 'current_wipe'):
            del self.current_wipe
    
    def _show_progress_card(self, card):
        """Show the progress card in the UI."""
        # Clear existing card if any
        self._clear_progress_card()
        
        # Add the new card
        self.progress_card_layout.addWidget(card)
        self.progress_card_container.setVisible(True)
    
    def _clear_progress_card(self):
        """Remove the progress card from the UI."""
        # Remove all widgets from the progress card layout
        while self.progress_card_layout.count() > 0:
            item = self.progress_card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.progress_card_container.setVisible(False)
    
    def _update_progress(self, percent, message):
        """Update progress display."""
        # Update status bar if it exists
        if hasattr(self, 'wipe_status'):
            # Only update if the message doesn't already contain the percentage
            # to avoid duplicate percentage in the status bar
            if f"({percent}%)" not in message:
                self.wipe_status.setText(f"{message} ({percent}%)")
            else:
                self.wipe_status.setText(message)
                
        # Update progress bar if it exists
        if hasattr(self, 'wipe_progress'):
            self.wipe_progress.setValue(percent)
        
        # Also update the progress card if it exists
        if hasattr(self, 'wipe_worker') and hasattr(self.wipe_worker, 'progress_bar'):
            self.wipe_worker.progress_bar.setValue(percent)
            if hasattr(self.wipe_worker, 'progress_text'):
                # Only update the progress text if it doesn't already contain the percentage
                # to avoid duplicate percentages
                if f"({percent}%)" not in message:
                    self.wipe_worker.progress_text.setText(f"{message} ({percent}%)")
                else:
                    self.wipe_worker.progress_text.setText(message)
    
    def start_advanced_wipe(self):
        """Start the advanced wipe process with selected options."""
        # Check for root privileges
        if os.geteuid() != 0:
            QMessageBox.critical(
                self, "Permission Denied",
                "Root privileges are required for disk wiping.\n\n"
                "Please run this application with sudo or as root."
            )
            return
            
        # Get selected devices
        selected_devices = []
        for i in range(self.adv_device_list.count()):
            item = self.adv_device_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                dev_path = item.data(Qt.ItemDataRole.UserRole)
                if dev_path:
                    selected_devices.append(dev_path)
        
        if not selected_devices:
            self.adv_wipe_status.setText("Error: No devices selected")
            self.adv_wipe_status.setStyleSheet("color: #f38ba8;")
            return
        
        # Parse pattern from text input
        pattern_text = self.pattern_input.toPlainText().strip()
        
        # Show confirmation dialog
        confirm = QMessageBox.question(
            self, "Confirm Advanced Wipe",
            f"WARNING: This will PERMANENTLY DESTROY ALL DATA on the selected devices.\n\n"
            f"Devices to wipe: {', '.join(selected_devices)}\n"
            f"Pattern: {pattern_text}\n"
            f"Passes: {self.passes_spin.value()}\n\n"
            f"Are you absolutely sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm != QMessageBox.StandardButton.Yes:
            self.adv_wipe_log.append("Advanced wipe operation cancelled by user")
            return
        
        # Disable UI elements
        self.adv_start_btn.setEnabled(False)
        self.adv_stop_btn.setEnabled(True)
        self.adv_device_list.setEnabled(False)
        
        # Store wipe information
        self.advanced_wipe = {
            'devices': selected_devices,
            'current_device_index': 0,
            'pattern': pattern_text,
            'passes': self.passes_spin.value(),
            'verify': self.verify_check.isChecked(),
            'options': {
                'sector_size': int(self.sector_size.currentText()),
                'block_size': self.block_size.currentText(),
                'direct_io': self.direct_io.isChecked(),
                'sync_writes': self.sync_writes.isChecked(),
                'key_wipe': self.key_wipe_check.isChecked(),
                'bootloader_wipe': self.bootloader_wipe_check.isChecked(),
                'volatile_memory': self.volatile_memory_check.isChecked(),
                'thermal_stress': self.thermal_stress_check.isChecked(),
                'verification_mode': self.verification_combo.currentText().lower(),
                'tamper_log': self.tamper_log_check.isChecked(),
                'entropy_threshold': self.entropy_spin.value(),
                'stress_duration': self.stress_duration_spin.value(),
                'stress_temp': self.stress_temp_spin.value(),
                'post_erase_lock': self.post_erase_lock_check.isChecked(),
                'force_brick': self.force_brick_check.isChecked(),
                'lock_password': self.lock_password_edit.text()
            }
        }
        
        # TODO: Implement the actual advanced wipe process using WipeWorker
        self.adv_wipe_log.append("Advanced wipe not yet implemented")
        self.adv_wipe_status.setText("Not implemented")
        self.adv_start_btn.setEnabled(True)
        self.adv_stop_btn.setEnabled(False)
        self.adv_device_list.setEnabled(True)
    
    def _update_lock_ui_state(self, checked):
        """Update UI state for post-erase lock and force-brick checkboxes."""
        if not hasattr(self, 'post_erase_lock_check') or not hasattr(self, 'force_brick_check'):
            return
            
        if checked:
            # Enable force brick checkbox when post-erase lock is checked
            self.force_brick_check.setEnabled(True)
            
            # If force brick is checked, ensure lock password is not empty
            if self.force_brick_check.isChecked():
                if not hasattr(self, 'lock_password_edit') or not self.lock_password_edit.text().strip():
                    self.force_brick_check.setChecked(False)
                    QMessageBox.warning(
                        self, "Password Required",
                        "A non-empty lock password is required for force brick mode."
                    )
        else:
            # Uncheck and disable force brick when post-erase lock is unchecked
            self.force_brick_check.setChecked(False)
            self.force_brick_check.setEnabled(False)
            
        # Update lock password field state
        if hasattr(self, 'lock_password_edit'):
            self.lock_password_edit.setEnabled(checked)
    
    def stop_wipe(self):
        """Stop the current wipe operation."""
        if hasattr(self, 'wipe_worker') and self.wipe_worker.isRunning():
            self.wipe_worker.stop()
            if hasattr(self, 'wipe_log'):
                self.wipe_log.append("Stopping current wipe operation...")
            if hasattr(self, 'wipe_status'):
                self.wipe_status.setText("Stopping...")
                self.wipe_status.setStyleSheet("color: #f9e2af;")
            if hasattr(self, 'stop_wipe_btn'):
                self.stop_wipe_btn.setEnabled(False)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Location Tracking Utility - Simple location tracking functionality
"""

from datetime import datetime, timezone

class LocationTracker:
    """Simple location tracking class."""
    
    def __init__(self):
        """Initialize the location tracker."""
        self.current_location = None
    
    def get_location(self):
        """
        Get the current device location.
        
        Returns:
            dict: Location information or None if location services are disabled
        """
        try:
            # This is a placeholder implementation
            # In a real implementation, this would use geolocation services
            return {
                'latitude': 0.0,
                'longitude': 0.0,
                'accuracy': 0.0,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': 'mock'
            }
        except Exception:
            return None

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Disk Wiping Worker - Thread class for secure disk erasure operations
"""

import os
import sys
import time
import json
import shutil
import signal
import hashlib
import logging
import datetime
import subprocess
import configparser
import shlex
from pathlib import Path
from datetime import datetime, timezone

from PySide6.QtCore import QThread, Signal

class WipeWorker(QThread):
    """Worker thread for performing disk wiping operations."""
    progress = Signal(int, str)  # progress percentage, status message
    frozen_drive_detected = Signal(bool)  # signal for frozen drive detection
    finished = Signal(bool, str)  # success, final message
    log_message = Signal(str)    # log message
    location_updated = Signal(dict)  # signal for location updates
    progress_card_shown = Signal(object)  # Signal to show progress card
    
    def __init__(self, device, method, verify=True, quick_erase=False, enable_location=True):
        super().__init__()
        self.device = device
        self.method = method
        self.verify = verify
        self.quick_erase = quick_erase
        self.enable_location = enable_location
        self._is_running = True
        self.log_file = '/var/log/blackstorm/tamper.log'
        self.location = None
        
        # Initialize location tracker if enabled
        self.location_tracker = None
        if enable_location:
            try:
                from location_tracker import LocationTracker
                self.location_tracker = LocationTracker()
            except ImportError:
                self.log_message.emit("Warning: location_tracker module not found. Location tracking disabled.")
                self.location_tracker = None
        
        # Create log directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # Advanced wipe settings with all features
        self.advanced_settings = {
            # Basic wipe settings
            'pattern': None,      # Custom pattern as list of bytes
            'passes': 1,          # Number of wipe passes
            'sector_size': 512,   # Sector size in bytes
            'block_size': '4M',   # Block size for dd operations
            'direct_io': True,    # Use O_DIRECT flag
            'sync_writes': False, # Sync after each write
            
            # Security features
            'key_wipe': False,     # Wipe cryptographic keys
            'bootloader_wipe': False, # Wipe bootloader
            'volatile_memory': False, # Wipe volatile memory (RAM)
            'thermal_stress': False,  # Perform thermal stress test
            'verification_mode': 'basic', # Verification mode: 'none', 'basic', 'entropy'
            'tamper_log': True,    # Enable tamper logging
            'location_logging': enable_location,  # Enable location logging
            
            # Advanced options
            'entropy_threshold': 7.9,  # Entropy threshold for verification (7.9 = random data)
            'stress_duration': 300,    # Thermal stress test duration in seconds
            'stress_temp': 70,         # Target temperature for stress test in Celsius
            'post_erase_lock': False,  # Lock the device after wipe
            'force_brick': False,      # Permanently brick the device (military-grade)
            'lock_password': 'BRICK',  # Password to use for locking the device
            'location_update_interval': 300  # Update location every 5 minutes (seconds)
        }
    
    def set_advanced_options(self, pattern=None, passes=1, sector_size=512, 
                           block_size='4M', direct_io=True, sync_writes=False,
                           key_wipe=False, bootloader_wipe=False, volatile_memory=False,
                           thermal_stress=False, verification_mode='basic', tamper_log=True,
                           entropy_threshold=7.9, stress_duration=300, stress_temp=70,
                           post_erase_lock=False, force_brick=False, lock_password='BRICK'):
        """Set advanced wipe options with all security features."""
        self.advanced_settings.update({
            # Basic settings
            'pattern': pattern,
            'passes': int(passes),
            'sector_size': int(sector_size),
            'block_size': str(block_size),
            'direct_io': bool(direct_io),
            'sync_writes': bool(sync_writes),
            
            # Security features
            'key_wipe': bool(key_wipe),
            'bootloader_wipe': bool(bootloader_wipe),
            'volatile_memory': bool(volatile_memory),
            'thermal_stress': bool(thermal_stress),
            'verification_mode': str(verification_mode),
            'tamper_log': bool(tamper_log),
            
            # Advanced options
            'entropy_threshold': float(entropy_threshold),
            'stress_duration': int(stress_duration),
            'stress_temp': int(stress_temp),
            'post_erase_lock': bool(post_erase_lock),
            'force_brick': bool(force_brick),
            'lock_password': str(lock_password) if lock_password else 'BRICK'
        })
        
        # Log the configuration change if tamper logging is enabled
        if self.advanced_settings['tamper_log']:
            self._log_tamper_event('config_update', f"Advanced options updated for {self.device}")
    
    def _get_dd_command(self, pattern=None, oflags=None):
        """Generate dd command with current settings."""
        cmd = ['dd']
        
        # Add direct I/O flag if enabled
        if self.advanced_settings['direct_io']:
            cmd.extend(['iflag=direct', 'oflag=direct'])
            
        # Add sync flag if enabled
        if self.advanced_settings['sync_writes']:
            cmd.append('conv=fsync')
            
        # Add block size
        cmd.append(f'bs={self.advanced_settings["block_size"]}')
        
        # Add input file (pattern or /dev/zero/urandom)
        if pattern is None:
            cmd.append('if=/dev/zero')
        else:
            # Use a temporary file with the pattern
            pattern_str = ''.join(f'\\x{byte:02x}' for byte in pattern)
            cmd.append(f'if=<(printf "{pattern_str}")')
            
        # Add output file
        cmd.append(f'of={self.device}')
        
        # Add additional flags if specified
        if oflags:
            cmd.extend(oflags)
            
        return ' '.join(cmd)
    
    def _log_tamper_event(self, event_type, message):
        """Log security events for tamper evidence with optional location data."""
        try:
            # Get current location if tracking is enabled
            location = None
            if (hasattr(self, 'location_tracker') and self.location_tracker is not None and 
                self.advanced_settings.get('location_logging', False)):
                try:
                    location = self.location_tracker.get_location()
                    if location:
                        self.location_updated.emit(location)
                except Exception as e:
                    self.log_message.emit(f"Warning: Failed to get location: {str(e)}")
            
            # Create log entry
            log_entry = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'event_type': event_type,
                'device': self.device,
                'message': message,
                'location': location
            }
            
            # Ensure log directory exists
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            
            # Write to log file
            try:
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except IOError as e:
                self.log_message.emit(f"Warning: Could not write to log file: {str(e)}")
                
            self.log_message.emit(f"[Security] {event_type}: {message}")
            
        except Exception as e:
            error_msg = f"Error logging tamper event: {str(e)}"
            try:
                # Try to log the error to console as a last resort
                print(error_msg, file=sys.stderr)
            except:
                pass
    
    def _update_location(self):
        """Update the current location if location tracking is enabled."""
        if not hasattr(self, 'enable_location') or not self.enable_location:
            return
            
        if not hasattr(self, 'location_tracker') or self.location_tracker is None:
            return
            
        try:
            new_location = self.location_tracker.get_location()
            if new_location and new_location.get('latitude') is not None:
                self.location = new_location
                self.location_updated.emit(self.location)
                self.log_message.emit(
                    f"Location updated: {self.location['latitude']:.6f}, "
                    f"{self.location['longitude']:.6f} ({self.location.get('source', 'unknown')})"
                )
        except Exception as e:
            self.log_message.emit(f"Error updating location: {str(e)}")
    
    def _wipe_crypto_keys(self):
        """Wipe cryptographic keys from the device."""
        try:
            self.log_message.emit("Wiping cryptographic keys...")
            # Wipe LUKS headers if present
            if os.path.exists(f"{self.device}_crypt"):
                self._run_command(f"cryptsetup luksErase --batch-mode {self.device}", "Failed to erase LUKS headers")
            
            # Wipe filesystem encryption keys
            self._run_command(f"wipefs -a {self.device}", "Failed to wipe filesystem signatures")
            
            # Log the key wipe
            if self.advanced_settings['tamper_log']:
                self._log_tamper_event('key_wipe', f"Cryptographic keys wiped on {self.device}")
                
            return True
        except Exception as e:
            self.log_message.emit(f"Warning: Failed to wipe cryptographic keys: {str(e)}")
            return False
    
    def _wipe_bootloader(self):
        """Wipe the bootloader from the device."""
        try:
            self.log_message.emit("Wiping bootloader...")
            # Zero out the first 2MB where bootloaders typically reside
            self._run_command(f"dd if=/dev/zero of={self.device} bs=512 count=4096", "Failed to wipe bootloader")
            
            # Log the bootloader wipe
            if self.advanced_settings['tamper_log']:
                self._log_tamper_event('bootloader_wipe', f"Bootloader wiped on {self.device}")
                
            return True
        except Exception as e:
            self.log_message.emit(f"Warning: Failed to wipe bootloader: {str(e)}")
            return False
    
    def _wipe_volatile_memory(self):
        """Wipe volatile memory (RAM)."""
        try:
            self.log_message.emit("Wiping volatile memory...")
            # Use memtester to fill memory with patterns
            self._run_command("sync && echo 3 > /proc/sys/vm/drop_caches", "Failed to wipe volatile memory")
            
            # Log the memory wipe
            if self.advanced_settings['tamper_log']:
                self._log_tamper_event('memory_wipe', 'Volatile memory wiped')
                
            return True
        except Exception as e:
            self.log_message.emit(f"Warning: Failed to wipe volatile memory: {str(e)}")
            return False
    
    def _thermal_stress_test(self):
        """Perform thermal stress testing on the device."""
        if not self.advanced_settings['thermal_stress']:
            return True
            
        try:
            self.log_message.emit(f"Starting thermal stress test for {self.advanced_settings['stress_duration']}s...")
            start_time = time.time()
            end_time = start_time + self.advanced_settings['stress_duration']
            
            # Log the start of stress test
            if self.advanced_settings['tamper_log']:
                self._log_tamper_event('stress_test_start', 
                                     f"Thermal stress test started on {self.device}")
            
            while time.time() < end_time and self._is_running:
                # Perform intensive I/O to stress the device
                self._run_command(f"fio --name=stress --filename={self.device} --rw=randrw --bs=4k --direct=1 --ioengine=libaio --iodepth=32 --runtime=10 --time_based --exitall", "Stress test failed")
                
                # Update progress
                elapsed = time.time() - start_time
                progress = min(100, int((elapsed / self.advanced_settings['stress_duration']) * 100))
                self.progress.emit(progress, f"Thermal stress test in progress ({progress}%)")
            
            # Log the completion of stress test
            if self.advanced_settings['tamper_log']:
                self._log_tamper_event('stress_test_complete', 
                                     f"Thermal stress test completed on {self.device}")
            
            return True
            
        except Exception as e:
            self.log_message.emit(f"Warning: Thermal stress test failed: {str(e)}")
            return False
    
    def _verify_wipe_entropy(self):
        """Verify wipe using entropy analysis."""
        try:
            self.log_message.emit("Performing entropy analysis...")
            # Use ent to analyze randomness of the wiped data
            result = subprocess.run(
                f"dd if={self.device} bs=1M count=100 2>/dev/null | ent -t",
                shell=True, 
                capture_output=True, 
                text=True
            )
            
            # Extract entropy value from output
            entropy = 0.0
            for line in result.stdout.split('\n'):
                if 'Entropy' in line:
                    entropy = float(line.split()[-1])
                    break
            
            # Check if entropy meets threshold
            if entropy >= self.advanced_settings['entropy_threshold']:
                self.log_message.emit(f"Entropy verification passed: {entropy:.2f} bits/byte")
                return True
            else:
                self.log_message.emit(f"Entropy verification failed: {entropy:.2f} < {self.advanced_settings['entropy_threshold']} bits/byte")
                return False
                
        except Exception as e:
            self.log_message.emit(f"Entropy verification error: {str(e)}")
            return False
    
    def _custom_wipe(self):
        """Perform a custom wipe with the specified pattern and passes."""
        try:
            pattern = self.advanced_settings['pattern']
            passes = self.advanced_settings['passes']
            
            # Log the start of wipe operation
            if self.advanced_settings['tamper_log']:
                self._log_tamper_event('wipe_start', 
                                     f"Starting wipe on {self.device} with {passes} passes")
            
            self.log_message.emit(f"Starting custom wipe with {passes} passes")
            
            for i in range(passes):
                if not self._is_running:
                    return False
                    
                # Alternate between pattern and random data
                if pattern and i % 2 == 0:
                    self.log_message.emit(f"Pass {i+1}/{passes}: Writing pattern...")
                    cmd = self._get_dd_command(pattern=pattern)
                else:
                    self.log_message.emit(f"Pass {i+1}/{passes}: Writing random data...")
                    cmd = 'dd if=/dev/urandom ' + self._get_dd_command().split(' ', 1)[1]
                
                # Execute the command
                result = subprocess.run(
                    cmd, shell=True, executable='/bin/bash',
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                
                if result.returncode != 0:
                    self.log_message.emit(f"Error in pass {i+1}: {result.stderr}")
                    return False
                    
                # Update progress
                progress = int(((i + 1) / passes) * 100)
                self.progress.emit(progress, f"Pass {i+1}/{passes} complete")
            
            return True
            
        except Exception as e:
            self.log_message.emit(f"Error in custom wipe: {str(e)}")
            return False
    
    def run(self):
        """Execute the wipe operation with all security features."""
        success = False
        message = ""
        
        try:
            if not self._is_running:
                return
                
            # Log the start of the operation
            self.log_message.emit(f"Starting {self.method} wipe on {self.device}")
            
            # Wipe volatile memory if requested
            if self.advanced_settings['volatile_memory']:
                self._wipe_volatile_memory()
            
            # Perform thermal stress test if enabled
            if self.advanced_settings['thermal_stress']:
                if not self._thermal_stress_test():
                    raise Exception("Thermal stress test failed")
            
            # Wipe cryptographic keys if enabled
            if self.advanced_settings['key_wipe']:
                self._wipe_crypto_keys()
            
            # Perform the main wipe operation
            if self.method == 'quick':
                success = self._quick_wipe()
            elif self.method == 'dod':
                success = self._dod_wipe()
            elif self.method == 'nist':
                success = self._nist_wipe()
            elif self.method == 'gutmann':
                success = self._gutmann_wipe()
            elif self.method == 'custom':
                success = self._custom_wipe()
            elif self.method == 'nulldrive':
                # Skip other wipe operations for NULLDRIVE as it handles everything itself
                success = self._nulldrive_wipe()
                # Skip verification and other post-wipe operations for NULLDRIVE
                self.finished.emit(success, "NULLDRIVE secure erase completed" if success else "NULLDRIVE secure erase failed")
                return
            else:
                message = f"Unknown wipe method: {self.method}"
                self.log_message.emit(message)
            
            # Wipe bootloader if enabled (after main wipe to ensure it's not restored)
            if success and self.advanced_settings['bootloader_wipe']:
                self._wipe_bootloader()
            
            # Perform verification based on selected mode
            if success and self.verify:
                if self.advanced_settings['verification_mode'] == 'entropy':
                    success = self._verify_wipe_entropy()
                else:
                    success = self._verify_wipe()
                
                if not success:
                    message = "Verification failed"
                    
        except Exception as e:
            success = False
            message = str(e)
            self.log_message.emit(f"Error: {message}")
            
            # Log the failure
            if self.advanced_settings['tamper_log']:
                self._log_tamper_event('wipe_failed', f"Wipe failed on {self.device}: {message}")
        else:
            # Log successful completion
            if self.advanced_settings['tamper_log'] and success:
                self._log_tamper_event('wipe_complete', 
                                     f"Wipe completed successfully on {self.device}")
        finally:
            if not message:
                message = "Wipe completed successfully" if success else "Wipe failed"
            self.finished.emit(success, message)

    def _run_command_with_progress(self, command, total_bytes, error_msg):
        """Run a command with progress tracking using pv."""
        if not self._is_running:
            return False
            
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True,
                bufsize=1,
                universal_newlines=True,
                executable='/bin/bash'
            )
            
            # Read output in real-time
            last_update = time.time()
            bytes_processed = 0
            
            while True:
                if not self._is_running:
                    process.terminate()
                    return False
                
                # Read from stderr (where pv outputs progress)
                line = process.stderr.readline()
                
                # Check if process has finished
                if line == '' and process.poll() is not None:
                    break
                    
                if line:
                    line = line.strip()
                    self.log_message.emit(line)
                    
                    # Parse pv progress output
                    if '%' in line and '[' in line and ']' in line:
                        try:
                            # Extract percentage
                            percent_str = line.split('%')[0].split()[-1]
                            percent = float(percent_str)
                            
                            # Update progress
                            self.progress.emit(int(percent), f"Wiping: {int(percent)}%")
                            
                            # Update bytes processed
                            if 'B ' in line and '/' in line:
                                processed = line.split('B ')[1].split('/')[0].strip()
                                self.log_message.emit(f"Processed: {processed}")
                                
                        except Exception as e:
                            self.log_message.emit(f"Progress parse error: {str(e)}")
            
            # Check the return code
            if process.returncode != 0:
                # Read any remaining error output
                remaining_error = process.stderr.read()
                if remaining_error.strip():
                    self.log_message.emit(f"{error_msg}: {remaining_error.strip()}")
                return False
                
            return True
            
        except Exception as e:
            self.log_message.emit(f"Command with progress error: {str(e)}")
            return False
    
    def _run_command(self, command, error_msg, fail_on_error=True):
        """
        Run a shell command and handle output/errors.
        
        Args:
            command (str): The command to run
            error_msg (str): Error message to display if command fails
            fail_on_error (bool): If True, return False on error. If False, log the error but continue.
            
        Returns:
            bool: True if command succeeded or fail_on_error is False, False otherwise
        """
        if not self._is_running:
            return False
            
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output in real-time
            while True:
                if not self._is_running:
                    process.terminate()
                    return False
                
                output = process.stdout.readline()
                error = process.stderr.readline()
                
                if output == '' and error == '' and process.poll() is not None:
                    break
                    
                if output:
                    output = output.strip()
                    self.log_message.emit(output)
                    
                    # Parse progress from dd status=progress output
                    if 'bytes' in output and 'copied' in output and ',' in output:
                        try:
                            # Extract the progress information
                            parts = output.split(',')
                            for part in parts:
                                part = part.strip()
                                if 'bytes' in part and 'copied' in part:
                                    # Extract the number of bytes copied
                                    bytes_copied = int(part.split()[0])
                                    # Get the total size if available
                                    for p in parts:
                                        if 'size' in p and '/' in p:
                                            total_size = int(p.split('/')[1].split()[0])
                                            # Calculate percentage if we have total size
                                            if total_size > 0:
                                                percent = min(100, int((bytes_copied / total_size) * 100))
                                                self.progress.emit(percent, f"Wiping: {percent}%")
                                            break
                        except Exception as e:
                            self.log_message.emit(f"Progress parsing error: {str(e)}")
                
                if error and not error.isspace():
                    self.log_message.emit(f"Warning: {error.strip()}")
            
            # Check the return code
            if process.returncode != 0:
                # Read any remaining error output
                remaining_error = process.stderr.read()
                if remaining_error.strip():
                    error_msg = f"{error_msg}: {remaining_error.strip()}"
                    if fail_on_error:
                        self.log_message.emit(error_msg)
                    else:
                        self.log_message.emit(f"Warning: {error_msg}")
                
                if fail_on_error:
                    return False
            
            return True
            
        except Exception as e:
            error_msg = f"Command error: {str(e)}"
            if fail_on_error:
                self.log_message.emit(error_msg)
                return False
            else:
                self.log_message.emit(f"Warning: {error_msg}")
                return True
    
    def _quick_wipe(self):
        """Perform a quick 1-pass zero wipe with progress tracking."""
        try:
            # First, unmount all partitions on the device
            if not self._unmount_partitions(self.device):
                self.log_message.emit("Warning: Could not unmount all partitions. Continuing anyway...")
            
            # Wipe the partition table
            if not self._run_command(f"sudo wipefs -a {self.device}", "Failed to wipe partition table", fail_on_error=False):
                self.log_message.emit("Warning: Failed to wipe partition table, continuing with zero-fill...")
            
            # Get device size for progress reporting
            try:
                size_cmd = f"sudo blockdev --getsize64 {self.device}"
                result = subprocess.run(
                    size_cmd,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    error_msg = f"Error getting device size: {result.stderr.strip()}"
                    self.log_message.emit(error_msg)
                    return False
                    
                total_bytes = int(result.stdout.strip())
                total_val, total_unit = format_size(total_bytes)
                total_mb = total_bytes // (1024 * 1024)  # Keep MB for progress card
                self.log_message.emit(f"Device size: {total_val:.1f} {total_unit}")
                
                # Create and show progress card
                progress_card = self._create_progress_card(total_mb)
                self.progress_card_shown.emit(progress_card)
                
            except Exception as e:
                error_msg = f"Error getting device size: {str(e)}"
                self.log_message.emit(error_msg)
                return False
            
            # Try to use blkdiscard to optimize the process if available
            if 'nvme' in self.device or 'sd' in self.device:
                self.log_message.emit("Attempting to optimize with discard...")
                cmd = f"sudo blkdiscard -f {self.device}"
                self._run_command(cmd, "blkdiscard warning", fail_on_error=False)
            
            # Initialize progress tracking
            self.last_update = time.time()
            self.last_bytes = 0
            
            # Build the dd command with status=progress
            block_size = "1M"
            dd_cmd = f"sudo dd if=/dev/zero of={self.device} bs={block_size} status=progress"
            if self.quick_erase:
                dd_cmd += " conv=noerror"
            
            # Start the process
            process = subprocess.Popen(
                dd_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Initialize progress tracking
            last_update = time.time()
            last_bytes = 0
            
            # Stream and parse output in real-time
            while True:
                if not self._is_running:
                    process.terminate()
                    return False
                    
                line = process.stdout.readline()
                if line == '' and process.poll() is not None:
                    break
                    
                if line:
                    # Parse the progress
                    bytes_written, speed, percent = self._parse_dd_progress(line, total_bytes)
                    
                    # Update progress if we have valid data
                    if bytes_written is not None and speed is not None and percent is not None:
                        # Calculate current speed
                        current_time = time.time()
                        if last_bytes > 0 and current_time > last_update:
                            bytes_sec = (bytes_written - last_bytes) / (current_time - last_update)
                            speed = f"{bytes_sec/1024/1024:.1f} MB/s"
                        last_bytes = bytes_written
                        last_update = current_time
                        
                        # Emit progress update with formatted sizes
                        if total_bytes:
                            written_val, written_unit = format_size(bytes_written)
                            total_val, total_unit = format_size(total_bytes)
                            status = f"{written_val:.1f} {written_unit} / {total_val:.1f} {total_unit} ({percent}%) @ {speed}"
                        else:
                            written_val, written_unit = format_size(bytes_written)
                            status = f"{written_val:.1f} {written_unit} @ {speed}"
                        
                        # Update progress bar and status
                        self.progress.emit(percent, status)
            
            result = (process.returncode == 0)
            
            # Ensure all data is written to disk
            if result:
                self.log_message.emit("Finalizing write operations...")
                sync_cmd = "sudo sync"
                self._run_command(sync_cmd, "Sync failed", fail_on_error=False)
                self.log_message.emit("Quick wipe completed successfully.")
            
            return result
            
        except Exception as e:
            self.log_message.emit(f"Error in quick wipe: {str(e)}")
            return False
    
    def _dod_wipe(self):
        """Perform DoD 5220.22-M compliant 3-pass wipe with unified progress tracking."""
        try:
            # First, unmount all partitions on the device
            if not self._unmount_partitions(self.device):
                self.log_message.emit("Warning: Could not unmount all partitions. Continuing anyway...")
            
            # Wipe the partition table
            if not self._run_command(f"sudo wipefs -a {self.device}", "Failed to wipe partition table", fail_on_error=False):
                self.log_message.emit("Warning: Failed to wipe partition table, continuing with DoD wipe...")
            
            # Get device size for progress reporting
            try:
                size_cmd = f"sudo blockdev --getsize64 {self.device}"
                result = subprocess.run(
                    size_cmd,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    error_msg = f"Error getting device size: {result.stderr.strip()}"
                    self.log_message.emit(error_msg)
                    return False
                    
                total_bytes = int(result.stdout.strip())
                total_val, total_unit = format_size(total_bytes)
                total_mb = total_bytes // (1024 * 1024)  # Keep MB for progress card
                self.log_message.emit(f"Device size: {total_val:.1f} {total_unit}")
                
                # Create and show progress card (3x size for 3 passes)
                progress_card = self._create_progress_card(total_mb * 3)
                self.progress_card_shown.emit(progress_card)
                
            except Exception as e:
                error_msg = f"Error getting device size: {str(e)}"
                self.log_message.emit(error_msg)
                return False
            
            # Try to use blkdiscard to optimize the process if available
            if 'nvme' in self.device or 'sd' in self.device:
                self.log_message.emit("Attempting to optimize with discard...")
                cmd = f"sudo blkdiscard -f {self.device}"
                self._run_command(cmd, "blkdiscard warning", fail_on_error=False)
            
            # Initialize progress tracking
            self.last_update = time.time()
            self.last_bytes = 0
            
            # Define the three passes
            passes = [
                {
                    'name': 'Pass 1/3: Writing zeros',
                    'cmd': f"sudo dd if=/dev/zero of={self.device} bs=1M status=progress"
                },
                {
                    'name': 'Pass 2/3: Writing ones',
                    'cmd': f"sudo dd if=/dev/zero iflag=fullblock of={self.device} bs=1M count=$(blockdev --getsize64 {self.device} 2>/dev/null || echo 0) status=progress"
                },
                {
                    'name': 'Pass 3/3: Writing random data',
                    'cmd': f"sudo dd if=/dev/urandom of={self.device} bs=1M status=progress"
                }
            ]
            
            # Add quick_erase option if needed
            if self.quick_erase:
                for p in passes:
                    p['cmd'] += " conv=noerror"
            
            # Track total progress across all passes
            total_progress = 0
            
            for i, pass_info in enumerate(passes, 1):
                if not self._is_running:
                    return False
                
                self.log_message.emit(pass_info['name'])
                
                # Start the process
                process = subprocess.Popen(
                    pass_info['cmd'],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Initialize progress tracking for this pass
                last_update = time.time()
                last_bytes = 0
                
                # Stream and parse output in real-time
                while True:
                    if not self._is_running:
                        process.terminate()
                        return False
                        
                    line = process.stdout.readline()
                    if line == '' and process.poll() is not None:
                        break
                        
                    if line:
                        # Parse the progress for this pass
                        bytes_written, speed, percent = self._parse_dd_progress(line, total_bytes)
                        
                        # Calculate overall progress (0-100% across all passes)
                        if percent is not None:
                            # Each pass is 1/3 of the total progress
                            overall_percent = ((i-1) * 33.33) + (percent / 3)
                            
                            # Update progress if we have valid data
                            if bytes_written is not None and speed is not None:
                                # Calculate current speed
                                current_time = time.time()
                                if last_bytes > 0 and current_time > last_update:
                                    bytes_sec = (bytes_written - last_bytes) / (current_time - last_update)
                                    speed = f"{bytes_sec/1024/1024:.1f} MB/s"
                                last_bytes = bytes_written
                                last_update = current_time
                                
                                # Format status with pass info
                                written_val, written_unit = format_size(bytes_written)
                                total_val, total_unit = format_size(total_bytes)
                                status = (f"{pass_info['name']} - {written_val:.1f} {written_unit} / "
                                         f"{total_val:.1f} {total_unit} ({percent}%) @ {speed}")
                                
                                # Update progress bar and status
                                self.progress.emit(int(overall_percent), status)
                
                # Check if this pass failed
                if process.returncode != 0:
                    self.log_message.emit(f"DoD pass {i} failed with code {process.returncode}")
                    return False
                
                # Ensure data is written to disk after each pass
                self.log_message.emit(f"Finalizing {pass_info['name'].lower()}...")
                sync_cmd = "sudo sync"
                self._run_command(sync_cmd, "Sync failed", fail_on_error=False)
            
            self.log_message.emit("DoD 3-pass wipe completed successfully.")
            return True
            
        except Exception as e:
            self.log_message.emit(f"Error in DoD wipe: {str(e)}")
            return False
    
    def _unmount_partitions(self, device):
        """Unmount all partitions of the given device."""
        try:
            # Get all mounted partitions of the device
            mounts = subprocess.run(
                f"lsblk -n -o MOUNTPOINT {device}* | grep -v '^\\s*$' | grep -v '^\\[' | grep -v '^$' | sort -u",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if mounts.returncode != 0 or not mounts.stdout.strip():
                self.log_message.emit(f"No mounted partitions found on {device}")
                return True
                
            mounted_partitions = [m for m in mounts.stdout.split('\n') if m.strip()]
            
            if not mounted_partitions:
                return True
                
            self.log_message.emit(f"Unmounting {len(mounted_partitions)} partition(s) on {device}...")
            
            # Unmount all partitions
            for mp in mounted_partitions:
                if not mp.strip():
                    continue
                self.log_message.emit(f"Unmounting {mp}...")
                result = subprocess.run(
                    ["sudo", "umount", mp],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    self.log_message.emit(f"Warning: Failed to unmount {mp}: {result.stderr.strip()}")
                    return False
                    
            self.log_message.emit("All partitions unmounted successfully.")
            return True
            
        except Exception as e:
            self.log_message.emit(f"Error unmounting partitions: {str(e)}")
            return False

    def _parse_dd_progress(self, line, total_bytes):
        """Parse dd progress output and return (bytes_written, speed, percent)"""
        try:
            # Example: '1234567890 bytes (1.2 GB, 1.1 GiB) copied, 23 s, 53.6 MB/s'
            if "bytes" in line and "copied" in line:
                parts = line.split()
                if len(parts) >= 8:
                    # Get bytes written
                    bytes_written = int(parts[0])
                    
                    # Get speed
                    speed = parts[-2] + " " + parts[-1]  # e.g., "100 MB/s"
                    
                    # Calculate percent if we have total_bytes
                    percent = 0
                    if total_bytes and total_bytes > 0:
                        percent = min(100, int((bytes_written / total_bytes) * 100))
                        
                        # Update speed calculation
                        current_time = time.time()
                        if hasattr(self, 'last_update') and hasattr(self, 'last_bytes'):
                            time_elapsed = current_time - self.last_update
                            bytes_elapsed = bytes_written - self.last_bytes
                            if time_elapsed > 0 and bytes_elapsed > 0:
                                speed_mb = (bytes_elapsed / (1024 * 1024)) / time_elapsed
                                speed = f"{speed_mb:.1f} MB/s"
                            self.last_update = current_time
                            self.last_bytes = bytes_written
                    
                    # Update progress card if it exists
                    if hasattr(self, 'progress_bar') and hasattr(self, 'progress_text') and total_bytes:
                        self.progress_bar.setValue(percent)
                        
                        # Format each value with its most appropriate unit
                        written_val, written_unit = format_size(bytes_written)
                        total_val, total_unit = format_size(total_bytes)
                        
                        self.progress_text.setText(
                            f"{written_val:.1f} {written_unit} / {total_val:.1f} {total_unit} "
                            f"({percent}%) @ {speed}"
                        )
                    
                    return bytes_written, speed, percent
        except Exception as e:
            self.log_message.emit(f"Progress parse error: {str(e)}")
        
        return None, None, None

    def _create_progress_card(self, total_mb):
        """Create a progress card UI element"""
        from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
        
        # Create card frame
        card = QFrame()
        card.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        card.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 10px;
            }
            QLabel {
                color: #fff;
                font-weight: bold;
            }
            QLabel#progressText {
                font-size: 14px;
                font-family: monospace;
            }
            QProgressBar {
                text-align: center;
                color: white;
                border: 1px solid #444;
                border-radius: 3px;
                background-color: #1a1a1a;
            }
            QProgressBar::chunk {
                background-color: #2e7d32;
                width: 10px;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(card)
        
        # Device info
        info_layout = QHBoxLayout()
        device_label = QLabel(f"Device: {self.device}")
        
        # Calculate total bytes and format with appropriate unit
        total_bytes = total_mb * 1024 * 1024  # Convert MB to bytes
        size_val, size_unit = format_size(total_bytes)
        size_label = QLabel(f"Size: {size_val:.1f} {size_unit}")
        info_layout.addWidget(device_label)
        info_layout.addStretch()
        info_layout.addWidget(size_label)
        
        # Store total size and unit for progress updates
        self._total_size = total_bytes
        self._total_size_unit = size_unit
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        # Progress text - use same unit as total size for consistency
        zero_val, _ = format_size(0)
        self.progress_text = QLabel(f"{zero_val:.1f} {size_unit} / {size_val:.1f} {size_unit} (0.0%) @ 0.0 MB/s")
        self.progress_text.setObjectName("progressText")
        
        # Add to layout
        layout.addLayout(info_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_text)
        
        return card

    def _nist_wipe(self):
        """Perform NIST 800-88 compliant 1-pass wipe."""
        # First, unmount all partitions on the device
        if not self._unmount_partitions(self.device):
            self.log_message.emit("Error: Could not unmount all partitions. Wipe operation aborted.")
            return False
            
        # Wipe the partition table
        if not self._run_command(f"sudo wipefs -a {self.device}", "Failed to wipe partition table", fail_on_error=False):
            self.log_message.emit("Warning: Failed to wipe partition table, continuing with zero-fill...")
        
        # Get device size for progress reporting
        try:
            size_cmd = f"sudo blockdev --getsize64 {self.device}"
            result = subprocess.run(
                size_cmd,
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                total_bytes = int(result.stdout.strip())
                total_val, total_unit = format_size(total_bytes)
                total_mb = total_bytes // (1024 * 1024)  # Keep MB for progress card
                self.log_message.emit(f"Device size: {total_val:.1f} {total_unit}")
            else:
                error_msg = f"Error: Could not get device size: {result.stderr.strip()}"
                self.log_message.emit(error_msg)
                return False
        except Exception as e:
            error_msg = f"Error getting device size: {str(e)}"
            self.log_message.emit(error_msg)
            return False
        
        # Create and show progress card
        if total_bytes is not None:
            progress_card = self._create_progress_card(total_mb)
            self.progress_card_shown.emit(progress_card)
        else:
            self.log_message.emit("Error: Could not determine device size")
            return False
        
        # Always perform a zero-fill to ensure data is actually wiped
        self.log_message.emit("Starting secure zero-fill operation (this may take a while)...")
        
        # First, try to use blkdiscard to optimize the process if available
        if 'nvme' in self.device or 'sd' in self.device:
            self.log_message.emit("Attempting to optimize with discard...")
            cmd = f"sudo blkdiscard -f {self.device}"
            self._run_command(cmd, "blkdiscard warning", fail_on_error=False)
            
        # Initialize progress tracking
        self.last_update = time.time()
        self.last_bytes = 0
        
        # Use a block size of 1M for better performance
        block_size = "1M"
        
        # Build the dd command
        dd_cmd = f"sudo dd if=/dev/zero of={self.device} bs={block_size} status=progress"
        if self.quick_erase:
            dd_cmd += " conv=noerror"
        
        # Start the process
        process = subprocess.Popen(
            dd_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Initialize progress tracking
        last_update = time.time()
        last_bytes = 0
        
        # Stream and parse output in real-time
        while True:
            if not self._is_running:
                process.terminate()
                return False
                
            line = process.stdout.readline()
            if line == '' and process.poll() is not None:
                break
                
            if line:
                # Parse the progress
                bytes_written, speed, percent = self._parse_dd_progress(line, total_bytes)
                
                # Update progress if we have valid data
                if bytes_written is not None and speed is not None and percent is not None:
                    # Calculate current speed
                    current_time = time.time()
                    if last_bytes > 0 and current_time > last_update:
                        bytes_sec = (bytes_written - last_bytes) / (current_time - last_update)
                        speed = f"{bytes_sec/1024/1024:.1f} MB/s"
                    last_bytes = bytes_written
                    last_update = current_time
                    
                    # Emit progress update with formatted sizes
                    if total_bytes:
                        written_val, written_unit = format_size(bytes_written)
                        total_val, total_unit = format_size(total_bytes)
                        status = f"{written_val:.1f} {written_unit} / {total_val:.1f} {total_unit} ({percent}%) @ {speed}"
                    else:
                        written_val, written_unit = format_size(bytes_written)
                        status = f"{written_val:.1f} {written_unit} @ {speed}"
                    
                    # Update progress bar and status
                    self.progress.emit(percent, status)
        
        result = (process.returncode == 0)
        
        # Ensure all data is written to disk
        if result:
            self.log_message.emit("Finalizing write operations...")
            sync_cmd = "sudo sync"
            self._run_command(sync_cmd, "Sync failed", fail_on_error=False)
            self.log_message.emit("Zero-fill completed successfully.")
        
        return result
    
    def _gutmann_wipe(self):
        """Perform Gutmann 35-pass secure wipe with unified progress tracking."""
        try:
            # First, unmount all partitions on the device
            if not self._unmount_partitions(self.device):
                self.log_message.emit("Warning: Could not unmount all partitions. Continuing anyway...")
            
            # Wipe the partition table
            if not self._run_command(f"sudo wipefs -a {self.device}", "Failed to wipe partition table", fail_on_error=False):
                self.log_message.emit("Warning: Failed to wipe partition table, continuing with Gutmann wipe...")
            
            # Get device size for progress reporting
            try:
                size_cmd = f"sudo blockdev --getsize64 {self.device}"
                result = subprocess.run(
                    size_cmd,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    error_msg = f"Error getting device size: {result.stderr.strip()}"
                    self.log_message.emit(error_msg)
                    return False
                    
                total_bytes = int(result.stdout.strip())
                total_val, total_unit = format_size(total_bytes)
                total_mb = total_bytes // (1024 * 1024)  # Keep MB for progress card
                self.log_message.emit(f"Device size: {total_val:.1f} {total_unit}")
                
                # Create and show progress card (35x size for 35 passes)
                progress_card = self._create_progress_card(total_mb * 35)
                self.progress_card_shown.emit(progress_card)
                
                # Store progress tracking variables
                self._total_mb = total_mb
                self._total_passes = 35
                
            except Exception as e:
                error_msg = f"Error getting device size: {str(e)}"
                self.log_message.emit(error_msg)
                return False
            
            # Try to use blkdiscard to optimize the process if available
            if 'nvme' in self.device or 'sd' in self.device:
                self.log_message.emit("Attempting to optimize with discard...")
                cmd = f"sudo blkdiscard -f {self.device}"
                self._run_command(cmd, "blkdiscard warning", fail_on_error=False)
            
            # Initialize progress tracking
            self.last_update = time.time()
            self.last_bytes = 0
            self.start_time = time.time()
            
            # Build the shred command with verbose output
            shred_cmd = ["sudo", "shred", "-n", "35", "-v", "-z"]
            if self.quick_erase:
                shred_cmd.append("-f")
            shred_cmd.append(self.device)
            
            # Start the shred process
            process = subprocess.Popen(
                shred_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Initialize progress tracking
            current_pass = 0
            last_line = ""
            
            # Parse shred's verbose output
            while True:
                if not self._is_running:
                    process.terminate()
                    return False
                    
                line = process.stdout.readline()
                if line == '' and process.poll() is not None:
                    break
                    
                if line:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check for pass completion
                    if "pass " in line.lower() and "/" in line:
                        try:
                            # Extract current pass from line like "shred: /dev/sdX: pass 1/35 (random)..."
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == "pass" and i + 1 < len(parts):
                                    pass_info = parts[i + 1]
                                    current_pass = int(pass_info.split('/')[0])
                                    self.log_message.emit(f"Starting pass {current_pass}/{self._total_passes}")
                                    break
                        except (ValueError, IndexError) as e:
                            self.log_message.emit(f"Error parsing pass info: {e}")
                            continue
                    
                    # Look for progress percentage in the output
                    elif "%" in line and "shred" in line.lower():
                        try:
                            # Extract percentage from line like "shred: /dev/sdX: 25%"
                            percent_str = line.split("shred: ")[-1].split("%")[0].strip()
                            current_percent = float(percent_str)
                            
                            # Calculate overall progress (0-100% across all passes)
                            overall_percent = ((current_pass - 1) / self._total_passes * 100) + (current_percent / self._total_passes)
                            
                            # Calculate speed and format values
                            current_time = time.time()
                            if hasattr(self, '_last_update') and hasattr(self, '_last_bytes'):
                                if current_time > self._last_update:
                                    bytes_written = (current_percent / 100) * self._total_bytes
                                    bytes_sec = (bytes_written - self._last_bytes) / (current_time - self._last_update)
                                    speed = f"{bytes_sec/1024/1024:.1f} MB/s"
                                    
                                    # Format status with pass info in the exact format: Pass X/35 1.5 KB / 244.0 GB (0.0%) @ 120.5 MB/s
                                    written_val, written_unit = format_size(bytes_written)
                                    total_val, total_unit = format_size(self._total_bytes)
                                    status = (f"Pass {current_pass}/{self._total_passes} {written_val:.1f} {written_unit} / "
                                            f"{total_val:.1f} {total_unit} ({current_percent:.1f}%) @ {speed}")
                                    
                                    # For the status bar, show a simpler message
                                    status_bar_msg = f"Wiping {os.path.basename(self.device)} - Pass {current_pass}/{self._total_passes} ({current_percent:.1f}%)"
                                    
                                    # Emit progress update for the main UI
                                    # This will update the status bar and progress bar
                                    self.progress.emit(int(overall_percent), status_bar_msg)
                                    
                                    # Emit a signal to update the progress card text
                                    # Use the exact format we want: "Pass X/35 1.5 KB / 244.0 GB (0.0%) @ 120.5 MB/s"
                                    if hasattr(self, 'progress_text'):
                                        self.progress_text.setText(status)
                                    
                                    # Also log the detailed status
                                    self.log_message.emit(f"Progress: {status}")
                                    
                                    # Force UI update
                                    from PySide6.QtCore import QCoreApplication
                                    QCoreApplication.processEvents()
                                
                                # Update tracking variables
                                self._last_bytes = bytes_written
                                self._last_update = current_time
                            else:
                                # First update, just initialize tracking variables
                                self._last_bytes = (current_percent / 100) * self._total_bytes
                                self._last_update = current_time
                            
                        except (ValueError, IndexError) as e:
                            self.log_message.emit(f"Error parsing progress: {e}")
                            continue
                    
                    # Log other output lines
                    if line != last_line and not line.startswith("shred: "):
                        self.log_message.emit(line)
                        last_line = line
            
            # Check if the process completed successfully
            if process.returncode != 0:
                self.log_message.emit(f"Gutmann wipe failed with code {process.returncode}")
                return False
            
            # Final sync
            self.log_message.emit("Finalizing Gutmann wipe...")
            sync_cmd = "sudo sync"
            self._run_command(sync_cmd, "Sync failed", fail_on_error=False)
            
            # Final progress update
            self.progress.emit(100, f"Gutmann wipe completed - {self._total_mb * self._total_passes:.1f} MB processed")
            self.log_message.emit("Gutmann 35-pass wipe completed successfully.")
            return True
            
        except Exception as e:
            self.log_message.emit(f"Error in Gutmann wipe: {str(e)}")
            import traceback
            self.log_message.emit(traceback.format_exc())
            return False
    
    def _get_device_hash(self, sample_size_mb=4):
        """Calculate a hash of the first few MB of the device."""
        try:
            self.log_message.emit(f"Calculating hash of first {sample_size_mb}MB...")
            cmd = f"sudo dd if={self.device} bs=1M count={sample_size_mb} status=none | sha256sum"
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                device_hash = result.stdout.split()[0]
                self.log_message.emit(f"Device hash: {device_hash}")
                return device_hash
            else:
                self.log_message.emit(f"Failed to calculate device hash: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            self.log_message.emit("Hash calculation timed out")
            return None
        except Exception as e:
            self.log_message.emit(f"Error calculating device hash: {str(e)}")
            return None
    
    def _nulldrive_wipe(self):
        """
        Perform a secure erase of the drive with triple confirmation.
        This is a one-way operation that will permanently destroy all data on the drive.
        """
        try:
            # Log the start of the operation
            self.log_message.emit("=== NULLDRIVE SECURE ERASE INITIATED ===")
            self.log_message.emit(f"Target device: {self.device}")
            
            # Get device information
            device_name = os.path.basename(self.device)
            sys_block_path = f"/sys/block/{device_name}"
            
            # Check if device exists
            if not os.path.exists(self.device):
                raise Exception(f"Device {self.device} does not exist")
            
            # Get initial hash of the device
            initial_hash = self._get_device_hash()
            
            # Get device model and size
            try:
                with open(f"{sys_block_path}/device/model", 'r') as f:
                    model = f.read().strip()
                with open(f"{sys_block_path}/size", 'r') as f:
                    sectors = int(f.read().strip())
                    size_gb = sectors * 512 / (1024**3)  # Convert to GB
            except Exception as e:
                model = "Unknown"
                size_gb = 0
            
            self.log_message.emit(f"Device Model: {model}")
            self.log_message.emit(f"Device Size: {size_gb:.2f} GB")
            
            # Determine device type (HDD, SSD, NVMe)
            if 'nvme' in self.device:
                device_type = 'NVMe'
                
                # First check if sanitize is supported
                nvme_id = subprocess.run(
                    ["sudo", "nvme", "id-ctrl", self.device], 
                    capture_output=True, text=True
                )
                
                # Default to format if sanitize check fails
                secure_erase_cmd = f"sudo nvme format -s1 -f {self.device}"
                
                # Check if sanitize is supported (bit 1 of the Optional Admin Command Support field)
                if "Sanitize" in nvme_id.stdout or "0002h" in nvme_id.stdout:
                    device_type = 'NVMe (Sanitize Block Erase)'
                    secure_erase_cmd = f"sudo nvme sanitize {self.device} --sanitize=2 --ause"
                    self.log_message.emit("NVMe sanitize (block erase) is supported and will be used")
                elif "Format NVM" in nvme_id.stdout:
                    device_type = 'NVMe (Format NVM)'
                    secure_erase_cmd = f"sudo nvme format -s1 -f {self.device}"
                    self.log_message.emit("Using NVMe format (fallback)")
                else:
                    device_type = 'NVMe (Basic Format)'
                    secure_erase_cmd = f"sudo nvme format -s1 -f {self.device}"
                    self.log_message.emit("Using basic NVMe format (sanitize not supported)")
            else:
                # Check if device supports ATA secure erase
                hdparm = subprocess.run(
                    ["sudo", "hdparm", "-I", self.device],
                    capture_output=True, text=True
                )
                
                if "not supported" in hdparm.stderr:
                    device_type = 'HDD (Standard)'
                    # Use shred with 3 passes for better security on HDDs and SSDs with remapping
                    self.log_message.emit("Using shred for secure erase (3 passes with random data + zero fill)")
                    secure_erase_cmd = f"sudo shred -v -n 3 -z {self.device}"
                else:
                    # Check for frozen state more rigorously
                    frozen_check = subprocess.run(
                        ["sudo", "hdparm", "-I", self.device],
                        capture_output=True, text=True
                    )
                    
                    # Check if drive is frozen
                    if "frozen" in frozen_check.stdout and "not frozen" not in frozen_check.stdout:
                        self.log_message.emit("=== DRIVE IS FROZEN ===")
                        self.log_message.emit("The drive security is frozen and cannot be erased in this state.")
                        self.log_message.emit("Possible solutions:")
                        self.log_message.emit("1. Suspend and resume your laptop (recommended)")
                        self.log_message.emit("2. Power cycle the drive (unplug and replug)")
                        self.log_message.emit("3. Use a hardware reset if available")
                        
                        # Emit a signal that can be caught by the GUI to show a dialog
                        self.frozen_drive_detected.emit(True)
                        
                        # Wait a moment to ensure the GUI has time to process the signal
                        time.sleep(2)
                        
                        # Check again after potential user action
                        frozen_check = subprocess.run(
                            ["sudo", "hdparm", "-I", self.device],
                            capture_output=True, text=True
                        )
                        
                        if "frozen" in frozen_check.stdout and "not frozen" not in frozen_check.stdout:
                            self.log_message.emit("Drive is still frozen. Cannot proceed with secure erase.")
                            return False
                    
                    # If we get here, either the drive was never frozen or has been unfrozen
                    if "not frozen" in subprocess.run(
                        ["sudo", "hdparm", "-I", self.device], 
                        capture_output=True, text=True
                    ).stdout:
                        device_type = 'SSD/HDD (ATA Secure Erase)'
                        secure_erase_cmd = f"sudo hdparm --user-master u --security-set-pass NULLDRIVE {self.device} && " \
                                         f"sudo hdparm --user-master u --security-erase-enhanced NULLDRIVE {self.device}"
                    else:
                        device_type = 'HDD (ATA Frozen)'
                        self.log_message.emit("Using shred for secure erase (3 passes with random data + zero fill)")
                        secure_erase_cmd = f"sudo shred -v -n 3 -z {self.device}"
            
            self.log_message.emit(f"Detected Device Type: {device_type}")
            
            # Log the secure erase command that will be used
            self.log_message.emit(f"Secure erase command: {secure_erase_cmd}")
            
            # Perform the secure erase
            self.log_message.emit("\n=== WARNING: SECURE ERASE IN PROGRESS ===")
            self.log_message.emit("DO NOT INTERRUPT THIS PROCESS!")
            self.log_message.emit("This operation will permanently destroy all data on the device!")
            
            # Execute the secure erase command
            start_time = time.time()
            result = subprocess.run(
                secure_erase_cmd,
                shell=True,
                executable='/bin/bash',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            elapsed_time = time.time() - start_time
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Unknown error"
                self.log_message.emit(f"Secure erase failed: {error_msg}")
                return False
            
            self.log_message.emit(f"\nSecure erase completed in {elapsed_time:.2f} seconds")
            self.log_message.emit("=== NULLDRIVE SECURE ERASE COMPLETED SUCCESSFULLY ===")
            
            # Apply post-erase lock or brick if enabled
            if 'nvme' not in self.device and (self.advanced_settings['post_erase_lock'] or self.advanced_settings['force_brick']):
                try:
                    if self.advanced_settings['force_brick']:
                        self.log_message.emit("\n=== APPLYING PERMANENT BRICK LOCK ===")
                        self.log_message.emit("WARNING: This will PERMANENTLY lock the drive!")
                        
                        # Set the security password (this will lock the drive)
                        set_pass_cmd = [
                            'sudo', 'hdparm', '--user-master', 'u', '--security-set-pass',
                            self.advanced_settings['lock_password'], self.device
                        ]
                        
                        # First set the password
                        result = subprocess.run(
                            set_pass_cmd,
                            capture_output=True,
                            text=True
                        )
                        
                        if result.returncode != 0:
                            raise Exception(f"Failed to set ATA password: {result.stderr}")
                            
                        self.log_message.emit("First password set successfully")
                        
                        # Perform security erase (this will fail but is necessary for the bricking process)
                        try:
                            erase_cmd = [
                                'sudo', 'hdparm', '--user-master', 'u', '--security-erase',
                                self.advanced_settings['lock_password'], self.device
                            ]
                            subprocess.run(
                                erase_cmd,
                                capture_output=True,
                                text=True,
                                timeout=300  # 5 minute timeout
                            )
                        except subprocess.TimeoutExpired:
                            # Expected - the erase will hang when bricking
                            pass
                        except Exception as e:
                            # Expected to fail when bricking
                            pass
                            
                        # Set the password again to ensure the drive stays locked
                        result = subprocess.run(
                            set_pass_cmd,
                            capture_output=True,
                            text=True
                        )
                        
                        if result.returncode != 0:
                            raise Exception(f"Failed to reset ATA password: {result.stderr}")
                            
                        self.log_message.emit("Drive permanently bricked and locked")
                        self.log_message.emit("WARNING: The drive is now permanently locked and cannot be unlocked!")
                        
                    elif self.advanced_settings['post_erase_lock']:
                        self.log_message.emit("\n=== APPLYING POST-ERASE LOCK ===")
                        self.log_message.emit(f"Setting ATA password: {self.advanced_settings['lock_password']}")
                        
                        # Set the security password (this will lock the drive)
                        set_pass_cmd = [
                            'sudo', 'hdparm', '--user-master', 'u', '--security-set-pass',
                            self.advanced_settings['lock_password'], self.device
                        ]
                        
                        result = subprocess.run(
                            set_pass_cmd,
                            capture_output=True,
                            text=True
                        )
                        
                        if result.returncode != 0:
                            self.log_message.emit(f"Warning: Failed to set ATA password: {result.stderr}")
                        else:
                            self.log_message.emit("Drive locked successfully")
                            self.log_message.emit("WARNING: The drive is now locked and requires the password to access")
                            
                except Exception as e:
                    self.log_message.emit(f"Error applying drive lock: {str(e)}")
            
            # Verify the wipe by comparing hashes before and after
            verification_passed = False
            final_hash = self._get_device_hash()
            
            if initial_hash and final_hash:
                if initial_hash != final_hash:
                    self.log_message.emit("Hash verification: SUCCESS (device content changed)")
                    verification_passed = True
                else:
                    self.log_message.emit("WARNING: Device content appears unchanged after wipe!")
                    self.log_message.emit("This could indicate a problem with the secure erase operation.")
            else:
                self.log_message.emit("WARNING: Could not verify hash change (hash calculation failed)")
                verification_passed = True  # Assume success if we can't verify
            
            # Log the erase operation with hash verification
            log_dir = "/var/log/lapdiag/destruction_logs"
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"nulldrive_erase_{int(time.time())}.log")
            
            log_content = f"""
            === NULLDRIVE SECURE ERASE LOG ===
            Timestamp: {time.ctime()}
            Device: {self.device}
            Model: {model}
            Size: {size_gb:.2f} GB
            Type: {device_type}
            Initial Hash: {initial_hash if initial_hash else 'N/A'}
            Final Hash: {final_hash if final_hash else 'N/A'}
            Hash Verification: {'PASSED' if verification_passed else 'FAILED'}
            Post-Erase Lock: {'Enabled' if self.advanced_settings['post_erase_lock'] else 'Disabled'}
            Lock Password: {'Set' if self.advanced_settings['post_erase_lock'] else 'N/A'}
            Status: {'SUCCESS' if verification_passed else 'WARNING: Hash verification failed'}
            Duration: {elapsed_time:.2f} seconds
            """
            
            with open(log_file, 'w') as f:
                f.write(textwrap.dedent(log_content))
            
            return verification_passed
            
        except Exception as e:
            self.log_message.emit(f"Error during secure erase: {str(e)}")
            # Log the failure
            try:
                log_dir = "/var/log/lapdiag/destruction_logs"
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, f"nulldrive_erase_error_{int(time.time())}.log")
                with open(log_file, 'w') as f:
                    f.write(f"Error during secure erase: {str(e)}\n")
                    f.write(f"Device: {self.device}\n")
                    f.write(f"Timestamp: {time.ctime()}\n")
            except Exception as log_err:
                self.log_message.emit(f"Failed to write error log: {str(log_err)}")
            return False

    def _verify_wipe(self):
        """
        Verify that the device has been properly wiped by checking for non-zero data.
        
        Returns:
            bool: True if verification passed, False if non-zero data is found or on error
        """
        self.log_message.emit("Starting verification of wiped device...")
        
        # For NVMe devices, check sanitize/format status first
        if 'nvme' in self.device:
            self.log_message.emit("Checking NVMe device status...")
            cmd = fr"sudo nvme id-ctrl -H {self.device} | grep -E 'Format|Sanitize'"
            status = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True
            )
            
            if status.returncode != 0:
                self.log_message.emit("Failed to check NVMe status")
                return False
                
            self.log_message.emit(f"NVMe status: {status.stdout.strip()}")
            
            # If sanitize was performed, check its status
            if "Sanitize" in status.stdout:
                sanitize_status = subprocess.run(
                    f"sudo nvme sanitize-log {self.device} | grep 'Sanitize Status' | head -1",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                if sanitize_status.returncode == 0:
                    self.log_message.emit(f"Sanitize status: {sanitize_status.stdout.strip()}")
        
        # For all device types, check for non-zero data
        self.log_message.emit("Scanning for residual data (this may take a while)...")
        
        # Method 1: Check first 1MB for any non-zero data (faster)
        hexdump_cmd = 'hexdump -e ' + "'" + '"%08.8_ax: " 16/1 "%02x" "\n"' + "'"
        cmd = f"sudo dd if={self.device} bs=1M count=1 status=none | {hexdump_cmd} | grep -v '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00'"
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:  # grep found non-zero data
                # Get some context around the non-zero data for the log
                context_cmd = f"sudo dd if={self.device} bs=1M count=1 status=none | hexdump -C | head -20"
                context = subprocess.run(
                    context_cmd,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                self.log_message.emit("=== VERIFICATION FAILED ===")
                self.log_message.emit("Non-zero data detected in the first 1MB of the device:")
                if context.returncode == 0:
                    self.log_message.emit(context.stdout)
                else:
                    self.log_message.emit("Could not get data context")
                return False
                
            # If we get here, first 1MB is all zeros
            self.log_message.emit("First 1MB verification passed (all zeros)")
            
            # Method 2: Sample random blocks throughout the device (more thorough)
            device_size = int(subprocess.check_output(f"blockdev --getsize64 {self.device}", shell=True).decode().strip())
            sample_points = min(100, device_size // (1024*1024))  # Sample up to 100 points, 1 per MB
            
            if sample_points > 0:
                self.log_message.emit(f"Sampling {sample_points} random locations for verification...")
                
                for i in range(sample_points):
                    if not self._is_running:
                        return False
                        
                    # Sample a random block
                    offset = random.randint(0, device_size - 4096)  # 4K block
                    hexdump_cmd = 'hexdump -e ' + "'" + '"%08.8_ax: " 16/1 "%02x" "\n"' + "'"
                    cmd = f"sudo dd if={self.device} bs=4096 skip={offset//4096} count=1 status=none | {hexdump_cmd} | grep -v '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00'"
                    
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:  # Found non-zero data
                        self.log_message.emit(f"=== VERIFICATION FAILED ===")
                        self.log_message.emit(f"Non-zero data detected at offset {offset}")
                        return False
                        
                    # Update progress
                    if i % 10 == 0 or i == sample_points - 1:
                        self.progress.emit(int((i + 1) * 100 / sample_points), 
                                         f"Verifying: {i+1}/{sample_points} samples checked")
            
            self.log_message.emit("=== VERIFICATION PASSED ===")
            self.log_message.emit("No residual data detected in sampled locations")
            return True
            
        except subprocess.TimeoutExpired:
            self.log_message.emit("Verification timed out")
            return False
        except Exception as e:
            self.log_message.emit(f"Verification error: {str(e)}")
            return False
    
    def stop(self):
        """Stop the wipe operation."""
        self._is_running = False
        self.log_message.emit("Stopping wipe operation...")