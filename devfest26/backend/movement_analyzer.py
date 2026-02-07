"""
Movement analyzer that detects specific movements from pose landmarks.
Supports: Jump, Squat, Move Left, Move Right
"""

import numpy as np
from collections import deque

class MovementAnalyzer:
    def __init__(self):
        # Baseline calibration values
        self.baseline_hip_y = None
        self.baseline_shoulder_x = None
        
        # History for smoothing
        self.hip_y_history = deque(maxlen=10)
        self.shoulder_x_history = deque(maxlen=10)
        self.knee_angle_history = deque(maxlen=10)
        
        # Thresholds (tuned for typical webcam setup)
        self.jump_threshold = 0.10      # How much hip must rise (Increased from 0.05)
        self.squat_threshold = 0.10     # How much hip must lower (Increased from 0.08)
        self.lateral_threshold = 0.08   # How much shoulder center must shift (Increased from 0.06)
        
        # Cooldown to prevent repeated triggers
        self.movement_cooldowns = {
            'jump': 0,
            'squat': 0,
            'moveLeft': 0,
            'moveRight': 0
        }
        self.cooldown_frames = 15
        
        # Calibration frames
        self.calibration_frames = 30
        self.frame_count = 0
        self.calibration_hip_values = []
        self.calibration_shoulder_values = []
        
    def analyze(self, landmarks):
        """
        Analyze landmarks and return detected movements.
        Returns dict with boolean for each movement type.
        """
        if landmarks is None:
            return {'jump': False, 'squat': False, 'moveLeft': False, 'moveRight': False}
        
        # Calculate key metrics
        hip_center_y = (landmarks['left_hip']['y'] + landmarks['right_hip']['y']) / 2
        shoulder_center_x = (landmarks['left_shoulder']['x'] + landmarks['right_shoulder']['x']) / 2
        
        # Add to history
        self.hip_y_history.append(hip_center_y)
        self.shoulder_x_history.append(shoulder_center_x)
        
        # Calibration phase
        self.frame_count += 1
        if self.frame_count <= self.calibration_frames:
            self.calibration_hip_values.append(hip_center_y)
            self.calibration_shoulder_values.append(shoulder_center_x)
            
            if self.frame_count == self.calibration_frames:
                self.baseline_hip_y = np.mean(self.calibration_hip_values)
                self.baseline_shoulder_x = np.mean(self.calibration_shoulder_values)
                print(f"Calibrated - Hip Y: {self.baseline_hip_y:.3f}, Shoulder X: {self.baseline_shoulder_x:.3f}")
            
            return {'jump': False, 'squat': False, 'moveLeft': False, 'moveRight': False}
        
        # Decrement cooldowns
        for key in self.movement_cooldowns:
            if self.movement_cooldowns[key] > 0:
                self.movement_cooldowns[key] -= 1
        
        movements = {
            'jump': False,
            'squat': False,
            'moveLeft': False,
            'moveRight': False
        }
        
        # Smoothed values
        smooth_hip_y = np.mean(list(self.hip_y_history))
        smooth_shoulder_x = np.mean(list(self.shoulder_x_history))
        
        # Detect JUMP (hip rises - Y decreases in image coordinates)
        hip_delta = self.baseline_hip_y - smooth_hip_y
        if hip_delta > self.jump_threshold and self.movement_cooldowns['jump'] == 0:
            movements['jump'] = True
            self.movement_cooldowns['jump'] = self.cooldown_frames
            print("🦘 JUMP detected!")
        
        # Detect SQUAT (hip lowers - Y increases in image coordinates)
        elif hip_delta < -self.squat_threshold and self.movement_cooldowns['squat'] == 0:
            movements['squat'] = True
            self.movement_cooldowns['squat'] = self.cooldown_frames
            print("🧎 SQUAT detected!")
        
        # Detect MOVE LEFT (shoulders shift left - X decreases)
        shoulder_delta = self.baseline_shoulder_x - smooth_shoulder_x
        if shoulder_delta > self.lateral_threshold and self.movement_cooldowns['moveLeft'] == 0:
            movements['moveLeft'] = True
            self.movement_cooldowns['moveLeft'] = self.cooldown_frames
            print("👈 MOVE LEFT detected!")
        
        # Detect MOVE RIGHT (shoulders shift right - X increases)
        elif shoulder_delta < -self.lateral_threshold and self.movement_cooldowns['moveRight'] == 0:
            movements['moveRight'] = True
            self.movement_cooldowns['moveRight'] = self.cooldown_frames
            print("👉 MOVE RIGHT detected!")
        
        return movements
    
    def reset_calibration(self):
        """Reset calibration to recalibrate."""
        self.baseline_hip_y = None
        self.baseline_shoulder_x = None
        self.frame_count = 0
        self.calibration_hip_values = []
        self.calibration_shoulder_values = []
        self.hip_y_history.clear()
        self.shoulder_x_history.clear()
        print("Calibration reset - please stand still for calibration")
