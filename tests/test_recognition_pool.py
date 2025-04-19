"""
Unit tests for the optimized RecognitionPool implementation.
"""

import pytest
import numpy as np
import cv2
import psutil
import time
import threading
from src.utils.parallel.recognition_pool import RecognitionPool, LRUCache

@pytest.fixture
def recognition_pool():
    """Create a recognition pool instance for testing."""
    pool = RecognitionPool()
    yield pool
    pool.shutdown()

@pytest.fixture
def sample_embedding():
    """Create a sample face embedding for testing."""
    # Create a normalized 512-dimensional embedding vector
    embedding = np.random.randn(512).astype(np.float32)
    embedding = embedding / np.linalg.norm(embedding)
    return embedding

def test_lru_cache():
    """Test LRU cache functionality."""
    cache = LRUCache(capacity=2)
    
    # Create test embeddings
    emb1 = np.random.randn(512).astype(np.float32)
    emb1 = emb1 / np.linalg.norm(emb1)
    
    emb2 = np.random.randn(512).astype(np.float32)
    emb2 = emb2 / np.linalg.norm(emb2)
    
    emb3 = np.random.randn(512).astype(np.float32)
    emb3 = emb3 / np.linalg.norm(emb3)
    
    # Test cache operations
    cache.put(emb1, ("person1", 0.9))
    cache.put(emb2, ("person2", 0.85))
    
    # Verify cache hits
    result1 = cache.get(emb1)
    assert result1 is not None
    assert result1[0] == "person1"
    
    # Test LRU eviction
    cache.put(emb3, ("person3", 0.95))
    result2 = cache.get(emb1)
    assert result2 is None  # emb1 should have been evicted

def test_batch_processing(recognition_pool, sample_embedding):
    """Test batch processing capabilities."""
    # Submit batch_size + 1 faces
    face_ids = []
    frame_id = 0
    
    for i in range(recognition_pool.batch_size + 1):
        # Create slightly different embeddings
        embedding = sample_embedding + np.random.randn(512) * 0.1
        embedding = embedding / np.linalg.norm(embedding)
        
        recognition_pool.process_face(
            embedding,
            face_id=i,
            frame_id=frame_id,
            persistent_id=f"face_{i}"
        )
        face_ids.append(i)
    
    # Wait for processing
    time.sleep(2)
    
    # Collect results
    results = []
    max_attempts = 50
    attempts = 0
    
    while len(results) < len(face_ids) and attempts < max_attempts:
        result = recognition_pool.get_result()
        if result:
            results.append(result)
        attempts += 1
        time.sleep(0.1)
    
    # Verify batch processing
    assert len(results) > 0
    for result in results:
        assert result.face_id in face_ids
        assert isinstance(result.cache_hit, bool)

def test_cache_hit_performance(recognition_pool, sample_embedding):
    """Test performance improvement from cache hits."""
    # First recognition (cache miss)
    recognition_pool.process_face(
        sample_embedding,
        face_id=1,
        frame_id=0,
        persistent_id="test_face"
    )
    
    # Wait for processing
    time.sleep(1)
    
    # Get result and processing time for cache miss
    miss_result = recognition_pool.get_result()
    miss_time = miss_result.processing_time if miss_result else float('inf')
    
    # Second recognition of same face (should be cache hit)
    recognition_pool.process_face(
        sample_embedding,
        face_id=2,
        frame_id=0,
        persistent_id="test_face"
    )
    
    # Get result and verify cache hit is faster
    hit_result = recognition_pool.get_result()
    
    assert hit_result is not None
    assert hit_result.cache_hit
    assert hit_result.processing_time < miss_time

def test_memory_pressure_handling(recognition_pool):
    """Test handling of memory pressure situations."""
    # Monitor initial memory
    initial_memory = psutil.virtual_memory().percent
    
    # Generate many unique embeddings to stress memory
    faces_processed = 0
    max_faces = 1000
    
    while faces_processed < max_faces:
        # Create new random embedding
        embedding = np.random.randn(512).astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)
        
        recognition_pool.process_face(
            embedding,
            face_id=faces_processed,
            frame_id=0,
            persistent_id=f"test_{faces_processed}"
        )
        
        faces_processed += 1
        
        # Check memory usage
        current_memory = psutil.virtual_memory().percent
        if current_memory > recognition_pool.memory_pressure_threshold * 100:
            break
    
    # Verify memory pressure handling
    assert faces_processed > 0
    assert psutil.virtual_memory().percent <= 95  # Should not reach critical levels

def test_cpu_utilization(recognition_pool, sample_embedding):
    """Test CPU utilization and thread affinity."""
    # Get initial CPU usage
    initial_cpu = psutil.cpu_percent(interval=0.1)
    
    # Process multiple faces
    for i in range(20):
        embedding = sample_embedding + np.random.randn(512) * 0.1
        embedding = embedding / np.linalg.norm(embedding)
        
        recognition_pool.process_face(
            embedding,
            face_id=i,
            frame_id=0,
            persistent_id=f"test_{i}"
        )
    
    # Let processing happen
    time.sleep(2)
    
    # Check CPU usage
    cpu_usage = psutil.cpu_percent(interval=0.1)
    
    # Verify CPU usage is within expected range
    assert cpu_usage <= recognition_pool.cpu_threshold * 100 + 10  # Allow 10% margin

def test_error_handling(recognition_pool):
    """Test error handling with invalid inputs."""
    # Test with None embedding
    recognition_pool.process_face(
        face_embedding=None,
        face_id=1,
        frame_id=0,
        persistent_id="test"
    )
    
    # Test with invalid embedding shape
    invalid_embedding = np.random.randn(100).astype(np.float32)  # Wrong size
    recognition_pool.process_face(
        face_embedding=invalid_embedding,
        face_id=2,
        frame_id=0,
        persistent_id="test"
    )
    
    # Verify pool continues to function
    valid_embedding = np.random.randn(512).astype(np.float32)
    valid_embedding = valid_embedding / np.linalg.norm(valid_embedding)
    
    recognition_pool.process_face(
        face_embedding=valid_embedding,
        face_id=3,
        frame_id=0,
        persistent_id="test"
    )
    
    time.sleep(1)
    result = recognition_pool.get_result()
    assert result is not None
    assert result.face_id == 3

def test_shutdown_cleanup(recognition_pool, sample_embedding):
    """Test proper cleanup during shutdown."""
    # Submit some faces
    for i in range(5):
        recognition_pool.process_face(
            sample_embedding,
            face_id=i,
            frame_id=0,
            persistent_id=f"test_{i}"
        )
    
    # Shutdown pool
    recognition_pool.shutdown()
    
    # Verify cleanup
    assert len(recognition_pool.workers) == 0
    assert recognition_pool.embedding_cache is None
    assert len(recognition_pool.batch_buffer) == 0
    assert recognition_pool.input_queue.empty()
    assert recognition_pool.result_queue.empty()

if __name__ == '__main__':
    pytest.main([__file__])