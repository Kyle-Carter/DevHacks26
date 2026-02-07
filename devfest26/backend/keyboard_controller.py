"""
Keyboard controller using pynput.
Simulates key presses based on detected movements.
"""

from pynput.keyboard import Key, Controller
import time

class KeyboardController:
    def __init__(self):
        self.keyboard = Controller()
        
        # Map from movement names to key codes
        self.key_map = {
            'Space': Key.space,
            'ArrowUp': Key.up,
            'ArrowDown': Key.down,
            'ArrowLeft': Key.left,
            'ArrowRight': Key.right,
            'KeyW': 'w',
            'KeyA': 'a',
            'KeyS': 's',
            'KeyD': 'd',
        }
        
        # Movement to key bindings (configured from frontend)
        self.bindings = {
            'jump': 'ArrowUp',
            'squat': 'ArrowDown',
            'moveLeft': 'ArrowLeft',
            'moveRight': 'ArrowRight'
        }
        
        # Track currently pressed keys to enable hold behavior
        self.pressed_keys = set()
        
    def set_bindings(self, bindings):
        """Update movement-to-key bindings from frontend."""
        self.bindings = bindings
        print(f"Updated key bindings: {bindings}")
        
    def on_movement(self, movements):
        """
        Handle detected movements by pressing corresponding keys.
        movements: dict with boolean for each movement type
        """
        for movement, active in movements.items():
            if movement not in self.bindings:
                continue
                
            key_code = self.bindings.get(movement)
            if not key_code:
                continue
                
            key = self.key_map.get(key_code)
            if not key:
                continue
            
            if active:
                self._press_key(key)
            # Note: We use tap (press+release) for most game inputs
    
    def _press_key(self, key):
        """Press and release a key."""
        self.keyboard.press(key)
        time.sleep(0.05)  # Short hold for game registration
        self.keyboard.release(key)
        print(f"⌨️ Key pressed: {key}")
    
    def hold_key(self, key, hold=True):
        """Hold or release a key for continuous movement."""
        if hold:
            if key not in self.pressed_keys:
                self.keyboard.press(key)
                self.pressed_keys.add(key)
        else:
            if key in self.pressed_keys:
                self.keyboard.release(key)
                self.pressed_keys.discard(key)
    
    def release_all(self):
        """Release all held keys."""
        for key in list(self.pressed_keys):
            self.keyboard.release(key)
        self.pressed_keys.clear()
