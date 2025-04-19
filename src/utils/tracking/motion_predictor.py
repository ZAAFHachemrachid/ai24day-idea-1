import numpy as np
from filterpy.kalman import KalmanFilter
from typing import Tuple, Dict, Optional

class MotionPredictor:
    """
    Handles motion prediction using Kalman filtering to predict face positions
    and movement patterns.
    """
    def __init__(self, dt: float = 0.1):
        """
        Initialize the motion predictor
        
        Args:
            dt (float): Time step between measurements/predictions
        """
        # Initialize Kalman filter with 6 state variables (x, y, vx, vy, ax, ay)
        # and 2 measurement variables (x, y)
        self.kf = KalmanFilter(dim_x=6, dim_z=2)
        self.dt = dt
        
        # State transition matrix
        self.kf.F = np.array([
            [1, 0, dt, 0, 0.5*dt**2, 0],    # x = x + vx*dt + 0.5*ax*dt^2
            [0, 1, 0, dt, 0, 0.5*dt**2],    # y = y + vy*dt + 0.5*ay*dt^2
            [0, 0, 1, 0, dt, 0],            # vx = vx + ax*dt
            [0, 0, 0, 1, 0, dt],            # vy = vy + ay*dt
            [0, 0, 0, 0, 1, 0],             # ax = ax
            [0, 0, 0, 0, 0, 1]              # ay = ay
        ])
        
        # Measurement matrix (we only measure position)
        self.kf.H = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0]
        ])
        
        # Measurement noise
        self.kf.R = np.eye(2) * 10
        
        # Process noise
        self.kf.Q = np.eye(6) * 0.1
        
        # Initial state covariance
        self.kf.P = np.eye(6) * 1000
        
        # Track prediction confidence
        self.confidence = 1.0
        self.prediction_history = []
        self.max_history = 10
        
    def initialize(self, x: float, y: float) -> None:
        """
        Initialize the Kalman filter with a starting position
        
        Args:
            x (float): Initial x position
            y (float): Initial y position
        """
        self.kf.x = np.array([x, y, 0, 0, 0, 0])
        self.prediction_history = [(x, y)]
        self.confidence = 1.0
        
    def predict(self) -> Tuple[float, float]:
        """
        Predict the next position
        
        Returns:
            Tuple[float, float]: Predicted (x, y) position
        """
        self.kf.predict()
        predicted_pos = (self.kf.x[0], self.kf.x[1])
        
        # Update prediction history
        self.prediction_history.append(predicted_pos)
        if len(self.prediction_history) > self.max_history:
            self.prediction_history.pop(0)
            
        # Update confidence based on prediction variance
        position_variance = np.trace(self.kf.P[:2, :2])
        self.confidence = 1.0 / (1.0 + position_variance)
        
        return predicted_pos
        
    def update(self, x: float, y: float) -> None:
        """
        Update the filter with a new measurement
        
        Args:
            x (float): Measured x position
            y (float): Measured y position
        """
        measurement = np.array([x, y])
        self.kf.update(measurement)
        
        # Calculate prediction error
        predicted = np.array(self.prediction_history[-1])
        measured = np.array([x, y])
        error = np.linalg.norm(predicted - measured)
        
        # Update confidence based on prediction error
        self.confidence *= 1.0 / (1.0 + error)
        self.confidence = max(0.1, min(1.0, self.confidence))
        
    def get_velocity(self) -> Tuple[float, float]:
        """
        Get current velocity estimate
        
        Returns:
            Tuple[float, float]: Velocity vector (vx, vy)
        """
        return self.kf.x[2], self.kf.x[3]
        
    def get_acceleration(self) -> Tuple[float, float]:
        """
        Get current acceleration estimate
        
        Returns:
            Tuple[float, float]: Acceleration vector (ax, ay)
        """
        return self.kf.x[4], self.kf.x[5]
        
    def get_confidence(self) -> float:
        """
        Get current prediction confidence
        
        Returns:
            float: Confidence value between 0 and 1
        """
        return self.confidence
        
    def get_search_region(self, frame_width: int, frame_height: int) -> Tuple[int, int, int, int]:
        """
        Calculate the search region for the next frame based on predictions
        
        Args:
            frame_width (int): Width of the frame
            frame_height (int): Height of the frame
            
        Returns:
            Tuple[int, int, int, int]: Search region (x, y, w, h)
        """
        predicted_x, predicted_y = self.predict()
        velocity_x, velocity_y = self.get_velocity()
        
        # Calculate search window size based on velocity and confidence
        window_size = int(100 * (1 + np.linalg.norm([velocity_x, velocity_y]) * (1 - self.confidence)))
        
        # Calculate search region
        x = max(0, int(predicted_x - window_size/2))
        y = max(0, int(predicted_y - window_size/2))
        w = min(window_size, frame_width - x)
        h = min(window_size, frame_height - y)
        
        return x, y, w, h