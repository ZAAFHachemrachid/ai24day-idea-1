import unittest
import numpy as np
import threading
import time
from src.utils.parallel.frame_buffer import ThreadSafeFrameBuffer

class TestThreadSafeFrameBuffer(unittest.TestCase):
    def setUp(self):
        self.buffer = ThreadSafeFrameBuffer(max_size=5)
        
    def test_put_frame(self):
        # Test basic frame insertion
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        success = self.buffer.put_frame(frame)
        
        self.assertTrue(success)
        self.assertEqual(self.buffer.size, 1)
        
    def test_priority_queue(self):
        # Test frame priority handling
        frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
        frame2 = np.ones((480, 640, 3), dtype=np.uint8)
        
        # Add frames with different priorities (lower number = higher priority)
        self.buffer.put_frame(frame1, priority=2)
        self.buffer.put_frame(frame2, priority=1)
        
        # Should get frame2 first (priority 1)
        result = self.buffer.get_frame()
        self.assertIsNotNone(result)
        priority, frame = result
        self.assertEqual(priority, 1)
        np.testing.assert_array_equal(frame, frame2)
        
        # Release the frame
        self.buffer.release_frame(frame)
        
    def test_frame_dropping(self):
        # Test frame dropping when buffer is full
        frames = []
        
        # Fill buffer beyond capacity
        for i in range(7):  # Buffer size is 5
            frame = np.full((480, 640, 3), i, dtype=np.uint8)
            success = self.buffer.put_frame(frame, priority=i)
            if success:
                frames.append(i)
                
        # Should have dropped oldest frames
        self.assertEqual(self.buffer.size, 5)
        
        # Verify we have the most recent frames
        result = self.buffer.get_metrics()
        self.assertEqual(result['frames_dropped'], 2)
        
    def test_frame_pooling(self):
        # Test frame pooling functionality
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add and remove frame multiple times
        self.buffer.put_frame(frame)
        result = self.buffer.get_frame()
        self.assertIsNotNone(result)
        _, pooled_frame = result
        self.buffer.release_frame(pooled_frame)
        
        # Add another frame - should reuse pooled frame
        self.buffer.put_frame(frame)
        result = self.buffer.get_frame()
        self.assertIsNotNone(result)
        _, reused_frame = result
        
        # Should be the same memory allocation
        self.assertEqual(pooled_frame.__array_interface__['data'][0],
                        reused_frame.__array_interface__['data'][0])
        
        self.buffer.release_frame(reused_frame)
        
    def test_clear(self):
        # Test clearing the buffer
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add some frames
        for _ in range(3):
            self.buffer.put_frame(frame)
            
        self.buffer.clear()
        self.assertEqual(self.buffer.size, 0)
        
    def test_metrics(self):
        # Test performance metrics
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # First fill the buffer (should succeed)
        for i in range(5):  # Buffer size is 5
            success = self.buffer.put_frame(frame, priority=i)
            self.assertTrue(success)
        
        # Try to add two more frames (should fail)
        success1 = self.buffer.put_frame(frame, priority=5)
        success2 = self.buffer.put_frame(frame, priority=6)
        
        # Both should fail as buffer is full
        self.assertFalse(success1)
        self.assertFalse(success2)
            
        metrics = self.buffer.get_metrics()
        
        # Verify metrics
        self.assertEqual(metrics['frames_received'], 7)  # Total frames attempted
        self.assertEqual(metrics['current_size'], 5)     # Buffer should be full
        self.assertEqual(metrics['frames_dropped'], 2)   # Two frames failed to add
        self.assertAlmostEqual(metrics['drop_ratio'], 2/7)  # Drop ratio calculation
        self.assertEqual(metrics['current_size'], 5)
        self.assertEqual(metrics['max_size'], 5)
        
    def test_thread_safety(self):
        # Test thread safety with concurrent operations
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        iterations = 100
        threads = 4
        
        def producer():
            for i in range(iterations):
                self.buffer.put_frame(frame, priority=i)
                time.sleep(0.001)  # Simulate some work
                
        def consumer():
            frames_processed = 0
            while frames_processed < iterations:
                result = self.buffer.get_frame()
                if result is not None:
                    _, frame = result
                    self.buffer.release_frame(frame)
                    frames_processed += 1
                time.sleep(0.001)  # Simulate some work
                
        # Create and start threads
        threads_list = []
        threads_list.append(threading.Thread(target=producer))
        threads_list.append(threading.Thread(target=consumer))
        
        for t in threads_list:
            t.start()
            
        # Wait for all threads to complete
        for t in threads_list:
            t.join()
            
        # Verify buffer state
        self.assertLessEqual(self.buffer.size, self.buffer.max_size)

if __name__ == '__main__':
    unittest.main()