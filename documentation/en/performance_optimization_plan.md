# Performance Optimization Plan

## Current State
- FPS range: 10-20 FPS
- Detection pool: 4 worker threads
- Frame buffer size: 10 frames
- Display: LANCZOS resampling

## Target State
- Target FPS: 45 FPS average
- Implementation across three key areas

## 1. Processing Optimizations
### Worker Thread Enhancement
```python
# detection_pool.py changes
class FaceDetectionPool:
    def __init__(self, num_workers: int = 6):  # Increased from 4
        self.num_workers = num_workers
        self.skip_frames = False
        self.batch_size = 2
```

### Frame Skipping Implementation
```python
def process_frame(self, frame: np.ndarray) -> int:
    if self.skip_frames and self.input_queue.qsize() > self.num_workers * 2:
        return -1  # Skip frame if we're falling behind
    # ... rest of implementation
```

### Batch Processing
```python
def _detection_worker(self):
    while self.active:
        frames = []
        frame_ids = []
        
        # Collect batch of frames
        for _ in range(self.batch_size):
            try:
                frame_id, frame = self.input_queue.get(timeout=0.1)
                frames.append(frame)
                frame_ids.append(frame_id)
            except:
                break
                
        if frames:
            # Process batch
            results = face_app.get_batch(frames)
            # Queue results
            for i, faces in enumerate(results):
                result = DetectionResult(faces, frame_ids[i], processing_time)
                self.result_queue.put(result)
```

## 2. Memory Management
### Enhanced Frame Buffer
```python
# frame_buffer.py changes
class ThreadSafeFrameBuffer:
    def __init__(self, max_size: int = 30):  # Increased from 10
        self.max_size = max_size
        self._frame_pool = []  # Memory pool for frame objects
```

### Smart Frame Dropping
```python
def put_frame(self, frame: np.ndarray) -> bool:
    if self._buffer.full():
        try:
            # Drop oldest frame when buffer is full
            self._buffer.get(block=False)
        except:
            pass
    # ... rest of implementation
```

### Memory Pooling
```python
def _get_frame_from_pool(self):
    if self._frame_pool:
        return self._frame_pool.pop()
    return None

def _return_frame_to_pool(self, frame):
    if len(self._frame_pool) < self.max_size:
        self._frame_pool.append(frame)
```

## 3. Display Pipeline
### Optimized Image Processing
```python
# camera_view.py changes
class CameraFrame:
    def __init__(self):
        self._last_dimensions = None
        self._cached_image = None
        
    def update_frame(self, frame):
        # Convert color space more efficiently
        if frame.shape[2] == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
        # Cache resized images
        current_dims = (self.winfo_width(), self.winfo_height())
        if self._last_dimensions != current_dims:
            self._cached_image = None
            
        if self._cached_image is None:
            # Use BILINEAR resampling instead of LANCZOS
            image = cv2.resize(frame, current_dims, 
                             interpolation=cv2.INTER_LINEAR)
            self._cached_image = ImageTk.PhotoImage(Image.fromarray(image))
            self._last_dimensions = current_dims
```

## Implementation Steps

1. Phase 1 - Processing Optimizations
   - Update DetectionPool initialization
   - Implement frame skipping
   - Add batch processing support

2. Phase 2 - Memory Management
   - Increase buffer size
   - Implement smart frame dropping
   - Add memory pooling

3. Phase 3 - Display Pipeline
   - Update resampling method
   - Add image caching
   - Optimize color conversion

## Testing and Validation

After each phase:
1. Measure FPS using cv2.getTickCount()
2. Monitor CPU and memory usage
3. Verify face detection accuracy is maintained
4. Check for frame dropping or stuttering

## Expected Metrics

- Processing Optimizations: +15-20 FPS
- Memory Management: +5-8 FPS
- Display Pipeline: +8-10 FPS
- Target Average: 45 FPS

## Rollback Plan

Keep original implementations in separate files:
- detection_pool_original.py
- frame_buffer_original.py
- camera_view_original.py

This allows quick rollback if performance degrades or issues arise.