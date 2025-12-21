"""
DROIDCOM - Advanced Tests Feature Module
Handles advanced testing features like stress tests, benchmarks, etc.
"""

import re
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
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
        test_window = tk.Toplevel(self)
        test_window.title("Screen Lock Duplicator")

        # Get screen dimensions to set height to full screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Keep original width (700) but use full screen height
        window_width = 700
        window_height = screen_height - 50  # Subtract a small amount to account for taskbar/window decorations

        # Center the window horizontally
        x_position = (screen_width - window_width) // 2

        # Set the geometry
        test_window.geometry(f"{window_width}x{window_height}+{x_position}+0")
        test_window.transient(self)
        test_window.grab_set()

        # Configure window content
        frame = ttk.Frame(test_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Title and description
        ttk.Label(frame, text="Screen Lock Duplicator", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text="This tool records your lock screen pattern/PIN and can replay it to unlock your device").pack(pady=(0, 5))

        # Lock type selection frame
        type_frame = ttk.LabelFrame(frame, text="Lock Screen Type")
        type_frame.pack(fill=tk.X, expand=False, pady=5)

        # Lock type radio buttons
        lock_type = tk.StringVar(value="pin")
        ttk.Radiobutton(type_frame, text="PIN", variable=lock_type, value="pin").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Radiobutton(type_frame, text="Pattern", variable=lock_type, value="pattern").grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Radiobutton(type_frame, text="Password", variable=lock_type, value="password").grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Input configuration frame
        input_frame = ttk.LabelFrame(frame, text="Lock Sequence")
        input_frame.pack(fill=tk.X, expand=False, pady=5)

        # Create the input widgets based on lock type
        pin_frame = ttk.Frame(input_frame)
        pin_frame.pack(fill=tk.X, expand=True, pady=5)

        ttk.Label(pin_frame, text="PIN/Password:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        pin_entry = ttk.Entry(pin_frame, show="*")
        pin_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Toggle to show/hide PIN
        show_pin = tk.BooleanVar(value=False)
        show_check = ttk.Checkbutton(pin_frame, text="Show PIN/Password", variable=show_pin, command=lambda: pin_entry.config(show="" if show_pin.get() else "*"))
        show_check.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Pattern input (simplified for this implementation)
        pattern_frame = ttk.Frame(input_frame)
        pattern_frame.pack(fill=tk.X, expand=True, pady=5)

        ttk.Label(pattern_frame, text="Pattern Sequence (0-8):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        pattern_entry = ttk.Entry(pattern_frame)
        pattern_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(pattern_frame, text="Example: 0,1,4,7,8 for Z pattern").grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Diagram showing pattern grid numbering
        pattern_diagram = ttk.Frame(pattern_frame, relief="ridge", borderwidth=1)
        pattern_diagram.grid(row=1, column=0, columnspan=3, padx=5, pady=5)

        # Create a 3x3 grid showing pattern numbers
        for i in range(3):
            for j in range(3):
                num = i * 3 + j
                ttk.Label(pattern_diagram, text=str(num), width=3, anchor="center").grid(row=i, column=j, padx=10, pady=10)

        # Options frame
        options_frame = ttk.LabelFrame(frame, text="Options")
        options_frame.pack(fill=tk.X, expand=False, pady=5)

        # Delay between actions
        ttk.Label(options_frame, text="Delay (ms):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        delay_var = tk.StringVar(value="100")
        delay_entry = ttk.Spinbox(options_frame, from_=50, to=500, increment=50, textvariable=delay_var, width=5)
        delay_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Autorun checkbox
        autorun_var = tk.BooleanVar(value=True)
        autorun_check = ttk.Checkbutton(options_frame, text="Automatically unlock after locking", variable=autorun_var)
        autorun_check.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Progress display
        progress_frame = ttk.LabelFrame(frame, text="Progress")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Text widget for output
        output_text = tk.Text(progress_frame, height=10, width=80)
        output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(progress_frame, command=output_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        output_text.config(yscrollcommand=scrollbar.set)

        # Status label
        status_var = tk.StringVar(value="Ready to start...")
        status_label = ttk.Label(frame, textvariable=status_var)
        status_label.pack(pady=5)

        # Action buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)

        # Save sequence button
        save_btn = ttk.Button(
            button_frame,
            text="Save Current Sequence",
            command=lambda: save_sequence()
        )
        save_btn.pack(side=tk.LEFT, padx=5)

        # Start test button
        start_btn = ttk.Button(
            button_frame,
            text="Run Duplicator",
            command=lambda: start_duplicate_test()
        )
        start_btn.pack(side=tk.LEFT, padx=5)

        # Close button
        ttk.Button(button_frame, text="Close", command=test_window.destroy).pack(side=tk.LEFT, padx=5)

        # Initialize saved sequence storage
        self.saved_lock_sequence = None
        self.saved_lock_type = None

        # Function to update output in the text widget
        def update_output(text):
            output_text.insert(tk.END, text + "\n")
            output_text.see(tk.END)
            output_text.update_idletasks()

        # Update status in the window
        def update_status(text):
            status_var.set(text)

        # Function to save the current sequence
        def save_sequence():
            current_type = lock_type.get()

            if current_type == "pin" or current_type == "password":
                sequence = pin_entry.get()
                if not sequence:
                    update_output("Error: Please enter a PIN or password")
                    return
            elif current_type == "pattern":
                sequence = pattern_entry.get()
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
            start_btn.config(state="normal")

        # Function to start the duplicate test
        def start_duplicate_test():
            if not self.saved_lock_sequence:
                update_output("Error: Please save a lock sequence first")
                return

            # Get the delay value
            try:
                delay = int(delay_var.get())
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
                    autorun_var.get(),
                    update_output,
                    update_status
                ),
                daemon=True
            ).start()

        # Initially disable the test button until a sequence is saved
        start_btn.config(state="disabled")

        # Initial status message
        update_output("Enter your lock screen pattern or PIN and save it to continue")
        update_output("\nFor pattern locks, use numbers 0-8 with commas (see diagram above)")
        update_output("For PIN locks, enter the numeric sequence")
        update_output("For password locks, enter the alphanumeric password")

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
        test_window = tk.Toplevel(self)
        test_window.title("Battery Drain Test")
        test_window.geometry("700x500")
        test_window.transient(self)
        test_window.grab_set()

        # Configure window content
        frame = ttk.Frame(test_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Title and description
        ttk.Label(frame, text="Battery Drain Test", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text="This test will stress the device to measure battery drain rate").pack(pady=(0, 5))

        # Battery level display
        battery_frame = ttk.LabelFrame(frame, text="Battery Information")
        battery_frame.pack(fill=tk.X, expand=False, pady=5)

        # Battery level labels
        batt_info_var = tk.StringVar(value="Checking battery information...")
        batt_info_label = ttk.Label(battery_frame, textvariable=batt_info_var, justify=tk.LEFT)
        batt_info_label.pack(pady=5, padx=5, anchor=tk.W)

        # Progress display
        progress_frame = ttk.LabelFrame(frame, text="Test Progress")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Text widget for output
        output_text = tk.Text(progress_frame, height=15, width=80)
        output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(progress_frame, command=output_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        output_text.config(yscrollcommand=scrollbar.set)

        # Status label
        status_var = tk.StringVar(value="Initializing test...")
        status_label = ttk.Label(frame, textvariable=status_var)
        status_label.pack(pady=5)

        # Close button
        ttk.Button(frame, text="Close", command=test_window.destroy).pack(pady=10)

        # Function to update output in the text widget
        def update_output(text):
            output_text.insert(tk.END, text + "\n")
            output_text.see(tk.END)
            output_text.update_idletasks()

        # Update status in the window
        def update_status(text):
            status_var.set(text)

        # Update battery info display
        def update_battery_info(text):
            batt_info_var.set(text)

        # Start the test in a separate thread
        threading.Thread(
            target=self._battery_drain_test_task,
            args=(update_output, update_status, update_battery_info, test_window),
            daemon=True
        ).start()

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
        test_window = tk.Toplevel(self)
        test_window.title("App Crash Forcer")
        test_window.geometry("700x500")
        test_window.transient(self)
        test_window.grab_set()

        # Configure window content
        frame = ttk.Frame(test_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Title and description
        ttk.Label(frame, text="App Crash Forcer", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text="This tool attempts to force Android applications to crash for testing purposes").pack(pady=(0, 5))

        # App selection frame
        app_frame = ttk.LabelFrame(frame, text="Target Application")
        app_frame.pack(fill=tk.X, expand=False, pady=5)

        # App selection dropdown
        app_var = tk.StringVar()
        app_dropdown = ttk.Combobox(app_frame, textvariable=app_var, state="readonly")
        app_dropdown.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        # Refresh apps button
        refresh_btn = ttk.Button(app_frame, text="Refresh", command=lambda: refresh_apps())
        refresh_btn.pack(side=tk.RIGHT, padx=5, pady=5)

        # Crash method selection
        method_frame = ttk.LabelFrame(frame, text="Crash Methods")
        method_frame.pack(fill=tk.X, expand=False, pady=5)

        # Create crash method options with checkboxes
        method_vars = {
            "memory": tk.BooleanVar(value=True),
            "broadcast": tk.BooleanVar(value=True),
            "activity": tk.BooleanVar(value=True),
            "native": tk.BooleanVar(value=False)  # Default off as it's more aggressive
        }

        ttk.Checkbutton(method_frame, text="Memory Pressure", variable=method_vars["memory"]).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Checkbutton(method_frame, text="Broadcast Storm", variable=method_vars["broadcast"]).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Checkbutton(method_frame, text="Activity Stack Overflow", variable=method_vars["activity"]).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Checkbutton(method_frame, text="Native Signal Injection (Root)", variable=method_vars["native"]).pack(anchor=tk.W, padx=5, pady=2)

        # Progress display
        progress_frame = ttk.LabelFrame(frame, text="Test Progress")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Text widget for output
        output_text = tk.Text(progress_frame, height=15, width=80)
        output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(progress_frame, command=output_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        output_text.config(yscrollcommand=scrollbar.set)

        # Status label
        status_var = tk.StringVar(value="Ready to start...")
        status_label = ttk.Label(frame, textvariable=status_var)
        status_label.pack(pady=5)

        # Action buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)

        # Start button
        start_btn = ttk.Button(
            button_frame,
            text="Start Crash Test",
            command=lambda: start_crash_test()
        )
        start_btn.pack(side=tk.LEFT, padx=5)

        # Close button
        ttk.Button(button_frame, text="Close", command=test_window.destroy).pack(side=tk.LEFT, padx=5)

        # Function to update output in the text widget
        def update_output(text):
            output_text.insert(tk.END, text + "\n")
            output_text.see(tk.END)
            output_text.update_idletasks()

        # Update status in the window
        def update_status(text):
            status_var.set(text)

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
                    app_dropdown['values'] = apps
                    app_dropdown.current(0)  # Select first app by default
                    update_output(f"Found {len(apps)} applications")
                    update_status("Ready to start")
                    start_btn.config(state="normal")
                else:
                    update_output("No third-party applications found")
                    update_status("No applications found")
                    start_btn.config(state="disabled")
            else:
                update_output("Could not retrieve application list")
                update_status("Could not get app list")
                start_btn.config(state="disabled")

        # Function to start the crash test
        def start_crash_test():
            selected_app = app_var.get()
            if not selected_app:
                update_output("Please select a target application first")
                return

            # Get selected crash methods
            enabled_methods = [method for method, var in method_vars.items() if var.get()]
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
        refresh_apps()

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
        test_window = tk.Toplevel(self)
        test_window.title("CPU Max Load Test")
        test_window.geometry("600x400")
        test_window.transient(self)
        test_window.grab_set()

        # Configure window content
        frame = ttk.Frame(test_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Title and description
        ttk.Label(frame, text="CPU Max Load Test", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text="This test will stress all CPU cores to measure performance").pack(pady=(0, 10))

        # Progress display
        progress_frame = ttk.LabelFrame(frame, text="Test Progress")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Text widget for output
        output_text = tk.Text(progress_frame, height=15, width=70)
        output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(progress_frame, command=output_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        output_text.config(yscrollcommand=scrollbar.set)

        # Status label
        status_var = tk.StringVar(value="Initializing test...")
        status_label = ttk.Label(frame, textvariable=status_var)
        status_label.pack(pady=5)

        # Close button
        ttk.Button(frame, text="Close", command=test_window.destroy).pack(pady=10)

        # Function to update output in the text widget
        def update_output(text):
            output_text.insert(tk.END, text + "\n")
            output_text.see(tk.END)
            output_text.update_idletasks()

        # Update status in the window
        def update_status(text):
            status_var.set(text)

        # Start the test in a separate thread
        threading.Thread(
            target=self._cpu_max_load_test_task,
            args=(update_output, update_status, test_window),
            daemon=True
        ).start()

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
        test_window = tk.Toplevel(self)
        test_window.title("RAM Fill Test")
        test_window.geometry("700x500")
        test_window.transient(self)
        test_window.grab_set()

        # Configure window content
        frame = ttk.Frame(test_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Title and description
        ttk.Label(frame, text="RAM Fill Test", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text="This test will progressively allocate more memory to stress the device RAM").pack(pady=(0, 5))

        # Progress display
        progress_frame = ttk.LabelFrame(frame, text="Test Progress")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Text widget for output
        output_text = tk.Text(progress_frame, height=15, width=80)
        output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(progress_frame, command=output_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        output_text.config(yscrollcommand=scrollbar.set)

        # Memory usage display
        memory_frame = ttk.LabelFrame(frame, text="Memory Usage")
        memory_frame.pack(fill=tk.X, expand=False, pady=5)

        # Memory usage labels
        mem_info_var = tk.StringVar(value="Waiting for memory information...")
        mem_info_label = ttk.Label(memory_frame, textvariable=mem_info_var, justify=tk.LEFT)
        mem_info_label.pack(pady=5, padx=5, anchor=tk.W)

        # Status label
        status_var = tk.StringVar(value="Initializing test...")
        status_label = ttk.Label(frame, textvariable=status_var)
        status_label.pack(pady=5)

        # Close button
        ttk.Button(frame, text="Close", command=test_window.destroy).pack(pady=10)

        # Function to update output in the text widget
        def update_output(text):
            output_text.insert(tk.END, text + "\n")
            output_text.see(tk.END)
            output_text.update_idletasks()

        # Update status in the window
        def update_status(text):
            status_var.set(text)

        # Update memory info display
        def update_memory_info(text):
            mem_info_var.set(text)

        # Start the test in a separate thread
        threading.Thread(
            target=self._ram_fill_test_task,
            args=(update_output, update_status, update_memory_info, test_window),
            daemon=True
        ).start()

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
        test_window = tk.Toplevel(self)
        test_window.title("GPU Stress Test")
        test_window.geometry("600x400")
        test_window.transient(self)
        test_window.grab_set()

        # Configure window content
        frame = ttk.Frame(test_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Title and description
        ttk.Label(frame, text="GPU Stress Test", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text="This test will stress the GPU with various rendering operations").pack(pady=(0, 10))

        # Progress display
        progress_frame = ttk.LabelFrame(frame, text="Test Progress")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Text widget for output
        output_text = tk.Text(progress_frame, height=15, width=70)
        output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(progress_frame, command=output_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        output_text.config(yscrollcommand=scrollbar.set)

        # Status label
        status_var = tk.StringVar(value="Initializing test...")
        status_label = ttk.Label(frame, textvariable=status_var)
        status_label.pack(pady=5)

        # Close button
        ttk.Button(frame, text="Close", command=test_window.destroy).pack(pady=10)

        # Function to update output in the text widget
        def update_output(text):
            output_text.insert(tk.END, text + "\n")
            output_text.see(tk.END)
            output_text.update_idletasks()

        # Update status in the window
        def update_status(text):
            status_var.set(text)

        # Start the test in a separate thread
        threading.Thread(
            target=self._gpu_stress_test_task,
            args=(update_output, update_status, test_window),
            daemon=True
        ).start()

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
        test_window = tk.Toplevel(self)
        test_window.title("Dalvik Cache Stress Test")
        test_window.geometry("700x500")
        test_window.transient(self)
        test_window.grab_set()

        # Configure window content
        frame = ttk.Frame(test_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Title and description
        ttk.Label(frame, text="Dalvik Cache Stress Test", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text="This test will stress the Dalvik/ART runtime cache system").pack(pady=(0, 5))

        # Cache info display
        cache_frame = ttk.LabelFrame(frame, text="Cache Information")
        cache_frame.pack(fill=tk.X, expand=False, pady=5)

        # Cache info labels
        cache_info_var = tk.StringVar(value="Checking cache information...")
        cache_info_label = ttk.Label(cache_frame, textvariable=cache_info_var, justify=tk.LEFT)
        cache_info_label.pack(pady=5, padx=5, anchor=tk.W)

        # Progress display
        progress_frame = ttk.LabelFrame(frame, text="Test Progress")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Text widget for output
        output_text = tk.Text(progress_frame, height=15, width=80)
        output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(progress_frame, command=output_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        output_text.config(yscrollcommand=scrollbar.set)

        # Status label
        status_var = tk.StringVar(value="Initializing test...")
        status_label = ttk.Label(frame, textvariable=status_var)
        status_label.pack(pady=5)

        # Close button
        ttk.Button(frame, text="Close", command=test_window.destroy).pack(pady=10)

        # Function to update output in the text widget
        def update_output(text):
            output_text.insert(tk.END, text + "\n")
            output_text.see(tk.END)
            output_text.update_idletasks()

        # Update status in the window
        def update_status(text):
            status_var.set(text)

        # Update cache info display
        def update_cache_info(text):
            cache_info_var.set(text)

        # Start the test in a separate thread
        threading.Thread(
            target=self._dalvik_cache_stress_test_task,
            args=(update_output, update_status, update_cache_info, test_window),
            daemon=True
        ).start()

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
        config_dialog = tk.Toplevel(self)
        config_dialog.title("Looped Benchmarking")
        config_dialog.geometry("750x850")
        config_dialog.resizable(False, False)
        config_dialog.transient(self)  # Set to be on top of the main window
        config_dialog.grab_set()  # Make the dialog modal

        # Add some padding
        padframe = ttk.Frame(config_dialog, padding="10 10 10 10")
        padframe.pack(fill=tk.BOTH, expand=True)

        # Create form elements
        ttk.Label(padframe, text="Benchmark Type:").grid(row=0, column=0, sticky="w", pady=5)
        benchmark_types = [
            "CPU Performance",
            "Storage I/O",
            "Memory Access",
            "UI Responsiveness",
            "All Benchmarks"
        ]
        benchmark_type = tk.StringVar(value=benchmark_types[0])
        benchmark_combo = ttk.Combobox(padframe, textvariable=benchmark_type, values=benchmark_types, width=20)
        benchmark_combo.grid(row=0, column=1, sticky="w", columnspan=2)

        ttk.Label(padframe, text="Number of Iterations:").grid(row=1, column=0, sticky="w", pady=5)
        iterations = tk.StringVar(value="5")
        ttk.Entry(padframe, textvariable=iterations, width=10).grid(row=1, column=1, sticky="w")

        ttk.Label(padframe, text="Time Between Iterations (s):").grid(row=2, column=0, sticky="w", pady=5)
        delay_sec = tk.StringVar(value="30")
        ttk.Entry(padframe, textvariable=delay_sec, width=10).grid(row=2, column=1, sticky="w")

        # Add a separator
        ttk.Separator(padframe, orient="horizontal").grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)

        # Create result frame
        result_frame = ttk.LabelFrame(padframe, text="Benchmark Results")
        result_frame.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=5)
        padframe.grid_rowconfigure(4, weight=1)

        # Add results text widget
        result_text = scrolledtext.ScrolledText(result_frame, height=10, width=45)
        result_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Add progress bar
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(padframe, variable=progress_var, maximum=100)
        progress_bar.grid(row=5, column=0, columnspan=3, sticky="ew", pady=5)

        # Status label
        status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(padframe, textvariable=status_var)
        status_label.grid(row=6, column=0, columnspan=3, sticky="w", pady=5)

        # Button frame
        btn_frame = ttk.Frame(padframe)
        btn_frame.grid(row=7, column=0, columnspan=3, pady=10)

        # Variable to control the benchmark process
        running = [False]  # Use a list to allow modification from nested functions

        # Start button function
        def start_benchmark():
            if running[0]:
                return  # Already running

            try:
                # Validate inputs
                try:
                    num_iterations = int(iterations.get())
                    if num_iterations < 1 or num_iterations > 100:
                        update_result("Number of iterations must be between 1 and 100.")
                        return
                except ValueError:
                    update_result("Number of iterations must be a number.")
                    return

                try:
                    between_delay = int(delay_sec.get())
                    if between_delay < 0:
                        update_result("Delay must be a positive number.")
                        return
                except ValueError:
                    update_result("Delay must be a number.")
                    return

                # Clear results
                result_text.delete(1.0, tk.END)
                update_result(f"Starting {benchmark_type.get()} benchmark with {num_iterations} iterations...")

                # Start the benchmark in a separate thread
                running[0] = True
                start_btn.config(state="disabled")
                stop_btn.config(state="normal")

                # Reset progress bar
                progress_var.set(0)
                status_var.set("Running...")

                benchmark_thread = threading.Thread(
                    target=lambda: self._run_looped_benchmark(
                        benchmark_type.get(), num_iterations, between_delay,
                        update_result, update_progress, lambda: running[0],
                        on_benchmark_complete),
                    daemon=True
                )
                benchmark_thread.start()

            except Exception as e:
                update_result(f"Error: {str(e)}")
                running[0] = False
                start_btn.config(state="normal")
                stop_btn.config(state="disabled")

        # Stop button function
        def stop_benchmark():
            running[0] = False
            update_result("Stopping benchmark...")
            update_progress(100, "Stopped")

        # Function to update results
        def update_result(message):
            result_text.insert(tk.END, f"{message}\n")
            result_text.see(tk.END)

        # Function to update progress
        def update_progress(percent, message=None):
            progress_var.set(percent)
            if message:
                status_var.set(message)

        # Function called when benchmark is complete
        def on_benchmark_complete():
            start_btn.config(state="normal")
            stop_btn.config(state="disabled")
            running[0] = False
            status_var.set("Completed")

        # Add buttons
        start_btn = ttk.Button(btn_frame, text="Start", command=start_benchmark)
        start_btn.pack(side="left", padx=5)

        stop_btn = ttk.Button(btn_frame, text="Stop", command=stop_benchmark, state="disabled")
        stop_btn.pack(side="left", padx=5)

        # Initial update
        update_result("Configure the benchmark parameters and click Start to begin.")

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
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
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
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("Monkey Testing")
            dialog.geometry("600x500")
            dialog.transient(self)
            dialog.grab_set()

            x_pos = (self.winfo_screenwidth() - 600) // 2
            y_pos = (self.winfo_screenheight() - 500) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            main_frame = ttk.Frame(dialog, padding=20)
            main_frame.pack(fill="both", expand=True)

            ttk.Label(main_frame, text="Monkey Testing", font=("Arial", 12, "bold")).pack(pady=(0, 10))

            ttk.Label(main_frame, text="Monkey is a program that generates random events on your device.").pack(pady=5)

            # Package selection
            pkg_frame = ttk.LabelFrame(main_frame, text="Target Package", padding=10)
            pkg_frame.pack(fill="x", pady=10)

            pkg_var = tk.StringVar()
            pkg_combo = ttk.Combobox(pkg_frame, textvariable=pkg_var, width=50)
            pkg_combo.pack(fill="x")

            # Load packages
            def load_packages():
                result = subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "pm", "list", "packages", "-3"],
                    capture_output=True, text=True, timeout=20
                )
                if result.returncode == 0:
                    packages = [line[8:] for line in result.stdout.strip().split('\n') if line.startswith('package:')]
                    emit_ui(self, lambda: pkg_combo.configure(values=packages))

            threading.Thread(target=load_packages, daemon=True).start()

            # Event count
            count_frame = ttk.Frame(main_frame)
            count_frame.pack(fill="x", pady=5)

            ttk.Label(count_frame, text="Number of events:").pack(side="left")
            count_var = tk.IntVar(value=1000)
            count_spinbox = ttk.Spinbox(count_frame, from_=100, to=100000, textvariable=count_var, width=15)
            count_spinbox.pack(side="left", padx=10)

            # Delay between events
            delay_frame = ttk.Frame(main_frame)
            delay_frame.pack(fill="x", pady=5)

            ttk.Label(delay_frame, text="Delay between events (ms):").pack(side="left")
            delay_var = tk.IntVar(value=500)
            delay_spinbox = ttk.Spinbox(delay_frame, from_=0, to=5000, textvariable=delay_var, width=15)
            delay_spinbox.pack(side="left", padx=10)

            # Seed
            seed_frame = ttk.Frame(main_frame)
            seed_frame.pack(fill="x", pady=5)

            ttk.Label(seed_frame, text="Random seed (0 = random):").pack(side="left")
            seed_var = tk.IntVar(value=0)
            seed_spinbox = ttk.Spinbox(seed_frame, from_=0, to=999999, textvariable=seed_var, width=15)
            seed_spinbox.pack(side="left", padx=10)

            # Output
            output_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=10, width=60)
            output_text.pack(fill="both", expand=True, pady=10)

            # Status
            status_label = ttk.Label(main_frame, text="Ready")
            status_label.pack(pady=5)

            running = {'value': False}

            def run_test():
                if running['value']:
                    return

                package = pkg_var.get()
                if not package:
                    messagebox.showerror("Error", "Please select a package")
                    return

                running['value'] = True
                set_text(status_label, "Running...")
                output_text.delete(1.0, tk.END)

                def run_monkey():
                    try:
                        count = count_var.get()
                        delay = delay_var.get()
                        seed = seed_var.get()

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
                            emit_ui(self, lambda l=line: [
                                append_text(output_text, l),
                                output_text.see(tk.END)
                            ])

                        process.wait()
                        emit_ui(self, lambda: set_text(status_label, "Completed"))

                    except Exception as e:
                        emit_ui(self, lambda: [
                            append_text(output_text, f"\nError: {str(e)}"),
                            set_text(status_label, "Error")
                        ])
                    finally:
                        running['value'] = False

                threading.Thread(target=run_monkey, daemon=True).start()

            def stop_test():
                running['value'] = False
                set_text(status_label, "Stopped")

            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill="x", pady=10)

            ttk.Button(buttons_frame, text="Run Test", command=run_test).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Stop", command=stop_test).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open monkey testing dialog: {str(e)}")

    def run_io_spike_generator(self):
        """Run I/O spike generator test"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial
            adb_cmd = self.adb_path if IS_WINDOWS else "adb"

            dialog = tk.Toplevel(self)
            dialog.title("I/O Spike Generator")
            dialog.geometry("500x400")
            dialog.transient(self)
            dialog.grab_set()

            x_pos = (self.winfo_screenwidth() - 500) // 2
            y_pos = (self.winfo_screenheight() - 400) // 2
            dialog.geometry(f"+{x_pos}+{y_pos}")

            main_frame = ttk.Frame(dialog, padding=20)
            main_frame.pack(fill="both", expand=True)

            ttk.Label(main_frame, text="I/O Spike Generator", font=("Arial", 12, "bold")).pack(pady=(0, 10))

            # File size
            size_frame = ttk.Frame(main_frame)
            size_frame.pack(fill="x", pady=5)

            ttk.Label(size_frame, text="File size (MB):").pack(side="left")
            size_var = tk.IntVar(value=100)
            size_spinbox = ttk.Spinbox(size_frame, from_=10, to=1000, textvariable=size_var, width=10)
            size_spinbox.pack(side="left", padx=10)

            # Block size
            block_frame = ttk.Frame(main_frame)
            block_frame.pack(fill="x", pady=5)

            ttk.Label(block_frame, text="Block size (KB):").pack(side="left")
            block_var = tk.IntVar(value=4)
            block_combo = ttk.Combobox(block_frame, textvariable=block_var, values=[1, 4, 16, 64, 256, 1024], width=10)
            block_combo.pack(side="left", padx=10)

            # Test type
            type_frame = ttk.Frame(main_frame)
            type_frame.pack(fill="x", pady=5)

            ttk.Label(type_frame, text="Test type:").pack(side="left")
            type_var = tk.StringVar(value="write")
            ttk.Radiobutton(type_frame, text="Write", variable=type_var, value="write").pack(side="left", padx=5)
            ttk.Radiobutton(type_frame, text="Read", variable=type_var, value="read").pack(side="left", padx=5)
            ttk.Radiobutton(type_frame, text="Both", variable=type_var, value="both").pack(side="left", padx=5)

            # Output
            output_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=10, width=50)
            output_text.pack(fill="both", expand=True, pady=10)

            # Progress
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(main_frame, variable=progress_var, maximum=100)
            progress_bar.pack(fill="x", pady=5)

            running = {'value': False}

            def run_io_test():
                if running['value']:
                    return

                running['value'] = True
                output_text.delete(1.0, tk.END)

                def io_thread():
                    try:
                        size_mb = size_var.get()
                        block_kb = block_var.get()
                        test_type = type_var.get()

                        block_count = (size_mb * 1024) // block_kb

                        emit_ui(self, lambda: [
                            append_text(output_text, "Starting I/O test...\n"),
                            append_text(output_text, f"File size: {size_mb} MB\n"),
                            append_text(output_text, f"Block size: {block_kb} KB\n\n")
                        ])

                        if test_type in ["write", "both"]:
                            emit_ui(self, lambda: append_text(output_text, "Running write test...\n"))

                            cmd = f"dd if=/dev/zero of=/data/local/tmp/iotest bs={block_kb}k count={block_count}"
                            result = subprocess.run(
                                [adb_cmd, "-s", serial, "shell", cmd],
                                capture_output=True, text=True, timeout=300
                            )

                            emit_ui(self, lambda: [
                                append_text(output_text, result.stderr),
                                append_text(output_text, "\n")
                            ])

                        if test_type in ["read", "both"]:
                            emit_ui(self, lambda: append_text(output_text, "Running read test...\n"))

                            cmd = f"dd if=/data/local/tmp/iotest of=/dev/null bs={block_kb}k"
                            result = subprocess.run(
                                [adb_cmd, "-s", serial, "shell", cmd],
                                capture_output=True, text=True, timeout=300
                            )

                            emit_ui(self, lambda: [
                                append_text(output_text, result.stderr),
                                append_text(output_text, "\n")
                            ])

                        # Cleanup
                        subprocess.run(
                            [adb_cmd, "-s", serial, "shell", "rm -f /data/local/tmp/iotest"],
                            capture_output=True, text=True, timeout=10
                        )

                        emit_ui(self, lambda: append_text(output_text, "\nTest completed!\n"))

                    except Exception as e:
                        emit_ui(self, lambda: append_text(output_text, f"\nError: {str(e)}\n"))
                    finally:
                        running['value'] = False

                threading.Thread(target=io_thread, daemon=True).start()

            def cancel_test():
                running['value'] = False
                subprocess.run(
                    [adb_cmd, "-s", serial, "shell", "rm -f /data/local/tmp/iotest"],
                    capture_output=True, text=True, timeout=10
                )

            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill="x", pady=10)

            ttk.Button(buttons_frame, text="Run Test", command=run_io_test).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Cancel", command=cancel_test).pack(side="left", padx=5)
            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open I/O spike generator: {str(e)}")

    def run_scrcpy_mirror(self):
        """Run scrcpy screen mirroring"""
        if not self.device_connected:
            messagebox.showinfo("Not Connected", "Please connect to a device first.")
            return

        try:
            serial = self.device_serial

            # Check if scrcpy is installed
            result = subprocess.run(
                ["which", "scrcpy"] if not IS_WINDOWS else ["where", "scrcpy"],
                capture_output=True, text=True
            )

            if result.returncode != 0:
                messagebox.showinfo(
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
                    emit_ui(self, lambda: self.log_message(f"scrcpy error: {str(e)}"))

            threading.Thread(target=launch_scrcpy, daemon=True).start()

            messagebox.showinfo("scrcpy Launched", "scrcpy screen mirroring has been launched.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch scrcpy: {str(e)}")

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
