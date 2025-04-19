"""
Unit tests for the optimized FaceDetectionPool implementation.
"""

import pytest
import numpy as np
import cv2
import psutil
import time
from src.utils.parallel.detection_pool import FaceDetectionPool, FrameQuality

@pytest.fixture
def detection_pool():
    """Create a detection pool instance for testing."""
    pool = FaceDetectionPool()
    yield pool
    pool.shutdown()

@pytest.fixture
def sample_frame():
    """Create a sample frame for testing."""
    # Create a 1080p test frame
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    # Add some features for quality assessment
    cv2.rectangle(frame, (100, 100), (300, 300), (255, 255, 255), -1)
    cv2.circle(frame, (500, 500), 50, (128, 128, 128), -1)
    return frame

def test_frame_quality_assessment():
    """Test frame quality assessment with SIMD operations."""
    # Create test frames of varying quality
    good_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    blank_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    noisy_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    # Test quality assessment
    good_score = FrameQuality.assess_quality(good_frame)
    blank_score = FrameQuality.assess_quality(blank_frame)
    noisy_score = FrameQuality.assess_quality(noisy_frame)
    
    # Verify scores
    assert good_score > blank_score
    assert 0.0 <= blank_score <= 1.0
    assert 0.0 <= good_score <= 1.0
    assert 0.0 <= noisy_score <= 1.0

def test_memory_pressure_handling(detection_pool, sample_frame):
    """Test handling of memory pressure situations."""
    # Monitor initial memory
    initial_memory = psutil.virtual_memory().percent
    
    # Submit frames until memory pressure threshold is reached
    frames_processed = 0
    max_frames = 1000
    
    while frames_processed < max_frames:
        frame_id = detection_pool.process_frame(sample_frame)
        if frame_id == -1:  # Frame was skipped
            break
        frames_processed += 1
        
        # Check memory usage
        current_memory = psutil.virtual_memory().percent
        if current_memory > detection_pool.memory_pressure_threshold * 100:
            break
    
    # Verify memory pressure handling
    assert frames_processed > 0
    assert psutil.virtual_memory().percent <= 95  # Should not reach critical levels

def test_cpu_utilization(detection_pool, sample_frame):
    """Test CPU utilization and thread affinity."""
    # Get initial CPU usage
    initial_cpu = psutil.cpu_percent(interval=0.1)
    
    # Process multiple frames
    frame_ids = []
    for _ in range(50):
        frame_id = detection_pool.process_frame(sample_frame)
        if frame_id != -1:
            frame_ids.append(frame_id)
    
    # Let processing happen
    time.sleep(2)
    
    # Check CPU usage
    cpu_usage = psutil.cpu_percent(interval=0.1)
    
    # Verify CPU usage is within expected range
    assert cpu_usage <= detection_pool.cpu_threshold * 100 + 10  # Allow 10% margin

def test_batch_processing(detection_pool, sample_frame):
    """Test batch processing capabilities."""
    # Submit batch_size + 1 frames
    frame_ids = []
    for _ in range(detection_pool.batch_size + 1):
        frame_id = detection_pool.process_frame(sample_frame)
        if frame_id != -1:
            frame_ids.append(frame_id)
    
    # Verify frames were accepted
    assert len(frame_ids) > 0
    
    # Wait for processing
    time.sleep(2)
    
    # Collect results
    results = []
    while len(results) < len(frame_ids):
        result = detection_pool.get_result()
        if result:
            results.append(result)
        if len(results) == len(frame_ids) or len(results) >= detection_pool.batch_size:
            break
    
    # Verify batch processing
    assert len(results) > 0
    for result in results:
        assert result.frame_id in frame_ids
        assert result.quality_score >= 0.0

def test_prefetch_buffer(detection_pool, sample_frame):
    """Test frame prefetching functionality."""
    # Submit frames to fill prefetch buffer
    frame_ids = []
    for _ in range(detection_pool.batch_size * 2):  # Fill prefetch buffer
        frame_id = detection_pool.process_frame(sample_frame)
        if frame_id != -1:
            frame_ids.append(frame_id)
    
    # Verify prefetch buffer usage
    assert len(detection_pool.prefetch_buffer) > 0
    
    # Process frames
    time.sleep(2)
    
    # Verify results
    results_count = 0
    max_attempts = 50
    attempts = 0
    
    while results_count < len(frame_ids) and attempts < max_attempts:
        result = detection_pool.get_result()
        if result:
            results_count += 1
        attempts += 1
        time.sleep(0.1)
    
    assert results_count > 0

def test_resource_monitoring(detection_pool):
    """Test resource monitoring capabilities."""
    # Check initial resource monitoring
    assert detection_pool._last_cpu_check == 0
    assert detection_pool._last_memory_check == 0
    
    # Trigger resource check
    should_skip = detection_pool._check_resources()
    
    # Verify monitoring updates
    assert detection_pool._last_cpu_check > 0
    assert detection_pool._last_memory_check > 0
    assert isinstance(should_skip, bool)

def test_shutdown_cleanup(detection_pool, sample_frame):
    """Test proper cleanup during shutdown."""
    # Submit some frames
    for _ in range(5):
        detection_pool.process_frame(sample_frame)
    
    # Shutdown pool
    detection_pool.shutdown()
    
    # Verify cleanup
    assert len(detection_pool.workers) == 0
    assert len(detection_pool.frame_buffer) == 0
    assert len(detection_pool.prefetch_buffer) == 0
    
    # Verify queues are empty
    assert detection_pool.input_queue.empty()
    assert detection_pool.result_queue.empty()

if __name__ == '__main__':
    pytest.main([__file__])