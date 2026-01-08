"""
Authentication & Password Testing Module for Hack Attack

This module provides tools for testing authentication mechanisms and password security.
It includes features for password strength testing, brute force simulation, and
credential validation.

Can be used both as a standalone GUI application or imported as a module.
"""

import json
import logging
import sys
import time
import threading
from datetime import datetime
import re
import hashlib
import json
import random
import string
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import requests

# Configure logging with both file and console handlers
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'authentication_testing.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'),  # Overwrite log file each run
        logging.StreamHandler(sys.stdout)  # Also log to console
    ]
)
logger = logging.getLogger(__name__)
logger.info("=== Starting Authentication Testing Module ===")
logger.info(f"Log file: {os.path.abspath(log_file)}")

# GUI Dependencies (only imported when running as standalone)
GUI_ENABLED = True
try:
    from PySide6.QtCore import QThread, Signal, Qt, QSize, QTimer, QEventLoop
    from PySide6.QtGui import QIcon, QFont, QColor, QAction, QTextCursor, QIntValidator
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QTreeWidget, QTreeWidgetItem, QTabWidget, QLabel,
        QStatusBar, QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem,
        QLineEdit, QProgressBar, QHeaderView, QStyle, QMenu, QGroupBox,
        QFormLayout, QCheckBox, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QSplitter
    )
    from PySide6 import QtCore, QtGui, QtWidgets
    GUI_ENABLED = True
except Exception as e:
    print(f"GUI disabled: {e}")
    GUI_ENABLED = False

# Logger is already configured at the top of the file

class BruteForcePasswordThread(QThread):
    """Thread for running password brute force simulation in the background."""
    update_signal = Signal(dict)
    finished_signal = Signal(dict)
    
    def __init__(self, target_password, charset, min_length, max_length, max_attempts, delay):
        super().__init__()
        logger.info(f"Initializing BruteForcePasswordThread with target: {target_password}")
        self.target_password = target_password
        self.charset = charset
        self.min_length = min_length
        self.max_length = max_length
        self.max_attempts = max_attempts
        self.delay = delay
        self._is_running = True
        self._stop_requested = False
        
        logger.info(f"Thread initialized: {self}")
        logger.info(f"Charset: {charset}")
        logger.info(f"Length range: {min_length}-{max_length}")
        logger.info(f"Max attempts: {max_attempts}")
        logger.info(f"Delay: {delay}")
    
    def run(self):
        """Run the brute force simulation."""
        start_time = time.time()
        attempts = 0
        found = False
    
        # Common PINs to try first - expanded list
        common_pins = [
            # Most common PINs
            '1234', '0000', '1111', '1212', '1004', '2000', '4444',
            '2222', '6969', '9999', '3333', '5555', '6666', '1122',
            '7777', '0001', '1313', '8888', '4321', '2001', '1010',
            # Additional common patterns
            '12345', '123456', '1234567', '12345678', '123456789', '1234567890',
            '11111', '22222', '33333', '44444', '55555', '66666', '77777', '88888', '99999',
            '147258', '258369', '13579', '24680', '159357', '112233', '121212',
            # Common years
            '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992',
            '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001',
            # Common number patterns
            '000000', '111111', '222222', '333333', '444444', '555555', '666666',
            '777777', '888888', '999999', '123123', '321321', '112233', '223344',
            # Common keyboard patterns
            'qwerty', 'asdfgh', 'zxcvbn', 'qazwsx', '1qaz2wsx', '1q2w3e4r', '1q2w3e',
            # Common words and names
            'password', 'iloveyou', 'princess', 'dragon', 'baseball', 'football', 'letmein',
            'monkey', 'mustang', 'access', 'shadow', 'master', 'michael', 'superman',
            'batman', 'starwars', 'trustno1', 'jordan', 'harley', 'hunter', 'soccer',
            'freedom', 'whatever', 'hello', 'charlie', 'andrew', 'thomas', 'tigger',
            'robert', 'snoopy', 'jessica', 'pepper', 'daniel', '1234qwer', 'qwer1234'
        ]
    
        # Remove duplicates and ensure all are strings
        common_pins = list(dict.fromkeys([str(pin) for pin in common_pins if str(pin).isdigit()]))
    
        # Try common PINs first
        for pin in common_pins:
            if not self._is_running:
                break
            
            attempts += 1
            current_time = time.time()
            time_taken = current_time - start_time
            
            # Update UI
            self.update_signal.emit({
                'attempt': attempts,
                'pin': pin,
                'time_taken': time_taken,
                'status': 'Trying common PINs...',
                'found': False
            })
        
            # Check if this is the target PIN
            if pin == self.target_password:
                found = True
                self.update_signal.emit({
                    'attempt': attempts,
                    'pin': pin,
                    'time_taken': time_taken,
                    'status': 'Found PIN!',
                    'found': True
                })
                # Emit final result and return immediately
                self.finished_signal.emit({
                    'found': True,
                    'attempts': attempts,
                    'time_taken': time_taken,
                    'pin': pin,
                    'was_stopped': False
                })
                return
                
            time.sleep(self.delay)
            
            # Check if we should stop
            if not self._is_running or attempts >= self.max_attempts:
                break
            
        # If not found in common PINs, try sequential numbers with different lengths
        if not found and self._is_running and attempts < self.max_attempts:
            # Get target PIN length and try that first
            target_length = len(self.target_pin)
            lengths_to_try = [target_length]  # Start with the actual length
            
            # Add other common lengths
            for length in [4, 6, 5, 3, 7, 8]:
                if length != target_length and length not in lengths_to_try:
                    lengths_to_try.append(length)
            
            # Try each length
            for length in lengths_to_try:
                if not self._is_running or attempts >= self.max_attempts or found:
                    break
                
                max_num = 10 ** length
                for i in range(max_num):
                    if not self._is_running or attempts >= self.max_attempts:
                        break
                        
                    pin = f"{i:0{length}d}"  # Format with leading zeros
                    attempts += 1
                    current_time = time.time()
                    time_taken = current_time - start_time
                    
                    # Check if this is the target PIN FIRST
                    if pin == self.target_pin:
                        found = True
                        # Update UI with found status
                        self.update_signal.emit({
                            'attempt': attempts,
                            'pin': pin,
                            'time_taken': time_taken,
                            'status': 'Found PIN!',
                            'found': True
                        })
                        # Emit final result
                        self.finished_signal.emit({
                            'found': True,
                            'attempts': attempts,
                            'time_taken': time_taken,
                            'pin': pin,
                            'was_stopped': False
                        })
                        # Stop the thread immediately
                        self._is_running = False
                        return  # Exit immediately when PIN is found
                    
                    # Update UI periodically (not every attempt to reduce overhead)
                    if attempts % 100 == 0:  # Update every 100 attempts
                        self.update_signal.emit({
                            'attempt': attempts,
                            'pin': pin,
                            'time_taken': time_taken,
                            'status': 'Trying sequential PINs...',
                            'found': False
                        })
                        
                    time.sleep(self.delay)
                
                # Check if we found it in this length iteration
                if found:
                    break
    
        # Only emit final result if we didn't already find the PIN
        if not found:
            end_time = time.time()
            self.finished_signal.emit({
                'found': False,
                'attempts': attempts,
                'time_taken': end_time - start_time,
                'pin': '',
                'was_stopped': not self._is_running
            })
    
    def _safe_sleep(self, seconds):
        """
        A thread-safe sleep function that can be interrupted by the stop method.
        
        Args:
            seconds: Number of seconds to sleep
        """
        if seconds <= 0:
            return
            
        # Convert to milliseconds and use QThread's msleep
        ms = int(seconds * 1000)
        chunk = 100  # Sleep in 100ms chunks to remain responsive
        
        while ms > 0 and self._is_running and not self._stop_requested:
            sleep_time = min(chunk, ms)
            self.msleep(sleep_time)
            ms -= sleep_time
    
    def _cleanup(self):
        """Clean up resources when stopping the thread."""
        try:
            logger.info("Cleaning up brute force thread")
            self._is_running = False
            self._stop_requested = True
            
            # Only try to quit and wait if the thread is still running
            if self.isRunning():
                self.quit()
                # Give it a short time to finish, but don't block indefinitely
                if not self.wait(1000):  # Wait up to 1 second
                    logger.warning("Thread did not finish in time, terminating")
                    self.terminate()
        except RuntimeError as e:
            # Ignore errors that occur when the C++ object is already deleted
            if "wrapped C/C++ object" not in str(e):
                logger.error(f"Error during cleanup: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during cleanup: {e}")
    
    def _try_combinations(self, start_time, attempts):
        """Try all combinations of the given character set."""
        from itertools import product
        
        # Register cleanup on thread exit
        import atexit
        atexit.register(self._cleanup)
        
        logger.info(f"=== Starting _try_combinations ===")
        logger.info(f"Start time: {start_time}")
        logger.info(f"Initial attempts: {attempts}")
        logger.info(f"Min length: {self.min_length}, Max length: {self.max_length}")
        logger.info(f"Target password: {self.target_password}")
        
        try:
            logger.info(f"Starting brute force with charset: {self.charset}")
            
            for length in range(self.min_length, self.max_length + 1):
                if not self._is_running or self._stop_requested:
                    logger.info("Stopping due to stop request")
                    self._cleanup()
                    return
                
                logger.info(f"Trying length: {length}")
                
                # Generate all possible combinations for this length
                from itertools import product
                for guess in product(self.charset, repeat=length):
                    # Get the password as string first
                    password = ''.join(guess)
                    attempts += 1
                    current_time = time.time()
                    time_taken = current_time - start_time
                    
                    # Update UI every 100 attempts or on success
                    if attempts % 100 == 0 or password == self.target_password:
                        self.update_signal.emit({
                            'attempt': attempts,
                            'password': password,
                            'time_taken': time_taken,
                            'status': f'Trying {password}...',
                            'found': password == self.target_password,
                            'length': length,
                            'min_length': self.min_length,
                            'max_length': self.max_length
                        })
                    
                    # Check if this is the target password
                    if password == self.target_password:
                        logger.info(f"Password found after {attempts} attempts")
                        self._handle_success(attempts, time_taken, password)
                        return  # This should stop the thread immediately
                    
                    # Small delay every 1000 attempts to keep UI responsive
                    if attempts % 1000 == 0:
                        self._safe_sleep(0.01)  # 10ms delay
                        
                        # Check if we should stop after sleep
                        if not self._is_running or self._stop_requested:
                            logger.info("Stopping after sleep in product loop")
                            self._cleanup()
                            return
                    
                    # Check max attempts
                    if self.max_attempts > 0 and attempts >= self.max_attempts:
                        logger.info(f"Max attempts ({self.max_attempts}) reached")
                        self._cleanup()
                        return
                        
        except Exception as e:
            logger.error(f"Error in _try_combinations: {str(e)}", exc_info=True)
            raise  # Re-raise the exception to ensure the thread stops
    
    def _handle_success(self, attempts, time_taken, password):
        """Handle successful password find."""
        try:
            logger.info(f"Password found! Attempts: {attempts}, Time: {time_taken:.2f}s")
            # Set flags to stop the thread
            self._is_running = False
            self._stop_requested = True
            
            # Emit the success signal
            self.update_signal.emit({
                'attempt': attempts,
                'password': password,
                'time_taken': time_taken,
                'status': 'Password found!',
                'found': True,
                'completed': True
            })
            
            logger.info("Success signal emitted, stopping thread")
            
            # Stop the thread immediately
            self._is_running = False
            self._stop_requested = True
            self.quit()
            
        except Exception as e:
            logger.error(f"Error in _handle_success: {str(e)}", exc_info=True)
            raise  # Re-raise the exception to ensure the thread stops
        self.finished_signal.emit({
            'found': True,
            'attempts': attempts,
            'time_taken': time_taken,
            'password': password,
            'was_stopped': False
        })
    def stop(self):
        """Stop the brute force operation."""
        logger.info("Stop requested - cleaning up thread")
        self._is_running = False
        self._stop_requested = True
        self.quit()
        if not self.wait(1000):  # Wait up to 1 second for clean exit
            logger.warning("Thread did not stop gracefully, terminating")
            self.terminate()
            self.wait(1000)


