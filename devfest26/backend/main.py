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
                print(f"📩 Received: {data}")
                
                if data['type'] == 'config':
                    # Update key bindings from frontend
                    self.keyboard_controller.set_bindings(data['mappings'])
                    await websocket.send(json.dumps({'type': 'config_ack'}))
                    
                elif data['type'] == 'start':
                    self.start_detection()
                    await websocket.send(json.dumps({'type': 'started'}))
                    
                elif data['type'] == 'stop':
                    self.stop_detection()
                    await websocket.send(json.dumps({'type': 'stopped'}))
                    
                elif data['type'] == 'recalibrate':
                    self.movement_analyzer.reset_calibration()
                    await websocket.send(json.dumps({'type': 'recalibrating'}))
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Frontend disconnected")
        finally:
            self.stop_detection()
            self.websocket = None
    
    def start_detection(self):
        """Start the pose detection loop."""
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
        
        self.capture_thread = threading.Thread(target=self._capture_loop)
        self.capture_thread.start()
        print("🎥 Motion detection started!")
        print("📍 Stand in view of camera and stay still for calibration...")
    
    def stop_detection(self):
        """Stop the pose detection loop."""
        self.running = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
            self.capture_thread = None
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        cv2.destroyAllWindows()
        self.keyboard_controller.release_all()
        print("🛑 Motion detection stopped")
    
    def _capture_loop(self):
        """Main capture and detection loop."""
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

async def main():
    """Main entry point."""
    print("=" * 50)
    print("🎮 MotionPlay Backend Server")
    print("=" * 50)
    print("Waiting for frontend connection on ws://localhost:8765")
    print("Press 'q' in preview window to quit")
    print("Press 'r' in preview window to recalibrate")
    print("=" * 50)
    
    backend = MotionPlayBackend()
    
    # Start detection immediately for standalone testing
    backend.start_detection()
    
    async with websockets.serve(backend.handle_client, "localhost", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
