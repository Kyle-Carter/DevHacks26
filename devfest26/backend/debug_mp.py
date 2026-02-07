
import sys
import os
import mediapipe

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current working directory: {os.getcwd()}")

try:
    print(f"mediapipe version: {getattr(mediapipe, '__version__', 'unknown')}")
    print(f"mediapipe file: {getattr(mediapipe, '__file__', 'unknown')}")
    # print(f"mediapipe dir: {dir(mediapipe)}") # Too verbose
    
    if hasattr(mediapipe, 'solutions'):
        print("mediapipe.solutions found")
    else:
        print("mediapipe.solutions NOT found")
except Exception as e:
    print(f"Error: {e}")