class BruteForceThread(QThread):
    """Thread for running PIN brute force simulation in the background."""
    update_signal = Signal(dict)
    finished_signal = Signal(dict)
    
    def __init__(self, target_pin, max_attempts, delay):
        super().__init__()
        self.target_pin = target_pin
        self.max_attempts = max_attempts
        self.delay = delay
        self._is_running = True
    
    def run(self):
        """Run the brute force simulation."""
        start_time = time.time()
        attempts = 0
        found = False
    
        # Common PINs to try first - expanded list
        common_pins = [
            # Most common PINs
            '1234', '0000', '1111', '1212', '1004', '2000', '4444',
            '2222', '6969', '9999', '3333', '5555', '6666', '1122',
            '7777', '0001', '1313', '8888', '4321', '2001', '1010',
            # Additional common patterns
            '12345', '123456', '1234567', '12345678', '123456789', '1234567890',
            '11111', '22222', '33333', '44444', '55555', '66666', '77777', '88888', '99999',
            '147258', '258369', '13579', '24680', '159357', '112233', '121212',
            # Common years
            '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992',
            '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001',
            # Common number patterns
            '000000', '111111', '222222', '333333', '444444', '555555', '666666',
            '777777', '888888', '999999', '123123', '321321', '112233', '223344',
            # Common keyboard patterns
            'qwerty', 'asdfgh', 'zxcvbn', 'qazwsx', '1qaz2wsx', '1q2w3e4r', '1q2w3e',
            # Common words and names
            'password', 'iloveyou', 'princess', 'dragon', 'baseball', 'football', 'letmein',
            'monkey', 'mustang', 'access', 'shadow', 'master', 'michael', 'superman',
            'batman', 'starwars', 'trustno1', 'jordan', 'harley', 'hunter', 'soccer',
            'freedom', 'whatever', 'hello', 'charlie', 'andrew', 'thomas', 'tigger',
            'robert', 'snoopy', 'jessica', 'pepper', 'daniel', '1234qwer', 'qwer1234'
        ]
    
        # Remove duplicates and ensure all are strings
        common_pins = list(dict.fromkeys([str(pin) for pin in common_pins if str(pin).isdigit()]))
    
        # Try common PINs first
        for pin in common_pins:
            if not self._is_running:
                break
            
            attempts += 1
            current_time = time.time()
            time_taken = current_time - start_time
            
            # Update UI
            self.update_signal.emit({
                'attempt': attempts,
                'pin': pin,
                'time_taken': time_taken,
                'status': 'Trying common PINs...',
                'found': False
            })
            
            # Check if this is the target PIN
            if pin == self.target_pin:
                found = True
                self.update_signal.emit({
                    'attempt': attempts,
                    'pin': pin,
                    'time_taken': time_taken,
                    'status': 'Found PIN!',
                    'found': True
                })
                # Emit final result and return immediately
                self.finished_signal.emit({
                    'found': True,
                    'attempts': attempts,
                    'time_taken': time_taken,
                    'pin': pin,
                    'was_stopped': False
                })
                return
                
            time.sleep(self.delay)
    
        # If not found in common PINs, try sequential numbers with different lengths
        if not found and self._is_running and attempts < self.max_attempts:
            # Get target PIN length and try that first
            target_length = len(self.target_pin)
            lengths_to_try = [target_length]  # Start with the actual length
        
            # Add other common lengths
            for length in [4, 6, 5, 3, 7, 8]:
                if length != target_length and length not in lengths_to_try:
                    lengths_to_try.append(length)
        
            # Try each length
            for length in lengths_to_try:
                if not self._is_running or attempts >= self.max_attempts or found:
                    break
                
                max_num = 10 ** length
                for i in range(max_num):
                    if not self._is_running or attempts >= self.max_attempts:
                        break
                    
                    pin = f"{i:0{length}d}"  # Format with leading zeros
                    attempts += 1
                    current_time = time.time()
                    time_taken = current_time - start_time
                
                    # Check if this is the target PIN FIRST
                    if pin == self.target_pin:
                        found = True
                        # Update UI with found status
                        self.update_signal.emit({
                            'attempt': attempts,
                            'pin': pin,
                            'time_taken': time_taken,
                            'status': 'Found PIN!',
                            'found': True
                        })
                        # Emit final result
                        self.finished_signal.emit({
                            'found': True,
                            'attempts': attempts,
                            'time_taken': time_taken,
                            'pin': pin,
                            'was_stopped': False
                        })
                        # Stop the thread immediately
                        self._is_running = False
                        return  # Exit immediately when PIN is found
                
                    # Update UI periodically (not every attempt to reduce overhead)
                    if attempts % 100 == 0:  # Update every 100 attempts
                        self.update_signal.emit({
                            'attempt': attempts,
                            'pin': pin,
                            'time_taken': time_taken,
                            'status': 'Trying sequential PINs...',
                            'found': False
                        })
                    
                    time.sleep(self.delay)
            
                # Check if we found it in this length iteration
                if found:
                    break
    
            # Only emit final result if we didn't already find the PIN
            if not found:
                end_time = time.time()
                self.finished_signal.emit({
                    'found': False,
                    'attempts': attempts,
                    'time_taken': end_time - start_time,
                    'pin': '',
                    'was_stopped': not self._is_running
                })
    
    def stop(self):
        """Stop the brute force operation."""
        self._is_running = False


