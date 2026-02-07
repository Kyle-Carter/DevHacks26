"""
Pose detection using MediaPipe Pose.
Extracts key landmarks for movement detection.
"""

import mediapipe as mp
import cv2
import numpy as np

class PoseDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
    def detect(self, frame):
        """
        Detect pose in frame and return landmarks.
        Returns dict with normalized landmark positions.
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)
        
        if not results.pose_landmarks:
            return None
            
        landmarks = results.pose_landmarks.landmark
        
        # Extract key landmarks for movement detection
        return {
            'nose': self._get_point(landmarks[self.mp_pose.PoseLandmark.NOSE]),
            'left_shoulder': self._get_point(landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]),
            'right_shoulder': self._get_point(landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]),
            'left_hip': self._get_point(landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]),
            'right_hip': self._get_point(landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP]),
            'left_knee': self._get_point(landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE]),
            'right_knee': self._get_point(landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE]),
            'left_ankle': self._get_point(landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE]),
            'right_ankle': self._get_point(landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE]),
        }
    
    def _get_point(self, landmark):
        """Extract x, y, visibility from landmark."""
        return {
            'x': landmark.x,
            'y': landmark.y,
            'visibility': landmark.visibility
        }
    
    def draw_landmarks(self, frame, draw=True):
        """Draw pose landmarks on frame for debugging."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)
        
        if results.pose_landmarks and draw:
            self.mp_draw.draw_landmarks(
                frame, 
                results.pose_landmarks, 
                self.mp_pose.POSE_CONNECTIONS
            )
        
        return frame
    
    def close(self):
        """Release resources."""
        self.pose.close()
