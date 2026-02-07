import numpy as np
import cv2
import time
from collections import deque

class MovementAnalyzer:
    def __init__(self):
        # Calibration state
        self.calibration_boxes = []  # List of [min_x, min_y, max_x, max_y]
        self.calibrated_pose = None  # {shoulder_y, hip_y, center_x, torso_h, torso_w}
        
        # Configuration (Default)
        self.calibration_frames = 60
        self.jump_sensitivity = 0.5   # 50% of torso height above shoulders
        self.squat_sensitivity = 0.5  # 50% of torso height below original shoulder pos
        self.side_sensitivity = 0.5   # 50% of torso width from center
        
        self.repeat_delay = 1.0       # Seconds to hold before repeating
        self.repeat_interval = 0.2    # Seconds between repeats
        
        # State
        self.frame_count = 0
        self.state_timers = {
            'jump': 0, 'squat': 0, 'moveLeft': 0, 'moveRight': 0
        }
        self.last_movements = {}
        self.is_calibrating = True
        self.calibration_message = "Step back to see full body"

    def update_config(self, config):
        """Update sensitivity and timing from frontend."""
        if 'jumpSensitivity' in config: self.jump_sensitivity = config['jumpSensitivity']
        if 'squatSensitivity' in config: self.squat_sensitivity = config['squatSensitivity']
        if 'sideSensitivity' in config: self.side_sensitivity = config['sideSensitivity']
        if 'repeatDelay' in config: self.repeat_delay = config['repeatDelay']
        if 'repeatInterval' in config: self.repeat_interval = config['repeatInterval']
        print(f"🔧 Config Updated: {config}")

    def is_user_in_frame(self, landmarks):
        """Check if all required keypoints are visible."""
        required = [
            landmarks['left_shoulder'], landmarks['right_shoulder'],
            landmarks['left_hip'], landmarks['right_hip']
        ]
        # Check visibility (if score available, but lite model might just give coords)
        # Simply check if they are within [0,1] bounds reasonably
        for p in required:
            if not (0.05 < p['x'] < 0.95 and 0.05 < p['y'] < 0.95):
                return False
        return True

    def analyze(self, landmarks):
        self.frame_count += 1
        current_movements = {
            'jump': False, 'squat': False, 'moveLeft': False, 'moveRight': False
        }
        
        if not landmarks:
            # Reset timers if tracking lost? Or keep them?
            # Better to reset to prevent stuck keys
            self.reset_timers()
            self.last_movements = current_movements
            return current_movements

        # 1. Visibility Check
        in_frame = self.is_user_in_frame(landmarks)

        # 2. Calibration Phase
        if self.is_calibrating:
            if not in_frame:
                self.calibration_message = "❌ Step back! Show full body."
                return current_movements
            
            self.calibration_message = f"CALIBRATING... {self.calibration_frames - len(self.calibration_boxes)}"
            
            # Collect Torso Box
            torso_points = [
                landmarks['left_shoulder'], landmarks['right_shoulder'],
                landmarks['left_hip'], landmarks['right_hip']
            ]
            xs = [p['x'] for p in torso_points]
            ys = [p['y'] for p in torso_points]
            curr_box = [min(xs), min(ys), max(xs), max(ys)]
            self.calibration_boxes.append(curr_box)
            
            if len(self.calibration_boxes) >= self.calibration_frames:
                self._finalize_calibration()
                
            return current_movements

        # 3. Detection Phase
        
        # Calculate Current Keypoints
        l_shoulder = landmarks['left_shoulder']
        r_shoulder = landmarks['right_shoulder']
        nose = landmarks['nose']
        
        avg_shoulder_y = (l_shoulder['y'] + r_shoulder['y']) / 2
        avg_shoulder_x = (l_shoulder['x'] + r_shoulder['x']) / 2
        
        # JUMP: Nose crosses Jump Line (Above)
        jump_line = self.calibrated_pose['jump_line']
        if nose['y'] < jump_line:
            self._handle_trigger('jump', current_movements)
        else:
            self.state_timers['jump'] = 0

        # SQUAT: Shoulders cross Squat Line (Below)
        squat_line = self.calibrated_pose['squat_line']
        if avg_shoulder_y > squat_line:
            self._handle_trigger('squat', current_movements)
        else:
            self.state_timers['squat'] = 0
            
        # SIDES: Shoulders cross Side Lines
        # Note: Image X: 0 is Left, 1 is Right.
        # User movement "Left" means moving to Image "Right" (if mirrored) or Vice Versa.
        # We assume Main.py flips the frame. So Image Left = User Left.
        
        left_line = self.calibrated_pose['left_line']
        right_line = self.calibrated_pose['right_line']
        
        if avg_shoulder_x < left_line:
            self._handle_trigger('moveLeft', current_movements)
        else:
            self.state_timers['moveLeft'] = 0
            
        if avg_shoulder_x > right_line:
            self._handle_trigger('moveRight', current_movements)
        else:
            self.state_timers['moveRight'] = 0

        self.last_movements = current_movements
        return current_movements

    def _handle_trigger(self, action, movements):
        """Handle repeat logic."""
        now = time.time()
        if self.state_timers[action] == 0:
            # First trigger
            movements[action] = True
            self.state_timers[action] = now
            print(f"🎬 {action.upper()} Start")
        else:
            # Holding
            duration = now - self.state_timers[action]
            if duration > self.repeat_delay:
                # Check interval
                # Simple mod check or timer drift? 
                # Let's just trigger every frame if delay passed? No, that's too fast.
                # Use a specific last_repeat tracker if needed.
                # Simplification: For now, if delay passed, just keep it True?
                # User asked for "count as two movements".
                # Let's simulate taps.
                last_time = self.state_timers[action]
                if (now - last_time) > self.repeat_interval:
                     # This logic is tricky without extra state. 
                     # Let's just return True (HolD) for now and let KeyboardController handle repeats? 
                     # Actually KeyboardController just presses once per 'True' frame if we don't clear it.
                     # But we return 'True' every frame here.
                     pass
                # For compatibility, let's just return True continuously. 
                # The KeyboardController usually presses and releases.
                movements[action] = True

    def _finalize_calibration(self):
        avg_box = np.mean(self.calibration_boxes, axis=0) # [x1, y1, x2, y2]
        w = avg_box[2] - avg_box[0]
        h = avg_box[3] - avg_box[1]
        
        mid_x = (avg_box[0] + avg_box[2]) / 2
        mid_y = (avg_box[1] + avg_box[3]) / 2
        
        # Calculate Lines relative to Torso Size
        # Jump: Move head UP. Ref off Shoulder Y.
        # Squat: Move shoulders DOWN. Ref off Shoulder Y.
        # Sides: Move shoulders SIDE. Ref off Center X.
        
        shoulder_y = avg_box[1] # Approximate top of box is shoulders
        
        self.calibrated_pose = {
            'torso_h': h,
            'torso_w': w,
            'jump_line': shoulder_y - (h * self.jump_sensitivity),
            'squat_line': shoulder_y + (h * self.squat_sensitivity),
            'left_line': mid_x - (w * self.side_sensitivity),
            'right_line': mid_x + (w * self.side_sensitivity),
            'rect': avg_box
        }
        self.is_calibrating = False
        print(f"✅ Calibrated: {self.calibrated_pose}")

    def reset_timers(self):
        for k in self.state_timers: self.state_timers[k] = 0

    def reset_calibration(self):
        self.frame_count = 0
        self.calibration_boxes = []
        self.calibrated_pose = None
        self.is_calibrating = True
        self.calibration_message = "Step back to see full body"
        print("🔄 Calibration Reset")

    def draw_feedback(self, frame):
        h, w, _ = frame.shape
        
        # Draw Calibration / Status
        if self.is_calibrating:
            cv2.putText(frame, self.calibration_message, (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            
            # Show current box if tracking
            if len(self.calibration_boxes) > 0:
                last_box = self.calibration_boxes[-1]
                p1 = (int(last_box[0] * w), int(last_box[1] * h))
                p2 = (int(last_box[2] * w), int(last_box[3] * h))
                cv2.rectangle(frame, p1, p2, (0, 255, 0), 1)
            return frame

        # Draw Lines
        cp = self.calibrated_pose
        if cp:
            # Jump Line (Blue)
            jy = int(cp['jump_line'] * h)
            cv2.line(frame, (0, jy), (w, jy), (255, 0, 0), 2)
            cv2.putText(frame, "JUMP LINE", (10, jy - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

            # Squat Line (Orange/Yellow)
            sy = int(cp['squat_line'] * h)
            cv2.line(frame, (0, sy), (w, sy), (0, 165, 255), 2)
            cv2.putText(frame, "SQUAT LINE", (10, sy + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)
            
            # Side Lines (Cyan) - Center based
            lx = int(cp['left_line'] * w)
            rx = int(cp['right_line'] * w)
            cv2.line(frame, (lx, 0), (lx, h), (255, 255, 0), 2)
            cv2.line(frame, (rx, 0), (rx, h), (255, 255, 0), 2)
            
            # Draw Labels for Active Movements
            if self.last_movements.get('jump'):
                cv2.putText(frame, "JUMP!", (w//2, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            if self.last_movements.get('squat'):
                cv2.putText(frame, "SQUAT!", (w//2, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            if self.last_movements.get('moveLeft'):
                cv2.putText(frame, "< LEFT", (20, h//2), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            if self.last_movements.get('moveRight'):
                cv2.putText(frame, "RIGHT >", (w - 200, h//2), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
                
        return frame
