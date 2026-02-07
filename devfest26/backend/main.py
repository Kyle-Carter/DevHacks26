"""
MotionPlay Backend Server
WebSocket server that captures webcam, detects poses, and simulates keyboard input.
"""

import asyncio
import json
import cv2
import websockets
import threading
from pose_detector import PoseDetector
from movement_analyzer import MovementAnalyzer
from keyboard_controller import KeyboardController

class MotionPlayBackend:
    def __init__(self):
        self.pose_detector = PoseDetector()
        self.movement_analyzer = MovementAnalyzer()
        self.keyboard_controller = KeyboardController()
        
        self.running = False
        self.capture_thread = None
        self.cap = None
        self.websocket = None
        self.show_preview = True  # Show webcam preview window
        
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
                    self.keyboard_controller.set_bindings(data['mappings'])
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
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            print("❌ Error: Could not open webcam")
            self.running = False
            return
        
        # Set camera properties for better performance
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("🎥 Camera initialized!")
        print("📍 Stand in view of camera and stay still for calibration...")
    
    def stop_detection(self):
        """Stop the pose detection loop."""
        self.running = False
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        cv2.destroyAllWindows()
        self.keyboard_controller.release_all()
        print("🛑 Motion detection stopped")
    
    def run_capture_loop(self):
        """Main capture and detection loop. MUST RUN ON MAIN THREAD."""
        if not self.running:
            return

        print("🎥 Starting capture loop...")
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
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
                
                # Add status text
                status = "Calibrating..." if self.movement_analyzer.frame_count <= 30 else "Active"
                cv2.putText(preview, f"MotionPlay - {status}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Show active movements
                y_offset = 60
                for movement, active in movements.items():
                    if active:
                        cv2.putText(preview, f"► {movement.upper()}", (10, y_offset),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                        y_offset += 25
                
                cv2.imshow('MotionPlay Preview', preview)
                
                # Handle key press for preview window
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.running = False
                elif key == ord('r'):
                    self.movement_analyzer.reset_calibration()
        
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
    main()
