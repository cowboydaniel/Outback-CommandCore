"""
DROIDCOM - Advanced Tests Feature Module
Handles advanced testing features like stress tests, benchmarks, etc.
"""

import re
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication, QTextCursor
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
import subprocess
import threading
import time

from ..constants import IS_WINDOWS
from ..utils.qt_dispatcher import append_text, emit_ui, set_text


class AdvancedTestsMixin:
    """Mixin class providing advanced testing functionality."""

    def run_screen_lock_duplicator(self):
        """Run the Screen Lock Duplicator tool

        This tool captures a user's lock screen pattern or PIN, saves it,
        and can replay it to automatically unlock the device.
        """
        self.log_message("Starting Screen Lock Duplicator...")

        # Check if a device is connected
        if not self.device_connected:
            self.log_message("No device connected. Please connect a device first.")
            return

        # Create a visualization window for the tool
        test_window = QDialog(self)
        self._dalvik_cache_dialog = test_window
        self._gpu_stress_dialog = test_window
        self._ram_fill_dialog = test_window
        self._cpu_max_load_dialog = test_window
        self._app_crash_dialog = test_window
        self._battery_drain_dialog = test_window
        self._screen_lock_dialog = test_window
        test_window.setWindowTitle("Screen Lock Duplicator")
        test_window.setWindowModality(Qt.ApplicationModal)

        # Get screen dimensions to set height to full screen
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()

        # Keep original width (700) but use full screen height
        window_width = 700
        window_height = screen_geometry.height() - 50  # Subtract a small amount to account for taskbar/window decorations

        # Center the window horizontally
        x_position = screen_geometry.x() + (screen_geometry.width() - window_width) // 2

        # Set the geometry
        test_window.resize(window_width, window_height)
        test_window.move(x_position, screen_geometry.y())

        # Configure window content
        main_layout = QVBoxLayout(test_window)

        # Title and description
        title_label = QLabel("Screen Lock Duplicator")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(title_label)
        main_layout.addWidget(QLabel("This tool records your lock screen pattern/PIN and can replay it to unlock your device"))

        # Lock type selection frame
        type_frame = QGroupBox("Lock Screen Type")
        type_layout = QGridLayout(type_frame)
        lock_type_group = QButtonGroup(type_frame)
        pin_radio = QRadioButton("PIN")
        pin_radio.setProperty("value", "pin")
        pattern_radio = QRadioButton("Pattern")
        pattern_radio.setProperty("value", "pattern")
        password_radio = QRadioButton("Password")
        password_radio.setProperty("value", "password")
        lock_type_group.addButton(pin_radio)
        lock_type_group.addButton(pattern_radio)
        lock_type_group.addButton(password_radio)
        pin_radio.setChecked(True)
        type_layout.addWidget(pin_radio, 0, 0)
        type_layout.addWidget(pattern_radio, 0, 1)
        type_layout.addWidget(password_radio, 0, 2)
        main_layout.addWidget(type_frame)

        # Input configuration frame
        input_frame = QGroupBox("Lock Sequence")
        input_layout = QVBoxLayout(input_frame)

        # PIN/password input
        pin_frame = QWidget()
        pin_layout = QGridLayout(pin_frame)
        pin_layout.addWidget(QLabel("PIN/Password:"), 0, 0)
        pin_entry = QLineEdit()
        pin_entry.setEchoMode(QLineEdit.Password)
        pin_layout.addWidget(pin_entry, 0, 1)

        # Toggle to show/hide PIN
        show_check = QCheckBox("Show PIN/Password")
        show_check.toggled.connect(
            lambda checked: pin_entry.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        )
        pin_layout.addWidget(show_check, 0, 2)
        pin_layout.setColumnStretch(1, 1)
        input_layout.addWidget(pin_frame)

        # Pattern input (simplified for this implementation)
        pattern_frame = QWidget()
        pattern_layout = QGridLayout(pattern_frame)
        pattern_layout.addWidget(QLabel("Pattern Sequence (0-8):"), 0, 0)
        pattern_entry = QLineEdit()
        pattern_layout.addWidget(pattern_entry, 0, 1)
        pattern_layout.addWidget(QLabel("Example: 0,1,4,7,8 for Z pattern"), 0, 2)
        pattern_layout.setColumnStretch(1, 1)

        # Diagram showing pattern grid numbering
        pattern_diagram = QGroupBox()
        pattern_diagram.setFlat(True)
        diagram_layout = QGridLayout(pattern_diagram)
        for i in range(3):
            for j in range(3):
                num = i * 3 + j
                label = QLabel(str(num))
                label.setAlignment(Qt.AlignCenter)
                label.setFixedWidth(30)
                diagram_layout.addWidget(label, i, j)
        pattern_layout.addWidget(pattern_diagram, 1, 0, 1, 3)
        input_layout.addWidget(pattern_frame)
        main_layout.addWidget(input_frame)

        # Options frame
        options_frame = QGroupBox("Options")
        options_layout = QGridLayout(options_frame)
        options_layout.addWidget(QLabel("Delay (ms):"), 0, 0)
        delay_entry = QSpinBox()
        delay_entry.setRange(50, 500)
        delay_entry.setSingleStep(50)
        delay_entry.setValue(100)
        delay_entry.setFixedWidth(70)
        options_layout.addWidget(delay_entry, 0, 1)

        autorun_check = QCheckBox("Automatically unlock after locking")
        autorun_check.setChecked(True)
        options_layout.addWidget(autorun_check, 0, 2)
        options_layout.setColumnStretch(2, 1)
        main_layout.addWidget(options_frame)

        # Progress display
        progress_frame = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_frame)
        output_text = QTextEdit()
        output_text.setReadOnly(True)
        progress_layout.addWidget(output_text)
        main_layout.addWidget(progress_frame, 1)

        # Status label
        status_label = QLabel("Ready to start...")
        main_layout.addWidget(status_label)

        # Action buttons
        button_frame = QWidget()
        button_layout = QHBoxLayout(button_frame)
        save_btn = QPushButton("Save Current Sequence")
        start_btn = QPushButton("Run Duplicator")
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(test_window.close)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(start_btn)
        button_layout.addWidget(close_btn)
        main_layout.addWidget(button_frame)

        # Initialize saved sequence storage
        self.saved_lock_sequence = None
        self.saved_lock_type = None

        # Function to update output in the text widget
        def update_output(text):
            QTimer.singleShot(0, lambda: [
                output_text.append(text),
                output_text.moveCursor(QTextCursor.End)
            ])

        # Update status in the window
        def update_status(text):
            QTimer.singleShot(0, lambda: status_label.setText(text))

        # Function to save the current sequence
        def save_sequence():
            current_type = next(
                (button.property("value") for button in lock_type_group.buttons() if button.isChecked()),
                "pin"
            )

            if current_type == "pin" or current_type == "password":
                sequence = pin_entry.text()
                if not sequence:
                    update_output("Error: Please enter a PIN or password")
                    return
            elif current_type == "pattern":
                sequence = pattern_entry.text()
                if not sequence:
                    update_output("Error: Please enter a pattern sequence")
                    return

                # Validate pattern format
                try:
                    # Check if it's comma-separated numbers
                    pattern_points = [int(p.strip()) for p in sequence.split(',')]
                    for p in pattern_points:
                        if p < 0 or p > 8:
                            raise ValueError("Pattern points must be between 0-8")
                except ValueError:
                    update_output("Error: Pattern must be comma-separated numbers from 0-8")
                    return

            # Save the sequence
            self.saved_lock_sequence = sequence
            self.saved_lock_type = current_type

            update_output(f"Saved {current_type.upper()} sequence successfully")
            update_status(f"Sequence saved: {current_type.upper()}")

            # Enable the test button now that we have a sequence
            start_btn.setEnabled(True)

        # Function to start the duplicate test
        def start_duplicate_test():
            if not self.saved_lock_sequence:
                update_output("Error: Please save a lock sequence first")
                return

            # Get the delay value
            try:
                delay = int(delay_entry.value())
                if delay < 50 or delay > 1000:
                    delay = 100  # Reset to default if out of range
            except ValueError:
                delay = 100  # Default if invalid entry

            # Start the test in a separate thread
            threading.Thread(
                target=self._screen_lock_duplicator_task,
                args=(
                    self.saved_lock_type,
                    self.saved_lock_sequence,
                    delay,
                    autorun_check.isChecked(),
                    update_output,
                    update_status
                ),
                daemon=True
            ).start()

        # Initially disable the test button until a sequence is saved
        start_btn.setEnabled(False)

        # Initial status message
        update_output("Enter your lock screen pattern or PIN and save it to continue")
        update_output("\nFor pattern locks, use numbers 0-8 with commas (see diagram above)")
        update_output("For PIN locks, enter the numeric sequence")
        update_output("For password locks, enter the alphanumeric password")
        save_btn.clicked.connect(save_sequence)
        start_btn.clicked.connect(start_duplicate_test)
        test_window.show()

    def _screen_lock_duplicator_task(self, lock_type, sequence, delay_ms, auto_unlock, update_output, update_status):
        """Background task for running the screen lock duplicator"""
        try:
            update_output(f"Starting Screen Lock Duplicator with {lock_type.upper()} sequence")
            update_status("Running test...")

            # Check if device is already locked
            is_locked = False
            try:
                # Check lock screen state
                lock_success, lock_output = self.run_adb_command(
                    ['shell', 'dumpsys', 'window', '|', 'grep', 'mDreamingLockscreen='],
                    device_serial=self.device_serial
                )
                # If it contains 'mDreamingLockscreen=true', device is locked
                is_locked = lock_success and 'mDreamingLockscreen=true' in lock_output
                update_output(f"Device current lock state: {'Locked' if is_locked else 'Unlocked'}")
            except Exception:
                # If we can't determine lock state, assume unlocked
                update_output("Unable to determine device lock state, proceeding with standard flow")

            # Only lock the device if it's not already locked
            if not is_locked:
                update_output("Locking the device...")
                self.run_adb_command(
                    ['shell', 'input', 'keyevent', 'KEYCODE_POWER'],
                    device_serial=self.device_serial
                )

                # Small delay to ensure device is locked
                time.sleep(1)

            # If auto_unlock is disabled, we're done after checking/locking
            if not auto_unlock:
                update_output("Device lock state confirmed. Auto-unlock disabled.")
                update_status("Device locked")
                return

            # Step 2: Wake the device back up
            update_output("Waking the device...")
            self.run_adb_command(
                ['shell', 'input', 'keyevent', 'KEYCODE_POWER'],
                device_serial=self.device_serial
            )

            # Wait for screen to wake up
            time.sleep(1)

            # Swipe up to show lock screen (needed on newer Android versions)
            update_output("Swiping up to show lock screen...")
            self.run_adb_command(
                ['shell', 'input', 'swipe', '500', '1500', '500', '500'],
                device_serial=self.device_serial
            )

            # Wait for swipe animation
            time.sleep(0.5)

            # Step 3: Input the lock sequence based on lock type
            if lock_type == "pin":
                self._enter_pin_sequence(sequence, delay_ms, update_output)
            elif lock_type == "password":
                self._enter_password_sequence(sequence, delay_ms, update_output)
            elif lock_type == "pattern":
                self._enter_pattern_sequence(sequence, delay_ms, update_output)

            # Step 4: Check if device is unlocked
            update_output("Waiting for device to process unlock...")
            # Add a 1-second delay to give slower devices time to process the unlock
            time.sleep(1)

            update_output("Checking if device was successfully unlocked...")

            # A simple check - try to run a command that would only work if unlocked
            success, output = self.run_adb_command(
                ['shell', 'dumpsys', 'window', '|', 'grep', 'mDreamingLockscreen='],
                device_serial=self.device_serial
            )

            if success and "mDreamingLockscreen=false" in output:
                update_output("Success! Device was unlocked")
                update_status("Test completed: Device unlocked")
            else:
                update_output("Device may not have been unlocked. Check the device.")
                update_status("Test completed: Unlock status unclear")

        except Exception as e:
            error_msg = f"Error during Screen Lock Duplicator test: {str(e)}"
            self.log_message(error_msg)
            update_output("\n" + error_msg)
            update_status("Test failed with errors")

            import traceback
            error_traceback = traceback.format_exc()
            self.log_message(error_traceback)
            update_output(error_traceback)

    def _enter_pin_sequence(self, pin, delay_ms, update_output):
        """Enter a PIN sequence on the device"""
        update_output("Entering PIN sequence...")

        # Convert delay to seconds for time.sleep()
        delay_sec = delay_ms / 1000.0

        # Enter each digit of the PIN
        for digit in pin:
            # Map digits to keycode
            if digit.isdigit():
                keycode = f"KEYCODE_{digit}"
                self.run_adb_command(
                    ['shell', 'input', 'keyevent', keycode],
                    device_serial=self.device_serial
                )
                time.sleep(delay_sec)

        # Press enter to confirm
        self.run_adb_command(
            ['shell', 'input', 'keyevent', 'KEYCODE_ENTER'],
            device_serial=self.device_serial
        )

        update_output("PIN sequence entered")

    def _enter_password_sequence(self, password, delay_ms, update_output):
        """Enter a password sequence on the device"""
        update_output("Entering password sequence...")

        # Use text input for password (more reliable than individual keycodes)
        self.run_adb_command(
            ['shell', 'input', 'text', password],
            device_serial=self.device_serial
        )

        # Brief delay
        time.sleep(delay_ms / 1000.0)

        # Press enter to confirm
        self.run_adb_command(
            ['shell', 'input', 'keyevent', 'KEYCODE_ENTER'],
            device_serial=self.device_serial
        )

        update_output("Password sequence entered")

    def _enter_pattern_sequence(self, pattern, delay_ms, update_output):
        """Enter a pattern sequence on the device using low-level sendevent commands"""
        update_output("Entering pattern sequence using low-level touch events...")

        # Parse the pattern points
        try:
            points = [int(p.strip()) for p in pattern.split(',')]
        except (ValueError, TypeError):
            update_output("Error parsing pattern! Using default Z pattern instead.")
            points = [0, 1, 4, 7, 8]  # Default Z pattern if invalid input

        # Display pattern being used
        update_output(f"Using pattern points: {points}")

        # Adjust these coordinates based on device resolution if needed
        # These coordinates work well for 1080p displays
        # The pattern grid is typically centered in the lock screen
        grid_coords = [
            (250, 500),  # 0: Top left
            (500, 500),  # 1: Top middle
            (750, 500),  # 2: Top right
            (250, 750),  # 3: Middle left
            (500, 750),  # 4: Center
            (750, 750),  # 5: Middle right
            (250, 1000), # 6: Bottom left
            (500, 1000), # 7: Bottom middle
            (750, 1000)  # 8: Bottom right
        ]

        # Validate all points are within range
        for p in points:
            if p < 0 or p >= len(grid_coords):
                update_output(f"Invalid pattern point: {p} (must be 0-8)")
                return

        if len(points) < 2:
            update_output("Error: Pattern must have at least 2 points")
            return

        # We need a more reliable approach using the wm size and the swipe command
        # First, get the screen dimensions to properly scale the pattern points
        try:
            # Get screen dimensions
            size_success, size_output = self.run_adb_command(
                ['shell', 'wm', 'size'],
                device_serial=self.device_serial
            )

            # Parse the dimensions
            # Format is typically: Physical size: 1080x2340
            dimensions_match = re.search(r'(\d+)x(\d+)', size_output) if size_success else None
            if dimensions_match:
                screen_width = int(dimensions_match.group(1))
                screen_height = int(dimensions_match.group(2))
                update_output(f"Detected screen size: {screen_width}x{screen_height}")

                # Scale the coordinates to the actual screen size
                # Our grid is designed for 1080p, so scale if different
                width_scale = screen_width / 1080.0
                height_scale = screen_height / 2340.0

                # Scale the grid coordinates
                scaled_grid = []
                for x, y in grid_coords:
                    scaled_x = int(x * width_scale)
                    scaled_y = int(y * height_scale)
                    scaled_grid.append((scaled_x, scaled_y))

                grid_coords = scaled_grid
                update_output("Adjusted pattern grid for device screen size")
            else:
                update_output("Could not detect screen size, using default coordinates")
        except Exception as e:
            update_output(f"Error detecting screen size: {str(e)}. Using default coordinates.")

        # Try a more reliable approach with multiple direct swipes between points
        update_output("Using direct screen swipes for pattern unlock...")

        # Now we use a direct approach that's visible on screen
        # 1. First, we make a long press on the first point (simulate touch down)
        first_x, first_y = grid_coords[points[0]]

        # Press down and hold at the first point
        self.run_adb_command(
            ['shell', f"input swipe {first_x} {first_y} {first_x} {first_y} 100"],
            device_serial=self.device_serial
        )

        # 2. Now perform each segment of the pattern with a very short duration
        # between them to make it appear continuous
        for i in range(len(points) - 1):
            start_idx = points[i]
            end_idx = points[i + 1]

            start_x, start_y = grid_coords[start_idx]
            end_x, end_y = grid_coords[end_idx]

            # Use a short swipe for this segment with longer duration for visibility
            segment_duration = 250  # 250ms is enough to see but quick enough to feel continuous

            update_output(f"Drawing from point {start_idx} to {end_idx}")

            # Execute swipe for this segment
            self.run_adb_command(
                ['shell', f"input swipe {start_x} {start_y} {end_x} {end_y} {segment_duration}"],
                device_serial=self.device_serial
            )

            # Minimal pause to ensure device registers each segment
            time.sleep(0.05)

        # Using an even more reliable approach for complex patterns
        if len(points) > 3:
            # As a backup, try one long continuous swipe from first to last point
            # This helps with devices that might not register all intermediate points
            update_output("Adding final continuous swipe for reliability...")

            first_x, first_y = grid_coords[points[0]]
            last_x, last_y = grid_coords[points[-1]]

            # Execute a long swipe from first to last point
            self.run_adb_command(
                ['shell', f"input swipe {first_x} {first_y} {last_x} {last_y} 800"],
                device_serial=self.device_serial
            )

        update_output("Pattern sequence completed")
        # Give the device a moment to process the pattern
        time.sleep(0.5)

    def run_battery_drain_test(self):
        """Run a battery drain test on the connected Android device

        This test will execute a variety of operations to stress the device and
        measure how quickly the battery drains under load.
        """
        self.log_message("Starting Battery Drain Test...")

        # Check if a device is connected
        if not self.device_connected:
            self.log_message("No device connected. Please connect a device first.")
            return

        # Create a visualization window for the test
        test_window = QDialog(self)
        test_window.setWindowTitle("Battery Drain Test")
        test_window.resize(700, 500)
        test_window.setWindowModality(Qt.ApplicationModal)

        # Configure window content
        main_layout = QVBoxLayout(test_window)

        # Title and description
        title_label = QLabel("Battery Drain Test")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(title_label)
        main_layout.addWidget(QLabel("This test will stress the device to measure battery drain rate"))

        # Battery level display
        battery_frame = QGroupBox("Battery Information")
        battery_layout = QVBoxLayout(battery_frame)
        batt_info_label = QLabel("Checking battery information...")
        batt_info_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        battery_layout.addWidget(batt_info_label)
        main_layout.addWidget(battery_frame)

        # Progress display
        progress_frame = QGroupBox("Test Progress")
        progress_layout = QVBoxLayout(progress_frame)
        output_text = QTextEdit()
        output_text.setReadOnly(True)
        progress_layout.addWidget(output_text)
        main_layout.addWidget(progress_frame, 1)

        # Status label
        status_label = QLabel("Initializing test...")
        main_layout.addWidget(status_label)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(test_window.close)
        main_layout.addWidget(close_btn)

        # Function to update output in the text widget
        def update_output(text):
            QTimer.singleShot(0, lambda: [
                output_text.append(text),
                output_text.moveCursor(QTextCursor.End)
            ])

        # Update status in the window
        def update_status(text):
            QTimer.singleShot(0, lambda: status_label.setText(text))

        # Update battery info display
        def update_battery_info(text):
            QTimer.singleShot(0, lambda: batt_info_label.setText(text))

        # Start the test in a separate thread
        threading.Thread(
            target=self._battery_drain_test_task,
            args=(update_output, update_status, update_battery_info, test_window),
            daemon=True
        ).start()
        test_window.show()

    def _battery_drain_test_task(self, update_output, update_status, update_battery_info, test_window):
        """Background task for running the battery drain test with UI updates"""
        try:
            # First check initial battery level
            update_status("Checking battery level...")
            update_output("Retrieving initial battery information...")

            success, battery_info = self.run_adb_command(
                ['shell', 'dumpsys', 'battery'],
                device_serial=self.device_serial
            )

            if success:
                self.log_message("Initial battery state:")
                update_output("Initial battery state:")
                initial_level = None
                charging = False

                # Format battery information for display
                battery_info_formatted = ""

                for line in battery_info.split('\n'):
                    if line.strip():
                        self.log_message(f"  {line.strip()}")
                        update_output(f"  {line.strip()}")

                        # Add key battery info to the battery display
                        if any(key in line for key in ['level', 'scale', 'voltage', 'temperature', 'status', 'powered', 'health']):
                            battery_info_formatted += line.strip() + "\n"

                        # Extract battery level
                        if 'level:' in line:
                            try:
                                initial_level = int(line.split(':')[1].strip())
                                level_msg = f"Initial battery level: {initial_level}%"
                                self.log_message(level_msg)
                                update_output(level_msg)
                            except (IndexError, ValueError):
                                pass

                        # Check if device is charging
                        if ('powered:' in line or 'AC powered:' in line or 'USB powered:' in line) and 'true' in line.lower():
                            charging = True

                # Update the battery info display
                update_battery_info(battery_info_formatted)

                if charging:
                    error_msg = "Device is currently charging. Disconnect charger to run the test."
                    self.log_message(error_msg)
                    update_output("\n" + error_msg)
                    update_status("Test aborted: Device is charging")
                    return

                if initial_level is None:
                    error_msg = "Could not determine battery level. Aborting test."
                    self.log_message(error_msg)
                    update_output("\n" + error_msg)
                    update_status("Test aborted: Unknown battery level")
                    return

                if initial_level < 20:
                    error_msg = "Battery level too low for testing. Please charge device above 20%."
                    self.log_message(error_msg)
                    update_output("\n" + error_msg)
                    update_status(f"Test aborted: Battery level ({initial_level}%) too low")
                    return

                # Continue with a valid battery level
                update_status(f"Starting test with battery at {initial_level}%")
            else:
                error_msg = "Could not retrieve battery information. Aborting test."
                self.log_message(error_msg)
                update_output(error_msg)
                update_status("Test aborted: Could not get battery info")
                return

            # Create a flag to control test duration
            self.battery_test_running = True

            # Start test sequence
            update_output("\nStarting battery drain test sequence...")
            update_status("Running test phase 1/3: CPU stress")

            # 1. CPU stress test - run some calculations
            update_output("Phase 1: Running CPU stress test for 10 seconds...")

            # Start CPU stress with a command
            cpu_cmd = "for i in $(seq 1 5000); do echo $((i*i*i)) > /dev/null; done"
            self.run_adb_command(
                ['shell', cpu_cmd],
                device_serial=self.device_serial
            )

            # Update progress
            update_output("CPU stress completed")

            # 2. Screen/GPU test - open app and scroll
            update_output("\nPhase 2: Running screen/GPU test for 10 seconds...")
            update_status("Running test phase 2/3: Screen/GPU")

            # Open settings app
            update_output("Opening Settings app...")
            self.run_adb_command(
                ['shell', 'am', 'start', '-a', 'android.settings.SETTINGS'],
                device_serial=self.device_serial
            )
            time.sleep(2)

            # Scroll several times
            update_output("Scrolling through settings...")
            for i in range(5):
                update_output(f"Scroll {i+1}/5")
                self.run_adb_command(
                    ['shell', 'input', 'swipe', '500', '1000', '500', '300'],
                    device_serial=self.device_serial
                )
                time.sleep(1)

            # 3. Network test - ping some servers
            update_output("\nPhase 3: Running network test for 10 seconds...")
            update_status("Running test phase 3/3: Network")

            update_output("Pinging servers...")
            ping_result, ping_output = self.run_adb_command(
                ['shell', 'ping', '-c', '10', '8.8.8.8'],
                device_serial=self.device_serial
            )

            if ping_result:
                update_output(f"Ping results:\n{ping_output}")
            else:
                update_output("Could not perform ping test")

            # Return to home screen
            update_output("\nReturning to home screen...")
            self.run_adb_command(
                ['shell', 'input', 'keyevent', 'KEYCODE_HOME'],
                device_serial=self.device_serial
            )

            # Test completed, now measure final battery level
            update_output("\nTest sequence completed. Checking final battery level...")
            update_status("Checking final battery level...")

            # Get final battery level
            success, battery_info = self.run_adb_command(
                ['shell', 'dumpsys', 'battery'],
                device_serial=self.device_serial
            )

            if success:
                final_level = None
                battery_info_formatted = "Final Battery State:\n"

                for line in battery_info.split('\n'):
                    if line.strip():
                        # Add key battery info to the battery display
                        if any(key in line for key in ['level', 'scale', 'voltage', 'temperature', 'status']):
                            battery_info_formatted += line.strip() + "\n"
                            update_output(f"  {line.strip()}")

                        # Extract battery level specifically
                        if 'level:' in line:
                            try:
                                final_level = int(line.split(':')[1].strip())
                                level_msg = f"Final battery level: {final_level}%"
                                self.log_message(level_msg)
                                update_output(level_msg)
                            except (ValueError, IndexError):
                                pass

                # Update the battery info display
                update_battery_info(battery_info_formatted)

                if final_level is not None and initial_level is not None:
                    drain = initial_level - final_level
                    drain_msg = f"Battery drain during test: {drain}%"
                    self.log_message(drain_msg)
                    update_output("\n" + drain_msg)

                    if drain > 0:
                        rate_msg = f"Estimated drain rate: {drain*2}% per minute, {drain*120}% per hour"
                        self.log_message(rate_msg)
                        update_output(rate_msg)
                        update_status(f"Test completed: Drain rate {drain*2}%/min")
                    else:
                        no_drain_msg = "No measurable battery drain detected during the test duration"
                        self.log_message(no_drain_msg)
                        update_output(no_drain_msg)
                        update_status("Test completed: No measurable drain")

            complete_msg = "Battery Drain Test completed"
            self.log_message(complete_msg)
            update_output("\n" + complete_msg)

        except Exception as e:
            error_msg = f"Error during Battery Drain Test: {str(e)}"
            self.log_message(error_msg)
            update_output("\n" + error_msg)
            update_status("Test failed with errors")

            import traceback
            error_traceback = traceback.format_exc()
            self.log_message(error_traceback)
            update_output(error_traceback)

            self.battery_test_running = False

    def run_app_crash_forcer(self):
        """Run the App Crash Forcer tool"""
        self.log_message("Starting App Crash Forcer...")

        # Check if a device is connected
        if not self.device_connected:
            self.log_message("No device connected. Please connect a device first.")
            return

        # Create a visualization window for the tool
        test_window = QDialog(self)
        test_window.setWindowTitle("App Crash Forcer")
        test_window.resize(700, 500)
        test_window.setWindowModality(Qt.ApplicationModal)

        # Configure window content
        main_layout = QVBoxLayout(test_window)

        # Title and description
        title_label = QLabel("App Crash Forcer")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(title_label)
        main_layout.addWidget(QLabel("This tool attempts to force Android applications to crash for testing purposes"))

        # App selection frame
        app_frame = QGroupBox("Target Application")
        app_layout = QHBoxLayout(app_frame)
        app_dropdown = QComboBox()
        app_dropdown.setEditable(False)
        app_layout.addWidget(app_dropdown)
        refresh_btn = QPushButton("Refresh")
        app_layout.addWidget(refresh_btn)
        main_layout.addWidget(app_frame)

        # Crash method selection
        method_frame = QGroupBox("Crash Methods")
        method_layout = QVBoxLayout(method_frame)

        method_vars = {
            "memory": QCheckBox("Memory Pressure"),
            "broadcast": QCheckBox("Broadcast Storm"),
            "activity": QCheckBox("Activity Stack Overflow"),
            "native": QCheckBox("Native Signal Injection (Root)")
        }
        method_vars["memory"].setChecked(True)
        method_vars["broadcast"].setChecked(True)
        method_vars["activity"].setChecked(True)
        method_vars["native"].setChecked(False)
        for checkbox in method_vars.values():
            method_layout.addWidget(checkbox)
        main_layout.addWidget(method_frame)

        # Progress display
        progress_frame = QGroupBox("Test Progress")
        progress_layout = QVBoxLayout(progress_frame)
        output_text = QTextEdit()
        output_text.setReadOnly(True)
        progress_layout.addWidget(output_text)
        main_layout.addWidget(progress_frame, 1)

        # Status label
        status_label = QLabel("Ready to start...")
        main_layout.addWidget(status_label)

        # Action buttons
        button_frame = QWidget()
        button_layout = QHBoxLayout(button_frame)
        start_btn = QPushButton("Start Crash Test")
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(test_window.close)
        button_layout.addWidget(start_btn)
        button_layout.addWidget(close_btn)
        main_layout.addWidget(button_frame)

        # Function to update output in the text widget
        def update_output(text):
            QTimer.singleShot(0, lambda: [
                output_text.append(text),
                output_text.moveCursor(QTextCursor.End)
            ])

        # Update status in the window
        def update_status(text):
            QTimer.singleShot(0, lambda: status_label.setText(text))

        # Function to refresh app list
        def refresh_apps():
            update_output("Retrieving list of installed applications...")
            update_status("Scanning for applications...")

            # Get list of installed third-party apps
            success, app_list = self.run_adb_command(
                ['shell', 'pm', 'list', 'packages', '-3'],  # -3 flag for third-party apps only
                device_serial=self.device_serial
            )

            if success and app_list:
                # Parse application package names
                apps = []
                for line in app_list.split('\n'):
                    if line.startswith('package:'):
                        apps.append(line[8:].strip())  # Remove 'package:' prefix

                if len(apps) > 0:
                    # Update dropdown with app list
                    app_dropdown.clear()
                    app_dropdown.addItems(apps)
                    app_dropdown.setCurrentIndex(0)
                    update_output(f"Found {len(apps)} applications")
                    update_status("Ready to start")
                    start_btn.setEnabled(True)
                else:
                    update_output("No third-party applications found")
                    update_status("No applications found")
                    start_btn.setEnabled(False)
            else:
                update_output("Could not retrieve application list")
                update_status("Could not get app list")
                start_btn.setEnabled(False)

        # Function to start the crash test
        def start_crash_test():
            selected_app = app_dropdown.currentText()
            if not selected_app:
                update_output("Please select a target application first")
                return

            # Get selected crash methods
            enabled_methods = [method for method, checkbox in method_vars.items() if checkbox.isChecked()]
            if not enabled_methods:
                update_output("Please select at least one crash method")
                return

            # Start the test in a separate thread
            threading.Thread(
                target=self._app_crash_forcer_task,
                args=(selected_app, enabled_methods, update_output, update_status),
                daemon=True
            ).start()

        # Populate app list initially
        refresh_btn.clicked.connect(refresh_apps)
        start_btn.clicked.connect(start_crash_test)
        refresh_apps()
        test_window.show()

    def _app_crash_forcer_task(self, target_app, methods, update_output, update_status):
        """Background task for running the app crash forcer"""
        try:
            update_output(f"Starting crash test for application: {target_app}")
            update_output(f"Using methods: {', '.join(methods)}")
            update_status("Starting crash test...")

            # First ensure the app is running
            update_output("Launching target application...")

            # Get the main activity for the package
            success, main_activity = self.run_adb_command(
                ['shell', 'cmd', 'package', 'resolve-activity', '--brief', target_app],
                device_serial=self.device_serial
            )

            activity_name = None
            if success and main_activity:
                # Extract activity name from output
                lines = main_activity.split('\n')
                for line in lines:
                    if '/' in line:
                        activity_name = line.strip()
                        break

            # If we couldn't get the main activity, try a direct launch
            if not activity_name:
                update_output("Could not determine main activity, attempting direct launch...")
                self.run_adb_command(
                    ['shell', 'monkey', '-p', target_app, '-c', 'android.intent.category.LAUNCHER', '1'],
                    device_serial=self.device_serial
                )
            else:
                update_output(f"Launching activity: {activity_name}")
                self.run_adb_command(
                    ['shell', 'am', 'start', '-n', activity_name],
                    device_serial=self.device_serial
                )

            # Wait for app to fully launch
            time.sleep(3)

            # Check if the app is running
            success, running_apps = self.run_adb_command(
                ['shell', 'ps', '|', 'grep', target_app],
                device_serial=self.device_serial
            )

            if not success or target_app not in running_apps:
                update_output("Warning: Application may not be running. Continuing anyway...")

            # Execute each selected crash method
            for method in methods:
                if method == "memory":
                    self._execute_memory_pressure_test(target_app, update_output, update_status)
                elif method == "broadcast":
                    self._execute_broadcast_storm_test(target_app, update_output, update_status)
                elif method == "activity":
                    self._execute_activity_stack_test(target_app, update_output, update_status)
                elif method == "native":
                    self._execute_native_signal_test(target_app, update_output, update_status)

            # Check if app is still running at the end
            success, running_check = self.run_adb_command(
                ['shell', 'ps', '|', 'grep', target_app],
                device_serial=self.device_serial
            )

            if success and target_app in running_check:
                update_output("Application survived all crash attempts!")
                update_status("Test completed: No crash detected")
            else:
                update_output("Application crashed successfully!")
                update_status("Test completed: App crashed")

            # Final message
            update_output("\nApp Crash Forcer test completed")

        except Exception as e:
            error_msg = f"Error during App Crash Forcer test: {str(e)}"
            self.log_message(error_msg)
            update_output("\n" + error_msg)
            update_status("Test failed with errors")

            import traceback
            error_traceback = traceback.format_exc()
            self.log_message(error_traceback)
            update_output(error_traceback)

    def _execute_memory_pressure_test(self, target_app, update_output, update_status):
        """Execute memory pressure crash method"""
        update_output("\nExecuting Memory Pressure test...")
        update_status("Running memory pressure test...")

        # Get the process ID of the target app
        success, pid_info = self.run_adb_command(
            ['shell', 'ps', '|', 'grep', target_app],
            device_serial=self.device_serial
        )

        if success and pid_info:
            # Extract PID from ps output (format varies by Android version)
            pid = None
            for line in pid_info.split('\n'):
                if target_app in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.isdigit() and int(part) > 100:  # Most likely a PID
                            pid = part
                            break
                    if pid:
                        break

            if pid:
                update_output(f"Target process ID: {pid}")

                # Use procrank to get memory information before test
                self.run_adb_command(
                    ['shell', 'dumpsys', 'meminfo', pid],
                    device_serial=self.device_serial
                )

                # Execute memory pressure
                update_output("Sending memory trimming requests to the app...")
                self.run_adb_command(
                    ['shell', 'am', 'send-trim-memory', pid, 'RUNNING_CRITICAL'],
                    device_serial=self.device_serial
                )

                # Wait a moment
                time.sleep(2)

                # Try to allocate a lot of memory in the app process (requires root)
                update_output("Attempting to force memory allocation (may require root)...")
                self.run_adb_command(
                    ['shell', 'su', '-c', f"kill -SIGUSR1 {pid}"],
                    device_serial=self.device_serial
                )

                update_output("Memory pressure test complete")
            else:
                update_output("Could not determine process ID")
        else:
            update_output("Could not find running process for the app")

    def _execute_broadcast_storm_test(self, target_app, update_output, update_status):
        """Execute broadcast storm crash method"""
        update_output("\nExecuting Broadcast Storm test...")
        update_status("Running broadcast storm test...")

        # Series of broadcast intents that might be handled by the app
        broadcasts = [
            "android.intent.action.CONFIGURATION_CHANGED",
            "android.intent.action.SCREEN_ON",
            "android.intent.action.SCREEN_OFF",
            "android.intent.action.BATTERY_CHANGED",
            "android.intent.action.BATTERY_LOW",
            "android.intent.action.DEVICE_STORAGE_LOW",
            "android.intent.action.DEVICE_STORAGE_OK",
            "android.intent.action.PACKAGE_ADDED",
            "android.intent.action.PACKAGE_REMOVED",
            "android.intent.action.PACKAGE_CHANGED",
            "android.net.conn.CONNECTIVITY_CHANGE"
        ]

        # Send a storm of broadcasts
        update_output(f"Sending {len(broadcasts) * 10} broadcast intents rapidly...")

        for _ in range(10):  # 10 rounds
            for broadcast in broadcasts:
                self.run_adb_command(
                    ['shell', 'am', 'broadcast', '-a', broadcast],
                    device_serial=self.device_serial
                )
                # No delay to maximize stress

        update_output("Broadcast storm test complete")

    def _execute_activity_stack_test(self, target_app, update_output, update_status):
        """Execute activity stack crash method"""
        update_output("\nExecuting Activity Stack test...")
        update_status("Running activity stack test...")

        # Get all activities in the app
        success, activities = self.run_adb_command(
            ['shell', 'cmd', 'package', 'query-activities', target_app],
            device_serial=self.device_serial
        )

        main_activity = None
        if success and activities:
            # Find an activity to launch repeatedly
            for line in activities.split('\n'):
                if target_app in line and '/' in line:
                    main_activity = line.strip()
                    break

            if not main_activity:
                # Try to get main activity as fallback
                success, main_info = self.run_adb_command(
                    ['shell', 'cmd', 'package', 'resolve-activity', '--brief', target_app],
                    device_serial=self.device_serial
                )

                if success and main_info:
                    for line in main_info.split('\n'):
                        if '/' in line:
                            main_activity = line.strip()
                            break

        if main_activity:
            update_output(f"Found activity to target: {main_activity}")

            # Launch the activity rapidly in a loop to create back stack overflow
            update_output("Launching activity repeatedly to overflow back stack...")
            for i in range(30):  # 30 repetitions
                update_output(f"Launch {i+1}/30...") if i % 5 == 0 else None
                self.run_adb_command(
                    ['shell', 'am', 'start', '-n', main_activity],
                    device_serial=self.device_serial
                )
                time.sleep(0.2)  # Small delay

            update_output("Activity stack test complete")
        else:
            update_output("Could not find a suitable activity to launch")

    def _execute_native_signal_test(self, target_app, update_output, update_status):
        """Execute native signal crash method (requires root)"""
        update_output("\nExecuting Native Signal test (requires root)...")
        update_status("Running native signal test...")

        # Get the process ID of the target app
        success, pid_info = self.run_adb_command(
            ['shell', 'ps', '|', 'grep', target_app],
            device_serial=self.device_serial
        )

        if success and pid_info:
            # Extract PID from ps output (format varies by Android version)
            pid = None
            for line in pid_info.split('\n'):
                if target_app in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.isdigit() and int(part) > 100:  # Most likely a PID
                            pid = part
                            break
                    if pid:
                        break

            if pid:
                update_output(f"Target process ID: {pid}")

                # Try to send SIGSEGV signal (requires root)
                update_output("Sending SIGSEGV signal to process...")
                self.run_adb_command(
                    ['shell', 'su', '-c', f"kill -SIGSEGV {pid}"],
                    device_serial=self.device_serial
                )

                # Wait to see if process crashed
                time.sleep(2)

                # Check if app is still running
                success, running_check = self.run_adb_command(
                    ['shell', 'ps', '|', 'grep', target_app],
                    device_serial=self.device_serial
                )

                if success and target_app in running_check:
                    update_output("Process survived SIGSEGV signal, trying SIGABRT...")

                    # Try SIGABRT as a fallback
                    self.run_adb_command(
                        ['shell', 'su', '-c', f"kill -SIGABRT {pid}"],
                        device_serial=self.device_serial
                    )
                else:
                    update_output("Process crashed successfully with SIGSEGV")

                update_output("Native signal test complete")
            else:
                update_output("Could not determine process ID")
        else:
            update_output("Could not find running process for the app")

    def run_cpu_max_load_test(self):
        """Run a dedicated CPU maximum load test

        This test will run a CPU-intensive operation and monitor CPU usage.
        It's designed to stress all CPU cores to their maximum capacity.
        """
        self.log_message("Starting CPU Max Load Test...")

        # Check if a device is connected
        if not self.device_connected:
            self.log_message("No device connected. Please connect a device first.")
            return

        # Create a visualization window for the test
        test_window = QDialog(self)
        test_window.setWindowTitle("CPU Max Load Test")
        test_window.resize(600, 400)
        test_window.setWindowModality(Qt.ApplicationModal)

        # Configure window content
        main_layout = QVBoxLayout(test_window)

        # Title and description
        title_label = QLabel("CPU Max Load Test")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(title_label)
        main_layout.addWidget(QLabel("This test will stress all CPU cores to measure performance"))

        # Progress display
        progress_frame = QGroupBox("Test Progress")
        progress_layout = QVBoxLayout(progress_frame)
        output_text = QTextEdit()
        output_text.setReadOnly(True)
        progress_layout.addWidget(output_text)
        main_layout.addWidget(progress_frame, 1)

        # Status label
        status_label = QLabel("Initializing test...")
        main_layout.addWidget(status_label)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(test_window.close)
        main_layout.addWidget(close_btn)

        # Function to update output in the text widget
        def update_output(text):
            QTimer.singleShot(0, lambda: [
                output_text.append(text),
                output_text.moveCursor(QTextCursor.End)
            ])

        # Update status in the window
        def update_status(text):
            QTimer.singleShot(0, lambda: status_label.setText(text))

        # Start the test in a separate thread
        threading.Thread(
            target=self._cpu_max_load_test_task,
            args=(update_output, update_status, test_window),
            daemon=True
        ).start()
        test_window.show()

    def _cpu_max_load_test_task(self, update_output, update_status, test_window):
        """Background task for running the CPU max load test with UI updates"""
        try:
            # First check CPU cores
            update_output("Detecting number of CPU cores...")
            success, cores_output = self.run_adb_command(
                ['shell', 'cat', '/proc/cpuinfo', '|', 'grep', 'processor', '|', 'wc', '-l'],
                device_serial=self.device_serial
            )

            if success:
                try:
                    num_cores = int(cores_output.strip())
                    self.log_message(f"Detected {num_cores} CPU cores")
                    update_output(f"Detected {num_cores} CPU cores")
                except ValueError:
                    num_cores = 4  # Fallback to a reasonable default
                    self.log_message(f"Could not determine CPU core count, assuming {num_cores} cores")
                    update_output(f"Could not determine CPU core count, assuming {num_cores} cores")
            else:
                num_cores = 4  # Fallback to a reasonable default
                self.log_message(f"Could not determine CPU core count, assuming {num_cores} cores")
                update_output(f"Could not determine CPU core count, assuming {num_cores} cores")

            # Start monitoring CPU usage in a separate thread
            self.cpu_test_running = True
            update_status("Running CPU stress test...")

            # Store CPU usage data for display
            cpu_readings = []

            # Create a monitor function that updates the UI
            def ui_monitor_cpu():
                while self.cpu_test_running:
                    # Get CPU usage using top command
                    success, output = self.run_adb_command(
                        ['shell', 'top', '-n', '1', '-d', '1', '|', 'grep', 'Cpu'],
                        device_serial=self.device_serial,
                        timeout=5
                    )

                    if success and output:
                        self.log_message(f"CPU Usage: {output.strip()}")
                        update_output(f"CPU Usage: {output.strip()}")
                        cpu_readings.append(output.strip())
                    else:
                        # Try an alternative approach if the first fails
                        success, output = self.run_adb_command(
                            ['shell', 'cat', '/proc/stat'],
                            device_serial=self.device_serial
                        )
                        if success:
                            proc_stat = output.split('\n')[0]
                            self.log_message(f"Raw CPU stats: First line of /proc/stat: {proc_stat}")
                            update_output(f"Raw CPU stats: {proc_stat}")
                            cpu_readings.append(proc_stat)

                    # Wait before next reading
                    time.sleep(2)

            # Start the monitor thread
            monitor_thread = threading.Thread(target=ui_monitor_cpu, daemon=True)
            monitor_thread.start()

            # Run the CPU stress test for 30 seconds
            self.log_message("Running CPU stress test for 30 seconds...")
            update_output("Running CPU stress test for 30 seconds...")

            # Create a script that will stress all CPU cores
            # Use a simpler approach that works on Android's restricted shell
            # Create individual busy loops for each core
            cmds = []
            for i in range(num_cores):
                cmds.append("while true; do echo \"CPU load $i\"; done &")

            # Join commands and add sleep + cleanup
            cpu_script = "; ".join(cmds) + "; sleep 30; pkill -f \"CPU load\""
            update_output(f"Using command: {cpu_script}")

            # Execute the script
            success, output = self.run_adb_command(
                ['shell', 'sh', '-c', cpu_script],
                device_serial=self.device_serial,
                timeout=35  # Give it a bit more than 30 seconds to allow for cleanup
            )

            # Stop monitoring
            self.cpu_test_running = False
            monitor_thread.join(2)  # Wait for monitor thread to finish, but timeout after 2 seconds

            # Update UI with final results
            if success:
                update_status("CPU Max Load Test completed successfully")
                update_output("\nCPU Max Load Test completed successfully")
                self.log_message("CPU Max Load Test completed successfully")
            else:
                update_status("CPU Max Load Test failed or was interrupted")
                update_output(f"\nCPU Max Load Test failed or was interrupted: {output}")
                self.log_message(f"CPU Max Load Test failed or was interrupted: {output}")

        except Exception as e:
            self.log_message(f"Error during CPU Max Load Test: {str(e)}")
            update_status(f"Error: {str(e)}")
            update_output(f"Error during CPU Max Load Test: {str(e)}")
            self.cpu_test_running = False
            import traceback
            error_traceback = traceback.format_exc()
            self.log_message(error_traceback)
            update_output(error_traceback)

    def _monitor_cpu_usage(self):
        """Monitor CPU usage during the CPU stress test"""
        try:
            # Monitor CPU usage every 2 seconds
            while self.cpu_test_running:
                # Get CPU usage using top command
                success, output = self.run_adb_command(
                    ['shell', 'top', '-n', '1', '-d', '1', '|', 'grep', 'Cpu'],
                    device_serial=self.device_serial,
                    timeout=5
                )

                if success and output:
                    self.log_message(f"CPU Usage: {output.strip()}")
                else:
                    # Try an alternative approach if the first fails
                    success, output = self.run_adb_command(
                        ['shell', 'cat', '/proc/stat'],
                        device_serial=self.device_serial
                    )
                    if success:
                        self.log_message(f"Raw CPU stats: First line of /proc/stat: {output.split('\n')[0]}")

                time.sleep(2)
        except Exception as e:
            self.log_message(f"Error monitoring CPU usage: {str(e)}")

    def run_ram_fill_test(self):
        """Run a test to fill RAM incrementally and monitor memory usage

        This test will progressively allocate more memory until a threshold is reached
        or the system becomes unstable, measuring impact on performance.
        """
        self.log_message("Starting RAM Fill Test...")

        # Check if a device is connected
        if not self.device_connected:
            self.log_message("No device connected. Please connect a device first.")
            return

        # Create a visualization window for the test
        test_window = QDialog(self)
        test_window.setWindowTitle("RAM Fill Test")
        test_window.resize(700, 500)
        test_window.setWindowModality(Qt.ApplicationModal)

        # Configure window content
        main_layout = QVBoxLayout(test_window)

        # Title and description
        title_label = QLabel("RAM Fill Test")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(title_label)
        main_layout.addWidget(QLabel("This test will progressively allocate more memory to stress the device RAM"))

        # Progress display
        progress_frame = QGroupBox("Test Progress")
        progress_layout = QVBoxLayout(progress_frame)
        output_text = QTextEdit()
        output_text.setReadOnly(True)
        progress_layout.addWidget(output_text)
        main_layout.addWidget(progress_frame, 1)

        # Memory usage display
        memory_frame = QGroupBox("Memory Usage")
        memory_layout = QVBoxLayout(memory_frame)
        mem_info_label = QLabel("Waiting for memory information...")
        mem_info_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        memory_layout.addWidget(mem_info_label)
        main_layout.addWidget(memory_frame)

        # Status label
        status_label = QLabel("Initializing test...")
        main_layout.addWidget(status_label)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(test_window.close)
        main_layout.addWidget(close_btn)

        # Function to update output in the text widget
        def update_output(text):
            QTimer.singleShot(0, lambda: [
                output_text.append(text),
                output_text.moveCursor(QTextCursor.End)
            ])

        # Update status in the window
        def update_status(text):
            QTimer.singleShot(0, lambda: status_label.setText(text))

        # Update memory info display
        def update_memory_info(text):
            QTimer.singleShot(0, lambda: mem_info_label.setText(text))

        # Start the test in a separate thread
        threading.Thread(
            target=self._ram_fill_test_task,
            args=(update_output, update_status, update_memory_info, test_window),
            daemon=True
        ).start()
        test_window.show()

    def _ram_fill_test_task(self, update_output, update_status, update_memory_info, test_window):
        """Background task for running the RAM fill test with UI updates"""
        try:
            # First get initial memory information
            update_status("Checking initial memory state...")
            update_output("Retrieving initial memory information...")

            success, mem_info = self.run_adb_command(
                ['shell', 'cat', '/proc/meminfo'],
                device_serial=self.device_serial
            )

            if success:
                self.log_message("Initial memory state:")
                update_output("Initial memory state:")

                # Format the memory information for display
                mem_info_formatted = ""
                displayed_lines = 0

                for line in mem_info.split('\n'):
                    if line.strip() and displayed_lines < 10:  # Show first 10 lines with content
                        self.log_message(f"  {line.strip()}")
                        update_output(f"  {line.strip()}")

                        # Add key memory info to the memory display
                        if any(key in line for key in ['MemTotal', 'MemFree', 'MemAvailable', 'SwapTotal', 'SwapFree']):
                            mem_info_formatted += line.strip() + "\n"

                        displayed_lines += 1

                # Update the memory info display
                update_memory_info(mem_info_formatted)
            else:
                self.log_message("Could not retrieve initial memory information")
                update_output("Could not retrieve initial memory information")
                update_memory_info("Memory information unavailable")
                update_status("Error retrieving memory data")

            # Start memory monitoring in a separate thread
            self.ram_test_running = True
            update_status("Starting memory monitoring...")

            # Create a UI memory monitor function that updates the visualization
            def ui_monitor_memory():
                while self.ram_test_running:
                    # Get memory usage summary
                    success, output = self.run_adb_command(
                        ['shell', 'cat', '/proc/meminfo', '|', 'grep', 'Mem'],
                        device_serial=self.device_serial
                    )

                    if success and output:
                        self.log_message(f"Memory Usage Update:\n{output.strip()}")

                        # Format for the memory display
                        mem_info_formatted = "Current Memory Usage:\n"
                        for line in output.split('\n'):
                            if line.strip():
                                mem_info_formatted += line.strip() + "\n"

                        # Update the memory info display
                        update_memory_info(mem_info_formatted)

                    # Also get top memory processes
                    success, procinfo = self.run_adb_command(
                        ['shell', 'ps', '-o', 'pid,ppid,rss,args', '|', 'head', '-5'],
                        device_serial=self.device_serial
                    )

                    if success and procinfo:
                        self.log_message(f"Top memory processes:\n{procinfo.strip()}")

                        # Add this to the output text but not to the memory display
                        update_output("\nTop memory processes:")
                        for line in procinfo.split('\n')[:5]:
                            if line.strip():
                                update_output(line.strip())

                    # Wait before next update
                    time.sleep(3)

            # Start the monitoring thread
            monitor_thread = threading.Thread(target=ui_monitor_memory, daemon=True)
            monitor_thread.start()

            # Create test files of increasing sizes up to 80% of available RAM or 2GB max
            # We'll create temporary files in chunks of 100MB
            chunk_size_mb = 100
            max_chunks = 20  # Maximum 2GB (20 * 100MB)

            self.log_message(f"Incrementally allocating memory in {chunk_size_mb}MB chunks...")
            update_output(f"\nStarting memory allocation test with {chunk_size_mb}MB chunks...")
            update_status(f"Allocating memory in {chunk_size_mb}MB chunks...")

            created_files = []
            for i in range(1, max_chunks + 1):
                # Create unique temp filename for this chunk
                temp_file = f"/data/local/tmp/memtest_{i}.dat"

                # Create the file with dd command
                chunk_message = f"Creating {chunk_size_mb}MB chunk {i}/{max_chunks}..."
                self.log_message(chunk_message)
                update_output(chunk_message)
                update_status(f"Allocating chunk {i}/{max_chunks} ({i * chunk_size_mb}MB total)")

                cmd = f"dd if=/dev/zero of={temp_file} bs=1M count={chunk_size_mb}"
                update_output(f"Command: {cmd}")

                success, output = self.run_adb_command(
                    ['shell', cmd],
                    device_serial=self.device_serial,
                    timeout=30  # Increase timeout for larger files
                )

                if success:
                    created_files.append(temp_file)
                    success_message = f"Successfully allocated {i * chunk_size_mb}MB total"
                    self.log_message(success_message)
                    update_output(success_message)

                    # Check if we've reached a critical memory threshold
                    update_output("Checking available memory...")
                    critical, mem_output = self.run_adb_command(
                        ['shell', 'cat', '/proc/meminfo', '|', 'grep', 'MemAvailable'],
                        device_serial=self.device_serial
                    )

                    if critical and 'MemAvailable' in mem_output:
                        # Show the available memory
                        update_output(f"Available memory: {mem_output.strip()}")

                        # Extract available memory in kB
                        try:
                            available = int(''.join(filter(str.isdigit, mem_output)))
                            available_mb = available // 1024  # Convert to MB

                            if available < 50000:  # Less than 50MB available
                                threshold_message = f"Critical memory threshold reached ({available_mb}MB available). Stopping allocation."
                                self.log_message(threshold_message)
                                update_output(threshold_message)
                                update_status(f"Test completed at {i * chunk_size_mb}MB - memory threshold reached")
                                break
                            else:
                                update_output(f"Memory check: {available_mb}MB still available")
                        except ValueError:
                            # Continue if we can't parse the value
                            update_output("Could not parse available memory value, continuing")
                            pass
                else:
                    error_message = f"Failed to allocate chunk {i}: {output}"
                    self.log_message(error_message)
                    update_output(error_message)
                    update_status(f"Test failed at {i * chunk_size_mb}MB")
                    break

                # Brief pause to allow system to stabilize and monitor to report
                time.sleep(2)

            # Test completed, get final memory state
            update_output("\nTest complete, checking final memory state...")
            update_status("Checking final memory state...")

            success, mem_info = self.run_adb_command(
                ['shell', 'cat', '/proc/meminfo'],
                device_serial=self.device_serial
            )

            if success:
                self.log_message("Final memory state:")
                update_output("Final memory state:")

                # Format for display
                mem_info_formatted = "Final Memory State:\n"
                displayed_lines = 0

                for line in mem_info.split('\n'):
                    if line.strip() and displayed_lines < 10:  # Show first 10 non-empty lines
                        self.log_message(f"  {line.strip()}")
                        update_output(f"  {line.strip()}")

                        # Add key memory info to the memory display
                        if any(key in line for key in ['MemTotal', 'MemFree', 'MemAvailable', 'SwapTotal', 'SwapFree']):
                            mem_info_formatted += line.strip() + "\n"

                        displayed_lines += 1

                # Update the memory info display
                update_memory_info(mem_info_formatted)

            # Cleanup - delete all created test files
            update_output("\nCleaning up test files...")
            update_status("Cleaning up test files...")
            self.log_message("Cleaning up test files...")

            files_cleaned = 0
            for file_path in created_files:
                success, _ = self.run_adb_command(
                    ['shell', 'rm', file_path],
                    device_serial=self.device_serial
                )

                if success:
                    files_cleaned += 1
                    if files_cleaned % 5 == 0:  # Update status every 5 files
                        update_output(f"Removed {files_cleaned}/{len(created_files)} test files")

            update_output(f"Cleanup complete: removed {files_cleaned}/{len(created_files)} test files")

            # Stop memory monitoring
            update_output("\nStopping memory monitoring...")
            update_status("Finalizing test...")
            self.ram_test_running = False
            monitor_thread.join(2)  # Wait but timeout after 2 seconds

            completion_message = "RAM Fill Test completed successfully"
            self.log_message(completion_message)
            update_output("\n" + completion_message)
            update_status("Test completed successfully")

            # Final memory info summary for the display
            success, final_mem = self.run_adb_command(
                ['shell', 'cat', '/proc/meminfo', '|', 'grep', '-E', "'MemTotal|MemFree|MemAvailable'"],
                device_serial=self.device_serial
            )

            if success and final_mem:
                update_output("\nFinal Memory Summary:\n" + final_mem.strip())

        except Exception as e:
            error_message = f"Error during RAM Fill Test: {str(e)}"
            self.log_message(error_message)
            update_output("\n" + error_message)
            update_status("Test failed with errors")

            self.ram_test_running = False

            import traceback
            error_traceback = traceback.format_exc()
            self.log_message(error_traceback)
            update_output(error_traceback)

            # Attempt cleanup in case of error
            cleanup_message = "Attempting cleanup after error..."
            self.log_message(cleanup_message)
            update_output("\n" + cleanup_message)

            # Try to clean up temp files
            self.run_adb_command(
                ['shell', 'rm', '/data/local/tmp/memtest_*.dat'],
                device_serial=self.device_serial
            )
            update_output("Cleanup attempted - please check device storage manually")

    def _monitor_memory_usage(self):
        """Monitor memory usage during the RAM fill test"""
        try:
            # Monitor memory usage every 3 seconds
            while self.ram_test_running:
                # Get memory usage summary
                success, output = self.run_adb_command(
                    ['shell', 'cat', '/proc/meminfo', '|', 'grep', 'Mem'],
                    device_serial=self.device_serial
                )

                if success and output:
                    self.log_message(f"Memory Status:\n{output.strip()}")

                # Also check memory pressure from process list
                success, procinfo = self.run_adb_command(
                    ['shell', 'ps', '-o', 'pid,ppid,rss,args', '|', 'head', '-5'],
                    device_serial=self.device_serial
                )

                if success and procinfo:
                    self.log_message(f"Top memory processes:\n{procinfo.strip()}")

                time.sleep(3)
        except Exception as e:
            self.log_message(f"Error monitoring memory usage: {str(e)}")

    def run_gpu_stress_test(self):
        """Run a GPU stress test on the connected Android device

        This test launches graphics-intensive apps and performs operations to stress
        the GPU by rendering complex content repeatedly.
        """
        self.log_message("Starting GPU Stress Test...")

        # Check if a device is connected
        if not self.device_connected:
            self.log_message("No device connected. Please connect a device first.")
            return

        # Create a visualization window for the test
        test_window = QDialog(self)
        test_window.setWindowTitle("GPU Stress Test")
        test_window.resize(600, 400)
        test_window.setWindowModality(Qt.ApplicationModal)

        # Configure window content
        main_layout = QVBoxLayout(test_window)

        # Title and description
        title_label = QLabel("GPU Stress Test")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(title_label)
        main_layout.addWidget(QLabel("This test will stress the GPU with various rendering operations"))

        # Progress display
        progress_frame = QGroupBox("Test Progress")
        progress_layout = QVBoxLayout(progress_frame)
        output_text = QTextEdit()
        output_text.setReadOnly(True)
        progress_layout.addWidget(output_text)
        main_layout.addWidget(progress_frame, 1)

        # Status label
        status_label = QLabel("Initializing test...")
        main_layout.addWidget(status_label)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(test_window.close)
        main_layout.addWidget(close_btn)

        # Function to update output in the text widget
        def update_output(text):
            QTimer.singleShot(0, lambda: [
                output_text.append(text),
                output_text.moveCursor(QTextCursor.End)
            ])

        # Update status in the window
        def update_status(text):
            QTimer.singleShot(0, lambda: status_label.setText(text))

        # Start the test in a separate thread
        threading.Thread(
            target=self._gpu_stress_test_task,
            args=(update_output, update_status, test_window),
            daemon=True
        ).start()
        test_window.show()

    def _gpu_stress_test_task(self, update_output, update_status, test_window):
        """Background task for running the GPU stress test with UI updates"""
        try:
            # First check if device has a GPU
            self.log_message("Checking device GPU information...")
            update_output("Checking device GPU information...")
            update_status("Detecting GPU...")

            success, gpu_info = self.run_adb_command(
                ['shell', 'dumpsys', 'SurfaceFlinger'],
                device_serial=self.device_serial
            )

            if success:
                self.log_message("Found GPU information. Starting test...")
                update_output("Found GPU information. Starting test...")
                if gpu_info:
                    # Extract and display some GPU information
                    lines = gpu_info.split('\n')
                    gpu_lines = [line for line in lines if 'GL' in line or 'GPU' in line or 'GLES' in line]
                    for line in gpu_lines[:5]:  # Show just the first few GPU-related lines
                        update_output(f"GPU info: {line.strip()}")
            else:
                self.log_message("Could not detect GPU information, but will continue test")
                update_output("Could not detect GPU information, but will continue test")

            # Method 1: Open Chrome and load a WebGL test
            self.log_message("Running WebGL rendering test...")
            update_output("---------------------------")
            update_output("Running WebGL rendering test...")
            update_status("Running WebGL test...")

            # Launch Chrome browser with a WebGL demo page
            webgl_url = "https://webglsamples.org/aquarium/aquarium.html"
            update_output(f"Opening browser with URL: {webgl_url}")

            success, output = self.run_adb_command(
                ['shell', 'am', 'start', '-a', 'android.intent.action.VIEW', '-d', webgl_url],
                device_serial=self.device_serial
            )

            if success:
                self.log_message("Launched WebGL test in browser")
                update_output("Launched WebGL test in browser")
                update_output("Running test for 15 seconds...")

                # Show countdown in UI
                for i in range(15, 0, -1):
                    update_status(f"WebGL test running... {i}s remaining")
                    time.sleep(1)
            else:
                self.log_message("Failed to launch browser for WebGL test")
                update_output(f"Failed to launch browser for WebGL test: {output}")
                update_status("WebGL test failed, continuing with other tests...")

            # Method 2: Run built-in GPU benchmark if available
            self.log_message("Running GPU rendering test with system animations...")
            update_output("---------------------------")
            update_output("Running GPU rendering test with system animations...")
            update_status("Running animations test...")

            # Open Settings and navigate to Developer options
            update_output("Opening Settings app...")
            settings_result, _ = self.run_adb_command(
                ['shell', 'am', 'start', '-a', 'android.settings.SETTINGS'],
                device_serial=self.device_serial
            )

            if settings_result:
                update_output("Settings app opened, waiting for load...")
            else:
                update_output("Could not open Settings app, trying alternate approach")

            time.sleep(2)

            # Scroll through settings several times to stress GPU
            update_output("Performing GPU-intensive scroll animations...")
            for i in range(10):
                self.run_adb_command(
                    ['shell', 'input', 'swipe', '500', '1000', '500', '300'],
                    device_serial=self.device_serial
                )
                if i % 2 == 0:  # Update status every other swipe
                    update_status(f"Animation test: {i+1}/10 complete")
                time.sleep(0.3)

            # Method 3: Enable GPU overdraw visualization to stress rendering
            self.log_message("Enabling GPU overdraw debugging...")
            update_output("---------------------------")
            update_output("Enabling GPU overdraw visualization to stress the renderer...")
            update_status("Running overdraw test...")

            overdraw_result, overdraw_output = self.run_adb_command(
                ['shell', 'setprop', 'debug.hwui.overdraw', 'show'],
                device_serial=self.device_serial
            )

            if overdraw_result:
                update_output("GPU overdraw visualization enabled")
            else:
                update_output(f"Could not enable GPU overdraw: {overdraw_output}")

            # Launch Gallery or Photos app which uses GPU
            self.log_message("Opening Gallery app for GPU rendering...")
            update_output("Opening Gallery app for GPU rendering test...")
            gallery_success = False

            # Try several common gallery apps
            update_output("Attempting to find and launch a gallery app...")
            for gallery_app in [
                "com.google.android.apps.photos",
                "com.android.gallery3d",
                "com.sec.android.gallery3d"
            ]:
                update_output(f"Trying gallery app: {gallery_app}")
                success, launch_output = self.run_adb_command(
                    ['shell', 'am', 'start', '-n', f"{gallery_app}/.MainActivity"],
                    device_serial=self.device_serial
                )

                if success:
                    gallery_success = True
                    message = f"Successfully opened gallery app: {gallery_app}"
                    self.log_message(message)
                    update_output(message)
                    update_status("Running gallery scrolling test...")
                    break
                else:
                    update_output(f"Could not open {gallery_app}: {launch_output}")

            if gallery_success:
                # Scroll through gallery
                update_output("Scrolling through gallery to stress GPU rendering...")
                for i in range(5):
                    update_output(f"Performing scroll {i+1}/5...")
                    self.run_adb_command(
                        ['shell', 'input', 'swipe', '500', '800', '500', '200'],
                        device_serial=self.device_serial
                    )
                    update_status(f"Gallery test: {i+1}/5 scrolls complete")
                    time.sleep(1)
            else:
                update_output("Could not open any gallery app, skipping this part of the test")
                update_status("Continuing with test...")

            # Disable GPU overdraw visualization
            update_output("---------------------------")
            update_output("Test complete, cleaning up...")
            update_status("Cleaning up...")

            update_output("Disabling GPU overdraw visualization")
            self.run_adb_command(
                ['shell', 'setprop', 'debug.hwui.overdraw', 'false'],
                device_serial=self.device_serial
            )

            # Return to home screen
            update_output("Returning to home screen")
            self.run_adb_command(
                ['shell', 'input', 'keyevent', 'KEYCODE_HOME'],
                device_serial=self.device_serial
            )

            complete_message = "GPU Stress Test completed successfully"
            self.log_message(complete_message)
            update_output("\n" + complete_message)
            update_status("Test completed successfully")

        except Exception as e:
            error_message = f"Error during GPU Stress Test: {str(e)}"
            self.log_message(error_message)
            update_output("\n" + error_message)
            update_status("Test failed with errors")

            import traceback
            error_traceback = traceback.format_exc()
            self.log_message(error_traceback)
            update_output(error_traceback)

            # Try to return to home screen in case of errors
            update_output("Attempting to return to home screen")
            self.run_adb_command(
                ['shell', 'input', 'keyevent', 'KEYCODE_HOME'],
                device_serial=self.device_serial
            )

    def run_dalvik_cache_stress_test(self):
        """Run a stress test that targets the Dalvik/ART cache system

        This test repeatedly launches and kills apps to stress the Dalvik/ART
        cache system and measure performance impact.
        """
        self.log_message("Starting Dalvik Cache Stress Test...")

        # Check if a device is connected
        if not self.device_connected:
            self.log_message("No device connected. Please connect a device first.")
            return

        # Create a visualization window for the test
        test_window = QDialog(self)
        test_window.setWindowTitle("Dalvik Cache Stress Test")
        test_window.resize(700, 500)
        test_window.setWindowModality(Qt.ApplicationModal)

        # Configure window content
        main_layout = QVBoxLayout(test_window)

        # Title and description
        title_label = QLabel("Dalvik Cache Stress Test")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(title_label)
        main_layout.addWidget(QLabel("This test will stress the Dalvik/ART runtime cache system"))

        # Cache info display
        cache_frame = QGroupBox("Cache Information")
        cache_layout = QVBoxLayout(cache_frame)
        cache_info_label = QLabel("Checking cache information...")
        cache_info_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        cache_layout.addWidget(cache_info_label)
        main_layout.addWidget(cache_frame)

        # Progress display
        progress_frame = QGroupBox("Test Progress")
        progress_layout = QVBoxLayout(progress_frame)
        output_text = QTextEdit()
        output_text.setReadOnly(True)
        progress_layout.addWidget(output_text)
        main_layout.addWidget(progress_frame, 1)

        # Status label
        status_label = QLabel("Initializing test...")
        main_layout.addWidget(status_label)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(test_window.close)
        main_layout.addWidget(close_btn)

        # Function to update output in the text widget
        def update_output(text):
            QTimer.singleShot(0, lambda: [
                output_text.append(text),
                output_text.moveCursor(QTextCursor.End)
            ])

        # Update status in the window
        def update_status(text):
            QTimer.singleShot(0, lambda: status_label.setText(text))

        # Update cache info display
        def update_cache_info(text):
            QTimer.singleShot(0, lambda: cache_info_label.setText(text))

        # Start the test in a separate thread
        threading.Thread(
            target=self._dalvik_cache_stress_test_task,
            args=(update_output, update_status, update_cache_info, test_window),
            daemon=True
        ).start()
        test_window.show()

    def _dalvik_cache_stress_test_task(self, update_output, update_status, update_cache_info, test_window):
        """Background task for running the Dalvik Cache stress test with UI updates"""
        try:
            # First check device SDK version - different commands for different Android versions
            update_status("Checking Android version...")
            update_output("Retrieving device Android version...")

            # Get Android version
            success, sdk_info = self.run_adb_command(
                ['shell', 'getprop', 'ro.build.version.sdk'],
                device_serial=self.device_serial
            )

            if success:
                try:
                    sdk_version = int(sdk_info.strip())
                    update_output(f"Device SDK version: {sdk_version}")
                except (ValueError, TypeError):
                    sdk_version = 0  # Default to 0 if we can't parse the version
                    update_output(f"Could not parse SDK version: {sdk_info}")
            else:
                sdk_version = 0
                update_output("Could not determine SDK version")

            # Check if using ART or Dalvik (ART replaced Dalvik in Android 5.0/SDK 21+)
            runtime_type = "ART" if sdk_version >= 21 else "Dalvik"
            update_output(f"Device is using {runtime_type} runtime")

            # Get initial cache information
            update_status("Checking initial cache state...")
            update_output("Retrieving initial cache information...")

            # For ART (Android 5.0+), use different commands than Dalvik
            if runtime_type == "ART":
                # Try to get cache info - will be different depending on Android version
                success, cache_info = self.run_adb_command(
                    ['shell', 'dumpsys', 'package', '|', 'grep', '-i', 'dexopt'],
                    device_serial=self.device_serial
                )
            else:
                # Older Dalvik VM info
                success, cache_info = self.run_adb_command(
                    ['shell', 'ls', '-la', '/data/dalvik-cache/'],
                    device_serial=self.device_serial
                )

            if success:
                update_output("Initial cache information:\n" + cache_info)
                update_cache_info(f"{runtime_type} Cache Information:\n{cache_info[:200]}...")
            else:
                update_output("Could not retrieve initial cache information")
                update_cache_info("Cache information unavailable")

            # Get list of installed apps for launching
            update_status("Finding applications for test...")
            update_output("Getting list of installed applications...")

            success, app_list = self.run_adb_command(
                ['shell', 'pm', 'list', 'packages', '-3'],  # -3 flag for third-party apps only
                device_serial=self.device_serial
            )

            if success and app_list:
                # Parse application package names
                apps = []
                for line in app_list.split('\n'):
                    if line.startswith('package:'):
                        apps.append(line[8:].strip())  # Remove 'package:' prefix

                if len(apps) > 0:
                    update_output(f"Found {len(apps)} applications for testing")
                    # Take only the first 5 apps for the test to avoid taking too long
                    test_apps = apps[:5]
                    update_output(f"Selected {len(test_apps)} applications for test: {', '.join(test_apps)}")
                else:
                    update_output("No suitable applications found for testing")
                    update_status("Test aborted: No applications found")
                    return
            else:
                update_output("Could not retrieve application list")
                update_status("Test aborted: Could not get app list")
                return

            # Start the stress test sequence
            update_output("\nStarting Dalvik/ART cache stress test sequence...")
            update_status("Running test: Launching applications")

            # Measure app launch times before cache stress
            initial_launch_times = {}

            update_output("\nMeasuring initial app launch times...")
            for app in test_apps:
                update_output(f"Launching {app}...")

                # Force stop the app first to ensure a clean launch
                self.run_adb_command(
                    ['shell', 'am', 'force-stop', app],
                    device_serial=self.device_serial
                )
                time.sleep(1)  # Wait for app to fully close

                # Launch app and measure time
                start_time = time.time()
                launch_result, _ = self.run_adb_command(
                    ['shell', 'am', 'start', '-n', f"{app}/.MainActivity"],
                    device_serial=self.device_serial
                )

                # Wait for app to fully launch (up to 5 seconds)
                time.sleep(3)

                if launch_result:
                    end_time = time.time()
                    launch_time = end_time - start_time
                    initial_launch_times[app] = launch_time
                    update_output(f"Initial launch time for {app}: {launch_time:.3f} seconds")
                else:
                    update_output(f"Failed to launch {app}")

                # Go back to home screen
                self.run_adb_command(
                    ['shell', 'input', 'keyevent', 'KEYCODE_HOME'],
                    device_serial=self.device_serial
                )
                time.sleep(1)

            # Perform stress test to clear and regenerate caches
            update_output("\nStressing cache by repeatedly launching and closing apps...")
            update_status("Running test: Cache stress cycles")

            # Define stress cycle count
            stress_cycles = 5

            for cycle in range(1, stress_cycles + 1):
                update_output(f"\nCycle {cycle}/{stress_cycles}:")
                update_status(f"Stress cycle {cycle}/{stress_cycles}")

                for app in test_apps:
                    # Launch app
                    update_output(f"Launching {app}...")
                    self.run_adb_command(
                        ['shell', 'am', 'start', '-n', f"{app}/.MainActivity"],
                        device_serial=self.device_serial
                    )
                    time.sleep(2)  # Let app run briefly

                    # Stop app
                    update_output(f"Stopping {app}...")
                    self.run_adb_command(
                        ['shell', 'am', 'force-stop', app],
                        device_serial=self.device_serial
                    )
                    time.sleep(1)  # Wait before next app

            # For more stress, try to clear some caches (this might require root on newer Android)
            if sdk_version < 23:  # For older Android versions, try clearing cache
                update_output("\nAttempting to clear runtime caches...")
                update_status("Running test: Cache clearing")

                # This is simplified and may not work on all devices, especially newer ones
                if runtime_type == "ART":
                    clear_cmd = "rm -rf /data/dalvik-cache/*"
                else:
                    clear_cmd = "rm -rf /data/dalvik-cache/*"

                # Try normal clear first
                clear_result, clear_output = self.run_adb_command(
                    ['shell', clear_cmd],
                    device_serial=self.device_serial
                )

                if not clear_result:
                    # Try with su if available (root)
                    update_output("Attempting with root privileges...")
                    self.run_adb_command(
                        ['shell', 'su', '-c', clear_cmd],
                        device_serial=self.device_serial
                    )

            # Measure app launch times after cache stress
            update_output("\nMeasuring app launch times after cache stress...")
            update_status("Measuring final launch times")

            final_launch_times = {}

            for app in test_apps:
                if app in initial_launch_times:  # Only test apps we successfully measured before
                    update_output(f"Re-launching {app}...")

                    # Force stop the app first
                    self.run_adb_command(
                        ['shell', 'am', 'force-stop', app],
                        device_serial=self.device_serial
                    )
                    time.sleep(1)

                    # Launch app and measure time
                    start_time = time.time()
                    launch_result, _ = self.run_adb_command(
                        ['shell', 'am', 'start', '-n', f"{app}/.MainActivity"],
                        device_serial=self.device_serial
                    )

                    # Wait for app to fully launch
                    time.sleep(3)

                    if launch_result:
                        end_time = time.time()
                        launch_time = end_time - start_time
                        final_launch_times[app] = launch_time
                        update_output(f"Final launch time for {app}: {launch_time:.3f} seconds")
                    else:
                        update_output(f"Failed to launch {app}")

                    # Go back to home screen
                    self.run_adb_command(
                        ['shell', 'input', 'keyevent', 'KEYCODE_HOME'],
                        device_serial=self.device_serial
                    )
                    time.sleep(1)

            # Return to home screen for final cleanup
            update_output("\nReturning to home screen...")
            self.run_adb_command(
                ['shell', 'input', 'keyevent', 'KEYCODE_HOME'],
                device_serial=self.device_serial
            )

            # Analyze and display results
            update_output("\nAnalyzing test results...")
            update_status("Analyzing results")

            if initial_launch_times and final_launch_times:
                results = []
                for app in initial_launch_times:
                    if app in final_launch_times:
                        initial = initial_launch_times[app]
                        final = final_launch_times[app]
                        diff = final - initial
                        percent = (diff / initial) * 100 if initial > 0 else 0

                        result = f"{app}: Initial: {initial:.3f}s, Final: {final:.3f}s, "
                        result += f"Difference: {diff:.3f}s ({percent:+.1f}%)"
                        results.append(result)

                # Format results for display
                if results:
                    result_text = "\nTest Results (Launch Time Comparison):\n"
                    result_text += "\n".join(results)
                    update_output(result_text)

                    # Update cache info with results summary
                    update_cache_info(f"{runtime_type} Cache Stress Test Results:\n" + "\n".join(results))

                    # Set final status based on average change
                    total_percent = sum([(final_launch_times[app] - initial_launch_times[app]) / initial_launch_times[app] * 100
                                         for app in initial_launch_times if app in final_launch_times and initial_launch_times[app] > 0])
                    avg_percent = total_percent / len(results) if results else 0

                    if avg_percent > 10:
                        update_status(f"Test completed: Performance degraded by {avg_percent:.1f}%")
                    elif avg_percent < -5:
                        update_status(f"Test completed: Performance improved by {abs(avg_percent):.1f}%")
                    else:
                        update_status("Test completed: No significant performance change")
                else:
                    update_output("Could not compare launch times for any applications")
                    update_status("Test completed with insufficient data")
            else:
                update_output("Could not collect sufficient launch time data for comparison")
                update_status("Test completed with insufficient data")

            # Final completion message
            completion_msg = "Dalvik/ART Cache Stress Test completed"
            self.log_message(completion_msg)
            update_output("\n" + completion_msg)

        except Exception as e:
            error_msg = f"Error during Dalvik Cache Stress Test: {str(e)}"
            self.log_message(error_msg)
            update_output("\n" + error_msg)
            update_status("Test failed with errors")

            import traceback
            error_traceback = traceback.format_exc()
            self.log_message(error_traceback)
            update_output(error_traceback)

    def run_looped_benchmarking(self):
        """Run a series of benchmarks in a loop to test performance stability

        This test executes various benchmarks repeatedly to measure performance
        consistency and detect degradation over time.
        """
        self.log_message("Starting Looped Benchmarking...")

        # Check if a device is connected
        if not hasattr(self, 'device_serial') or not self.device_serial:
            self.log_message("No device connected. Please connect a device first.")
            return

        # Create a configuration dialog for the benchmark
        config_dialog = QDialog(self)
        self._looped_benchmark_dialog = config_dialog
        config_dialog.setWindowTitle("Looped Benchmarking")
        config_dialog.resize(750, 850)
        config_dialog.setWindowModality(Qt.ApplicationModal)

        # Add some padding
        main_layout = QVBoxLayout(config_dialog)

        # Form layout
        form_frame = QWidget()
        form_layout = QGridLayout(form_frame)
        main_layout.addWidget(form_frame)

        benchmark_types = [
            "CPU Performance",
            "Storage I/O",
            "Memory Access",
            "UI Responsiveness",
            "All Benchmarks"
        ]
        form_layout.addWidget(QLabel("Benchmark Type:"), 0, 0)
        benchmark_combo = QComboBox()
        benchmark_combo.addItems(benchmark_types)
        form_layout.addWidget(benchmark_combo, 0, 1, 1, 2)

        form_layout.addWidget(QLabel("Number of Iterations:"), 1, 0)
        iterations_spin = QSpinBox()
        iterations_spin.setRange(1, 100)
        iterations_spin.setValue(5)
        form_layout.addWidget(iterations_spin, 1, 1)

        form_layout.addWidget(QLabel("Time Between Iterations (s):"), 2, 0)
        delay_spin = QSpinBox()
        delay_spin.setRange(0, 3600)
        delay_spin.setValue(30)
        form_layout.addWidget(delay_spin, 2, 1)

        # Create result frame
        result_frame = QGroupBox("Benchmark Results")
        result_layout = QVBoxLayout(result_frame)
        result_text = QTextEdit()
        result_text.setReadOnly(True)
        result_layout.addWidget(result_text)
        main_layout.addWidget(result_frame, 1)

        # Add progress bar
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        main_layout.addWidget(progress_bar)

        # Status label
        status_label = QLabel("Ready")
        main_layout.addWidget(status_label)

        # Button frame
        btn_frame = QWidget()
        btn_layout = QHBoxLayout(btn_frame)
        main_layout.addWidget(btn_frame)

        # Variable to control the benchmark process
        running = [False]  # Use a list to allow modification from nested functions

        # Start button function
        def start_benchmark():
            if running[0]:
                return  # Already running

            try:
                # Validate inputs
                num_iterations = iterations_spin.value()
                between_delay = delay_spin.value()

                # Clear results
                result_text.clear()
                update_result(f"Starting {benchmark_combo.currentText()} benchmark with {num_iterations} iterations...")

                # Start the benchmark in a separate thread
                running[0] = True
                start_btn.setEnabled(False)
                stop_btn.setEnabled(True)

                # Reset progress bar
                progress_bar.setValue(0)
                status_label.setText("Running...")

                benchmark_thread = threading.Thread(
                    target=lambda: self._run_looped_benchmark(
                        benchmark_combo.currentText(), num_iterations, between_delay,
                        update_result, update_progress, lambda: running[0],
                        on_benchmark_complete),
                    daemon=True
                )
                benchmark_thread.start()

            except Exception as e:
                update_result(f"Error: {str(e)}")
                running[0] = False
                start_btn.setEnabled(True)
                stop_btn.setEnabled(False)

        # Stop button function
        def stop_benchmark():
            running[0] = False
            update_result("Stopping benchmark...")
            update_progress(100, "Stopped")

        # Function to update results
        def update_result(message):
            QTimer.singleShot(0, lambda: [
                result_text.append(message),
                result_text.moveCursor(QTextCursor.End)
            ])

        # Function to update progress
        def update_progress(percent, message=None):
            def apply_progress():
                progress_bar.setValue(int(percent))
                if message:
                    status_label.setText(message)

            QTimer.singleShot(0, apply_progress)

        # Function called when benchmark is complete
        def on_benchmark_complete():
            def finalize():
                start_btn.setEnabled(True)
                stop_btn.setEnabled(False)
                running[0] = False
                status_label.setText("Completed")

            QTimer.singleShot(0, finalize)

        # Add buttons
        start_btn = QPushButton("Start")
        start_btn.clicked.connect(start_benchmark)
        btn_layout.addWidget(start_btn)

        stop_btn = QPushButton("Stop")
        stop_btn.setEnabled(False)
        stop_btn.clicked.connect(stop_benchmark)
        btn_layout.addWidget(stop_btn)

        # Initial update
        update_result("Configure the benchmark parameters and click Start to begin.")
        config_dialog.show()

    def _run_looped_benchmark(self, benchmark_type, iterations, delay_sec, result_callback, progress_callback, should_continue, on_complete):
        """Run the selected benchmark in a loop"""
        try:
            # Initialize results storage
            results = []

            # Determine which benchmarks to run
            benchmarks = []
            if benchmark_type == "All Benchmarks" or benchmark_type == "CPU Performance":
                benchmarks.append(self._run_cpu_benchmark)
            if benchmark_type == "All Benchmarks" or benchmark_type == "Storage I/O":
                benchmarks.append(self._run_storage_benchmark)
            if benchmark_type == "All Benchmarks" or benchmark_type == "Memory Access":
                benchmarks.append(self._run_memory_benchmark)
            if benchmark_type == "All Benchmarks" or benchmark_type == "UI Responsiveness":
                benchmarks.append(self._run_ui_benchmark)

            if not benchmarks:
                result_callback("No benchmarks selected.")
                progress_callback(100, "Completed")
                on_complete()
                return

            # Run the benchmark iterations
            for i in range(iterations):
                if not should_continue():
                    break

                result_callback(f"Starting iteration {i+1}/{iterations}")
                iteration_results = {}

                for benchmark_func in benchmarks:
                    if not should_continue():
                        break

                    # Run the specific benchmark and get results
                    name, score = benchmark_func()
                    iteration_results[name] = score

                    # Update results
                    result_callback(f"  {name}: {score}")

                results.append(iteration_results)

                # Update progress
                progress_percent = ((i + 1) / iterations) * 100
                progress_callback(progress_percent, f"Completed iteration {i+1}/{iterations}")

                # Wait between iterations, but allow for early termination
                if i < iterations - 1 and should_continue():
                    result_callback(f"Waiting {delay_sec} seconds before next iteration...")

                    # Wait in small increments to allow cancellation
                    for j in range(delay_sec):
                        if not should_continue():
                            break
                        time.sleep(1)

            # Analyze and report results if we completed all iterations
            if should_continue() and len(results) == iterations:
                result_callback("\nBenchmark Summary:")

                # Calculate statistics for each benchmark type
                for benchmark_name in results[0].keys():
                    scores = [result[benchmark_name] for result in results if benchmark_name in result]
                    if scores:
                        avg = sum(scores) / len(scores)
                        min_score = min(scores)
                        max_score = max(scores)

                        # Calculate standard deviation
                        if len(scores) > 1:
                            variance = sum((x - avg) ** 2 for x in scores) / len(scores)
                            std_dev = variance ** 0.5
                            variation = (std_dev / avg) * 100 if avg > 0 else 0
                        else:
                            std_dev = 0
                            variation = 0

                        result_callback(f"  {benchmark_name}:")
                        result_callback(f"    Average: {avg:.2f}")
                        result_callback(f"    Min: {min_score:.2f}, Max: {max_score:.2f}")
                        result_callback(f"    Variability: {variation:.2f}% (lower is better)")

                        # Detect performance degradation
                        if len(scores) >= 3:
                            # Check if scores are consistently declining
                            declining = all(scores[i] > scores[i+1] for i in range(len(scores)-1))
                            if declining:
                                result_callback("    WARNING: Performance appears to be consistently declining!")

            # Final message
            if should_continue():
                result_callback("\nBenchmark completed successfully.")
            else:
                result_callback("\nBenchmark was interrupted.")

        except Exception as e:
            result_callback(f"Error during benchmark: {str(e)}")
            import traceback
            result_callback(traceback.format_exc())
        finally:
            on_complete()

    def _run_cpu_benchmark(self):
        """Run a CPU benchmark and return the results"""
        self.log_message("Running CPU benchmark...")

        try:
            # Use a shell script to measure performance of CPU operations
            # We'll calculate primes as a CPU benchmark
            cpu_script = """
            start=$(date +%s%N)
            for i in $(seq 1 1000); do
                for j in $(seq 1 100); do
                    echo $i | awk 'BEGIN{s=0}{for(i=1;i<=$1;i++)if($1%i==0)s+=i}END{print s}'
                done | grep -v "^" > /dev/null
            done
            end=$(date +%s%N)
            elapsed=$(( (end - start) / 1000000 ))
            echo $elapsed
            """

            success, output = self.run_adb_command(
                ['shell', 'sh', '-c', cpu_script],
                device_serial=self.device_serial,
                timeout=120  # Allow up to 2 minutes for the benchmark
            )

            if success and output.strip().isdigit():
                # Lower is better (less time to complete)
                elapsed_ms = int(output.strip())
                score = 10000.0 / elapsed_ms if elapsed_ms > 0 else 0  # Normalize to a score where higher is better
                return "CPU Performance", score
            else:
                # Try an alternative approach if the first method fails
                alt_script = """
                start_time=$(date +%s)
                for i in $(seq 1 10000); do
                    echo $i > /dev/null
                done
                end_time=$(date +%s)
                echo $((end_time - start_time))
                """

                success, output = self.run_adb_command(
                    ['shell', 'sh', '-c', alt_script],
                    device_serial=self.device_serial
                )

                if success and output.strip().isdigit():
                    elapsed_sec = int(output.strip())
                    score = 100.0 / elapsed_sec if elapsed_sec > 0 else 0
                    return "CPU Performance", score

                return "CPU Performance", 0.0
        except Exception as e:
            self.log_message(f"Error in CPU benchmark: {str(e)}")
            return "CPU Performance", 0.0

    def _run_storage_benchmark(self):
        """Run a storage I/O benchmark and return the results"""
        self.log_message("Running storage I/O benchmark...")

        try:
            # Run a simple dd command to test write speed
            write_script = "dd if=/dev/zero of=/data/local/tmp/iotest bs=4k count=10000; sync"

            success, write_output = self.run_adb_command(
                ['shell', 'sh', '-c', f"{write_script}; echo $?"],
                device_serial=self.device_serial,
                timeout=60
            )

            # Run a simple read benchmark
            read_script = "dd if=/data/local/tmp/iotest of=/dev/null bs=4k count=10000"

            success, read_output = self.run_adb_command(
                ['shell', 'sh', '-c', f"{read_script}; echo $?"],
                device_serial=self.device_serial,
                timeout=30
            )

            # Clean up the test file
            self.run_adb_command(
                ['shell', 'rm', '/data/local/tmp/iotest'],
                device_serial=self.device_serial
            )

            # Parse the output to extract throughput
            write_speed = 0
            read_speed = 0

            if success:
                # Try to extract the throughput from dd output
                # Output format varies by device, so try multiple patterns

                # Use a secondary timing method if dd doesn't provide timing info
                timing_script = """
                start=$(date +%s%N)
                dd if=/dev/zero of=/data/local/tmp/speedtest bs=4k count=5000 2>/dev/null
                sync
                end=$(date +%s%N)
                echo $((end - start))
                rm /data/local/tmp/speedtest
                """

                success, timing_output = self.run_adb_command(
                    ['shell', 'sh', '-c', timing_script],
                    device_serial=self.device_serial,
                    timeout=30
                )

                if success and timing_output.strip().isdigit():
                    # Calculate MB/s: 5000 blocks * 4KB / nanoseconds * 10^9 / (1024*1024) for MB/s
                    nanos = int(timing_output.strip())
                    if nanos > 0:
                        mb_per_sec = (5000 * 4 * 1024) / nanos * 10**9 / (1024*1024)
                        score = mb_per_sec  # Higher is better
                        return "Storage I/O", score

                # Fallback to a basic score if timing failed
                return "Storage I/O", 50.0
            else:
                return "Storage I/O", 0.0
        except Exception as e:
            self.log_message(f"Error in storage benchmark: {str(e)}")
            return "Storage I/O", 0.0

    def _run_memory_benchmark(self):
        """Run a memory access benchmark and return the results"""
        self.log_message("Running memory access benchmark...")

        try:
            # Create a script that allocates and accesses memory
            mem_script = """
            start=$(date +%s%N)
            # Create a large file in memory
            dd if=/dev/zero of=/dev/shm/memtest bs=1M count=50 2>/dev/null
            # Read it back multiple times
            for i in $(seq 1 5); do
                cat /dev/shm/memtest > /dev/null
            done
            # Clean up
            rm /dev/shm/memtest 2>/dev/null || rm /data/local/tmp/memtest 2>/dev/null
            end=$(date +%s%N)
            elapsed=$(( (end - start) / 1000000 ))
            echo $elapsed
            """

            # First check if /dev/shm exists
            success, shm_check = self.run_adb_command(
                ['shell', 'ls', '/dev/shm'],
                device_serial=self.device_serial
            )

            if not success or 'No such file or directory' in shm_check:
                # Use data/local/tmp instead if /dev/shm doesn't exist
                mem_script = mem_script.replace('/dev/shm', '/data/local/tmp')

            # Run the benchmark
            success, output = self.run_adb_command(
                ['shell', 'sh', '-c', mem_script],
                device_serial=self.device_serial,
                timeout=60
            )

            if success and output.strip().isdigit():
                elapsed_ms = int(output.strip())
                score = 5000.0 / elapsed_ms if elapsed_ms > 0 else 0  # Normalize so higher is better
                return "Memory Access", score
            else:
                # Alternative simpler test
                alt_script = """
                start=$(date +%s)
                for i in $(seq 1 5); do
                    dd if=/dev/zero of=/data/local/tmp/memtest bs=1M count=20 2>/dev/null
                    cat /data/local/tmp/memtest > /dev/null
                    rm /data/local/tmp/memtest
                done
                end=$(date +%s)
                echo $((end - start))
                """

                success, output = self.run_adb_command(
                    ['shell', 'sh', '-c', alt_script],
                    device_serial=self.device_serial
                )

                if success and output.strip().isdigit():
                    elapsed_sec = int(output.strip())
                    score = 20.0 / elapsed_sec if elapsed_sec > 0 else 0
                    return "Memory Access", score

                return "Memory Access", 0.0
        except Exception as e:
            self.log_message(f"Error in memory benchmark: {str(e)}")
            return "Memory Access", 0.0

    def _run_ui_benchmark(self):
        """Run a UI responsiveness benchmark and return the results"""
        self.log_message("Running UI responsiveness benchmark...")

        try:
            # Measure how quickly the device can perform UI operations
            # We'll use app switching and screen navigation as a metric

            # First clear any background tasks
            self.run_adb_command(
                ['shell', 'input', 'keyevent', 'KEYCODE_HOME'],
                device_serial=self.device_serial
            )
            time.sleep(1)

            # Script to time app switching and UI operations
            ui_script = """
            start=$(date +%s%N)
            # Go home
            input keyevent KEYCODE_HOME
            sleep 0.5
            # Open recent apps
            input keyevent KEYCODE_APP_SWITCH
            sleep 0.5
            # Navigate and go back home
            input swipe 500 500 300 500
            sleep 0.5
            input keyevent KEYCODE_HOME
            sleep 0.5
            # Open settings
            am start -a android.settings.SETTINGS
            sleep 1
            # Scroll a few times
            input swipe 500 1000 500 300
            sleep 0.5
            input swipe 500 1000 500 300
            sleep 0.5
            # Go back home
            input keyevent KEYCODE_HOME
            end=$(date +%s%N)
            elapsed=$(( (end - start) / 1000000 ))
            echo $elapsed
            """

            success, output = self.run_adb_command(
                ['shell', 'sh', '-c', ui_script],
                device_serial=self.device_serial,
                timeout=60
            )

            if success and output.strip().isdigit():
                elapsed_ms = int(output.strip())
                # For UI tests, we want a score where higher is better
                # A typical good device might complete this in 4-5 seconds
                # So normalize to a 0-100 scale where 100 is 4 seconds or less
                if elapsed_ms <= 4000:
                    score = 100.0
                else:
                    score = max(0, 100 - (elapsed_ms - 4000) / 100)

                return "UI Responsiveness", score
            else:
                return "UI Responsiveness", 0.0
        except Exception as e:
            self.log_message(f"Error in UI benchmark: {str(e)}")
            return "UI Responsiveness", 0.0

    def run_hardware_stress_test(self):
        """Run a comprehensive hardware stress test"""
        if not self.device_connected:
            QMessageBox.information(self, "Not Connected", "Please connect to a device first.")
            return

        self.log_message("Starting comprehensive Hardware Stress Test...")
        threading.Thread(target=self._hardware_stress_test_task, daemon=True).start()

    def _hardware_stress_test_task(self):
        """Background task for running the hardware stress test"""
        try:
            self.log_message("Running CPU stress test...")
            cpu_script = "for i in $(seq 1 8); do while : ; do : ; done & done; sleep 15; killall sh"
            success, output = self.run_adb_command(['shell', 'sh', '-c', cpu_script], device_serial=self.device_serial, timeout=20)

            if success:
                self.log_message("CPU stress test completed")
            else:
                self.log_message("CPU stress test failed or was interrupted")

            self.log_message("Running memory allocation test...")
            mem_script = "dd if=/dev/zero of=/data/local/tmp/memtest bs=1M count=100; rm /data/local/tmp/memtest"
            success, output = self.run_adb_command(['shell', 'sh', '-c', mem_script], device_serial=self.device_serial)

            if success:
                self.log_message("Memory allocation test completed")
            else:
                self.log_message(f"Memory allocation test failed: {output}")

            self.log_message("Running storage I/O test...")
            io_script = "dd if=/dev/zero of=/data/local/tmp/iotest bs=4k count=25000; sync; rm /data/local/tmp/iotest"
            success, output = self.run_adb_command(['shell', 'sh', '-c', io_script], device_serial=self.device_serial)

            if success:
                self.log_message("Storage I/O test completed")
            else:
                self.log_message(f"Storage I/O test failed: {output}")

            self.log_message("Running UI rendering test...")
            self.run_adb_command(['shell', 'am', 'start', '-a', 'android.settings.SETTINGS'], device_serial=self.device_serial)
            time.sleep(2)

            for i in range(5):
                self.run_adb_command(['shell', 'input', 'swipe', '500', '1000', '500', '300'], device_serial=self.device_serial)
                time.sleep(0.5)

            self.run_adb_command(['shell', 'input', 'keyevent', 'KEYCODE_HOME'], device_serial=self.device_serial)

            self.log_message("Hardware stress test completed successfully")

        except Exception as e:
            self.log_message(f"Hardware stress test failed: {str(e)}")

    def _monkey_testing_dialog(self):
        """Show dialog for Monkey testing"""
        if not self.device_connected:
            QMessageBox.information(self, "Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = QDialog(self)
            self._io_spike_dialog = dialog
            self._monkey_dialog = dialog
            dialog.setWindowTitle("Monkey Testing")
            dialog.resize(600, 500)
            dialog.setWindowModality(Qt.ApplicationModal)

            screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
            x_pos = screen_geometry.x() + (screen_geometry.width() - 600) // 2
            y_pos = screen_geometry.y() + (screen_geometry.height() - 500) // 2
            dialog.move(x_pos, y_pos)

            main_layout = QVBoxLayout(dialog)
            title_label = QLabel("Monkey Testing")
            title_label.setStyleSheet("font-size: 12px; font-weight: bold;")
            main_layout.addWidget(title_label)
            main_layout.addWidget(QLabel("Monkey is a program that generates random events on your device."))

            # Package selection
            pkg_frame = QGroupBox("Target Package")
            pkg_layout = QVBoxLayout(pkg_frame)
            pkg_combo = QComboBox()
            pkg_layout.addWidget(pkg_combo)
            main_layout.addWidget(pkg_frame)

            # Load packages
            def load_packages():
                result = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "pm", "list", "packages", "-3"],
                    capture_output=True, text=True, timeout=20
                )
                if result.returncode == 0:
                    packages = [line[8:] for line in result.stdout.strip().split('\n') if line.startswith('package:')]
                    QTimer.singleShot(0, lambda: pkg_combo.addItems(packages))

            threading.Thread(target=load_packages, daemon=True).start()

            # Event count
            count_frame = QWidget()
            count_layout = QHBoxLayout(count_frame)
            count_layout.addWidget(QLabel("Number of events:"))
            count_spinbox = QSpinBox()
            count_spinbox.setRange(100, 100000)
            count_spinbox.setValue(1000)
            count_layout.addWidget(count_spinbox)
            count_layout.addStretch(1)
            main_layout.addWidget(count_frame)

            # Delay between events
            delay_frame = QWidget()
            delay_layout = QHBoxLayout(delay_frame)
            delay_layout.addWidget(QLabel("Delay between events (ms):"))
            delay_spinbox = QSpinBox()
            delay_spinbox.setRange(0, 5000)
            delay_spinbox.setValue(500)
            delay_layout.addWidget(delay_spinbox)
            delay_layout.addStretch(1)
            main_layout.addWidget(delay_frame)

            # Seed
            seed_frame = QWidget()
            seed_layout = QHBoxLayout(seed_frame)
            seed_layout.addWidget(QLabel("Random seed (0 = random):"))
            seed_spinbox = QSpinBox()
            seed_spinbox.setRange(0, 999999)
            seed_spinbox.setValue(0)
            seed_layout.addWidget(seed_spinbox)
            seed_layout.addStretch(1)
            main_layout.addWidget(seed_frame)

            # Output
            output_text = QTextEdit()
            output_text.setReadOnly(True)
            main_layout.addWidget(output_text, 1)

            # Status
            status_label = QLabel("Ready")
            main_layout.addWidget(status_label)

            running = {'value': False}

            def run_test():
                if running['value']:
                    return

                package = pkg_combo.currentText()
                if not package:
                    QMessageBox.critical(dialog, "Error", "Please select a package")
                    return

                running['value'] = True
                status_label.setText("Running...")
                output_text.clear()

                def run_monkey():
                    try:
                        count = count_spinbox.value()
                        delay = delay_spinbox.value()
                        seed = seed_spinbox.value()

                        cmd = [adb_cmd, "-s", serial, "shell", "monkey",
                               "-p", package,
                               "-v",
                               "--throttle", str(delay),
                               str(count)]

                        if seed > 0:
                            cmd.insert(-1, "-s")
                            cmd.insert(-1, str(seed))

                        process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True
                        )

                        for line in iter(process.stdout.readline, ''):
                            if not running['value']:
                                process.terminate()
                                break
                            QTimer.singleShot(0, lambda l=line: output_text.append(l.rstrip("\n")))

                        process.wait()
                        QTimer.singleShot(0, lambda: status_label.setText("Completed"))

                    except Exception as e:
                        def report_error():
                            output_text.append(f"\nError: {str(e)}")
                            status_label.setText("Error")

                        QTimer.singleShot(0, report_error)
                    finally:
                        running['value'] = False

                threading.Thread(target=run_monkey, daemon=True).start()

            def stop_test():
                running['value'] = False
                status_label.setText("Stopped")

            buttons_frame = QWidget()
            buttons_layout = QHBoxLayout(buttons_frame)
            run_btn = QPushButton("Run Test")
            run_btn.clicked.connect(run_test)
            buttons_layout.addWidget(run_btn)
            stop_btn = QPushButton("Stop")
            stop_btn.clicked.connect(stop_test)
            buttons_layout.addWidget(stop_btn)
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            buttons_layout.addStretch(1)
            buttons_layout.addWidget(close_btn)
            main_layout.addWidget(buttons_frame)
            dialog.show()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open monkey testing dialog: {str(e)}")

    def run_io_spike_generator(self):
        """Run I/O spike generator test"""
        if not self.device_connected:
            QMessageBox.information(self, "Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = QDialog(self)
            dialog.setWindowTitle("I/O Spike Generator")
            dialog.resize(500, 400)
            dialog.setWindowModality(Qt.ApplicationModal)

            screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
            x_pos = screen_geometry.x() + (screen_geometry.width() - 500) // 2
            y_pos = screen_geometry.y() + (screen_geometry.height() - 400) // 2
            dialog.move(x_pos, y_pos)

            main_layout = QVBoxLayout(dialog)

            title_label = QLabel("I/O Spike Generator")
            title_label.setStyleSheet("font-size: 12px; font-weight: bold;")
            main_layout.addWidget(title_label)

            # File size
            size_frame = QWidget()
            size_layout = QHBoxLayout(size_frame)
            size_layout.addWidget(QLabel("File size (MB):"))
            size_spinbox = QSpinBox()
            size_spinbox.setRange(10, 1000)
            size_spinbox.setValue(100)
            size_layout.addWidget(size_spinbox)
            size_layout.addStretch(1)
            main_layout.addWidget(size_frame)

            # Block size
            block_frame = QWidget()
            block_layout = QHBoxLayout(block_frame)
            block_layout.addWidget(QLabel("Block size (KB):"))
            block_combo = QComboBox()
            block_combo.addItems(["1", "4", "16", "64", "256", "1024"])
            block_combo.setCurrentText("4")
            block_layout.addWidget(block_combo)
            block_layout.addStretch(1)
            main_layout.addWidget(block_frame)

            # Test type
            type_frame = QWidget()
            type_layout = QHBoxLayout(type_frame)
            type_layout.addWidget(QLabel("Test type:"))
            type_group = QButtonGroup(dialog)
            write_radio = QRadioButton("Write")
            write_radio.setProperty("value", "write")
            read_radio = QRadioButton("Read")
            read_radio.setProperty("value", "read")
            both_radio = QRadioButton("Both")
            both_radio.setProperty("value", "both")
            write_radio.setChecked(True)
            for btn in (write_radio, read_radio, both_radio):
                type_group.addButton(btn)
                type_layout.addWidget(btn)
            type_layout.addStretch(1)
            main_layout.addWidget(type_frame)

            # Output
            output_text = QTextEdit()
            output_text.setReadOnly(True)
            main_layout.addWidget(output_text, 1)

            # Progress
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(0)
            main_layout.addWidget(progress_bar)

            running = {'value': False}
            def append_output(message):
                QTimer.singleShot(0, lambda: output_text.append(message))

            def run_io_test():
                if running['value']:
                    return

                running['value'] = True
                output_text.clear()

                def io_thread():
                    try:
                        size_mb = size_spinbox.value()
                        block_kb = int(block_combo.currentText())
                        test_type = next(
                            (button.property("value") for button in type_group.buttons() if button.isChecked()),
                            "write"
                        )

                        block_count = (size_mb * 1024) // block_kb

                        append_output("Starting I/O test...")
                        append_output(f"File size: {size_mb} MB")
                        append_output(f"Block size: {block_kb} KB\n")

                        if test_type in ["write", "both"]:
                            append_output("Running write test...")

                            cmd = f"dd if=/dev/zero of=/data/local/tmp/iotest bs={block_kb}k count={block_count}"
                            result = subprocess.run(
                                [adb_cmd, "-s", serial, "shell", cmd],
                                capture_output=True, text=True, timeout=300
                            )

                            append_output(result.stderr)

                        if test_type in ["read", "both"]:
                            append_output("Running read test...")

                            cmd = f"dd if=/data/local/tmp/iotest of=/dev/null bs={block_kb}k"
                            result = subprocess.run(
                                [adb_cmd, "-s", serial, "shell", cmd],
                                capture_output=True, text=True, timeout=300
                            )

                            append_output(result.stderr)

                        # Cleanup
                        subprocess.run(
                            [adb_cmd, "-s", serial, "shell", "rm -f /data/local/tmp/iotest"],
                            capture_output=True, text=True, timeout=10
                        )

                        append_output("\nTest completed!")

                    except Exception as e:
                        append_output(f"\nError: {str(e)}")
                    finally:
                        running['value'] = False

                threading.Thread(target=io_thread, daemon=True).start()

            def cancel_test():
                running['value'] = False
                subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "rm -f /data/local/tmp/iotest"],
                    capture_output=True, text=True, timeout=10
                )

            buttons_frame = QWidget()
            buttons_layout = QHBoxLayout(buttons_frame)
            run_btn = QPushButton("Run Test")
            run_btn.clicked.connect(run_io_test)
            buttons_layout.addWidget(run_btn)
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(cancel_test)
            buttons_layout.addWidget(cancel_btn)
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            buttons_layout.addStretch(1)
            buttons_layout.addWidget(close_btn)
            main_layout.addWidget(buttons_frame)
            dialog.show()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open I/O spike generator: {str(e)}")

    def run_scrcpy_mirror(self):
        """Run scrcpy screen mirroring"""
        if not self.device_connected:
            QMessageBox.information(self, "Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial

            # Check if scrcpy is installed
            result = subprocess.run(
                ["which", "scrcpy"] if not IS_WINDOWS else ["where", "scrcpy"],
                capture_output=True, text=True
            )

            if result.returncode != 0:
                QMessageBox.information(
                    self,
                    "scrcpy Not Found",
                    "scrcpy is not installed on your system.\n\n"
                    "Please install scrcpy to use screen mirroring:\n"
                    "- Linux: sudo apt install scrcpy\n"
                    "- Mac: brew install scrcpy\n"
                    "- Windows: Download from GitHub"
                )
                return

            # Launch scrcpy
            self.log_message("Launching scrcpy for screen mirroring...")

            def launch_scrcpy():
                try:
                    subprocess.run(
                        ["scrcpy", "-s", serial],
                        capture_output=True, text=True
                    )
                except Exception as e:
                    QTimer.singleShot(0, lambda: self.log_message(f"scrcpy error: {str(e)}"))

            threading.Thread(target=launch_scrcpy, daemon=True).start()

            QMessageBox.information(self, "scrcpy Launched", "scrcpy screen mirroring has been launched.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch scrcpy: {str(e)}")

    def run_adb_command(self, command, device_serial=None, timeout=60):
        """Run an ADB command and return the result"""
        try:
            adb_cmd = self.adb_path if self.adb_path else 'adb'

            cmd = [adb_cmd]

            if device_serial:
                cmd.extend(['-s', device_serial])

            cmd.extend(command)

            self.log_message(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                self.log_message(f"Command failed: {result.stderr.strip()}")
                return False, result.stderr.strip()

        except subprocess.TimeoutExpired:
            self.log_message(f"Command timed out after {timeout} seconds")
            return False, f"Command timed out after {timeout} seconds"
        except Exception as e:
            self.log_message(f"Error running command: {str(e)}")
            return False, str(e)
