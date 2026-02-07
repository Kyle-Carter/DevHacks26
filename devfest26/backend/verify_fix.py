
import cv2
import numpy as np
import sys
import os

try:
    from pose_detector import PoseDetector
    
    print("Initializing PoseDetector...")
    detector = PoseDetector()
    print("PoseDetector initialized successfully.")
    
    # Create valid dummy image (black image)
    # MediaPipe expects RGB inputs
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    print("Running detection on dummy image...")
    result = detector.detect(img)
    print(f"Detection result: {result}") # Should be None or dict, not error
    
    print("Test drawing...")
    detector.draw_landmarks(img)
    print("Drawing completed.")
    
    print("SUCCESS: PoseDetector works without AttributeError")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
