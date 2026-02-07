"""
MotionPlay Backend Server
WebSocket server that captures webcam, detects poses, and simulates keyboard input.
"""

import asyncio
import json
import cv2
import websockets
import threading
import time
import sys
from pose_detector import PoseDetector
from movement_analyzer import MovementAnalyzer
from keyboard_controller import KeyboardController

class ThreadedCamera:
    """
    Dedicated thread for grabbing frames from the camera.
    This prevents the main loop from getting stuck processing old buffered frames.
    """
    def __init__(self, src=0):
        self.capture = cv2.VideoCapture(src)
        # Optimize camera settings immediately
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.capture.set(cv2.CAP_PROP_FPS, 30)
        # self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Specific to backend, might not work on all
        
        self.lock = threading.Lock()
        self.frame = None
        self.ret = False
        self.running = False
        self.thread = None

    def start(self):
        if self.running: return self
        self.running = True
        self.thread = threading.Thread(target=self.update, args=(), daemon=True)
        self.thread.start()
        return self

    def update(self):
        while self.running:
            if self.capture.isOpened():
                ret, frame = self.capture.read()
                with self.lock:
                    self.ret = ret
                    self.frame = frame
            else:
                time.sleep(0.1)

    def read(self):
        with self.lock:
            return self.ret, self.frame

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        self.capture.release()

class MotionPlayBackend:
    def __init__(self):
        self.pose_detector = PoseDetector()
        self.movement_analyzer = MovementAnalyzer()
        self.keyboard_controller = KeyboardController()
        
        self.running = False
        self.capture_thread = None
        self.cap = None # Will hold ThreadedCamera instance
        self.websocket = None
        self.show_preview = True
        
    async def handle_client(self, websocket):
        """Handle WebSocket connection from frontend."""
        print("🔌 Frontend connected!")
        self.websocket = websocket
        
        try:
            async for message in websocket:
                data = json.loads(message)
                # print(f"📩 Received: {data}") # Reduce verbosity
                
                if data['type'] == 'config':
                    # Update key bindings from frontend
                    if 'mappings' in data and data['mappings']:
                        self.keyboard_controller.set_bindings(data['mappings'])
                    
                    # Update sensitivity settings
                    if 'sensitivity' in data and data['sensitivity']:
                        self.movement_analyzer.update_config(data['sensitivity'])
                        
                    await websocket.send(json.dumps({'type': 'config_ack'}))
                    
                elif data['type'] == 'start':
                    # Camera is already running in main thread, just acknowledge
                    # We could add logic to pause/resume detection processing if needed
                    await websocket.send(json.dumps({'type': 'started'}))
                    
                elif data['type'] == 'stop':
                    # Don't actually stop the camera loop, just acknowledge
                    await websocket.send(json.dumps({'type': 'stopped'}))
                    
                elif data['type'] == 'recalibrate':
                    self.movement_analyzer.reset_calibration()
                    await websocket.send(json.dumps({'type': 'recalibrating'}))
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Frontend disconnected")
        finally:
            self.websocket = None
    
    def start_detection(self):
        """Initialize camera for detection (called before loop)."""
        if self.running:
            return
            
        self.running = True
        # Initialize Threaded Camera
        try:
            self.cap = ThreadedCamera(0).start()
            print("🎥 Threaded Camera initialized!")
            print("📍 Stand in view of camera and stay still for calibration...")
        except Exception as e:
            print(f"❌ Error initializing camera: {e}")
            self.running = False
    
    def stop_detection(self):
        """Stop the pose detection loop."""
        self.running = False
        
        if self.cap:
            self.cap.stop()
            self.cap = None
        
        cv2.destroyAllWindows()
        self.keyboard_controller.release_all()
        print("🛑 Motion detection stopped")
    
    def run_capture_loop(self):
        """Main capture and detection loop. MUST RUN ON MAIN THREAD."""
        if not self.running or not self.cap:
            return

        try:
            print("🎥 Starting capture loop...")
            frame_count = 0
            start_time = time.time()
            
            while self.running:
                ret, frame = self.cap.read()
                
                if not ret or frame is None:
                    # Thread might be starting up
                    time.sleep(0.01)
                    continue
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Detect pose
                landmarks = self.pose_detector.detect(frame)
                
                # Analyze movements
                movements = self.movement_analyzer.analyze(landmarks)
                
                # Trigger keyboard input
                self.keyboard_controller.on_movement(movements)
                
                # Show preview window
                if self.show_preview:
                    preview = self.pose_detector.draw_landmarks(frame.copy())
                    
                    # Draw Bounding Box Feedback (Safe Zone, Labels, Calibration)
                    preview = self.movement_analyzer.draw_feedback(preview)
                    
                    # FPS Counter
                    frame_count += 1
                    elapsed = time.time() - start_time
                    if elapsed > 1.0:
                        fps = frame_count / elapsed
                        frame_count = 0
                        start_time = time.time()
                        print(f"⚡ FPS: {fps:.1f}") # Log FPS to verify performance
                        
                    cv2.putText(preview, f"FPS: {int(frame_count / max(elapsed, 0.001))}", (10, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    cv2.imshow('MotionPlay Preview', preview)
                    
                    # Handle key press for preview window
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        self.running = False
                    elif key == ord('r'):
                        self.movement_analyzer.reset_calibration()
        finally:
            self.stop_detection()


def run_server(backend):
    """Run WebSocket server in a separate thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def server_task():
        print("Waiting for frontend connection on ws://localhost:8765")
        async with websockets.serve(backend.handle_client, "localhost", 8765):
            await asyncio.Future()  # Run forever
            
    loop.run_until_complete(server_task())

def main():
    """Main entry point."""
    print("=" * 50)
    print("🎮 MotionPlay Backend Server")
    print("=" * 50)
    print("Press 'q' in preview window to quit")
    print("Press 'r' in preview window to recalibrate")
    print("=" * 50)
    
    backend = MotionPlayBackend()
    
    # Initialize camera
    backend.start_detection()
    
    # Start WebSocket server in background thread
    server_thread = threading.Thread(target=run_server, args=(backend,), daemon=True)
    server_thread.start()
    
    # Run capture loop on main thread (required for macOS OpenCV)
    try:
        backend.run_capture_loop()
    except KeyboardInterrupt:
        print("\nStopping...")
        backend.stop_detection()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
