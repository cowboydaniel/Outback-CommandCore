"""
DROIDCOM - Device Info Feature Module
Handles device information retrieval and display.
"""

import subprocess
import tempfile
import time
import os
import re
import logging

from ..constants import IS_WINDOWS


class DeviceInfoMixin:
    """Mixin class providing device information functionality."""

    def _get_device_info(self, serial, adb_cmd):
        """Get device information using ADB"""
        try:
            device_info = {
                'serial': serial
            }

            # Get model
            model_cmd = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'getprop', 'ro.product.model'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            if model_cmd.returncode == 0:
                device_info['model'] = model_cmd.stdout.strip()

            # Get manufacturer
            manufacturer_cmd = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'getprop', 'ro.product.manufacturer'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            if manufacturer_cmd.returncode == 0:
                device_info['manufacturer'] = manufacturer_cmd.stdout.strip()

            # Get Android version
            version_cmd = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'getprop', 'ro.build.version.release'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            if version_cmd.returncode == 0:
                device_info['android_version'] = version_cmd.stdout.strip()

            # Get battery level
            battery_cmd = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'dumpsys', 'battery'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            if battery_cmd.returncode == 0 and battery_cmd.stdout.strip():
                try:
                    battery_output = battery_cmd.stdout.strip()
                    level = 'Unknown'
                    for line in battery_output.split('\n'):
                        if 'level:' in line or 'level =' in line:
                            parts = line.split(':' if ':' in line else '=')
                            if len(parts) > 1:
                                level_str = parts[1].strip()
                                if level_str.isdigit():
                                    level = level_str
                                    break

                    if level != 'Unknown':
                        device_info['battery'] = f"{level}%"
                    else:
                        # Fallback method
                        battery_cmd2 = subprocess.run(
                            [adb_cmd, '-s', serial, 'shell', 'cat', '/sys/class/power_supply/battery/capacity'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            timeout=5
                        )
                        if battery_cmd2.returncode == 0:
                            level = battery_cmd2.stdout.strip()
                            if level.isdigit():
                                device_info['battery'] = f"{level}%"
                except Exception:
                    device_info['battery'] = 'Unknown'

            # Get storage info
            storage_cmd = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'df', '/storage/emulated/0'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            if storage_cmd.returncode == 0:
                try:
                    lines = storage_cmd.stdout.strip().split('\n')
                    if len(lines) >= 2:
                        parts = lines[1].split()
                        if len(parts) >= 4:
                            total = int(parts[1]) / (1024 * 1024)
                            used = int(parts[2]) / (1024 * 1024)
                            device_info['storage'] = f"{used:.1f} GB used / {total:.1f} GB total"
                except Exception:
                    device_info['storage'] = 'Unknown'

            # Get RAM info
            ram_cmd = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'cat', '/proc/meminfo'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            if ram_cmd.returncode == 0:
                try:
                    ram_output = ram_cmd.stdout.strip()
                    for line in ram_output.split('\n'):
                        if 'MemTotal' in line:
                            mem_kb = int(line.split(':')[1].strip().split()[0])
                            total_ram_gb = mem_kb / (1024 * 1024)
                            device_info['ram'] = f"{total_ram_gb:.1f} GB"
                            break
                except Exception:
                    device_info['ram'] = 'Unknown'

            # Get CPU info
            cpu_cmd = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'getprop', 'ro.product.cpu.abi'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            if cpu_cmd.returncode == 0:
                device_info['cpu'] = cpu_cmd.stdout.strip()

            # Get screen resolution
            screen_cmd = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'wm', 'size'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            if screen_cmd.returncode == 0:
                try:
                    screen_output = screen_cmd.stdout.strip()
                    if 'size:' in screen_output:
                        resolution = screen_output.split('size:')[1].strip()
                        device_info['resolution'] = resolution
                except Exception:
                    device_info['resolution'] = 'Unknown'

            # Get kernel version
            kernel_cmd = subprocess.run(
                [adb_cmd, '-s', serial, 'shell', 'uname', '-r'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            if kernel_cmd.returncode == 0:
                device_info['kernel'] = kernel_cmd.stdout.strip()

            # Try to get IMEI
            self._get_device_imei(device_info, serial, adb_cmd)

            return device_info

        except Exception as e:
            self.log_message(f"Error getting device info: {str(e)}")
            return None

    def _get_device_imei(self, device_info, serial, adb_cmd):
        """Try to get device IMEI using multiple methods"""
        try:
            # Method 1: Using dialer method with OCR
            self.log_message("Trying dialer code method to get IMEI...")

            temp_dir = tempfile.mkdtemp()
            screenshot_path = os.path.join(temp_dir, "imei_screen.png")

            try:
                # Launch the dialer with *#06# code
                try:
                    subprocess.run(
                        [adb_cmd, '-s', serial, 'shell', 'am', 'start', '-a', 'android.intent.action.DIAL'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=10
                    )
                except Exception:
                    pass

                time.sleep(2)

                # Use Popen with communicate for better subprocess handling
                try:
                    dial_proc = subprocess.Popen(
                        [adb_cmd, '-s', serial, 'shell', 'am', 'start', '-a', 'android.intent.action.DIAL', '-d', 'tel:*#06#'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    try:
                        dial_proc.communicate(timeout=10)
                    except subprocess.TimeoutExpired:
                        dial_proc.kill()
                        dial_proc.wait()
                except Exception:
                    pass

                time.sleep(2)

                # Capture screenshot using Popen with communicate for binary data handling
                try:
                    screencap_proc = subprocess.Popen(
                        [adb_cmd, '-s', serial, 'exec-out', 'screencap', '-p'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    try:
                        stdout_data, _ = screencap_proc.communicate(timeout=10)
                        if screencap_proc.returncode == 0 and stdout_data:
                            with open(screenshot_path, 'wb') as f:
                                f.write(stdout_data)

                            try:
                                # OCR with Popen
                                ocr_proc = subprocess.Popen(
                                    ['tesseract', screenshot_path, 'stdout'],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True
                                )
                                try:
                                    ocr_stdout, _ = ocr_proc.communicate(timeout=15)
                                    if ocr_proc.returncode == 0:
                                        ocr_text = ocr_stdout.strip()
                                        self.log_message("OCR text extracted from dialer screen.")

                                        imei = None

                                        for line in ocr_text.split('\n'):
                                            if 'IMEI' in line.upper() or 'Device ID' in line:
                                                digits = ''.join(c for c in line if c.isdigit())
                                                if len(digits) >= 14:
                                                    imei = digits
                                                    break

                                        if not imei:
                                            imei_matches = re.findall(r'\b\d{14,16}\b', ocr_text)
                                            if imei_matches:
                                                for match in imei_matches:
                                                    if 14 <= len(match) <= 16:
                                                        imei = match
                                                        break

                                        if imei:
                                            self.log_message("IMEI found in OCR text!")
                                            device_info['imei'] = imei
                                except subprocess.TimeoutExpired:
                                    ocr_proc.kill()
                                    ocr_proc.wait()
                                    self.log_message("OCR processing timed out")
                            except Exception as e:
                                self.log_message(f"OCR processing error: {str(e)}")
                    except subprocess.TimeoutExpired:
                        screencap_proc.kill()
                        screencap_proc.wait()
                        self.log_message("Screenshot capture timed out")
                except Exception:
                    pass

            finally:
                # Clean up temp files properly
                try:
                    if os.path.exists(screenshot_path):
                        os.remove(screenshot_path)
                except Exception:
                    pass
                try:
                    if os.path.exists(temp_dir):
                        os.rmdir(temp_dir)
                except Exception:
                    pass

            # Method 2: service call iphonesubinfo
            if 'imei' not in device_info:
                self.log_message("Trying service call method for IMEI...")
                try:
                    imei_proc = subprocess.Popen(
                        [adb_cmd, '-s', serial, 'shell', 'service', 'call', 'iphonesubinfo', '1'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    try:
                        stdout_data, _ = imei_proc.communicate(timeout=5)
                        if imei_proc.returncode == 0:
                            imei_output = stdout_data.strip()
                            imei = ''
                            parcel_found = False
                            for line in imei_output.split('\n'):
                                if not parcel_found and 'Parcel' in line:
                                    parcel_found = True
                                elif parcel_found:
                                    hex_values = line.strip().split()
                                    for hex_val in hex_values:
                                        if hex_val.startswith("'") and hex_val.endswith("'"):
                                            char = hex_val.strip("'")
                                            if char.isdigit():
                                                imei += char
                                        elif len(hex_val) == 2 and hex_val != '00':
                                            try:
                                                char = chr(int(hex_val, 16))
                                                if char.isdigit():
                                                    imei += char
                                            except:
                                                pass

                            if imei and len(imei) >= 14:
                                imei = ''.join(c for c in imei if c.isdigit())
                                if len(imei) >= 14:
                                    device_info['imei'] = imei
                    except subprocess.TimeoutExpired:
                        imei_proc.kill()
                        imei_proc.wait()
                        self.log_message("Service call IMEI query timed out")
                except Exception as e:
                    self.log_message(f"Service call method error: {str(e)}")

            # Method 3: dumpsys iphonesubinfo
            if 'imei' not in device_info:
                self.log_message("Trying dumpsys method for IMEI...")
                try:
                    dumpsys_proc = subprocess.Popen(
                        [adb_cmd, '-s', serial, 'shell', 'dumpsys', 'iphonesubinfo'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    try:
                        stdout_data, _ = dumpsys_proc.communicate(timeout=5)
                        if dumpsys_proc.returncode == 0:
                            imei_output = stdout_data.strip()
                            for line in imei_output.split('\n'):
                                if 'Device ID' in line or 'IMEI' in line:
                                    parts = line.split('=' if '=' in line else ':')
                                    if len(parts) > 1:
                                        imei = parts[1].strip()
                                        if imei and len(imei) >= 14 and imei.isdigit():
                                            device_info['imei'] = imei
                                            break
                    except subprocess.TimeoutExpired:
                        dumpsys_proc.kill()
                        dumpsys_proc.wait()
                        self.log_message("Dumpsys IMEI query timed out")
                except Exception as e:
                    self.log_message(f"Dumpsys method error: {str(e)}")

        except Exception as e:
            self.log_message(f"Error getting IMEI: {str(e)}")

        # Fallback to Android ID
        if 'imei' not in device_info:
            try:
                android_id_cmd = subprocess.run(
                    [adb_cmd, '-s', serial, 'shell', 'settings', 'get', 'secure', 'android_id'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=5
                )
                if android_id_cmd.returncode == 0:
                    android_id = android_id_cmd.stdout.strip()
                    if android_id and len(android_id) > 8:
                        device_info['device_id'] = android_id
            except Exception:
                pass

    def update_device_info(self):
        """Update the device info display with the connected device information"""
        if not self.device_info:
            return

        # Update basic info fields
        if 'model' in self.device_info:
            self.info_fields['Model'].set(self.device_info['model'])

        if 'manufacturer' in self.device_info:
            self.info_fields['Manufacturer'].set(self.device_info['manufacturer'])

        if 'android_version' in self.device_info:
            self.info_fields['Android Version'].set(self.device_info['android_version'])

        if 'serial' in self.device_info:
            serial = str(self.device_info['serial']).strip()
            if '\n' in serial:
                serial = serial.split('\n')[0].strip()
            self.info_fields['Serial Number'].set(serial)

        if 'battery' in self.device_info:
            self.info_fields['Battery Level'].set(self.device_info['battery'])

        if 'imei' in self.device_info:
            self.info_fields['IMEI'].set(self.device_info['imei'])
        elif 'device_id' in self.device_info:
            self.info_fields['IMEI'].set(f"{self.device_info['device_id']} (Android ID)")

        # Update advanced info fields
        if 'storage' in self.device_info:
            self.adv_info_fields['Storage'].set(self.device_info['storage'])

        if 'ram' in self.device_info:
            self.adv_info_fields['RAM'].set(self.device_info['ram'])

        if 'resolution' in self.device_info:
            self.adv_info_fields['Screen Resolution'].set(self.device_info['resolution'])

        if 'cpu' in self.device_info:
            self.adv_info_fields['CPU'].set(self.device_info['cpu'])

        if 'kernel' in self.device_info:
            self.adv_info_fields['Kernel'].set(self.device_info['kernel'])
