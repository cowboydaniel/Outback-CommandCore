#!/usr/bin/env python3
"""
BLACKSTORM - Secure Data Erasure & Forensic Suite
Forensic Tools Tab module.
"""
import os
import sys
import json
import time
import re
import hashlib
import subprocess
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QGroupBox, QTabWidget, QListWidget, QListWidgetItem, QComboBox,
    QCheckBox, QSpinBox, QFormLayout, QTextEdit, QLineEdit,
    QProgressBar, QMessageBox, QFileDialog, QGridLayout
)
from PySide6.QtCore import Qt, QThread, Signal

class DiskImagingWorker(QThread):
    """Worker thread for performing disk imaging operations."""
    progress = Signal(int, str)  # progress percentage, status message
    finished = Signal(bool, str)  # success, final message
    log_message = Signal(str)    # log message
    
    def __init__(self, source_device, output_path, verify=True, compress=False, 
                 split_size=0, hash_algorithm='sha256'):
        super().__init__()
        self.source_device = source_device
        self.output_path = output_path
        self.verify = verify
        self.compress = compress
        self.split_size = split_size  # in GB, 0 means no splitting
        self.hash_algorithm = hash_algorithm
        self._is_running = True
        self.log_file = '/var/log/blackstorm/imaging.log'
        
        # Create log directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def run(self):
        """Perform the disk imaging operation."""
        try:
            self._log_operation_start()
            
            # Validate source device
            if not os.path.exists(self.source_device):
                raise FileNotFoundError(f"Source device {self.source_device} not found")
            
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(self.output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # Get device size for progress tracking
            device_size = self._get_device_size()
            if device_size == 0:
                raise ValueError(f"Could not determine size of device {self.source_device}")
            
            # Prepare imaging command
            cmd = self._prepare_imaging_command(device_size)
            
            # Start the imaging process
            self._execute_imaging(cmd, device_size)
            
            # Verify the image if requested
            if self.verify and self._is_running:
                self._verify_image()
            
            if self._is_running:
                self.finished.emit(True, f"Successfully created image at {self.output_path}")
            
        except Exception as e:
            self.log_message.emit(f"Error: {str(e)}")
            self.finished.emit(False, f"Imaging failed: {str(e)}")
        finally:
            self._cleanup()
    
    def _log_operation_start(self):
        """Log the start of the imaging operation."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] Starting disk imaging of {self.source_device} to {self.output_path}"
        self._write_to_log(log_entry)
        self.log_message.emit(log_entry)
    
    def _get_device_size(self):
        """Get the size of the source device in bytes."""
        try:
            result = subprocess.run(
                ['blockdev', '--getsize64', self.source_device],
                capture_output=True, text=True, check=True
            )
            return int(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            self.log_message.emit(f"Warning: Could not get device size: {e.stderr}")
            return 0
    
    def _prepare_imaging_command(self, device_size):
        """Prepare the dd command for imaging."""
        # Base dd command
        cmd = ['dd']
        
        # Add input file
        cmd.extend(['if=' + self.source_device])
        
        # Add output file
        if self.compress:
            # Use gzip for compression
            cmd.extend(['|', 'gzip', '>', self.output_path + '.gz'])
        else:
            cmd.extend(['of=' + self.output_path])
        
        # Add block size for better performance
        cmd.extend(['bs=4M'])
        
        # Add status=progress for progress tracking
        cmd.extend(['status=progress'])
        
        return ' '.join(cmd)
    
    def _execute_imaging(self, cmd, device_size):
        """Execute the imaging command and track progress."""
        self.log_message.emit(f"Starting imaging with command: {cmd}")
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Track progress
        bytes_copied = 0
        progress_pattern = re.compile(r'(\d+) bytes \(.*\) copied')
        
        while True:
            if not self._is_running:
                process.terminate()
                raise Exception("Imaging cancelled by user")
            
            # Read output line by line
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
                
            if line:
                self.log_message.emit(line.strip())
                
                # Extract progress information
                match = progress_pattern.search(line)
                if match:
                    bytes_copied = int(match.group(1))
                    progress = (bytes_copied / device_size) * 100
                    self.progress.emit(int(progress), f"Imaging: {progress:.1f}%")
        
        # Check return code
        if process.returncode != 0:
            raise Exception(f"dd command failed with return code {process.returncode}")
    
    def _verify_image(self):
        """Verify the integrity of the created image."""
        self.log_message.emit("Verifying image integrity...")
        self.progress.emit(0, "Verifying image")
        
        # Get hashes of source and destination
        source_hash = self._calculate_hash(self.source_device)
        dest_hash = self._calculate_hash(self.output_path + ('.gz' if self.compress else ''))
        
        if source_hash == dest_hash:
            self.log_message.emit("Image verification successful")
        else:
            raise Exception("Image verification failed: hashes do not match")
    
    def _calculate_hash(self, file_path):
        """Calculate hash of a file or device."""
        hash_obj = hashlib.new(self.hash_algorithm)
        block_size = 65536  # 64KB chunks
        
        try:
            with open(file_path, 'rb') as f:
                while self._is_running:
                    data = f.read(block_size)
                    if not data:
                        break
                    hash_obj.update(data)
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            raise Exception(f"Failed to calculate {self.hash_algorithm} hash: {str(e)}")
    
    def _write_to_log(self, message):
        """Write a message to the log file."""
        try:
            with open(self.log_file, 'a') as f:
                f.write(message + '\n')
        except Exception as e:
            self.log_message.emit(f"Warning: Failed to write to log file: {str(e)}")
    
    def _cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'process') and self.process.poll() is None:
            self.process.terminate()
    
    def stop(self):
        """Stop the imaging operation."""
        self._is_running = False
        self._cleanup()

class UnifiedAcquisitionWorker(QThread):
    """Worker thread for performing adaptive disk acquisition with recovery capabilities."""
    progress = Signal(int, str)  # progress percentage, status message
    log_message = Signal(str)    # log message
    stats_update = Signal(dict)  # statistics update
    mode_changed = Signal(int, str)  # new mode index, reason for change
    finished = Signal(bool, str, dict)  # success, message, final stats
    
    def __init__(self, source_device, output_path, options):
        super().__init__()
        self.source_device = source_device
        self.output_path = output_path
        self.options = options
        self._is_running = True
        
        # Initialize recovery state
        self.current_mode = options['starting_mode']
        self.stats = {
            'total_size': 0,
            'recovered': 0,
            'bad_sectors': 0,
            'retry_sectors': 0,
            'recovery_rate': 100.0,
            'elapsed_time': 0,
            'current_phase': 0,
            'total_phases': 1
        }
        
        # Create log directory
        log_dir = '/var/log/blackstorm/acquisition'
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize log file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        device_name = os.path.basename(source_device)
        self.log_file = f"{log_dir}/acquisition_{device_name}_{timestamp}.log"
        self.bad_sectors_file = f"{log_dir}/badsectors_{device_name}_{timestamp}.txt"
    
    def run(self):
        """Execute the acquisition process with adaptive recovery."""
        start_time = time.time()
        success = False
        message = ""
        
        try:
            # Log start of operation
            self._log_message(f"Starting acquisition of {self.source_device} to {self.output_path}")
            self._log_message(f"Initial mode: {self.current_mode} ({self._get_mode_name()})")
            
            # Get device size
            self.stats['total_size'] = self._get_device_size()
            if self.stats['total_size'] == 0:
                raise ValueError(f"Could not determine size of device {self.source_device}")
            
            self._log_message(f"Device size: {self.stats['total_size'] / (1024**3):.2f} GB")
            
            # Create output directory if needed
            output_dir = os.path.dirname(self.output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # Start acquisition with initial mode
            self._log_message("Starting initial acquisition phase")
            initial_success = self._acquire_with_current_mode()
            
            # Check recovery rate and adapt if needed
            if initial_success and self.stats['recovery_rate'] == 100.0:
                success = True
                message = "Acquisition completed successfully"
            elif self.options['auto_mode']:
                # Perform progressive recovery
                success = self._perform_progressive_recovery()
                if success:
                    message = f"Acquisition completed with recovery (Rate: {self.stats['recovery_rate']:.2f}%)"
                else:
                    message = f"Acquisition failed to recover all data (Rate: {self.stats['recovery_rate']:.2f}%)"
            else:
                # Single mode only
                success = initial_success
                if success:
                    message = f"Acquisition completed with recovery rate: {self.stats['recovery_rate']:.2f}%"
                else:
                    message = "Acquisition failed in fixed mode"
            
            # Perform verification if requested and successful
            if success and self.options['verify']:
                verify_success = self._verify_image()
                if not verify_success:
                    success = False
                    message = "Verification failed, image may be corrupted"
            
        except Exception as e:
            success = False
            message = str(e)
            self._log_message(f"Error during acquisition: {message}")
        finally:
            # Calculate total elapsed time
            self.stats['elapsed_time'] = time.time() - start_time
            
            # Log completion
            elapsed_str = self._format_time(self.stats['elapsed_time'])
            self._log_message(f"Acquisition {('completed' if success else 'failed')}: {message}")
            self._log_message(f"Total time: {elapsed_str}")
            self._log_message(f"Recovery rate: {self.stats['recovery_rate']:.2f}%")
            
            # Emit final signal
            self.finished.emit(success, message, self.stats.copy())
    
    def _get_mode_name(self):
        """Get the name of the current mode."""
        mode_names = [
            "Standard",
            "Light Recovery",
            "Aggressive Recovery",
            "Deep Recovery",
            "Forensic Recovery"
        ]
        return mode_names[min(self.current_mode, len(mode_names) - 1)]
    
    def _get_device_size(self):
        """Get the size of the source device in bytes."""
        try:
            result = subprocess.run(
                ['blockdev', '--getsize64', self.source_device],
                capture_output=True, text=True, check=True
            )
            return int(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            self._log_message(f"Warning: Could not get device size: {e.stderr}")
            return 0
    
    def _log_message(self, message):
        """Log a message to both the UI and the log file."""
        # Emit to UI
        self.log_message.emit(message)
        
        # Write to log file
        try:
            with open(self.log_file, 'a') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            self.log_message.emit(f"Warning: Failed to write to log file: {str(e)}")
    
    def _update_stats(self):
        """Update statistics and emit update signal."""
        # Calculate recovery rate
        if self.stats['total_size'] > 0:
            self.stats['recovery_rate'] = (self.stats['recovered'] / self.stats['total_size']) * 100.0
        
        # Emit stats update
        self.stats_update.emit(self.stats.copy())
    
    def _format_time(self, seconds):
        """Format time in seconds to a readable string."""
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    
    def _check_for_mode_progression(self):
        """Check if we need to progress to a more aggressive recovery mode."""
        if not self.options['auto_mode'] or self.current_mode >= 4:
            return False
            
        # Decision logic based on recovery statistics
        progress_needed = False
        reason = ""
        
        # Check recovery rate thresholds
        if self.stats['recovery_rate'] < 99.9 and self.current_mode == 0:
            progress_needed = True
            reason = "Minor read errors detected"
        elif self.stats['recovery_rate'] < 98.0 and self.current_mode <= 1:
            progress_needed = True
            reason = "Multiple read errors detected"
        elif self.stats['recovery_rate'] < 95.0 and self.current_mode <= 2:
            progress_needed = True
            reason = "Significant data loss detected"
        elif self.stats['recovery_rate'] < 90.0 and self.current_mode <= 3:
            progress_needed = True
            reason = "Critical data loss detected"
            
        # Check bad sector count thresholds
        if self.stats['bad_sectors'] > 100 and self.current_mode <= 1:
            progress_needed = True
            reason = "High number of bad sectors detected"
        elif self.stats['bad_sectors'] > 1000 and self.current_mode <= 2:
            progress_needed = True
            reason = "Very high number of bad sectors detected"
        elif self.stats['bad_sectors'] > 10000 and self.current_mode <= 3:
            progress_needed = True
            reason = "Extreme number of bad sectors detected"
            
        if progress_needed:
            self.current_mode += 1
            self._log_message(f"Progressing to mode {self.current_mode} ({self._get_mode_name()})")
            self._log_message(f"Reason: {reason}")
            self.mode_changed.emit(self.current_mode, reason)
            return True
            
        return False
    
    def _acquire_with_current_mode(self):
        """Perform acquisition using the current mode settings."""
        mode = self.current_mode
        
        # Configure command based on mode
        if mode == 0:  # Standard mode
            return self._standard_acquisition()
        elif mode == 1:  # Light Recovery
            return self._light_recovery()
        elif mode == 2:  # Aggressive Recovery
            return self._aggressive_recovery()
        elif mode == 3:  # Deep Recovery
            return self._deep_recovery()
        elif mode == 4:  # Forensic Recovery
            return self._forensic_recovery()
        else:
            self._log_message(f"Unknown mode: {mode}")
            return False
    
    def _standard_acquisition(self):
        """Perform standard acquisition (healthy drive)."""
        self._log_message("Using standard acquisition mode (healthy drive)")
        
        # Configure dd command
        block_size = "4M"  # Efficient for healthy drives
        cmd = [
            'dd', f'if={self.source_device}', f'of={self.output_path}',
            f'bs={block_size}', 'status=progress', 'conv=noerror,sync'
        ]
        
        # Add compression if requested
        if self.options['compress']:
            output_gz = f"{self.output_path}.gz"
            cmd = [
                'dd', f'if={self.source_device}', 'bs=4M', 'status=progress',
                '|', 'gzip', f'> {output_gz}'
            ]
            cmd = ' '.join(cmd)
        else:
            cmd = ' '.join(cmd)
        
        self._log_message(f"Command: {cmd}")
        
        try:
            # Start process
            process = subprocess.Popen(
                cmd, shell=True, executable='/bin/bash',
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Track progress
            total_size = self.stats['total_size']
            pattern = re.compile(r'(\d+) bytes \(.*\) copied')
            
            while process.poll() is None and self._is_running:
                line = process.stdout.readline()
                if not line:
                    continue
                
                # Log output
                self._log_message(line.strip())
                
                # Parse progress
                match = pattern.search(line)
                if match:
                    bytes_copied = int(match.group(1))
                    self.stats['recovered'] = bytes_copied
                    self._update_stats()
                    
                    # Update progress
                    percent = min(99, int((bytes_copied / total_size) * 100))
                    self.progress.emit(percent, f"Acquiring: {percent}%")
            
            # Check result
            if not self._is_running:
                self._log_message("Acquisition stopped by user")
                return False
                
            if process.returncode != 0:
                self._log_message(f"dd command failed with return code {process.returncode}")
                # Even partial acquisition should be processed
                return False
            
            # Calculate final stats
            self.stats['recovered'] = total_size  # Assume full recovery for standard mode
            self.stats['recovery_rate'] = 100.0
            self._update_stats()
            
            return True
            
        except Exception as e:
            self._log_message(f"Error in standard acquisition: {str(e)}")
            return False
    
    def _light_recovery(self):
        """Perform light recovery for drives with minor issues."""
        self._log_message("Using light recovery mode")
        
        # Use ddrescue with basic settings
        output_map = f"{self.output_path}.map"
        
        # Configure ddrescue command
        cmd = [
            'ddrescue', '-d', '-n',  # Direct disk access, no scraping
            '-b', str(self.options['block_size']),
            self.source_device, self.output_path, output_map
        ]
        
        if not self._run_ddrescue(cmd, output_map):
            return False
            
        # Run a second pass if recovery wasn't perfect
        if self.stats['recovery_rate'] < 99.99 and self._is_running:
            self._log_message("Running second pass to recover remaining blocks")
            
            cmd = [
                'ddrescue', '-d', '-r3',  # Direct access, 3 retries
                '-b', str(self.options['block_size']),
                self.source_device, self.output_path, output_map
            ]
            
            return self._run_ddrescue(cmd, output_map)
        
        return True
    
    def _aggressive_recovery(self):
        """Perform aggressive recovery for drives with moderate issues."""
        self._log_message("Using aggressive recovery mode")
        
        # Use multi-pass ddrescue with more retries
        output_map = f"{self.output_path}.map"
        
        # First pass - quick scan
        cmd = [
            'ddrescue', '-d', '-n',
            '-b', str(self.options['block_size']),
            self.source_device, self.output_path, output_map
        ]
        
        if not self._run_ddrescue(cmd, output_map):
            return False
            
        # Second pass - retry bad sectors
        if self.stats['recovery_rate'] < 99.99 and self._is_running:
            self._log_message("Running retry pass with reduced block size")
            
            cmd = [
                'ddrescue', '-d', '-r3',
                '-b', str(int(self.options['block_size'] / 2)),  # Half block size
                self.source_device, self.output_path, output_map
            ]
            
            if not self._run_ddrescue(cmd, output_map):
                return False
        
        # Third pass - scrape mode for stubborn sectors
        if self.stats['recovery_rate'] < 99.5 and self._is_running:
            self._log_message("Running scrape pass for stubborn sectors")
            
            cmd = [
                'ddrescue', '-d', '-r2', '-s',  # Scrape mode
                self.source_device, self.output_path, output_map
            ]
            
            return self._run_ddrescue(cmd, output_map)
        
        return True
    
    def _deep_recovery(self):
        """Perform deep recovery for drives with severe issues."""
        self._log_message("Using deep recovery mode")
        
        # Use advanced ddrescue techniques with reverse direction
        output_map = f"{self.output_path}.map"
        
        # First pass - quick scan
        cmd = [
            'ddrescue', '-d', '-n',
            '-b', str(self.options['block_size']),
            self.source_device, self.output_path, output_map
        ]
        
        if not self._run_ddrescue(cmd, output_map):
            return False
            
        # Second pass - retry with smaller blocks
        if self.stats['recovery_rate'] < 99.99 and self._is_running:
            self._log_message("Running retry pass with smaller blocks")
            
            cmd = [
                'ddrescue', '-d', '-r3',
                '-b', str(int(self.options['block_size'] / 4)),  # Quarter block size
                self.source_device, self.output_path, output_map
            ]
            
            if not self._run_ddrescue(cmd, output_map):
                return False
        
        # Third pass - reverse direction
        if self.stats['recovery_rate'] < 99.5 and self._is_running:
            self._log_message("Running pass in reverse direction")
            
            cmd = [
                'ddrescue', '-d', '-r3', '-R',  # Reverse direction
                self.source_device, self.output_path, output_map
            ]
            
            if not self._run_ddrescue(cmd, output_map):
                return False
        
        # Fourth pass - scrape mode with very small blocks
        if self.stats['recovery_rate'] < 99.0 and self._is_running:
            self._log_message("Running final scrape pass with very small blocks")
            
            cmd = [
                'ddrescue', '-d', '-r5', '-s', 
                '-b', '512',  # Smallest possible block size
                self.source_device, self.output_path, output_map
            ]
            
            return self._run_ddrescue(cmd, output_map)
        
        return True
    
    def _forensic_recovery(self):
        """Perform forensic recovery for drives with critical failure."""
        self._log_message("Using forensic recovery mode (critical drive)")
        
        # Use specialized techniques for severely damaged drives
        output_map = f"{self.output_path}.map"
        
        # First pass - direct access disabled (important for damaged drives)
        cmd = [
            'ddrescue', '-n',  # No direct access
            '-b', '4096',     # Small block size
            '-c', '64',       # Cluster size
            self.source_device, self.output_path, output_map
        ]
        
        if not self._run_ddrescue(cmd, output_map):
            return False
            
        # Multiple passes with different approaches
        if self._is_running:
            passes = [
                # Second pass - retry errors with smaller blocks
                ['ddrescue', '-r3', '-b', '1024', '-c', '16', 
                 self.source_device, self.output_path, output_map],
                
                # Third pass - try with direct mode
                ['ddrescue', '-d', '-r3', 
                 self.source_device, self.output_path, output_map],
                
                # Fourth pass - trim mode (for partially failed sectors)
                ['ddrescue', '-d', '-r2', '-t', 
                 self.source_device, self.output_path, output_map],
                
                # Fifth pass - reverse direction with scraping
                ['ddrescue', '-r5', '-s', '-R', 
                 self.source_device, self.output_path, output_map],
                
                # Final pass - byte by byte for critical areas
                ['ddrescue', '-d', '-r7', '-b', '512', '-s', 
                 self.source_device, self.output_path, output_map]
            ]
            
            self.stats['total_phases'] = len(passes) + 1  # +1 for initial pass
            
            for i, cmd in enumerate(passes):
                if not self._is_running:
                    return False
                    
                if self.stats['recovery_rate'] >= 99.99:
                    self._log_message("Recovery complete, skipping remaining passes")
                    break
                    
                self.stats['current_phase'] = i + 2  # +2 because initial pass is 1
                self._log_message(f"Running recovery pass {i+2}/{self.stats['total_phases']}")
                
                if not self._run_ddrescue(cmd, output_map):
                    return False
        
        # Final attempt with custom DC3DD for any remaining sectors
        if self.stats['recovery_rate'] < 99.0 and self._is_running:
            self._log_message("Attempting final recovery with DC3DD for remaining sectors")
            
            # Extract bad sector list from ddrescue map
            bad_sectors = self._extract_bad_sectors_from_map(output_map)
            
            if bad_sectors and len(bad_sectors) > 0:
                # Targeted recovery of specific sectors
                return self._targeted_sector_recovery(bad_sectors)
        
        # Return success even with partial recovery
        return True
    
    def _run_ddrescue(self, cmd, map_file):
        """Run ddrescue command and parse output for progress and stats."""
        try:
            self._log_message(f"Running: {' '.join(cmd)}")
            
            # Start process
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Track progress
            progress_pattern = re.compile(r'rescued:\s+(\d+)B.*errsize:\s+(\d+)B')
            
            while process.poll() is None and self._is_running:
                line = process.stdout.readline()
                if not line:
                    continue
                
                # Check for progress updates
                match = progress_pattern.search(line)
                if match:
                    rescued = self._parse_size(match.group(1))
                    errors = self._parse_size(match.group(2))
                    
                    # Update stats
                    self.stats['recovered'] = rescued
                    self.stats['bad_sectors'] = errors // 512  # Estimate bad sectors
                    self._update_stats()
                    
                    # Update progress
                    if self.stats['total_size'] > 0:
                        percent = min(99, int((rescued / self.stats['total_size']) * 100))
                        phase_info = ""
                        if self.stats['total_phases'] > 1:
                            phase_info = f" (Phase {self.stats['current_phase']}/{self.stats['total_phases']})"
                        
                        self.progress.emit(percent, f"Recovering: {percent}%{phase_info}")
            
            # Check result
            if not self._is_running:
                self._log_message("Recovery stopped by user")
                return False
                
            if process.returncode != 0:
                self._log_message(f"ddrescue failed with return code {process.returncode}")
                return False
            
            # Parse final stats from map file
            self._parse_ddrescue_map(map_file)
            
            return True
            
        except Exception as e:
            self._log_message(f"Error in ddrescue: {str(e)}")
            return False
    
    def _parse_size(self, size_str):
        """Parse size string with unit (e.g., '100kB') to bytes."""
        if not size_str:
            return 0
            
        # Remove trailing 'B' and handle units
        size_str = size_str.strip()
        
        # Split number and unit
        match = re.match(r'(\d+)(?:\.\d+)?([kMGT])?', size_str)
        if not match:
            return 0
            
        value = float(match.group(1))
        unit = match.group(2)
        
        # Convert to bytes
        if unit == 'k':
            return int(value * 1024)
        elif unit == 'M':
            return int(value * 1024 * 1024)
        elif unit == 'G':
            return int(value * 1024 * 1024 * 1024)
        elif unit == 'T':
            return int(value * 1024 * 1024 * 1024 * 1024)
        else:
            return int(value)
    
    def _parse_ddrescue_map(self, map_file):
        """Parse ddrescue map file to update statistics."""
        try:
            with open(map_file, 'r') as f:
                content = f.read()
                
            # Look for the summary line
            summary_match = re.search(r'rescued:\s+(\d+)B.*errsize:\s+(\d+)B', content)
            if summary_match:
                rescued = self._parse_size(summary_match.group(1))
                errors = self._parse_size(summary_match.group(2))
                
                self.stats['recovered'] = rescued
                self.stats['bad_sectors'] = errors // 512
                self._update_stats()
                
                # Log bad sectors if needed
                if self.options['log_bad_sectors'] and self.stats['bad_sectors'] > 0:
                    self._extract_bad_sectors_from_map(map_file, save_to_file=True)
        except Exception as e:
            self._log_message(f"Error parsing ddrescue map: {str(e)}")
    
    def _extract_bad_sectors_from_map(self, map_file, save_to_file=False):
        """Extract list of bad sectors from ddrescue map file."""
        bad_sectors = []
        
        try:
            with open(map_file, 'r') as f:
                lines = f.readlines()
                
            # Skip header lines
            data_lines = [l for l in lines if not l.startswith('#')]
            
            # Parse sector information
            for line in data_lines:
                parts = line.strip().split()
                if len(parts) >= 3 and parts[2] in ['?', '*', '/']:
                    # This is a bad/unreadable sector
                    pos = int(parts[0], 16)  # Position is in hex
                    size = int(parts[1], 16)  # Size is in hex
                    
                    # Convert to sector numbers (assuming 512-byte sectors)
                    start_sector = pos // 512
                    end_sector = (pos + size - 1) // 512
                    
                    # Add range to list
                    bad_sectors.append((start_sector, end_sector))
            
            # Save to file if requested
            if save_to_file and bad_sectors:
                with open(self.bad_sectors_file, 'w') as f:
                    f.write(f"# Bad sectors for {self.source_device}\n")
                    f.write(f"# Extracted on {datetime.now()}\n")
                    f.write("# Format: start_sector end_sector size_in_sectors\n")
                    
                    for start, end in bad_sectors:
                        f.write(f"{start} {end} {end-start+1}\n")
                
                self._log_message(f"Saved {len(bad_sectors)} bad sector ranges to {self.bad_sectors_file}")
                
            return bad_sectors
                
        except Exception as e:
            self._log_message(f"Error extracting bad sectors: {str(e)}")
            return []
    
    def _targeted_sector_recovery(self, bad_sectors):
        """Perform targeted recovery of specific bad sectors."""
        try:
            recovered_sectors = 0
            total_sectors = sum(end - start + 1 for start, end in bad_sectors)
            
            self._log_message(f"Attempting targeted recovery of {total_sectors} sectors")
            
            for i, (start, end) in enumerate(bad_sectors):
                if not self._is_running:
                    return False
                    
                # Update progress
                percent = min(99, int((i / len(bad_sectors)) * 100))
                self.progress.emit(percent, f"Targeted recovery: {percent}%")
                
                # Calculate offset and size
                offset = start * 512
                size = (end - start + 1) * 512
                
                # Try dc3dd for this sector range
                cmd = [
                    'dc3dd', f'if={self.source_device}', f'of={self.output_path}',
                    f'bs=512', f'count={end-start+1}', f'skip={start}', f'seek={start}',
                    'mlog=-', 'hlog=-', 'verb=on', 'noerror'
                ]
                
                self._log_message(f"Recovering sectors {start}-{end}")
                
                result = subprocess.run(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                # Check if sectors were recovered
                if "errors=0" in result.stdout:
                    recovered_sectors += (end - start + 1)
                    self._log_message(f"Successfully recovered sectors {start}-{end}")
                
                # Update stats
                self.stats['retry_sectors'] += (end - start + 1)
                
                # Recalculate recovery rate
                if total_sectors > 0:
                    recovery_improvement = (recovered_sectors / total_sectors) * (self.stats['bad_sectors'] / (self.stats['total_size'] / 512))
                    self.stats['recovery_rate'] = min(100.0, 100.0 - ((self.stats['bad_sectors'] - recovered_sectors) / (self.stats['total_size'] / 512)) * 100)
                    self._update_stats()
            
            self._log_message(f"Targeted recovery complete: {recovered_sectors}/{total_sectors} sectors recovered")
            return True
            
        except Exception as e:
            self._log_message(f"Error in targeted recovery: {str(e)}")
            return False
    
    def _perform_progressive_recovery(self):
        """Perform progressive recovery, escalating through modes as needed."""
        self._log_message("Starting progressive recovery")
        
        while self.current_mode < 4 and self.stats['recovery_rate'] < 99.99 and self._is_running:
            # Progress to next mode
            self.current_mode += 1
            self._log_message(f"Progressing to mode {self.current_mode} ({self._get_mode_name()})")
            
            reason = f"Recovery rate is {self.stats['recovery_rate']:.2f}%, attempting more aggressive recovery"
            self.mode_changed.emit(self.current_mode, reason)
            
            # Execute with new mode
            success = self._acquire_with_current_mode()
            if not success:
                self._log_message(f"Recovery failed in mode {self.current_mode}")
                # Continue to next mode even on failure
        
        # Return success if recovery rate is acceptable or we've tried all modes
        return self.stats['recovery_rate'] > 90.0
    
    def _verify_image(self):
        """Verify the acquired image."""
        self._log_message("Verifying image integrity")
        self.progress.emit(99, "Verifying image")
        
        try:
            # Skip verification for compressed images
            if self.options['compress'] and self.output_path.endswith('.gz'):
                self._log_message("Skipping verification for compressed image")
                return True
                
            # Calculate hash for readable portions only
            if self.stats['bad_sectors'] > 0:
                self._log_message("Image contains bad sectors, verifying readable portions only")
                
                # Use hash algorithms specified in options
                for hash_algo in self.options['hash_algorithms']:
                    # Calculate hash
                    cmd = f"md5sum {self.output_path}"
                    if hash_algo == 'sha1':
                        cmd = f"sha1sum {self.output_path}"
                    elif hash_algo == 'sha256':
                        cmd = f"sha256sum {self.output_path}"
                        
                    result = subprocess.run(
                        cmd, shell=True, capture_output=True, text=True
                    )
                    
                    if result.returncode == 0:
                        hash_value = result.stdout.split()[0]
                        self._log_message(f"{hash_algo.upper()} hash: {hash_value}")
                        
                        # Write hash to file
                        with open(f"{self.output_path}.{hash_algo}", 'w') as f:
                            f.write(hash_value)
                
                # For partial images, use file size as basic verification
                expected_size = self.stats['total_size'] - (self.stats['bad_sectors'] * 512)
                actual_size = os.path.getsize(self.output_path)
                
                size_diff = abs(actual_size - expected_size)
                if size_diff > 1024*1024:  # Allow 1MB difference
                    self._log_message(f"Warning: Image size mismatch - expected ~{expected_size}, got {actual_size}")
                    return False
                    
                return True
            else:
                # For complete images, compare with source
                self._log_message("Performing full verification")
                
                # Calculate and save hash
                for hash_algo in self.options['hash_algorithms']:
                    self._log_message(f"Calculating {hash_algo.upper()} hash")
                    
                    hash_cmd = f"md5sum"
                    if hash_algo == 'sha1':
                        hash_cmd = f"sha1sum"
                    elif hash_algo == 'sha256':
                        hash_cmd = f"sha256sum"
                    
                    # Source hash
                    src_result = subprocess.run(
                        f"{hash_cmd} {self.source_device}",
                        shell=True, capture_output=True, text=True
                    )
                    
                    # Destination hash
                    dst_result = subprocess.run(
                        f"{hash_cmd} {self.output_path}",
                        shell=True, capture_output=True, text=True
                    )
                    
                    if src_result.returncode == 0 and dst_result.returncode == 0:
                        src_hash = src_result.stdout.split()[0]
                        dst_hash = dst_result.stdout.split()[0]
                        
                        self._log_message(f"Source {hash_algo.upper()}: {src_hash}")
                        self._log_message(f"Image {hash_algo.upper()}: {dst_hash}")
                        
                        # Write hash to file
                        with open(f"{self.output_path}.{hash_algo}", 'w') as f:
                            f.write(dst_hash)
                        
                        if src_hash != dst_hash:
                            self._log_message(f"Warning: {hash_algo.upper()} hash mismatch")
                            return False
                
                return True
                
        except Exception as e:
            self._log_message(f"Error during verification: {str(e)}")
            return False
    
    def stop(self):
        """Stop the acquisition process."""
        self._is_running = False
        self._log_message("Stopping acquisition...")

class ForensicToolsTab(QWidget):
    """Forensic Tools tab for BLACKSTORM application."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface for Forensic Tools tab."""
        layout = QVBoxLayout(self)
        
        # Create tab widget for sub-tabs
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Add the sub-tabs
        self.create_forensic_tools_tab()
    def check_device_health(self):
        """Checks the health status of the selected device and updates the UI."""
        selected_items = self.disk_device_list.selectedItems()
        if not selected_items:
            self.health_indicator.setText("No device selected")
            self.health_indicator.setStyleSheet("font-weight: bold; color: #89b4fa;")
            return
        
        device_path = selected_items[0].data(Qt.ItemDataRole.UserRole)
    
        # Log the check
        self.acquisition_log.append(f"Checking health of {device_path}...")
    
        try:
            # Use smartctl to get device health information
            if 'nvme' in device_path:
                # For NVMe devices, we need to get both health and error logs
                cmd = ['sudo', 'smartctl', '-x', '-j', device_path]
            else:
                cmd = ['sudo', 'smartctl', '-H', '-A', '-j', device_path]
            
            # Run smartctl with error handling
            self.acquisition_log.append(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Log the full command and output for debugging
            self.acquisition_log.append(f"Command: {' '.join(cmd)}")
            self.acquisition_log.append(f"Exit code: {result.returncode}")
            self.acquisition_log.append("=== STDOUT ===")
            self.acquisition_log.append(result.stdout[:500])  # First 500 chars of stdout
            self.acquisition_log.append("=== STDERR ===")
            self.acquisition_log.append(result.stderr.strip() or "(empty)")
            
            # Try to parse JSON output even if there was a non-zero exit code
            # as some NVMe drives return useful data even with an error
            try:
                # Parse JSON output
                smart_data = json.loads(result.stdout)
                
                # Check if there are any error messages in the JSON
                if 'smartctl' in smart_data and 'messages' in smart_data['smartctl']:
                    for msg in smart_data['smartctl']['messages']:
                        if msg.get('severity') == 'error':
                            self.acquisition_log.append(f"Warning: {msg.get('string', 'Unknown error')}")
                
                # Check if this is an NVMe device
                if 'nvme_smart_health_information_log' in smart_data:
                    # Handle NVMe specific health check
                    nvme_health = smart_data.get('nvme_smart_health_information_log', {})
                    
                    # Check critical warning flags
                    critical_warning = nvme_health.get('critical_warning', 0)
                    available_spare = nvme_health.get('available_spare', 0)
                    percentage_used = nvme_health.get('percentage_used', 0)
                    
                    issues = []
                    
                    if critical_warning & 0x1:  # Available spare space is below threshold
                        issues.append("Available spare space is below threshold")
                    if critical_warning & 0x2:  # Temperature is above threshold
                        issues.append("Temperature is above threshold")
                    if critical_warning & 0x4:  # Device reliability is degraded
                        issues.append("Device reliability is degraded")
                    if critical_warning & 0x8:  # Media is in read-only mode
                        issues.append("Media is in read-only mode")
                    if critical_warning & 0x10:  # Volatile memory backup failed
                        issues.append("Volatile memory backup failed")
                    
                    # Determine health status based on issues and thresholds
                    if critical_warning > 0 or available_spare < 10 or percentage_used > 80:
                        health = "Warning"
                        color = "#f9e2af"  # Yellow
                        if critical_warning > 0 or available_spare < 5 or percentage_used > 90:
                            health = "Critical"
                            color = "#f38ba8"  # Red
                    else:
                        health = "Healthy"
                        color = "#a6e3a1"  # Green
                        
                    # Log detailed NVMe health information
                    self.acquisition_log.append(f"NVMe Health Status: {health}")
                    self.acquisition_log.append(f"Available Spare: {available_spare}%")
                    self.acquisition_log.append(f"Percentage Used: {percentage_used}%")
                    self.acquisition_log.append(f"Temperature: {nvme_health.get('temperature', 'N/A')}°C")
                    
                    if issues:
                        self.acquisition_log.append("Health issues detected:")
                        for issue in issues:
                            self.acquisition_log.append(f"- {issue}")
                    
                    # Update the health indicator
                    self.health_indicator.setText(health)
                    self.health_indicator.setStyleSheet(f"font-weight: bold; color: {color};")
                    return
                
                # If we get here, it's not an NVMe device or we couldn't get NVMe health info
                if 'smart_status' in smart_data and 'passed' in smart_data['smart_status']:
                    if smart_data['smart_status']['passed']:
                        health = "Healthy"
                        color = "#a6e3a1"  # Green
                    else:
                        health = "Failed"
                        color = "#f38ba8"  # Red
                else:
                    health = "Unknown"
                    color = "#cba6f7"  # Purple
                
                # Update health indicator for non-NVMe devices
                self.health_indicator.setText(health)
                self.health_indicator.setStyleSheet(f"font-weight: bold; color: {color};")
                
            except json.JSONDecodeError as e:
                self.acquisition_log.append(f"Failed to parse smartctl output: {str(e)}")
                self.health_indicator.setText("Parse Error")
                self.health_indicator.setStyleSheet("font-weight: bold; color: #f38ba8;")
                return
                
            # For ATA/SATA devices, use the existing logic
            if 'smart_status' in smart_data and 'passed' in smart_data['smart_status']:
                if smart_data['smart_status']['passed']:
                    health = "Healthy"
                    color = "#a6e3a1"  # Green
                    
                    # Even for healthy drives, check for pending or reallocated sectors
                    pending_sectors = 0
                    reallocated_sectors = 0
                    
                    if 'ata_smart_attributes' in smart_data:
                        for attr in smart_data['ata_smart_attributes']['table']:
                            if attr['id'] == 5:  # Reallocated Sectors Count
                                reallocated_sectors = attr['raw']['value']
                            elif attr['id'] == 197:  # Current Pending Sector Count
                                pending_sectors = attr['raw']['value']
                                    
                        if pending_sectors > 0 or reallocated_sectors > 0:
                            health = "Warning"
                            color = "#f9e2af"  # Yellow
                    else:
                        health = "Failed"
                        color = "#f38ba8"  # Red
                else:
                    # Check for specific attributes that indicate health issues
                    health_score = 100
                    issues = []
                    
                    if 'ata_smart_attributes' in smart_data:
                        for attr in smart_data['ata_smart_attributes']['table']:
                            # Check critical attributes
                            if attr['id'] == 5:  # Reallocated Sectors Count
                                if attr['raw']['value'] > 0:
                                    health_score -= min(50, attr['raw']['value'])
                                    issues.append(f"Reallocated Sectors: {attr['raw']['value']}")
                            elif attr['id'] == 187:  # Reported Uncorrectable Errors
                                if attr['raw']['value'] > 0:
                                    health_score -= min(30, attr['raw']['value'] * 5)
                                    issues.append(f"Uncorrectable Errors: {attr['raw']['value']}")
                            elif attr['id'] == 197:  # Current Pending Sector Count
                                if attr['raw']['value'] > 0:
                                    health_score -= min(40, attr['raw']['value'] * 2)
                                    issues.append(f"Pending Sectors: {attr['raw']['value']}")
                            elif attr['id'] == 198:  # Offline Uncorrectable Sector Count
                                if attr['raw']['value'] > 0:
                                    health_score -= min(40, attr['raw']['value'] * 2)
                                    issues.append(f"Offline Uncorrectable: {attr['raw']['value']}")
                    
                    # Set health status based on calculated score
                    if health_score >= 90:
                        health = "Good"
                        color = "#a6e3a1"  # Green
                    elif health_score >= 70:
                        health = "Fair"
                        color = "#89b4fa"  # Blue
                    elif health_score >= 40:
                        health = "Poor"
                        color = "#f9e2af"  # Yellow
                    elif health_score >= 10:
                        health = "Critical"
                        color = "#f38ba8"  # Red
                    else:
                        health = "Failed"
                        color = "#f38ba8"  # Red
                    
                    # Add issues to log
                    if issues:
                        self.acquisition_log.append("Health issues detected:")
                        for issue in issues:
                            self.acquisition_log.append(f"- {issue}")
            else:
                health = "Unknown"
                color = "#cba6f7"  # Purple
                self.acquisition_log.append(f"Could not determine device health: {result.stderr}")
        except Exception as e:
            health = "Error"
            color = "#f38ba8"  # Red
            self.acquisition_log.append(f"Error checking device health: {str(e)}")
        
        # Update health indicator
        self.health_indicator.setText(health)
        self.health_indicator.setStyleSheet(f"font-weight: bold; color: {color};")
        
        # Automatically select the appropriate starting mode based on health
        if self.auto_recovery.isChecked():
            if health == "Healthy" or health == "Good":
                self.mode_combo.setCurrentIndex(0)  # Standard
            elif health == "Fair":
                self.mode_combo.setCurrentIndex(1)  # Light Recovery
            elif health == "Poor":
                self.mode_combo.setCurrentIndex(2)  # Aggressive Recovery
            elif health == "Critical":
                self.mode_combo.setCurrentIndex(3)  # Deep Recovery
            elif health == "Failed" or health == "Error":
                self.mode_combo.setCurrentIndex(4)  # Forensic Recovery
        
        # Update stage indicators based on selected mode
        self.update_stage_indicators()

    def update_stage_indicators(self):
        """Updates the stage indicators based on the selected mode."""
        current_index = self.mode_combo.currentIndex()
        
        for i, indicator in enumerate(self.stage_indicators):
            if i < current_index:
                # Previous stages (completed)
                indicator.setStyleSheet("""
                    background-color: #a6e3a1;
                    color: #1e1e2e;
                    border: 1px solid #45475a;
                    border-radius: 4px;
                    padding: 4px 8px;
                    margin: 0 2px;
                    font-weight: bold;
                """)
            elif i == current_index:
                # Current stage
                indicator.setStyleSheet("""
                    background-color: #f9e2af;
                    color: #1e1e2e;
                    border: 1px solid #45475a;
                    border-radius: 4px;
                    padding: 4px 8px;
                    margin: 0 2px;
                    font-weight: bold;
                """)
            else:
                # Future stages
                indicator.setStyleSheet("""
                    background-color: #313244;
                    color: #cdd6f4;
                    border: 1px solid #45475a;
                    border-radius: 4px;
                    padding: 4px 8px;
                    margin: 0 2px;
                """)

    def start_unified_acquisition(self):
        """Start the unified acquisition process that adapts based on drive health."""
        # Check for root privileges
        if os.geteuid() != 0:
            QMessageBox.critical(
                self, "Permission Denied",
                "Root privileges are required for disk operations.\n\n"
                "Please run this application with sudo or as root."
            )
            return
            
        # Get selected source device
        selected_items = self.disk_device_list.selectedItems()
        if not selected_items:
            self.acquisition_status.setText("Error: No source device selected")
            self.acquisition_status.setStyleSheet("color: #f38ba8;")
            return
            
        source_device = selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        # Get output path
        output_path = self.image_path_edit.text().strip()
        if not output_path:
            self.acquisition_status.setText("Error: No output path specified")
            self.acquisition_status.setStyleSheet("color: #f38ba8;")
            return
        
        # Get selected recovery mode
        mode_index = self.mode_combo.currentIndex()
        mode_name = self.mode_combo.currentText()
        
        # Get hash algorithms
        hash_algorithms = []
        if self.hash_md5.isChecked():
            hash_algorithms.append('md5')
        if self.hash_sha1.isChecked():
            hash_algorithms.append('sha1')
        if self.hash_sha256.isChecked():
            hash_algorithms.append('sha256')
            
        if not hash_algorithms:
            hash_algorithms = ['sha256']  # Default to SHA-256 if none selected
        
        # Get recovery options
        recovery_options = {
            'auto_mode': self.auto_recovery.isChecked(),
            'starting_mode': mode_index,
            'retries': self.retry_spin.value(),
            'block_size': int(self.block_size_combo.currentText()),
            'skip_size': self.skip_size_combo.currentText(),
            'timeout': self.timeout_spin.value(),
            'skip_errors': self.skip_errors.isChecked(),
            'log_bad_sectors': self.log_bad_sectors.isChecked(),
            'reverse_direction': self.reverse_direction.isChecked(),
            'trim_zeros': self.trim_zeros.isChecked(),
            'phase_retry': self.phase_retry.isChecked(),
            'verify': self.verify_check.isChecked(),
            'compress': self.compress_check.isChecked(),
            'hash_algorithms': hash_algorithms,
        }
        
        # Show confirmation dialog
        message = (
            f"Source: {source_device}\n"
            f"Destination: {output_path}\n"
            f"Starting Mode: {mode_name}\n"
            f"Auto Progression: {'Enabled' if recovery_options['auto_mode'] else 'Disabled'}\n"
            f"Verify: {'Yes' if recovery_options['verify'] else 'No'}\n"
            f"Hash: {', '.join(hash_algorithms)}\n\n"
        )
        
        if mode_index >= 2:  # Aggressive, Deep, or Forensic mode
            message += (
                "WARNING: Advanced recovery modes may put additional stress on failing drives.\n"
                "This could potentially cause further damage to critically failing hardware.\n\n"
            )
            
        message += "Are you sure you want to start the acquisition process?"
        
        confirm = QMessageBox.question(
            self, "Confirm Acquisition",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm != QMessageBox.StandardButton.Yes:
            self.acquisition_log.append("Acquisition operation cancelled by user")
            return
        
        # Update UI
        self.start_acquisition_btn.setEnabled(False)
        self.stop_acquisition_btn.setEnabled(True)
        self.disk_device_list.setEnabled(False)
        self.mode_combo.setEnabled(False)
        self.auto_recovery.setEnabled(False)
        
        # Update status
        self.acquisition_status.setText(f"Starting acquisition in {mode_name} mode...")
        self.acquisition_status.setStyleSheet("color: #a6e3a1;")
        self.acquisition_log.append(f"Starting acquisition of {source_device} to {output_path}")
        self.acquisition_log.append(f"Initial mode: {mode_name}")
        
        # Update progress display
        self.acquisition_progress.setValue(0)
        
        # Reset statistics
        self.stats_area.clear()
        self.stats_area.append("Acquisition started. Gathering initial statistics...")
        
        # Create and start worker thread
        self.acquisition_worker = UnifiedAcquisitionWorker(
            source_device=source_device,
            output_path=output_path,
            options=recovery_options
        )
        
        # Connect signals
        self.acquisition_worker.progress.connect(self._update_acquisition_progress)
        self.acquisition_worker.log_message.connect(self.acquisition_log.append)
        self.acquisition_worker.stats_update.connect(self._update_acquisition_stats)
        self.acquisition_worker.mode_changed.connect(self._handle_mode_change)
        self.acquisition_worker.finished.connect(self._on_acquisition_finished)
        
        # Start the worker
        self.acquisition_worker.start()

    def _update_acquisition_progress(self, percent, message):
        """Update progress bar and status during acquisition."""
        self.acquisition_progress.setValue(percent)
        self.acquisition_status.setText(message)

    def _update_acquisition_stats(self, stats_dict):
        """Update the statistics display with current recovery information."""
        self.stats_area.clear()
        
        if 'total_size' in stats_dict:
            total_size_gb = stats_dict['total_size'] / (1024**3)
            self.stats_area.append(f"Total Size: {total_size_gb:.2f} GB")
        
        if 'recovered' in stats_dict:
            recovered_gb = stats_dict['recovered'] / (1024**3)
            self.stats_area.append(f"Recovered: {recovered_gb:.2f} GB")
        
        if 'bad_sectors' in stats_dict:
            self.stats_area.append(f"Bad Sectors: {stats_dict['bad_sectors']}")
        
        if 'retry_sectors' in stats_dict:
            self.stats_area.append(f"Retry Attempts: {stats_dict['retry_sectors']}")
        
        if 'recovery_rate' in stats_dict:
            self.stats_area.append(f"Recovery Rate: {stats_dict['recovery_rate']:.2f}%")
        
        if 'elapsed_time' in stats_dict:
            hours, remainder = divmod(stats_dict['elapsed_time'], 3600)
            minutes, seconds = divmod(remainder, 60)
            self.stats_area.append(f"Elapsed Time: {int(hours)}h {int(minutes)}m {int(seconds)}s")

    def _handle_mode_change(self, new_mode_index, reason):
        """Handle a change in recovery mode."""
        old_mode = self.mode_combo.currentText()
        self.mode_combo.setCurrentIndex(new_mode_index)
        new_mode = self.mode_combo.currentText()
        
        self.acquisition_log.append(f"Mode changed: {old_mode} -> {new_mode}")
        self.acquisition_log.append(f"Reason: {reason}")
        
        # Update stage indicators
        self.update_stage_indicators()
        
        # Update status text
        self.acquisition_status.setText(f"Switched to {new_mode} mode: {reason}")
        
        # Show notification
        QMessageBox.information(
            self,
            "Recovery Mode Changed",
            f"The recovery mode has automatically progressed to '{new_mode}'.\n\n"
            f"Reason: {reason}\n\n"
            f"The system will now use more aggressive recovery techniques."
        )

    def _on_acquisition_finished(self, success, message, stats):
        """Handle completion of the acquisition process."""
        # Update UI
        self.start_acquisition_btn.setEnabled(True)
        self.stop_acquisition_btn.setEnabled(False)
        self.disk_device_list.setEnabled(True)
        self.mode_combo.setEnabled(not self.auto_recovery.isChecked())
        self.auto_recovery.setEnabled(True)
        
        # Update final stats
        if stats:
            self._update_acquisition_stats(stats)
            
            # Add final recovery rate to log
            if 'recovery_rate' in stats:
                self.acquisition_log.append(f"Final recovery rate: {stats['recovery_rate']:.2f}%")
        
        # Update status
        if success:
            self.acquisition_status.setText("Acquisition completed successfully")
            self.acquisition_status.setStyleSheet("color: #a6e3a1;")
        else:
            self.acquisition_status.setText(f"Error: {message}")
            self.acquisition_status.setStyleSheet("color: #f38ba8;")
        
        # Log completion
        self.acquisition_log.append(f"Acquisition finished: {message}")
        
        # Show completion dialog
        icon = QMessageBox.Icon.Information if success else QMessageBox.Icon.Warning
        
        result_message = f"Acquisition {'completed successfully' if success else 'failed'}"
        if stats and 'recovery_rate' in stats:
            result_message += f"\nRecovery rate: {stats['recovery_rate']:.2f}%"
        
        QMessageBox.information(
            self,
            "Acquisition Complete",
            f"{result_message}\n\n{message}",
            icon
        )
        
        # Clean up worker
        if hasattr(self, 'acquisition_worker'):
            self.acquisition_worker.quit()
            self.acquisition_worker.wait()
            del self.acquisition_worker

    def stop_acquisition(self):
        """Stop the current acquisition process."""
        if hasattr(self, 'acquisition_worker') and self.acquisition_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Confirm Stop",
                "Are you sure you want to stop the current acquisition?\n\n"
                "This may result in an incomplete or corrupted image file.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.acquisition_worker.stop()
                self.acquisition_log.append("Stopping acquisition operation...")
                self.acquisition_status.setText("Stopping...")
                self.acquisition_status.setStyleSheet("color: #f9e2af;")
                self.stop_acquisition_btn.setEnabled(False)

    def start_damaged_drive_rescue(self):
        """Start the damaged drive recovery process."""
        selected_items = self.rescue_device_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Device Selected", "Please select a source device to recover.")
            return
            
        output_path = self.rescue_output_path.text().strip()
        if not output_path:
            QMessageBox.warning(self, "No Output Path", "Please specify an output path for the recovered image.")
            return
            
        # Get selected device
        device = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if not device:
            QMessageBox.critical(self, "Error", "Could not determine selected device.")
            return
            
        # Get options
        retries = self.rescue_retries.value()
        block_size = int(self.rescue_block_size.currentText())
        skip_errors = self.rescue_skip_errors.isChecked()
        log_errors = self.rescue_log_errors.isChecked()
        
        # Show confirmation
        confirm = QMessageBox.question(
            self, "Confirm Recovery",
            f"WARNING: This will attempt to read from a potentially failing device.\n\n"
            f"Source: {device}\n"
            f"Destination: {output_path}\n\n"
            f"Read retries: {retries}\n"
            f"Block size: {block_size} bytes\n"
            f"Skip errors: {'Yes' if skip_errors else 'No'}\n"
            f"Log bad sectors: {'Yes' if log_errors else 'No'}\n\n"
            f"Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            # TODO: Implement the actual recovery process
            QMessageBox.information(
                self, "Recovery Started",
                "The damaged drive recovery process has been started.\n\n"
                "This is a placeholder - the actual recovery functionality will be implemented in a future update."
            )

    def create_forensic_tools_tab(self):
        """Create the Forensic Tools tab with its subtabs."""
        tab = QTabWidget()
    
        # ===== Unified Disk Acquisition Tab (combines Imaging and Rescue) =====
        data_rescue_tab = QWidget()
        layout = QVBoxLayout()
        
        # Description
        desc = QLabel(
            "This tool provides comprehensive disk acquisition capabilities, automatically adapting "
            "from standard imaging to advanced recovery techniques based on drive health. "
            "The system will progressively use more aggressive recovery methods if errors are encountered."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("margin-bottom: 15px;")
        
        # Top section - Source device and destination
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
    
        # Source device selection with health indicator
        source_group = QGroupBox("Source Device")
        source_layout = QVBoxLayout()
        
        self.disk_device_list = QListWidget()
        self.disk_device_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.disk_device_list.itemSelectionChanged.connect(self.check_device_health)
        
        # Health status indicator
        health_layout = QHBoxLayout()
        health_layout.addWidget(QLabel("Drive Health:"))
        self.health_indicator = QLabel("Unknown")
        self.health_indicator.setStyleSheet("font-weight: bold; color: #89b4fa;")
        health_layout.addWidget(self.health_indicator)
        health_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.clicked.connect(self.refresh_devices)
        
        source_layout.addWidget(QLabel("Select source device:"))
        source_layout.addWidget(self.disk_device_list)
        source_layout.addLayout(health_layout)
        source_layout.addWidget(refresh_btn)
        source_group.setLayout(source_layout)
        
        # Destination options
        dest_group = QGroupBox("Destination")
        dest_layout = QVBoxLayout()
        
        # Output file path
        path_layout = QHBoxLayout()
        self.image_path_edit = QLineEdit()
        self.image_path_edit.setPlaceholderText("Select or enter output image path...")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_image_path)
        
        path_layout.addWidget(self.image_path_edit)
        path_layout.addWidget(browse_btn)
        
        # Image format options
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Image Format:"))
        self.image_format_combo = QComboBox()
        self.image_format_combo.addItems(["Raw (dd)", "EnCase (E01)", "AFF4", "QCOW2", "IMG", "ISO"])
        
        # Compression option
        self.compress_check = QCheckBox("Compress Image")
        
        format_layout.addWidget(self.image_format_combo)
        format_layout.addWidget(self.compress_check)
        format_layout.addStretch()
        
        dest_layout.addLayout(path_layout)
        dest_layout.addLayout(format_layout)
        dest_group.setLayout(dest_layout)
        
        # Add groups to top layout
        top_layout.addWidget(source_group)
        top_layout.addWidget(dest_group)
        
        # Middle section - Acquisition Options (combines imaging and recovery options)
        options_group = QGroupBox("Acquisition Options")
        options_tabs = QTabWidget()
        
        # Basic Options Tab
        basic_tab = QWidget()
        basic_layout = QGridLayout()
        
        # Hashing options
        self.hash_md5 = QCheckBox("MD5")
        self.hash_sha1 = QCheckBox("SHA-1")
        self.hash_sha256 = QCheckBox("SHA-256")
        self.hash_sha256.setChecked(True)
        
        # Verification option
        self.verify_check = QCheckBox("Verify after acquisition")
        self.verify_check.setChecked(True)
        
        # Add basic options
        basic_layout.addWidget(QLabel("Hash Algorithms:"), 0, 0)
        basic_layout.addWidget(self.hash_md5, 0, 1)
        basic_layout.addWidget(self.hash_sha1, 0, 2)
        basic_layout.addWidget(self.hash_sha256, 0, 3)
        basic_layout.addWidget(self.verify_check, 1, 0, 1, 4)
        basic_tab.setLayout(basic_layout)
        
        # Recovery Options Tab
        recovery_tab = QWidget()
        recovery_layout = QVBoxLayout()
        
        # Automatic mode
        mode_group = QGroupBox("Recovery Mode")
        mode_layout = QVBoxLayout()
        
        self.auto_recovery = QCheckBox("Enable automatic mode progression")
        self.auto_recovery.setChecked(True)
        self.auto_recovery.setToolTip("Automatically escalate to more aggressive recovery techniques if errors are encountered")
    
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Standard (Healthy Drive)",
            "Light Recovery (Minor Issues)",
            "Aggressive Recovery (Moderate Issues)",
            "Deep Recovery (Severe Issues)",
            "Forensic Recovery (Critical Failure)"
        ])
        self.mode_combo.setEnabled(False)  # Disabled when automatic mode is active
    
        self.auto_recovery.toggled.connect(lambda checked: self.mode_combo.setEnabled(not checked))
    
        mode_layout.addWidget(self.auto_recovery)
        mode_layout.addWidget(QLabel("Starting Mode:"))
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)
    
        # Recovery parameters
        params_group = QGroupBox("Recovery Parameters")
        params_layout = QFormLayout()
        
        # Read retries
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(1, 100)
        self.retry_spin.setValue(3)
        params_layout.addRow("Read Retries:", self.retry_spin)
        
        # Block size
        self.block_size_combo = QComboBox()
        self.block_size_combo.addItems(["512", "1024", "2048", "4096", "8192", "16384"])
        self.block_size_combo.setCurrentText("4096")
        params_layout.addRow("Block Size (bytes):", self.block_size_combo)
        
        # Skip size
        self.skip_size_combo = QComboBox()
        self.skip_size_combo.addItems(["512", "4K", "16K", "64K", "1M", "10M"])
        self.skip_size_combo.setCurrentText("64K")
        params_layout.addRow("Bad Area Skip Size:", self.skip_size_combo)
        
        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" sec")
        params_layout.addRow("Read Timeout:", self.timeout_spin)
        
        params_group.setLayout(params_layout)
        
        # Recovery options
        options_inner_group = QGroupBox("Additional Options")
        options_inner_layout = QVBoxLayout()
        
        self.skip_errors = QCheckBox("Skip read errors (create partial image)")
        self.skip_errors.setChecked(True)
        
        self.log_bad_sectors = QCheckBox("Log bad sectors to file")
        self.log_bad_sectors.setChecked(True)
        
        self.reverse_direction = QCheckBox("Try reverse read direction")
        self.reverse_direction.setChecked(True)
        
        self.trim_zeros = QCheckBox("Trim trailing zeros")
        
        self.phase_retry = QCheckBox("Use phase-based approach (multiple passes)")
        self.phase_retry.setChecked(True)
        
        options_inner_layout.addWidget(self.skip_errors)
        options_inner_layout.addWidget(self.log_bad_sectors)
        options_inner_layout.addWidget(self.reverse_direction)
        options_inner_layout.addWidget(self.trim_zeros)
        options_inner_layout.addWidget(self.phase_retry)
        options_inner_group.setLayout(options_inner_layout)
        
        # Add all widgets to recovery layout
        recovery_layout.addWidget(mode_group)
        recovery_layout.addWidget(params_group)
        recovery_layout.addWidget(options_inner_group)
        recovery_tab.setLayout(recovery_layout)
        
        # Add tabs to options
        options_tabs.addTab(basic_tab, "Basic")
        options_tabs.addTab(recovery_tab, "Recovery")
        options_group.setLayout(QVBoxLayout())
        options_group.layout().addWidget(options_tabs)
        
        # Status and Progress Area
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        # Health progression indicator
        health_progress_layout = QHBoxLayout()
        health_progress_layout.addWidget(QLabel("Recovery Progression:"))
        
        self.health_stage_layout = QHBoxLayout()
        stages = ["Standard", "Light", "Aggressive", "Deep", "Forensic"]
        self.stage_indicators = []
        
        for stage in stages:
            indicator = QLabel(stage)
            indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
            indicator.setStyleSheet("""
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 4px 8px;
                margin: 0 2px;
            """)
            self.stage_indicators.append(indicator)
            self.health_stage_layout.addWidget(indicator)
        
        health_progress_layout.addLayout(self.health_stage_layout)
        
        # Progress bar
        self.acquisition_progress = QProgressBar()
        self.acquisition_progress.setRange(0, 100)
        self.acquisition_progress.setValue(0)
        
        # Status text
        self.acquisition_status = QLabel("Ready")
        self.acquisition_status.setStyleSheet("font-weight: bold; color: #89b4fa;")
        
        # Recovery statistics
        self.stats_area = QTextEdit()
        self.stats_area.setReadOnly(True)
        self.stats_area.setMaximumHeight(80)
        self.stats_area.setPlaceholderText("Acquisition statistics will appear here")
        
        # Log area
        self.acquisition_log = QTextEdit()
        self.acquisition_log.setReadOnly(True)
        self.acquisition_log.setMaximumHeight(150)
        
        # Add widgets to status layout
        status_layout.addLayout(health_progress_layout)
        status_layout.addWidget(self.acquisition_progress)
        status_layout.addWidget(self.acquisition_status)
        status_layout.addWidget(QLabel("Statistics:"))
        status_layout.addWidget(self.stats_area)
        status_layout.addWidget(QLabel("Activity Log:"))
        status_layout.addWidget(self.acquisition_log)
        status_group.setLayout(status_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        self.start_acquisition_btn = QPushButton("Start Acquisition")
        self.start_acquisition_btn.setStyleSheet("background-color: #a6e3a1;")
        self.start_acquisition_btn.clicked.connect(self.start_unified_acquisition)
        
        self.stop_acquisition_btn = QPushButton("Stop")
        self.stop_acquisition_btn.setEnabled(False)
        self.stop_acquisition_btn.clicked.connect(self.stop_acquisition)
        
        button_layout.addWidget(self.start_acquisition_btn)
        button_layout.addWidget(self.stop_acquisition_btn)
        
        # Add all sections to main layout
        layout.addWidget(desc)
        layout.addWidget(top_widget)
        layout.addWidget(options_group)
        layout.addWidget(status_group)
        layout.addLayout(button_layout)
        
        data_rescue_tab.setLayout(layout)
        
        # ===== Memory Analysis Tab =====
        memory_tab = QWidget()
        memory_layout = QVBoxLayout()
        memory_layout.addWidget(QLabel("Memory Analysis Tools"))
        memory_tab.setLayout(memory_layout)
        
        # ===== Artifact Analysis Tab =====
        artifacts_tab = QWidget()
        artifacts_layout = QVBoxLayout()
        artifacts_layout.addWidget(QLabel("Artifact Analysis Tools"))
        artifacts_tab.setLayout(artifacts_layout)
        
        # Add all tabs
        tab.addTab(data_rescue_tab, "Data Rescue")
        tab.addTab(memory_tab, "Memory Analysis")
        tab.addTab(artifacts_tab, "Artifact Analysis")
        
        # Initial device refresh
        self.refresh_devices()
        
        return tab

    def _get_available_devices(self):
        """Get a list of available storage devices."""
        devices = []
        
        try:
            # Use lsblk to get device information in JSON format
            result = subprocess.run(
                ['lsblk', '-d', '-o', 'NAME,PATH,SIZE,MODEL', '--json'],
                capture_output=True, text=True, check=True
            )
            
            # Parse the JSON output
            data = json.loads(result.stdout)
            
            for device in data.get('blockdevices', []):
                # Skip loop devices and RAM disks
                if device['name'].startswith(('loop', 'ram')):
                    continue
                    
                name = device['name']
                path = device['path']
                size = device.get('size', 'Unknown')
                model = device.get('model', '').strip() or 'Unknown Model'
                
                device_info = f"{name} - {size} {model}"
                devices.append((name, path, device_info))
                
                # Log device for debugging
                if hasattr(self, 'acquisition_log'):
                    self.acquisition_log.append(f"Found device: {path} ({size} {model})")
                    
        except Exception as e:
            if hasattr(self, 'acquisition_log'):
                self.acquisition_log.append(f"Error detecting devices: {str(e)}")
            else:
                print(f"Error detecting devices: {str(e)}")
        
        return devices

    def _populate_device_list(self, list_widget, devices, selectable=True):
        """Populate a QListWidget with detected devices."""
        # Clear the list first
        list_widget.clear()
        
        # Add devices to the list
        for _, path, info in devices:
            item = QListWidgetItem(info)
            item.setData(Qt.ItemDataRole.UserRole, path)
            list_widget.addItem(item)
        
        # Make the first item selected if there are any items
        if list_widget.count() > 0 and selectable:
            list_widget.setCurrentRow(0)

    def refresh_devices(self):
        """Refresh the list of available storage devices."""
        # Log action
        if hasattr(self, 'acquisition_log'):
            self.acquisition_log.append("Scanning for storage devices...")
        
        # Reset health indicator
        if hasattr(self, 'health_indicator'):
            self.health_indicator.setText("Unknown")
            self.health_indicator.setStyleSheet("font-weight: bold; color: #89b4fa;")
        
        # Get list of available devices
        devices = self._get_available_devices()
        
        # Populate device lists
        if hasattr(self, 'disk_device_list'):
            self._populate_device_list(self.disk_device_list, devices)
            if hasattr(self, 'acquisition_log'):
                self.acquisition_log.append(f"Found {len(devices)} storage devices")

    def _browse_image_path(self):
        """Open a file dialog to select the output image path."""
        # Get the selected device name to use as default filename
        default_name = "disk_image.dd"
        selected_items = self.disk_device_list.selectedItems()
        if selected_items:
            device_path = selected_items[0].data(Qt.ItemDataRole.UserRole)
            # Extract device name without path
            device_name = os.path.basename(device_path)
            default_name = f"{device_name}_image.dd"
        
        # Open save file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Output Image Location",
            os.path.expanduser(f"~/{default_name}"),
            "Disk Images (*.dd *.img *.raw);;All Files (*.*)"
        )
        
        if file_path:
            self.image_path_edit.setText(file_path)