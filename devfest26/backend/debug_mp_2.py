
import sys
import mediapipe

print(f"mediapipe dir: {dir(mediapipe)}")

try:
    import mediapipe.solutions
    print("Successfully imported mediapipe.solutions")
except ImportError as e:
    print(f"Failed to import mediapipe.solutions: {e}")

try:
    from mediapipe import solutions
    print("Successfully imported solutions from mediapipe")
except ImportError as e:
    print(f"Failed to import solutions from mediapipe: {e}")