class AuthenticationTester:
    """Main class for authentication and password testing."""
    
    def __init__(self):
        """Initialize the AuthenticationTester class."""
        self.common_passwords = self._load_common_passwords()
        self.test_results = {}
        self.brute_force_stop_flag = False
    
    def _load_common_passwords(self) -> List[str]:
        """Load a list of common passwords for testing."""
        # This is a basic list - in a real application, you might want to load this from a file
        # or use a more comprehensive password list
        return [
            'password', '123456', '123456789', '12345', '12345678',
            '1234567', '123123', '1234567890', 'admin', 'welcome',
            'qwerty', 'abc123', 'password1', '1234', 'test', 'passw0rd'
        ]
    
    def check_pin_strength(self, pin: str) -> Dict[str, Any]:
        """
        Check the strength of a numeric PIN code.
        
        Args:
            pin: The PIN code to check (should contain only digits)
            
        Returns:
            Dictionary containing strength metrics and suggestions
        """
        if not pin.isdigit():
            raise ValueError("PIN must contain only digits")
            
        result = {
            'length': len(pin),
            'is_sequential': self._is_sequential(pin),
            'is_repeating': self._is_repeating(pin),
            'has_pattern': self._has_pattern(pin),
            'is_common': pin in ['0000', '1111', '1234', '1212', '1004', '2000', '4444', '9999', '000000', '123456', '654321'],
            'unique_digits': len(set(pin)),
            'score': 0,
            'strength': 'Very Weak',
            'suggestions': []
        }
        
        # Calculate score (0-100)
        # Length (max 40 points)
        if result['length'] == 4:
            result['score'] += 20
        elif result['length'] == 6:
            result['score'] += 30
        elif result['length'] >= 8:
            result['score'] += 40
            
        # Uniqueness (max 30 points)
        if result['unique_digits'] >= 4:
            result['score'] += int((result['unique_digits'] / result['length']) * 30)
            
        # Penalties
        if result['is_sequential']:
            result['score'] = max(0, result['score'] - 30)
            result['suggestions'].append("Avoid sequential numbers (e.g., 1234, 4567)")
            
        if result['is_repeating']:
            result['score'] = max(0, result['score'] - 20)
            result['suggestions'].append("Avoid repeating numbers (e.g., 1111, 1212)")
            
        if result['has_pattern']:
            result['score'] = max(0, result['score'] - 15)
            result['suggestions'].append("Avoid simple patterns (e.g., 2580, 1478)")
            
        if result['is_common']:
            result['score'] = max(0, result['score'] - 40)
            result['suggestions'].append("Avoid commonly used PINs")
            
        # Determine strength
        if result['score'] >= 80:
            result['strength'] = 'Very Strong'
        elif result['score'] >= 60:
            result['strength'] = 'Strong'
        elif result['score'] >= 40:
            result['strength'] = 'Moderate'
        elif result['score'] >= 20:
            result['strength'] = 'Weak'
            
        # Add suggestions
        if result['length'] < 4:
            result['suggestions'].append("Use at least 4 digits")
        elif result['length'] < 6:
            result['suggestions'].append("Consider using 6 or more digits for better security")
            
        if result['unique_digits'] < 3:
            result['suggestions'].append("Use more unique digits")
            
        if not result['suggestions'] and result['score'] > 60:
            result['suggestions'].append("Good PIN! Consider using a longer PIN for better security.")
            
        return result
        
    def _is_sequential(self, pin: str) -> bool:
        """Check if PIN is a simple sequence (e.g., 1234, 4567, 9876)."""
        if len(pin) < 2:
            return False
            
        # Check ascending sequence
        if all((int(pin[i+1]) - int(pin[i])) == 1 for i in range(len(pin)-1)):
            return True
            
        # Check descending sequence
        if all((int(pin[i]) - int(pin[i+1])) == 1 for i in range(len(pin)-1)):
            return True
            
        return False
        
    def _is_repeating(self, pin: str) -> bool:
        """Check if PIN has repeating patterns (e.g., 1122, 1212)."""
        # Check if all digits are the same
        if len(set(pin)) == 1:
            return True
            
        # Check for repeating pairs (e.g., 1212, 123123)
        if len(pin) % 2 == 0:
            half = len(pin) // 2
            if pin[:half] == pin[half:]:
                return True
                
        # Check for alternating patterns (e.g., 1212, 123123)
        for i in range(1, len(pin)//2 + 1):
            if len(pin) % i == 0:
                pattern = pin[:i]
                if all(pin[j:j+i] == pattern for j in range(i, len(pin), i)):
                    return True
                    
        return False
        
    def _has_pattern(self, pin: str) -> bool:
        """Check if PIN forms a pattern on a keypad (e.g., 1478, 2580)."""
        if len(pin) < 3:
            return False
            
        # Common keypad patterns
        keypad = [
            '123', '456', '789', '147', '258', '369', '159', '357',
            '321', '654', '987', '741', '852', '963', '951', '753'
        ]
        
        # Check for any 3+ digit pattern
        for i in range(len(pin) - 2):
            if pin[i:i+3] in keypad:
                return True
                
        return False
        
    def brute_force_pin(self, target_pin: str, max_attempts: int = 10000, delay: float = 0.1) -> Dict[str, Any]:
        """
        Simulate a brute force attack on a numeric PIN.
        
        Args:
            target_pin: The PIN to find (simulated, not actually known to this method)
            max_attempts: Maximum number of attempts before giving up
            delay: Delay between attempts in seconds (simulates network/processing delay)
            
        Returns:
            Dictionary containing results of the brute force attempt
        """
        if not target_pin.isdigit():
            raise ValueError("Target PIN must contain only digits")
            
        attempts = 0
        found = False
        start_time = time.time()
        
        # Common PINs to try first
        common_pins = [
            '1234', '0000', '1111', '1212', '1004', '2000', '4444', '2222', '6969', '9999', 
            '3333', '5555', '6666', '1122', '1313', '2001', '1010', '4321', '12345', '000000'
        ]
        
        # Try common PINs first
        for pin in common_pins:
            if self.brute_force_stop_flag:
                break
                
            attempts += 1
            time.sleep(delay)  # Simulate network/processing delay
            
            if pin == target_pin:
                found = True
                break
        
        # If not found in common PINs, try sequential numbers
        if not found and not self.brute_force_stop_flag:
            for i in range(10000):  # Try all 4-digit combinations
                if self.brute_force_stop_flag:
                    break
                    
                pin = f"{i:04d}"
                attempts += 1
                time.sleep(delay)  # Simulate network/processing delay
                
                if pin == target_pin:
                    found = True
                    break
                
                if attempts >= max_attempts:
                    break
        
        end_time = time.time()
        time_taken = end_time - start_time
        
        return {
            'success': found,
            'attempts': attempts,
            'time_taken': time_taken,
            'pin_found': target_pin if found else None,
            'attempts_per_second': attempts / time_taken if time_taken > 0 else 0,
            'max_attempts': max_attempts,
            'stopped_early': self.brute_force_stop_flag
        }
        
    def stop_brute_force(self):
        """Stop an ongoing brute force operation."""
        self.brute_force_stop_flag = True
    
    def check_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Check the strength of a password.
        
        Args:
            password: The password to check
            
        Returns:
            Dictionary containing strength metrics and suggestions
        """
        result = {
            'length': len(password),
            'has_upper': any(c.isupper() for c in password),
            'has_lower': any(c.islower() for c in password),
            'has_digit': any(c.isdigit() for c in password),
            'has_special': any(not c.isalnum() for c in password),
            'is_common': password.lower() in [p.lower() for p in self.common_passwords],
            'score': 0,
            'strength': 'Very Weak',
            'suggestions': []
        }
        
        # Calculate score (0-100)
        if result['length'] >= 8:
            result['score'] += 30
        if result['length'] >= 12:
            result['score'] += 20
            
        if result['has_upper']:
            result['score'] += 10
        if result['has_lower']:
            result['score'] += 10
        if result['has_digit']:
            result['score'] += 10
        if result['has_special']:
            result['score'] += 20
            
        if result['is_common']:
            result['score'] = max(0, result['score'] - 30)
            result['suggestions'].append("Avoid using common passwords")
            
        # Determine strength
        if result['score'] >= 80:
            result['strength'] = 'Very Strong'
        elif result['score'] >= 60:
            result['strength'] = 'Strong'
        elif result['score'] >= 40:
            result['strength'] = 'Moderate'
        elif result['score'] >= 20:
            result['strength'] = 'Weak'
            
        # Add suggestions
        if result['length'] < 8:
            result['suggestions'].append("Use at least 8 characters")
        if not result['has_upper']:
            result['suggestions'].append("Include uppercase letters")
        if not result['has_lower']:
            result['suggestions'].append("Include lowercase letters")
        if not result['has_digit']:
            result['suggestions'].append("Include numbers")
        if not result['has_special']:
            result['suggestions'].append("Include special characters")
            
        return result
    
    def test_http_auth(
        self,
        url: str,
        username: str,
        password: str,
        verify_ssl: bool = True,
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Test HTTP Basic Authentication.
        
        Args:
            url: The URL to test
            username: Username to test
            password: Password to test
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary containing test results
        """
        result = {
            'success': False,
            'status_code': 0,
            'time_taken': 0,
            'error': None
        }
        
        start_time = time.monotonic()
        try:
            response = requests.get(
                url,
                auth=(username, password),
                timeout=timeout,
                verify=verify_ssl
            )
            result['status_code'] = response.status_code
            result['success'] = 200 <= response.status_code < 300
            if not result['success']:
                result['error'] = response.reason or "Authentication failed"
        except requests.exceptions.RequestException as e:
            result['error'] = str(e)
        finally:
            result['time_taken'] = time.monotonic() - start_time
            
        return result

class AuthenticationTestingGUI(QMainWindow):
    """GUI for the Authentication Testing tool."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.authentication_tester = AuthenticationTester()
        
        # Set up the main window
        self.setWindowTitle("Hack Attack - Authentication Testing")
        self.setMinimumSize(800, 600)
        
        # Create and set up status bar first
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        
        # Initialize the UI
        try:
            self.init_ui()
            self.apply_styles()
            self.show_status("Ready", 3000)
        except Exception as e:
            self.show_status(f"Initialization error: {str(e)}", 5000)
            logger.error(f"UI initialization failed: {str(e)}")
        
    def init_ui(self):
        """Initialize the main UI components."""
        try:
            # Create tab widget
            self.tab_widget = QTabWidget()
            
            # Add tabs
            self.tab_widget.addTab(self.setup_password_strength_tab(), "Password Strength")
            self.tab_widget.addTab(self.setup_pin_strength_tab(), "PIN Strength")
            self.tab_widget.addTab(self.setup_pin_brute_force_tab(), "PIN Brute Force")
            self.tab_widget.addTab(self.setup_password_brute_force_tab(), "Password Brute Force")
            self.tab_widget.addTab(self.create_http_auth_tab(), "HTTP Auth Tester")
            
            # Set main layout
            self.main_layout.addWidget(self.tab_widget)
            
        except Exception as e:
            logger.error(f"Error initializing UI: {str(e)}")
            raise
    
    def show_status(self, message, timeout=3000):
        """Display a status message in the status bar.
        
        Args:
            message (str): The message to display
            timeout (int): How long to show the message in milliseconds
        """
        self.status_bar.showMessage(message, timeout)
    
    def setup_password_strength_tab(self):
        """Set up the password strength checker tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Password input
        form_layout = QFormLayout()
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password to check")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.textChanged.connect(self.update_password_strength)
        form_layout.addRow("Password:", self.password_input)
        
        # Show password checkbox
        self.show_password_checkbox = QCheckBox("Show password")
        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)
        form_layout.addRow("", self.show_password_checkbox)
        
        # Strength indicator
        self.strength_bar = QProgressBar()
        self.strength_bar.setRange(0, 100)
        self.strength_bar.setTextVisible(True)
        self.strength_bar.setFormat("Strength: %p%")
        form_layout.addRow("Strength:", self.strength_bar)
        
        # Strength label
        self.strength_label = QLabel("Enter a password to test its strength")
        form_layout.addRow("", self.strength_label)
        
        # Suggestions
        self.suggestions_label = QLabel("")
        self.suggestions_label.setWordWrap(True)
        form_layout.addRow("Suggestions:", self.suggestions_label)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        return tab
    
    def setup_pin_strength_tab(self):
        """Set up the PIN strength checker tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # PIN input
        form_layout = QFormLayout()
        self.pin_input = QLineEdit()
        self.pin_input.setPlaceholderText("Enter a numeric PIN")
        self.pin_input.setMaxLength(12)  # Reasonable max length for a PIN
        
        # Use regex validator to allow only digits
        regex = QtCore.QRegularExpression(r"^\d*$")
        validator = QtGui.QRegularExpressionValidator(regex, self.pin_input)
        self.pin_input.setValidator(validator)
        
        self.pin_input.textChanged.connect(self.update_pin_strength)
        form_layout.addRow("PIN:", self.pin_input)
        
        # Strength indicator
        self.pin_strength_bar = QProgressBar()
        self.pin_strength_bar.setRange(0, 100)
        self.pin_strength_bar.setTextVisible(True)
        self.pin_strength_bar.setFormat("Strength: %p%")
        form_layout.addRow("Strength:", self.pin_strength_bar)
        
        # Strength label
        self.pin_strength_label = QLabel("Enter a PIN to test its strength")
        form_layout.addRow("", self.pin_strength_label)
        
        # PIN details
        self.pin_details_label = QLabel("")
        self.pin_details_label.setWordWrap(True)
        form_layout.addRow("Details:", self.pin_details_label)
        
        # Suggestions
        self.pin_suggestions_label = QLabel("")
        self.pin_suggestions_label.setWordWrap(True)
        form_layout.addRow("Suggestions:", self.pin_suggestions_label)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        return tab
    
    def setup_password_brute_force_tab(self):
        """Set up the password brute force simulator tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Target password input
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Target Password:"))
        self.target_password_input = QLineEdit()
        self.target_password_input.setPlaceholderText("Enter password to find")
        target_layout.addWidget(self.target_password_input)
        layout.addLayout(target_layout)
        
        # Character set selection
        charset_group = QGroupBox("Character Set")
        charset_layout = QVBoxLayout()
        
        self.lowercase_cb = QCheckBox("Lowercase (a-z)")
        self.lowercase_cb.setChecked(True)
        self.uppercase_cb = QCheckBox("Uppercase (A-Z)")
        self.digits_cb = QCheckBox("Digits (0-9)")
        self.special_cb = QCheckBox("Special (!@#$%^&*)")
        
        charset_layout.addWidget(self.lowercase_cb)
        charset_layout.addWidget(self.uppercase_cb)
        charset_layout.addWidget(self.digits_cb)
        charset_layout.addWidget(self.special_cb)
        charset_group.setLayout(charset_layout)
        layout.addWidget(charset_group)
        
        # Length range
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("Min Length:"))
        self.min_length = QSpinBox()
        self.min_length.setRange(1, 20)
        self.min_length.setValue(4)
        length_layout.addWidget(self.min_length)
        
        length_layout.addWidget(QLabel("Max Length:"))
        self.max_length = QSpinBox()
        self.max_length.setRange(1, 20)
        self.max_length.setValue(8)
        length_layout.addWidget(self.max_length)
        layout.addLayout(length_layout)
        
        # Delay between attempts
        options_layout = QHBoxLayout()
        options_layout.addStretch()
        options_layout.addWidget(QLabel("Delay between attempts (s):"))
        self.pw_delay = QDoubleSpinBox()
        self.pw_delay.setRange(0.0, 10.0)
        self.pw_delay.setValue(0.1)
        self.pw_delay.setSingleStep(0.1)
        options_layout.addWidget(self.pw_delay)
        
        layout.addLayout(options_layout)
        
        # Start/Stop button
        self.pw_brute_force_button = QPushButton("Start Brute Force")
        self.pw_brute_force_button.clicked.connect(self.toggle_password_brute_force)
        layout.addWidget(self.pw_brute_force_button)
        
        # Progress bar
        self.pw_progress_bar = QProgressBar()
        self.pw_progress_bar.setRange(0, 100)
        layout.addWidget(self.pw_progress_bar)
        
        # Results
        self.pw_results_label = QLabel("")
        layout.addWidget(self.pw_results_label)
        
        # Log
        self.pw_log = QTextEdit()
        self.pw_log.setReadOnly(True)
        layout.addWidget(self.pw_log)
        
        # Initialize state
        self.pw_brute_force_thread = None
        self.pw_brute_force_running = False
        
        return tab

    def setup_pin_brute_force_tab(self):
        """Set up the PIN brute force simulator tab."""
        self.pin_brute_force_tab = QWidget()
        layout = QVBoxLayout(self.pin_brute_force_tab)
        
        # Target PIN input
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Target PIN:"))
        self.target_pin_input = QLineEdit()
        self.target_pin_input.setPlaceholderText("Enter 4-8 digit PIN")
        self.target_pin_input.setValidator(QIntValidator(0, 99999999))  # Up to 8 digits
        target_layout.addWidget(self.target_pin_input)
        layout.addLayout(target_layout)
        
        # Max attempts and delay
        options_layout = QHBoxLayout()
        
        options_layout.addWidget(QLabel("Max Attempts:"))
        self.max_attempts_input = QSpinBox()
        self.max_attempts_input.setRange(1000, 1000000)
        self.max_attempts_input.setValue(10000)
        self.max_attempts_input.setSingleStep(1000)
        options_layout.addWidget(self.max_attempts_input)
        
        options_layout.addWidget(QLabel("Delay (s):"))
        self.delay_input = QDoubleSpinBox()
        self.delay_input.setRange(0.0, 10.0)
        self.delay_input.setValue(0.1)
        self.delay_input.setSingleStep(0.1)
        options_layout.addWidget(self.delay_input)
        
        layout.addLayout(options_layout)
        
        # Start/Stop button
        self.brute_force_button = QPushButton("Start Brute Force")
        self.brute_force_button.clicked.connect(self.toggle_brute_force)
        layout.addWidget(self.brute_force_button)
        
        # Progress bar
        self.bf_progress_bar = QProgressBar()
        self.bf_progress_bar.setRange(0, 100)
        layout.addWidget(self.bf_progress_bar)
        
        # Results
        self.bf_results_label = QLabel("")
        layout.addWidget(self.bf_results_label)
        
        # Log
        self.bf_log = QTextEdit()
        self.bf_log.setReadOnly(True)
        layout.addWidget(self.bf_log)
        
        # Initialize state
        
        # Brute force thread
        self.bf_thread = None
        self.bf_running = False
        
        return self.pin_brute_force_tab
        
    def toggle_brute_force(self):
        """Toggle the brute force simulation on/off."""
        if self.bf_running:
            self.stop_brute_force()
        else:
            self.start_brute_force()
    
    def start_brute_force(self):
        """Start the brute force simulation."""
        target_pin = self.target_pin_input.text().strip()
        if not target_pin or not target_pin.isdigit() or not (4 <= len(target_pin) <= 8):
            QMessageBox.warning(self, "Error", "Please enter a valid 4-8 digit PIN")
            return
            
        # Update UI
        self.bf_running = True
        self.brute_force_button.setText("Stop Brute Force")
        self.bf_progress_bar.setValue(0)
        self.bf_results_label.setText("")
        self.bf_log.clear()
        
        # Create and start thread
        self.bf_thread = BruteForceThread(
            target_pin=target_pin,
            max_attempts=self.max_attempts_input.value(),
            delay=self.delay_input.value()
        )
        
        # Connect signals
        self.bf_thread.update_signal.connect(self.update_brute_force_ui)
        self.bf_thread.finished_signal.connect(self.brute_force_finished)
        
        # Start the thread
        self.bf_thread.start()
        
        self.status_bar.showMessage("Brute force simulation started...", 3000)
    
    def stop_brute_force(self):
        """Stop the brute force simulation."""
        if self.bf_thread:
            self.bf_thread.stop()
            self.bf_thread.wait()
            self.bf_running = False
            self.brute_force_button.setText("Start Brute Force")
            self.status_bar.showMessage("Brute force simulation stopped", 3000)
    
    def update_brute_force_ui(self, data):
        """Update the UI with brute force progress."""
        if 'pin' in data:
            self.bf_log.append(f"Attempt {data['attempt']}: {data['pin']}")
            
        if 'status' in data:
            self.bf_results_label.setText(f"Status: {data['status']}")
            
        if 'attempt' in data and 'time_taken' in data:
            attempts_per_second = data['attempt'] / max(1, data['time_taken'])
            self.bf_results_label.setText(
                f"Attempts: {data['attempt']} | "
                f"Current: {data.get('pin', '')} | "
                f"Time: {data['time_taken']:.2f}s | "
                f"Speed: {attempts_per_second:.1f} attempts/s"
            )
    
    def brute_force_finished(self, result):
        """Handle completion of brute force operation."""
        self.bf_running = False
        self.brute_force_button.setText("Start Brute Force")
        
        if result['found']:
            self.bf_results_label.setText(f"Found PIN: {result['pin']} in {result['attempts']} attempts")
            self.status_bar.showMessage(f"PIN found in {result['attempts']} attempts!", 5000)
        else:
            self.bf_results_label.setText("PIN not found")
            self.status_bar.showMessage("PIN not found", 3000)
            
    def toggle_password_brute_force(self):
        """Toggle the password brute force simulation on/off."""
        if self.pw_brute_force_running:
            self.stop_password_brute_force()
        else:
            self.start_password_brute_force()
    
    def start_password_brute_force(self):
        """Start the password brute force simulation."""
        try:
            logger.info("===== Starting password brute force =====")
            target_password = self.target_password_input.text().strip()
            if not target_password:
                QMessageBox.warning(self, "Error", "Please enter a target password")
                return
                
            # Build character set
            charset = ""
            if self.lowercase_cb.isChecked():
                charset += "abcdefghijklmnopqrstuvwxyz"
            if self.uppercase_cb.isChecked():
                charset += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            if self.digits_cb.isChecked():
                charset += "0123456789"
            if self.special_cb.isChecked():
                charset += "!@#$%^&*()_+-=[]{}|;:,.<>?"
                
            if not charset:
                QMessageBox.warning(self, "Error", "Please select at least one character set")
                return
                
            min_length = self.min_length.value()
            max_length = self.max_length.value()
            
            if min_length > max_length:
                QMessageBox.warning(self, "Error", "Minimum length cannot be greater than maximum length")
                return
                
            # Clear previous results
            self.pw_progress_bar.setValue(0)
            self.pw_results_label.setText("Starting brute force...")
            self.pw_log.clear()
            self.pw_log.append("Starting password brute force simulation...")
            self.pw_log.append(f"Target: {target_password}")
            self.pw_log.append(f"Character set: {' '.join(charset)}")
            self.pw_log.append(f"Length range: {min_length}-{max_length} characters")
            self.pw_log.append("-" * 40)
            
            # Enable/Disable UI elements
            self.target_password_input.setEnabled(False)
            self.lowercase_cb.setEnabled(False)
            self.uppercase_cb.setEnabled(False)
            self.digits_cb.setEnabled(False)
            self.special_cb.setEnabled(False)
            self.min_length.setEnabled(False)
            self.max_length.setEnabled(False)
            self.pw_delay.setEnabled(False)
            
            # Create and start thread with max_attempts set to 0 for infinite attempts
            logger.info(f"Creating brute force thread with target: {target_password}")
            logger.info(f"Charset: {charset}")
            logger.info(f"Length range: {min_length}-{max_length}")
            
            self.pw_brute_force_thread = BruteForcePasswordThread(
                target_password=target_password,
                charset=charset,
                min_length=min_length,
                max_length=max_length,
                max_attempts=0,  # 0 means infinite attempts
                delay=self.pw_delay.value()
            )
            
            # Debug signal connections
            logger.info("Connecting signals...")
            
            # Connect signals with explicit connection type
            self.pw_brute_force_thread.update_signal.connect(
                self.update_password_brute_force_ui,
                QtCore.Qt.ConnectionType.QueuedConnection  # Ensure thread-safe connection
            )
            self.pw_brute_force_thread.finished_signal.connect(
                self.password_brute_force_finished,
                QtCore.Qt.ConnectionType.QueuedConnection  # Ensure thread-safe connection
            )
            logger.info("Signals connected with QueuedConnection")
            
            # Test signal connection directly
            logger.info("Testing direct signal emission...")
            try:
                self.update_password_brute_force_ui({
                    'attempt': 0,
                    'password': 'DIRECT_TEST',
                    'time_taken': 0,
                    'status': 'Testing direct UI update...',
                    'found': False
                })
                logger.info("Direct UI update test successful")
            except Exception as e:
                logger.error(f"Direct UI update test failed: {e}", exc_info=True)
            
            # Start the thread
            logger.info("Starting brute force thread...")
            self.pw_brute_force_thread.start()
            logger.info("Brute force thread started")
            
            # Force immediate UI update
            self.pw_log.append("Brute force thread started. Waiting for updates...")
            QApplication.processEvents()
            
            # Update UI
            self.pw_brute_force_button.setText("Stop Brute Force")
            status_msg = "Password brute force simulation started..."
            self.status_bar.showMessage(status_msg, 3000)
            logger.info(status_msg)
            
        except Exception as e:
            logger.error(f"Error starting brute force: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to start brute force: {str(e)}")
            self.pw_results_label.setText(f"Error: {str(e)}")
    
    def stop_password_brute_force(self):
        """Stop the password brute force simulation."""
        logger.info("Stop password brute force requested")
        if hasattr(self, 'pw_brute_force_thread') and self.pw_brute_force_thread is not None:
            logger.info("Stopping brute force thread...")
            try:
                # Request the thread to stop
                self.pw_brute_force_thread.stop()
                
                # Wait for the thread to finish with a timeout
                if self.pw_brute_force_thread.isRunning():
                    logger.info("Waiting for brute force thread to finish...")
                    if not self.pw_brute_force_thread.wait(2000):  # Wait up to 2 seconds
                        logger.warning("Thread did not stop gracefully, terminating...")
                        self.pw_brute_force_thread.terminate()
                        self.pw_brute_force_thread.wait(1000)  # Give it a moment to terminate
                
                # Clean up the thread
                self.pw_brute_force_thread.quit()
                self.pw_brute_force_thread = None
                logger.info("Brute force thread stopped and cleaned up")
                
            except Exception as e:
                logger.error(f"Error stopping brute force thread: {str(e)}")
            finally:
                # Update UI state
                self.pw_brute_force_running = False
                self.pw_brute_force_button.setText("Start Brute Force")
                self.status_bar.showMessage("Password brute force simulation stopped", 3000)
        else:
            logger.warning("No active brute force thread to stop")
    
    def update_password_brute_force_ui(self, data):
        """Update the UI with password brute force progress."""
        logger.info("=== UI Update Received ===")
        logger.info(f"Received data: {data}")
        logger.info(f"Current thread: {threading.current_thread().name}")
        
        # Log the entire data dictionary for debugging
        for key, value in data.items():
            logger.info(f"  {key}: {value}")
            
        try:
            # Log the data we receive for debugging
            logger.info(f"Processing UI update for attempt {data.get('attempt', 'N/A')}")
            logger.info(f"Password: {data.get('password', 'N/A')}")
            logger.info(f"Status: {data.get('status', 'N/A')}")
            
            # Update log with password attempts
            if 'password' in data:
                attempt_num = data.get('attempt', 0)
                password = data['password']
                status = data.get('status', '')
                log_line = f"Attempt {attempt_num}: {password} - {status}"
                logger.info(f"Adding to log: {log_line}")
                self.pw_log.append(log_line)
                logger.debug(log_line)
                
                # Auto-scroll to bottom
                scrollbar = self.pw_log.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
                
            # Update status if provided
            if 'status' in data:
                status = data['status']
                self.pw_results_label.setText(f"Status: {status}")
                self.pw_log.append(f"Status: {status}")
                logger.info(f"Status: {status}")
            
            # Update progress information
            if 'attempt' in data and 'time_taken' in data:
                attempt = data['attempt']
                time_taken = max(0.1, data['time_taken'])  # Avoid division by zero
                password = data.get('password', '')
                
                # Calculate attempts per second
                attempts_per_second = attempt / time_taken
                
                # Update the results label
                status_text = (
                    f"Attempts: {attempt:,} | "
                    f"Current: {password} | "
                    f"Time: {time_taken:.1f}s | "
                    f"Speed: {attempts_per_second:,.1f} attempts/s"
                )
                self.pw_results_label.setText(status_text)
                
                # Update progress bar (0-100% based on length progress)
                if 'length' in data:
                    length = data['length']
                    min_len = data.get('min_length', 1)
                    max_len = data.get('max_length', 8)
                    if max_len > min_len:
                        progress = int(((length - min_len) / (max_len - min_len)) * 100)
                        self.pw_progress_bar.setValue(progress)
                
            # Force UI update
            QApplication.processEvents()
            
        except Exception as e:
            error_msg = f"Error updating UI: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.pw_log.append(f"ERROR: {error_msg}")
            QMessageBox.critical(self, "UI Update Error", error_msg)
    
    def password_brute_force_finished(self, result):
        """Handle completion of password brute force operation."""
        self.pw_brute_force_running = False
        self.pw_brute_force_button.setText("Start Brute Force")
        
        if result['found']:
            self.pw_results_label.setText(f"Found password: {result['password']} in {result['attempts']} attempts")
            self.status_bar.showMessage(f"Password found in {result['attempts']} attempts!", 5000)
        else:
            self.pw_results_label.setText("Password not found")
            self.status_bar.showMessage("Password not found", 3000)
    
    def create_http_auth_tab(self):
        """Create the HTTP Authentication testing tab."""
        self.http_auth_tab = QWidget()
        layout = QVBoxLayout()
        
        # URL input
        form_layout = QFormLayout()
        
        self.auth_url_input = QLineEdit("http://")
        form_layout.addRow("URL:", self.auth_url_input)
        
        # Username and password
        self.auth_username_input = QLineEdit()
        form_layout.addRow("Username:", self.auth_username_input)
        
        self.auth_password_input = QLineEdit()
        self.auth_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.auth_password_input)

        self.auth_verify_ssl_checkbox = QCheckBox("Verify SSL certificates")
        self.auth_verify_ssl_checkbox.setChecked(True)
        form_layout.addRow("SSL Verification:", self.auth_verify_ssl_checkbox)

        self.auth_timeout_input = QDoubleSpinBox()
        self.auth_timeout_input.setRange(1.0, 120.0)
        self.auth_timeout_input.setDecimals(1)
        self.auth_timeout_input.setSingleStep(1.0)
        self.auth_timeout_input.setValue(10.0)
        self.auth_timeout_input.setSuffix(" s")
        form_layout.addRow("Timeout:", self.auth_timeout_input)
        
        # Test button
        self.test_auth_button = QPushButton("Test Authentication")
        self.test_auth_button.clicked.connect(self.test_http_auth)
        form_layout.addRow("", self.test_auth_button)
        
        # Results
        self.auth_result_label = QLabel("")
        self.auth_result_label.setWordWrap(True)
        form_layout.addRow("Result:", self.auth_result_label)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        self.http_auth_tab.setLayout(layout)
    
    def update_password_strength(self):
        """Update the password strength indicator."""
        password = self.password_input.text()
        
        if not password:
            self.strength_bar.setValue(0)
            self.strength_label.setText("Enter a password to test its strength")
            self.suggestions_label.setText("")
            return
            
        result = self.authentication_tester.check_password_strength(password)
        
        self.strength_bar.setValue(result['score'])
        self.strength_label.setText(f"Strength: {result['strength']} ({result['score']}/100)")
        
        if result['suggestions']:
            self.suggestions_label.setText("• " + "\n• ".join(result['suggestions']))
        else:
            self.suggestions_label.setText("Great! This is a strong password.")
    
    def toggle_password_visibility(self):
        """Toggle password visibility."""
        if self.show_password_checkbox.isChecked():
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            
    def update_pin_strength(self):
        """Update the PIN strength indicator."""
        pin = self.pin_input.text()
        
        if not pin:
            self.pin_strength_bar.setValue(0)
            self.pin_strength_label.setText("Enter a PIN to test its strength")
            self.pin_details_label.setText("")
            self.pin_suggestions_label.setText("")
            return
            
        try:
            result = self.authentication_tester.check_pin_strength(pin)
            
            self.pin_strength_bar.setValue(int(result['score']))
            self.pin_strength_label.setText(f"Strength: {result['strength']} ({result['score']}/100)")
            
            # Set details
            details = []
            details.append(f"• Length: {result['length']} digits")
            details.append(f"• Unique digits: {result['unique_digits']}")
            details.append(f"• Sequential: {'Yes' if result['is_sequential'] else 'No'}")
            details.append(f"• Repeating pattern: {'Yes' if result['is_repeating'] else 'No'}")
            details.append(f"• Has keypad pattern: {'Yes' if result['has_pattern'] else 'No'}")
            details.append(f"• Common PIN: {'Yes' if result['is_common'] else 'No'}")
            
            self.pin_details_label.setText("\n".join(details))
            
            # Set suggestions
            if result['suggestions']:
                self.pin_suggestions_label.setText("• " + "\n• ".join(result['suggestions']))
            else:
                self.pin_suggestions_label.setText("Great! This is a strong PIN.")
                
            # Update progress bar color based on strength
            if result['score'] >= 80:
                self.set_progress_bar_style(self.pin_strength_bar, "#a6e3a1")  # Green
            elif result['score'] >= 60:
                self.set_progress_bar_style(self.pin_strength_bar, "#f9e2af")  # Yellow
            elif result['score'] >= 40:
                self.set_progress_bar_style(self.pin_strength_bar, "#f38ba8")  # Red
            else:
                self.set_progress_bar_style(self.pin_strength_bar, "#f38ba8")  # Red
                
        except ValueError as e:
            self.pin_strength_label.setText("Invalid PIN: " + str(e))
            self.pin_strength_bar.setValue(0)
            
    def set_progress_bar_style(self, progress_bar, color):
        """Set the progress bar color."""
        progress_bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
                width: 10px;
                margin: 0.5px;
            }}
        """)
        
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a URL")
            return
            
        if not username:
            QMessageBox.warning(self, "Error", "Please enter a username")
            return
            
        self.test_auth_button.setEnabled(False)
        self.test_auth_button.setText("Testing...")
        
        # Simulate network delay in a separate thread
        QTimer.singleShot(100, lambda: self._perform_auth_test(url, username, password))
    
    def _perform_auth_test(self, url, username, password):
        """Perform the actual authentication test."""
        result = self.authentication_tester.test_http_auth(url, username, password)
        
        self.test_auth_button.setEnabled(True)
        self.test_auth_button.setText("Test Authentication")
        
        if result['success']:
            self.auth_result_label.setText(
                f"✅ Authentication successful! (Status: {result['status_code']}, "
                f"Time: {result['time_taken']:.2f}s)"
            )
        else:
            if result['status_code'] == 401:
                self.auth_result_label.setText(
                    f"❌ Authentication failed: Invalid credentials (Status: 401)"
                )
            else:
                self.auth_result_label.setText(
                    f"❌ Authentication failed: {result.get('error', 'Unknown error')}"
                )
    
    def update_brute_force_ui(self, data):
        """Update the UI with brute force progress."""
        self.bf_log.append(f"Attempt {data['attempt']}: Trying {data['pin']} - {data['status']}")
        self.bf_progress_bar.setValue(min(100, int((data['attempt'] / self.max_attempts_input.value()) * 100)))
        self.bf_progress_bar.setFormat(f"{data['attempt']}/{self.max_attempts_input} attempts ({data['time_taken']:.1f}s)")
        
        if data.get('found', False):
            self.bf_results_label.setText(
                f"✅ Found PIN: {data['pin']} after {data['attempt']} attempts "
                f"in {data['time_taken']:.2f} seconds"
            )
    
    def brute_force_finished(self, result):
        """Handle completion of brute force operation."""
        self.bf_running = False
        self.brute_force_button.setText("Start Brute Force")
        self.bf_progress_bar.setValue(100)
        
        if result['was_stopped']:
            self.bf_log.append("Brute force stopped by user")
            self.bf_results_label.setText("Brute force stopped by user")
        elif result['found']:
            self.bf_log.append(f"✅ Found PIN: {result['pin']}")
            self.bf_results_label.setText(
                f"✅ Found PIN: {result['pin']} after {result['attempts']} attempts "
                f"in {result['time_taken']:.2f} seconds"
            )
        else:
            self.bf_log.append("❌ PIN not found (reached max attempts)")
            self.bf_results_label.setText(
                f"❌ PIN not found after {result['attempts']} attempts "
                f"in {result['time_taken']:.2f} seconds"
            )
    
    def toggle_brute_force(self):
        """Toggle the brute force simulation on/off."""
        if self.bf_running:
            self.stop_brute_force()
        else:
            self.start_brute_force()
    
    def start_brute_force(self):
        """Start the brute force simulation."""
        target_pin = self.target_pin_input.text().strip()
        if not target_pin or not target_pin.isdigit():
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid numeric PIN")
            return
            
        max_attempts = self.max_attempts_input.value()
        delay = self.delay_input.value()
        
        # Clear previous results
        self.bf_log.clear()
        self.bf_results_label.clear()
        self.bf_progress_bar.setValue(0)
        
        # Create and start the brute force thread
        self.bf_thread = BruteForceThread(target_pin, max_attempts, delay)
        self.bf_thread.update_signal.connect(self.update_brute_force_ui)
        self.bf_thread.finished_signal.connect(self.brute_force_finished)
        
        self.bf_running = True
        self.brute_force_button.setText("Stop Brute Force")
        self.bf_thread.start()
        self.bf_log.append(f"Starting brute force attack on PIN: {target_pin}")
        self.statusBar().showMessage("Brute force simulation started...", 3000)
    
    def stop_brute_force(self):
        """Stop the brute force simulation."""
        if self.bf_thread and self.bf_thread.isRunning():
            self.bf_thread.stop()
            self.bf_running = False
            self.brute_force_button.setText("Start Brute Force")
            self.statusBar().showMessage("Brute force stopped by user", 3000)
    
    def test_http_auth(self):
        """Handle HTTP authentication test button click."""
        url = self.auth_url_input.text().strip()
        username = self.auth_username_input.text().strip()
        password = self.auth_password_input.text()
        verify_ssl = self.auth_verify_ssl_checkbox.isChecked()
        timeout = self.auth_timeout_input.value()
        
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a URL")
            return
            
        if not username:
            QMessageBox.warning(self, "Error", "Please enter a username")
            return
            
        # Disable the button while testing
        self.test_auth_button.setEnabled(False)
        self.test_auth_button.setText("Testing...")
        self.auth_result_label.setText("Testing authentication...")
        
        # Use a timer to prevent UI freeze
        QTimer.singleShot(
            100,
            lambda: self._perform_http_auth_test(
                url,
                username,
                password,
                verify_ssl,
                timeout
            )
        )
    
    def _perform_http_auth_test(self, url, username, password, verify_ssl, timeout):
        """Perform the actual HTTP authentication test."""
        try:
            result = self.authentication_tester.test_http_auth(
                url,
                username,
                password,
                verify_ssl=verify_ssl,
                timeout=timeout
            )
                
            # Update UI with results
            if result['success']:
                self.auth_result_label.setText(
                    f"✅ Authentication successful! (Status: {result['status_code']}, "
                    f"Time: {result['time_taken']:.2f}s)"
                )
            else:
                error_detail = result.get('error') or "Authentication failed"
                status_code = result.get('status_code')
                if status_code:
                    message = (
                        f"❌ Authentication failed: {error_detail} "
                        f"(Status: {status_code}, Time: {result['time_taken']:.2f}s)"
                    )
                else:
                    message = f"❌ Authentication failed: {error_detail}"
                self.auth_result_label.setText(
                    message
                )
                
        except Exception as e:
            self.auth_result_label.setText(f"❌ Error: {str(e)}")
            logger.error(f"HTTP Auth test failed: {str(e)}")
            
        finally:
            # Re-enable the button
            self.test_auth_button.setEnabled(True)
            self.test_auth_button.setText("Test Authentication")
    
    def apply_styles(self):
        """Apply consistent styling to the UI."""
        self.setStyleSheet("""
            QWidget {
                font-size: 13px;
                color: #cdd6f4;
                background-color: #1e1e2e;
            }
            QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 5px;
                color: #cdd6f4;
                min-height: 25px;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #74c7ec;
            }
            QPushButton:disabled {
                background-color: #45475a;
                color: #6c7086;
            }
            QProgressBar {
                border: 1px solid #45475a;
                border-radius: 4px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #a6e3a1;
                width: 10px;
            }
            QTabWidget::pane {
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 10px;
                margin-top: 5px;
            }
            QTabBar::tab {
                background: #313244;
                color: #cdd6f4;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid #45475a;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #45475a;
                border-bottom-color: #89b4fa;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
            QLabel {
                color: #cdd6f4;
            }
            QGroupBox {
                border: 1px solid #45475a;
                border-radius: 4px;
                margin-top: 1em;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

def main():
    """Main function to run the Authentication Testing tool as a standalone application."""
    if not GUI_ENABLED:
        print("GUI dependencies not available. Please install PySide6 to use the GUI.")
        return 1
        
    try:
        # Create the application
        app = QApplication(sys.argv)
        
        # Set application style
        app.setStyle('Fusion')
        
        # Create and show the main window
        window = AuthenticationTestingGUI()
        window.show()
        
        # Start the event loop
        return app.exec()
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    main()
