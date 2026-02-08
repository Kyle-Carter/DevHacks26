"""
Keyboard controller using pynput.
Simulates key presses based on detected movements.
"""

from pynput.keyboard import Key, Controller
import time
import sys
import ctypes
import threading

# Windows DirectInput Structures
if sys.platform == 'win32':
    LONG = ctypes.c_long
    DWORD = ctypes.c_ulong
    ULONG_PTR = ctypes.POINTER(DWORD)
    WORD = ctypes.c_ushort

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = (('dx', LONG), ('dy', LONG), ('mouseData', DWORD), ('dwFlags', DWORD), ('time', DWORD), ('dwExtraInfo', ULONG_PTR))

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = (('wVk', WORD), ('wScan', WORD), ('dwFlags', DWORD), ('time', DWORD), ('dwExtraInfo', ULONG_PTR))

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = (('uMsg', DWORD), ('wParamL', WORD), ('wParamH', WORD))

    class INPUT(ctypes.Structure):
        class _INPUT(ctypes.Union):
            _fields_ = (('ki', KEYBDINPUT), ('mi', MOUSEINPUT), ('hi', HARDWAREINPUT))
        _anonymous_ = ('_input',)
        _fields_ = (('type', DWORD), ('_input', _INPUT))

    LPINPUT = ctypes.POINTER(INPUT)
    
    SendInput = ctypes.windll.user32.SendInput
    SendInput.argtypes = (ctypes.c_uint, LPINPUT, ctypes.c_int)
    SendInput.restype = ctypes.c_uint

    # Correct Hardware Scan Codes (DirectInput / PS/2 Set 1)
    # Reference: https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
    # Arrow keys are Extended Keys (E0 prefix), managed via flags.
    SCANCODE_MAP = {
        'Space': 0x39,
        'ArrowUp': 0x48,
        'ArrowDown': 0x50,
        'ArrowLeft': 0x4B,
        'ArrowRight': 0x4D,
        'w': 0x11,
        'a': 0x1E,
        's': 0x1F,
        'd': 0x20,
        'W': 0x11,
        'A': 0x1E,
        'S': 0x1F,
        'D': 0x20,
    }

    # Extended keys need flag 0x0001 (KEYEVENTF_EXTENDEDKEY)
    EXTENDED_KEYS = {'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'}

    def PressKey(hexKeyCode, isExtended=False):
        dwFlags = 0x0008 # KEYEVENTF_SCANCODE
        if isExtended:
            dwFlags |= 0x0001
        
        x = INPUT(type=1, ki=KEYBDINPUT(wVk=0, wScan=hexKeyCode, dwFlags=dwFlags, time=0, dwExtraInfo=None))
        SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

    def ReleaseKey(hexKeyCode, isExtended=False):
        dwFlags = 0x0008 | 0x0002 # KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
        if isExtended:
            dwFlags |= 0x0001
            
        x = INPUT(type=1, ki=KEYBDINPUT(wVk=0, wScan=hexKeyCode, dwFlags=dwFlags, time=0, dwExtraInfo=None))
        SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

class KeyboardController:
    def __init__(self):
        self.is_windows = sys.platform == 'win32'
        if not self.is_windows:
            self.keyboard = Controller()
        
        # Map from movement names to key codes (Standard)
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
        
        # Threading support
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        self.active_movements = set() # Movements currently triggered by pose
        self.pressed_keys = set() # Keys currently physically pressed
        
        # Minimum press duration
        self.MIN_PRESS_DURATION = 0.1 # seconds
        self.key_start_times = {} # Track when each key was pressed

    def start(self):
        """Start the background input thread."""
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._input_loop, daemon=True)
        self.thread.start()
        print("⌨️ Keyboard Controller Thread Started")

    def stop(self):
        """Stop the background input thread."""
        self.running = False
        if self.thread:
            self.thread.join()
        self.release_all()
        print("⌨️ Keyboard Controller Thread Stopped")

    def set_bindings(self, bindings):
        """Update movement-to-key bindings from frontend."""
        with self.lock:
            self.bindings = bindings
        print(f"Updated key bindings: {bindings}")
        
    def on_movement(self, movements):
        """
        Update active movements state. Non-blocking.
        movements: dict with boolean for each movement type
        """
        with self.lock:
            self.active_movements = {m for m, active in movements.items() if active}

    def _input_loop(self):
        """Background loop to handle key presses."""
        while self.running:
            try:
                current_time = time.time()
                
                with self.lock:
                    current_active = self.active_movements.copy()
                    current_bindings = self.bindings.copy()

                # Determine which keys SHOULD be pressed right now based on vision
                vision_target_keys = set()
                for movement in current_active:
                    if movement in current_bindings:
                        vision_target_keys.add(current_bindings[movement])

                # Determine keys that MUST stay pressed due to minimum duration
                min_duration_keys = set()
                for key in self.pressed_keys:
                    start_time = self.key_start_times.get(key, 0)
                    if current_time - start_time < self.MIN_PRESS_DURATION:
                        min_duration_keys.add(key)
                
                # Effective target includes vision targets AND keys that haven't been held long enough
                effective_target_keys = vision_target_keys | min_duration_keys

                # Identify keys to Press vs Release
                keys_to_press = effective_target_keys - self.pressed_keys
                keys_to_release = self.pressed_keys - effective_target_keys

                # Execute Releases first
                for key in keys_to_release:
                    self._release_key_internal(key)
                    self.pressed_keys.remove(key)
                    if key in self.key_start_times:
                        del self.key_start_times[key]

                # Execute Presses
                for key in keys_to_press:
                    self._press_key_internal(key)
                    self.pressed_keys.add(key)
                    self.key_start_times[key] = current_time
                
                # Sleep briefly to avoid high CPU usage, but keep responsive
                time.sleep(0.01)

            except Exception as e:
                print(f"Error in input loop: {e}")
                time.sleep(0.1)

    def _press_key_internal(self, key_str):
        """Perform the actual platform-specific key press."""
        if self.is_windows:
            # Use DirectInput Scan Codes
            scancode = SCANCODE_MAP.get(key_str) or SCANCODE_MAP.get(key_str.replace('Key', ''))
            is_extended = key_str in EXTENDED_KEYS
            
            if scancode:
                PressKey(scancode, is_extended)
                print(f"⌨️ [Win] Key DOWN: {key_str}")
            else:
                print(f"⚠️ [Win] Unknown key: {key_str}")
        else:
            # Standard Pynput
            key = self.key_map.get(key_str)
            if not key and len(key_str) == 1:
                key = key_str.lower()
                
            if key:
                self.keyboard.press(key)
                print(f"⌨️ Key DOWN: {key}")

    def _release_key_internal(self, key_str):
        """Perform the actual platform-specific key release."""
        if self.is_windows:
            scancode = SCANCODE_MAP.get(key_str) or SCANCODE_MAP.get(key_str.replace('Key', ''))
            is_extended = key_str in EXTENDED_KEYS
            
            if scancode:
                ReleaseKey(scancode, is_extended)
                print(f"⌨️ [Win] Key UP: {key_str}")
        else:
            key = self.key_map.get(key_str)
            if not key and len(key_str) == 1:
                key = key_str.lower()
                
            if key:
                self.keyboard.release(key)
                print(f"⌨️ Key UP: {key}")
    
    def release_all(self):
        """Release all held keys."""
        with self.lock:
            keys_to_release = list(self.pressed_keys)
            
        for key in keys_to_release:
            self._release_key_internal(key)
        
        self.pressed_keys.clear()
