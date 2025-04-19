"""
Performance logging system for tracking application metrics.
"""

import os
import time
import threading
import logging
import psutil
from pathlib import Path
from datetime import datetime
import csv
from typing import Optional, Dict
import numpy as np

class PerformanceLogger:
    """Singleton class for logging performance metrics."""
    
    _instance: Optional['PerformanceLogger'] = None
    _lock = threading.Lock()
    
    def __init__(self):
        """Initialize the performance logger."""
        if PerformanceLogger._instance is not None:
            raise RuntimeError("Use PerformanceLogger.instance() instead")
            
        # Initialize logger first for error tracking
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        try:
            # Initialize system monitoring
            self.process = psutil.Process()
            
            # Setup logging infrastructure
            self._setup_directories()
            self._setup_files()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize performance logger: {str(e)}")
            # Re-raise to prevent partial initialization
            raise
        
        # Performance metrics
        self.detection_times = []
        self.recognition_times = []
        self.fps_samples = []
        self.last_frame_time = time.time()
        
        # Threading
        self._metrics_lock = threading.Lock()
        self._logging_thread = threading.Thread(target=self._periodic_logging, daemon=True)
        self._active = True
        self._logging_thread.start()
        
    @classmethod
    def instance(cls) -> 'PerformanceLogger':
        """Get the singleton instance of PerformanceLogger."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
        
    def _setup_directories(self):
        """Create necessary directory structure for logs."""
        today = datetime.now().strftime("%Y-%m-%d")
        self.base_dir = Path("logs/performance")
        self.daily_dir = self.base_dir / today
        self.latest_link = self.base_dir / "latest"
        
        # Create directories
        self.daily_dir.mkdir(parents=True, exist_ok=True)
        
        # Update latest symlink
        try:
            # Remove existing symlink if it exists
            if self.latest_link.exists():
                if self.latest_link.is_symlink():
                    self.latest_link.unlink()
                else:
                    # If it's not a symlink but exists, remove directory
                    import shutil
                    shutil.rmtree(self.latest_link)
                    
            # Create new symlink
            self.latest_link.symlink_to(self.daily_dir, target_is_directory=True)
            
        except Exception as e:
            self.logger.warning(f"Failed to update latest symlink: {str(e)}")
            # Continue without symlink if it fails
        
    def _setup_files(self):
        """Initialize log files with headers."""
        try:
            # Set directory permissions
            self.daily_dir.chmod(0o755)  # rwxr-xr-x
            
            # System metrics file
            self.system_metrics_file = self.daily_dir / "system_metrics.csv"
            self._create_csv_file(
                self.system_metrics_file,
                ['timestamp', 'cpu_percent', 'memory_percent',
                 'memory_used_mb', 'memory_available_mb']
            )
                
            # Processing times file
            self.processing_times_file = self.daily_dir / "processing_times.csv"
            self._create_csv_file(
                self.processing_times_file,
                ['timestamp', 'avg_detection_time', 'avg_recognition_time',
                 'detection_count', 'recognition_count']
            )
                
            # FPS log file
            self.fps_file = self.daily_dir / "fps_log.csv"
            self._create_csv_file(
                self.fps_file,
                ['timestamp', 'fps', 'sample_period']
            )
            
        except Exception as e:
            self.logger.error(f"Failed to setup log files: {str(e)}")
            raise
            
    def _create_csv_file(self, file_path: Path, headers: list):
        """Create a CSV file with headers if it doesn't exist.
        
        Args:
            file_path: Path to the CSV file
            headers: List of column headers
        """
        try:
            if not file_path.exists():
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                file_path.chmod(0o644)  # rw-r--r--
        except Exception as e:
            self.logger.error(f"Failed to create {file_path.name}: {str(e)}")
            raise
                
    def log_detection_time(self, processing_time: float):
        """Log a face detection processing time.
        
        Args:
            processing_time: Time taken to process in seconds
            
        Raises:
            ValueError: If processing_time is None or negative
        """
        if processing_time is None:
            raise ValueError("Processing time cannot be None")
        if processing_time < 0:
            self.logger.warning("Negative processing time received, using absolute value")
            processing_time = abs(processing_time)
            
        with self._metrics_lock:
            self.detection_times.append(processing_time)
            
    def log_recognition_time(self, processing_time: float):
        """Log a face recognition processing time.
        
        Args:
            processing_time: Time taken to process in seconds
            
        Raises:
            ValueError: If processing_time is None or negative
        """
        if processing_time is None:
            raise ValueError("Processing time cannot be None")
        if processing_time < 0:
            self.logger.warning("Negative processing time received, using absolute value")
            processing_time = abs(processing_time)
            
        with self._metrics_lock:
            self.recognition_times.append(processing_time)
            
    def log_frame_processed(self):
        """Log that a frame was processed for FPS calculation."""
        current_time = time.time()
        with self._metrics_lock:
            time_diff = current_time - self.last_frame_time
            if time_diff > 0:  # Avoid division by zero
                self.fps_samples.append(1.0 / time_diff)
            self.last_frame_time = current_time
            
    def _write_system_metrics(self):
        """Write current system metrics to file."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            with open(self.system_metrics_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    cpu_percent,
                    memory.percent,
                    memory.used / (1024 * 1024),  # Convert to MB
                    memory.available / (1024 * 1024)  # Convert to MB
                ])
        except Exception as e:
            self.logger.error(f"Error writing system metrics: {str(e)}")
            
    def _write_processing_metrics(self):
        """Write processing time metrics to file."""
        try:
            with self._metrics_lock:
                detection_times = self.detection_times.copy()
                recognition_times = self.recognition_times.copy()
                self.detection_times.clear()
                self.recognition_times.clear()
                
            if detection_times or recognition_times:
                # Calculate means safely
                det_mean = float(np.mean(detection_times)) if detection_times else 0.0
                rec_mean = float(np.mean(recognition_times)) if recognition_times else 0.0
                
                # Ensure directory exists
                self.processing_times_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(self.processing_times_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        datetime.now().isoformat(),
                        det_mean,
                        rec_mean,
                        len(detection_times),
                        len(recognition_times)
                    ])
        except Exception as e:
            self.logger.error(f"Error writing processing metrics: {str(e)}")
                
    def _write_fps_metrics(self):
        """Write FPS metrics to file."""
        with self._metrics_lock:
            fps_samples = self.fps_samples.copy()
            self.fps_samples.clear()
            
        if fps_samples:
            try:
                with open(self.fps_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        datetime.now().isoformat(),
                        np.mean(fps_samples),
                        len(fps_samples)
                    ])
            except Exception as e:
                self.logger.error(f"Error writing FPS metrics: {str(e)}")
                
    def _cleanup_old_logs(self):
        """Clean up log files older than 30 days."""
        try:
            cutoff = datetime.now().timestamp() - (30 * 24 * 60 * 60)  # 30 days
            for item in self.base_dir.iterdir():
                if item.is_dir() and item.name != "latest":
                    try:
                        dir_date = datetime.strptime(item.name, "%Y-%m-%d")
                        if dir_date.timestamp() < cutoff:
                            import shutil
                            shutil.rmtree(item)
                            self.logger.info(f"Cleaned up old logs: {item}")
                    except ValueError:
                        continue  # Skip directories that don't match date format
        except Exception as e:
            self.logger.error(f"Error cleaning up old logs: {str(e)}")
            
    def _check_log_rotation(self):
        """Check if we need to rotate to a new day's log files."""
        current_date = datetime.now().strftime("%Y-%m-%d")
        if self.daily_dir.name != current_date:
            try:
                # Setup new day's directory and files
                self._setup_directories()
                self._setup_files()
                self.logger.info(f"Rotated logs to new day: {current_date}")
            except Exception as e:
                self.logger.error(f"Error rotating log files: {str(e)}")

    def _periodic_logging(self):
        """Background thread for periodic metric logging."""
        cleanup_counter = 0  # Count seconds for cleanup timing
        last_date = datetime.now().strftime("%Y-%m-%d")
        
        while self._active:
            try:
                # Check for day rollover
                current_date = datetime.now().strftime("%Y-%m-%d")
                if current_date != last_date:
                    self._check_log_rotation()
                    last_date = current_date
                
                # Write current metrics
                self._write_system_metrics()
                self._write_processing_metrics()
                self._write_fps_metrics()
                
                # Handle cleanup every 24 hours (86400 seconds)
                cleanup_counter += 1
                if cleanup_counter >= 86400:
                    self._cleanup_old_logs()
                    cleanup_counter = 0
                    
            except Exception as e:
                self.logger.error(f"Error in periodic logging: {str(e)}")
                time.sleep(5)  # Add delay on error to prevent tight loops
                continue
                
            try:
                time.sleep(1)  # Log every second
            except Exception:
                break  # Handle interrupt during sleep
            
    def shutdown(self):
        """Clean shutdown of the logger."""
        self._active = False
        if self._logging_thread.is_alive():
            self._logging_thread.join(timeout=2.0)
            
        # Final write of any remaining metrics
        self._write_processing_metrics()
        self._write_fps_metrics()