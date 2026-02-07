"""
Pose detection using MediaPipe Tasks API.
Extracts key landmarks for movement detection.
"""

import mediapipe as mp
import cv2
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class PoseDetector:
    def __init__(self):
        # Create an PoseLandmarker object.
        base_options = python.BaseOptions(model_asset_path='pose_landmarker_lite.task')
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            output_segmentation_masks=False)
        self.detector = vision.PoseLandmarker.create_from_options(options)
        
        # Define connection pairs for consistent drawing
        # These correspond to standard MediaPipe Pose topology
        self.POSE_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5),
            (5, 6), (6, 8), (9, 10), (11, 12), (11, 13),
            (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
            (12, 14), (14, 16), (16, 18), (16, 20), (16, 22),
            (18, 20), (11, 23), (12, 24), (23, 24), (23, 25),
            (24, 26), (25, 27), (26, 28), (27, 29), (28, 30),
            (29, 31), (30, 32), (27, 31), (28, 32)
        ]

    def detect(self, frame):
        """
        Detect pose in frame and return landmarks.
        Returns dict with normalized landmark positions.
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        detection_result = self.detector.detect(mp_image)
        
        if not detection_result.pose_landmarks:
            return None
            
        # Get the first detected pose
        landmarks = detection_result.pose_landmarks[0]
        
        # Extract key landmarks for movement detection
        # Indices based on: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
        return {
            'nose': self._get_point(landmarks[0]),
            'left_shoulder': self._get_point(landmarks[11]),
            'right_shoulder': self._get_point(landmarks[12]),
            'left_hip': self._get_point(landmarks[23]),
            'right_hip': self._get_point(landmarks[24]),
            'left_knee': self._get_point(landmarks[25]),
            'right_knee': self._get_point(landmarks[26]),
            'left_ankle': self._get_point(landmarks[27]),
            'right_ankle': self._get_point(landmarks[28]),
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
        if not draw:
            return frame
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        detection_result = self.detector.detect(mp_image)
        
        if not detection_result.pose_landmarks:
            return frame

        landmarks = detection_result.pose_landmarks[0]
        height, width, _ = frame.shape

        # Draw connections
        for connection in self.POSE_CONNECTIONS:
            start_idx = connection[0]
            end_idx = connection[1]
            
            if start_idx >= len(landmarks) or end_idx >= len(landmarks):
                continue
                
            start_point = landmarks[start_idx]
            end_point = landmarks[end_idx]
            
            # Draw line only if both points are visible enough
            if start_point.visibility > 0.5 and end_point.visibility > 0.5:
                cv2.line(frame, 
                        (int(start_point.x * width), int(start_point.y * height)), 
                        (int(end_point.x * width), int(end_point.y * height)), 
                        (255, 255, 255), 2) # White lines

        # Draw landmarks
        for landmark in landmarks:
             if landmark.visibility > 0.5:
                cv2.circle(frame, 
                          (int(landmark.x * width), int(landmark.y * height)), 
                          5, (0, 0, 255), -1) # Red dots
        
        return frame
    
    def close(self):
        """Release resources."""
        # Tasks API doesn't strictly require explicit close like solutions, 
        # but good to keep structure if we add cleanup later.
        pass

