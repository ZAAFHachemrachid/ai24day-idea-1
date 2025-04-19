import unittest
import time
import shutil
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from src.utils.performance_logger import PerformanceLogger

class TestPerformanceLogger(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        # Clear any existing test logs
        self.test_log_dir = Path("logs/performance")
        if self.test_log_dir.exists():
            shutil.rmtree(self.test_log_dir)
            
        # Reset singleton instance
        PerformanceLogger._instance = None
        
    def tearDown(self):
        """Clean up after tests."""
        try:
            if hasattr(self, 'logger') and self.logger:
                self.logger.shutdown()
                time.sleep(0.1)  # Give time for threads to shut down
            
            # Clean up test logs
            if self.test_log_dir.exists():
                # Force remove readonly files
                def remove_readonly(func, path, _):
                    import stat
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                
                shutil.rmtree(self.test_log_dir, onerror=remove_readonly)
        except Exception as e:
            print(f"Warning: Cleanup failed: {str(e)}")
            
    def test_singleton_pattern(self):
        """Test that logger follows singleton pattern."""
        logger1 = PerformanceLogger.instance()
        logger2 = PerformanceLogger.instance()
        self.assertIs(logger1, logger2)
        
    def test_directory_creation(self):
        """Test log directory structure creation."""
        logger = PerformanceLogger.instance()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Check directory structure
        self.assertTrue(logger.base_dir.exists())
        self.assertTrue(logger.daily_dir.exists())
        self.assertEqual(logger.daily_dir.name, today)
        
        # Check log files
        self.assertTrue(logger.system_metrics_file.exists())
        self.assertTrue(logger.processing_times_file.exists())
        self.assertTrue(logger.fps_file.exists())
        
    def test_metric_logging(self):
        """Test logging of various metrics."""
        logger = PerformanceLogger.instance()
        
        # Log some test metrics
        logger.log_detection_time(0.1)
        logger.log_recognition_time(0.2)
        logger.log_frame_processed()
        
        # Wait for periodic logging
        time.sleep(2)
        logger._write_processing_metrics()  # Force write
        
        # Check that files have content
        with open(logger.processing_times_file) as f:
            content = f.read()
            self.assertIn("0.1", content)  # Detection time
            self.assertIn("0.2", content)  # Recognition time
            
        with open(logger.fps_file) as f:
            self.assertTrue(len(f.readlines()) > 1)  # Header + at least one metric
            
    def test_log_rotation(self):
        """Test log rotation at day boundary."""
        logger = PerformanceLogger.instance()
        
        # Mock datetime to simulate day change
        tomorrow = datetime.now() + timedelta(days=1)
        with patch('src.utils.performance_logger.datetime') as mock_datetime:
            mock_datetime.now.return_value = tomorrow
            mock_datetime.strftime = datetime.strftime
            mock_datetime.strptime = datetime.strptime
            
            # Trigger log rotation check
            logger._check_log_rotation()
            
            # Verify new log directory was created
            tomorrow_dir = logger.base_dir / tomorrow.strftime("%Y-%m-%d")
            self.assertTrue(tomorrow_dir.exists())
            
    def test_cleanup_old_logs(self):
        """Test cleanup of old log files."""
        logger = PerformanceLogger.instance()
        
        # Create some old log directories
        old_date = datetime.now() - timedelta(days=40)
        old_dir = logger.base_dir / old_date.strftime("%Y-%m-%d")
        old_dir.mkdir(parents=True, exist_ok=True)
        
        # Run cleanup
        logger._cleanup_old_logs()
        
        # Verify old directory was removed
        self.assertFalse(old_dir.exists())
        
    def test_error_handling(self):
        """Test error handling in logging operations."""
        logger = PerformanceLogger.instance()
        
        # Test negative values get converted to absolute
        logger.log_detection_time(-1.5)
        with logger._metrics_lock:
            self.assertEqual(logger.detection_times[-1], 1.5)
            
        # Test None values raise ValueError
        with self.assertRaises(ValueError):
            logger.log_recognition_time(None)
            
        # Test negative recognition times
        logger.log_recognition_time(-0.5)
        with logger._metrics_lock:
            self.assertEqual(logger.recognition_times[-1], 0.5)
        
        # Test file write errors
        def raise_error(*args, **kwargs):
            raise IOError("Test error")
            
        with patch('builtins.open', side_effect=raise_error):
            logger._write_system_metrics()  # Should log error but not crash
            
        # Verify logger is still functional after errors
        self.assertTrue(logger._active)
        logger.log_detection_time(0.1)  # Should work fine
        
if __name__ == '__main__':
    unittest.main()