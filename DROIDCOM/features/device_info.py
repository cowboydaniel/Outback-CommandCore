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
import threading

from ..constants import IS_WINDOWS
from ..utils.qt_dispatcher import emit_ui


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
            emit_ui(self, lambda e=e: self.log_message(f"Error getting device info: {str(e)}"))
            return None

    def _check_tesseract_installed(self):
        """Check if tesseract is installed"""
        try:
            result = subprocess.run(
                ['tesseract', '--version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=2
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
        except Exception:
            return False

    def _dialer_method_worker(self, device_info, serial, adb_cmd, result_list, dialer_status):
        """Worker function for dialer IMEI method - runs in thread with timeout"""
        try:
            # Skip dialer method if tesseract is not available
            if not self._check_tesseract_installed():
                return

            temp_dir = tempfile.mkdtemp()
            screenshot_path = os.path.join(temp_dir, "imei_screen.png")

            try:
                # Launch the dialer with *#06# code
                try:
                    dialer_launch_cmd = [
                        adb_cmd,
                        '-s',
                        serial,
                        'shell',
                        'am',
                        'start',
                        '-a',
                        'android.intent.action.DIAL'
                    ]
                    dialer_launch = subprocess.run(
                        dialer_launch_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=10
                    )
                    if dialer_launch.returncode != 0:
                        stderr_msg = dialer_launch.stderr.strip()
                        emit_ui(
                            self,
                            lambda cmd=dialer_launch_cmd, stderr_msg=stderr_msg: self.log_message(
                                f"Dialer launch failed for command {cmd}: {stderr_msg or 'no stderr output'}"
                            )
                        )
                        dialer_status['failed'] = True
                        dialer_status['reason'] = stderr_msg or 'Dialer launch command failed'
                except Exception as e:
                    emit_ui(
                        self,
                        lambda cmd=[adb_cmd, '-s', serial, 'shell', 'am', 'start', '-a', 'android.intent.action.DIAL'], e=e: self.log_message(
                            f"Dialer launch exception for command {cmd}: {str(e)}"
                        )
                    )
                    dialer_status['failed'] = True
                    dialer_status['reason'] = str(e)

                time.sleep(2)

                # Use Popen with communicate for better subprocess handling
                try:
                    dial_cmd = [
                        adb_cmd,
                        '-s',
                        serial,
                        'shell',
                        'am',
                        'start',
                        '-a',
                        'android.intent.action.DIAL',
                        '-d',
                        'tel:*#06#'
                    ]
                    dial_proc = subprocess.Popen(
                        dial_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    try:
                        _, dial_stderr = dial_proc.communicate(timeout=10)
                        if dial_proc.returncode != 0:
                            stderr_msg = (dial_stderr or '').strip()
                            emit_ui(
                                self,
                                lambda cmd=dial_cmd, stderr_msg=stderr_msg: self.log_message(
                                    f"Dialer code launch failed for command {cmd}: {stderr_msg or 'no stderr output'}"
                                )
                            )
                            dialer_status['failed'] = True
                            dialer_status['reason'] = stderr_msg or 'Dialer code launch failed'
                    except subprocess.TimeoutExpired:
                        dial_proc.kill()
                        dial_proc.wait()
                        emit_ui(
                            self,
                            lambda cmd=dial_cmd: self.log_message(
                                f"Dialer code launch timed out for command {cmd}"
                            )
                        )
                        dialer_status['failed'] = True
                        dialer_status['reason'] = 'Dialer code launch timed out'
                except Exception as e:
                    emit_ui(
                        self,
                        lambda cmd=[adb_cmd, '-s', serial, 'shell', 'am', 'start', '-a', 'android.intent.action.DIAL', '-d', 'tel:*#06#'], e=e: self.log_message(
                            f"Dialer code launch exception for command {cmd}: {str(e)}"
                        )
                    )
                    dialer_status['failed'] = True
                    dialer_status['reason'] = str(e)

                time.sleep(2)

                # Capture screenshot using Popen with communicate for binary data handling
                try:
                    screencap_cmd = [adb_cmd, '-s', serial, 'exec-out', 'screencap', '-p']
                    screencap_proc = subprocess.Popen(
                        screencap_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    try:
                        stdout_data, screencap_stderr = screencap_proc.communicate(timeout=10)
                        if screencap_proc.returncode == 0 and stdout_data:
                            with open(screenshot_path, 'wb') as f:
                                f.write(stdout_data)

                            try:
                                # OCR with Popen
                                ocr_cmd = ['tesseract', screenshot_path, '-']
                                ocr_proc = subprocess.Popen(
                                    ocr_cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True
                                )
                                try:
                                    ocr_stdout, ocr_stderr = ocr_proc.communicate(timeout=15)
                                    if ocr_proc.returncode == 0:
                                        ocr_text = ocr_stdout.strip()

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
                                            result_list.append(imei)
                                    else:
                                        stderr_msg = (ocr_stderr or '').strip()
                                        emit_ui(
                                            self,
                                            lambda cmd=ocr_cmd, stderr_msg=stderr_msg: self.log_message(
                                                f"OCR failed for command {cmd}: {stderr_msg or 'no stderr output'}"
                                            )
                                        )
                                        dialer_status['failed'] = True
                                        dialer_status['reason'] = stderr_msg or 'OCR failed'
                                except subprocess.TimeoutExpired:
                                    ocr_proc.kill()
                                    ocr_proc.wait()
                                    emit_ui(
                                        self,
                                        lambda cmd=ocr_cmd: self.log_message(
                                            f"OCR timed out for command {cmd}"
                                        )
                                    )
                                    dialer_status['failed'] = True
                                    dialer_status['reason'] = 'OCR timed out'
                            except Exception as e:
                                emit_ui(
                                    self,
                                    lambda cmd=ocr_cmd, e=e: self.log_message(
                                        f"OCR exception for command {cmd}: {str(e)}"
                                    )
                                )
                                dialer_status['failed'] = True
                                dialer_status['reason'] = str(e)
                        elif screencap_proc.returncode != 0:
                            stderr_msg = (screencap_stderr or '').strip()
                            emit_ui(
                                self,
                                lambda cmd=screencap_cmd, stderr_msg=stderr_msg: self.log_message(
                                    f"Screencap failed for command {cmd}: {stderr_msg or 'no stderr output'}"
                                )
                            )
                            dialer_status['failed'] = True
                            dialer_status['reason'] = stderr_msg or 'Screencap failed'
                    except subprocess.TimeoutExpired:
                        screencap_proc.kill()
                        screencap_proc.wait()
                        emit_ui(
                            self,
                            lambda cmd=screencap_cmd: self.log_message(
                                f"Screencap timed out for command {cmd}"
                            )
                        )
                        dialer_status['failed'] = True
                        dialer_status['reason'] = 'Screencap timed out'
                except Exception as e:
                    emit_ui(
                        self,
                        lambda cmd=[adb_cmd, '-s', serial, 'exec-out', 'screencap', '-p'], e=e: self.log_message(
                            f"Screencap exception for command {cmd}: {str(e)}"
                        )
                    )
                    dialer_status['failed'] = True
                    dialer_status['reason'] = str(e)

            finally:
                # Clean up temp files properly
                try:
                    if os.path.exists(screenshot_path):
                        os.remove(screenshot_path)
                except Exception:
                    emit_ui(self, lambda: self.log_message("Failed to remove IMEI screenshot temp file"))
                try:
                    if os.path.exists(temp_dir):
                        os.rmdir(temp_dir)
                except Exception:
                    emit_ui(self, lambda: self.log_message("Failed to remove IMEI temp directory"))
        except Exception as e:
            emit_ui(self, lambda e=e: self.log_message(f"Dialer method worker error: {str(e)}"))
            dialer_status['failed'] = True
            dialer_status['reason'] = str(e)

    def _get_device_imei(self, device_info, serial, adb_cmd):
        """Try to get device IMEI using multiple methods"""
        try:
            # Method 1: Using dialer method with OCR (run in thread with timeout)
            # Only try this method if tesseract is installed
            if self._check_tesseract_installed():
                emit_ui(self, lambda: self.log_message("Trying dialer code method to get IMEI..."))
            else:
                emit_ui(self, lambda: self.log_message("Skipping dialer method - tesseract OCR not installed, using alternative methods..."))

            result_list = []
            dialer_status = {'failed': False, 'reason': None}
            dialer_thread = threading.Thread(
                target=self._dialer_method_worker,
                args=(device_info, serial, adb_cmd, result_list, dialer_status),
                daemon=True
            )
            dialer_thread.start()
            dialer_thread.join(timeout=35)  # Wait max 35 seconds

            if dialer_thread.is_alive():
                emit_ui(self, lambda: self.log_message("Dialer method timed out"))
            elif result_list:
                imei = result_list[0]
                if imei:
                    emit_ui(self, lambda: self.log_message("IMEI found in OCR text!"))
                    device_info['imei'] = imei
            elif dialer_status['failed']:
                reason = dialer_status['reason'] or 'unknown error'
                emit_ui(self, lambda reason=reason: self.log_message(f"Dialer method failed: {reason}"))

            # Method 2: service call iphonesubinfo
            if 'imei' not in device_info:
                emit_ui(self, lambda: self.log_message("Trying service call method for IMEI..."))
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
                        emit_ui(self, lambda: self.log_message("Service call IMEI query timed out"))
                except Exception as e:
                    emit_ui(self, lambda e=e: self.log_message(f"Service call method error: {str(e)}"))

            # Method 3: dumpsys iphonesubinfo
            if 'imei' not in device_info:
                emit_ui(self, lambda: self.log_message("Trying dumpsys method for IMEI..."))
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
                        emit_ui(self, lambda: self.log_message("Dumpsys IMEI query timed out"))
                except Exception as e:
                    emit_ui(self, lambda e=e: self.log_message(f"Dumpsys method error: {str(e)}"))

        except Exception as e:
            emit_ui(self, lambda e=e: self.log_message(f"Error getting IMEI: {str(e)}"))

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
