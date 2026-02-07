"""
Keyboard controller using pynput.
Simulates key presses based on detected movements.
"""

from pynput.keyboard import Key, Controller
import time
import sys
import ctypes

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

    # DirectInput Scan Codes
    DI_K_SPACE = 0x39
    DI_K_UP = 0xC8
    DI_K_LEFT = 0xCB
    DI_K_RIGHT = 0xCD
    DI_K_DOWN = 0xD0
    DI_K_W = 0x11
    DI_K_A = 0x1E
    DI_K_S = 0x1F
    DI_K_D = 0x20

    SCANCODE_MAP = {
        'Space': DI_K_SPACE,
        'ArrowUp': DI_K_UP,
        'ArrowDown': DI_K_DOWN,
        'ArrowLeft': DI_K_LEFT,
        'ArrowRight': DI_K_RIGHT,
        'w': DI_K_W,
        'a': DI_K_A,
        's': DI_K_S,
        'd': DI_K_D,
        'W': DI_K_W,
        'A': DI_K_A,
        'S': DI_K_S,
        'D': DI_K_D,
    }

    def PressKey(hexKeyCode):
        x = INPUT(type=1, ki=KEYBDINPUT(wVk=0, wScan=hexKeyCode, dwFlags=0x0008, time=0, dwExtraInfo=None))
        SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

    def ReleaseKey(hexKeyCode):
        x = INPUT(type=1, ki=KEYBDINPUT(wVk=0, wScan=hexKeyCode, dwFlags=0x0008 | 0x0002, time=0, dwExtraInfo=None))
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
                
            key_code_str = self.bindings.get(movement)
            if not key_code_str:
                continue
            
            if active:
                self._press_key(key_code_str)
            # Note: We use tap (press+release) for most game inputs
    
    def _press_key(self, key_str):
        """Press and release a key."""
        if self.is_windows:
            # Use DirectInput Scan Codes
            scancode = SCANCODE_MAP.get(key_str) or SCANCODE_MAP.get(key_str.replace('Key', ''))
            if scancode:
                PressKey(scancode)
                time.sleep(0.05)
                ReleaseKey(scancode)
                print(f"⌨️ [Win] Key pressed: {key_str}")
            else:
                print(f"⚠️ [Win] Unknown key for DirectInput: {key_str}")
        else:
            # Standard Pynput
            key = self.key_map.get(key_str)
            if not key and len(key_str) == 1:
                key = key_str.lower() # Single chars
                
            if key:
                self.keyboard.press(key)
                time.sleep(0.05)  # Short hold for game registration
                self.keyboard.release(key)
                print(f"⌨️ Key pressed: {key}")
    
    def hold_key(self, key_str, hold=True):
        """Hold or release a key for continuous movement."""
        # TODO: Implement hold for Windows if needed (current logic relies on repeated taps)
        pass
    
    def release_all(self):
        """Release all held keys."""
        # Pynput release
        if not self.is_windows:
            for key in list(self.pressed_keys):
                self.keyboard.release(key)
            self.pressed_keys.clear()
