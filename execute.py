#!/usr/bin/env python3
import time
import os
import sys

# HID Keyboard scan codes
# The letter keys are now uppercase to match the lookup logic.
KEY_CODES = {
    'A': 0x04, 'B': 0x05, 'C': 0x06, 'D': 0x07, 'E': 0x08, 'F': 0x09,
    'G': 0x0a, 'H': 0x0b, 'I': 0x0c, 'J': 0x0d, 'K': 0x0e, 'L': 0x0f,
    'M': 0x10, 'N': 0x11, 'O': 0x12, 'P': 0x13, 'Q': 0x14, 'R': 0x15,
    'S': 0x16, 'T': 0x17, 'U': 0x18, 'V': 0x19, 'W': 0x1a, 'X': 0x1b,
    'Y': 0x1c, 'Z': 0x1d, '1': 0x1e, '2': 0x1f, '3': 0x20, '4': 0x21,
    '5': 0x22, '6': 0x23, '7': 0x24, '8': 0x25, '9': 0x26, '0': 0x27,
    'ENTER': 0x28, 'ESC': 0x29, 'BACKSPACE': 0x2a, 'TAB': 0x2b,
    'SPACE': 0x2c, 'CAPS': 0x39, 'F1': 0x3a, 'F2': 0x3b, 'F3': 0x3c,
    'F4': 0x3d, 'F5': 0x3e, 'F6': 0x3f, 'F7': 0x40, 'F8': 0x41,
    'F9': 0x42, 'F10': 0x43, 'F11': 0x44, 'F12': 0x45, 'UP': 0x52,
    'DOWN': 0x51, 'LEFT': 0x50, 'RIGHT': 0x4f
}

# Modifier key bitmasks
MODIFIER_KEYS = {
    'CTRL': 0x01, 'SHIFT': 0x02, 'ALT': 0x04, 'GUI': 0x08
}

def get_hid_device():
    """Get the HID device file handle."""
    # This function helps avoid opening and closing the file repeatedly.
    # NOTE: In a real-world scenario, you might want to open this once
    # at the start of the script and close it at the end.
    return open('/dev/hidg0', 'rb+')

def send_key(key, modifier=0):
    """Send a single key press and release."""
    if isinstance(key, str):
        key_code = KEY_CODES.get(key.upper())
        if key_code is None:
            print(f"Warning: Key '{key}' not found.")
            return
    else:
        key_code = key

    with get_hid_device() as hid:
        # Press the key
        hid.write(bytes([modifier, 0, key_code, 0, 0, 0, 0, 0]))
        time.sleep(0.01)
        # Release all keys
        hid.write(bytes([0, 0, 0, 0, 0, 0, 0, 0]))
        time.sleep(0.01)

def send_combo(keys):
    """
    Send a key combination like Windows+R.
    This function now correctly simulates holding the modifier key.
    """
    modifiers = 0
    main_key_code = 0

    for key in keys:
        upper_key = key.upper()
        if upper_key in MODIFIER_KEYS:
            modifiers |= MODIFIER_KEYS[upper_key]
        elif upper_key in KEY_CODES:
            main_key_code = KEY_CODES[upper_key]

    if main_key_code == 0:
        print(f"Warning: No valid main key found in combination: {keys}")
        return

    with get_hid_device() as hid:
        # Press the modifier and the key together
        hid.write(bytes([modifiers, 0, main_key_code, 0, 0, 0, 0, 0]))
        time.sleep(0.01)
        # Release all keys
        hid.write(bytes([0, 0, 0, 0, 0, 0, 0, 0]))
        time.sleep(0.01)

def send_string(text):
    """Send a string of characters."""
    for char in text:
        # Determine if shift is needed
        is_upper = char.isupper()
        is_symbol = char in "~!@#$%^&*()_+{}|:\"<>?"
        
        modifier = MODIFIER_KEYS['SHIFT'] if is_upper or is_symbol else 0
        
        # A simple mapping for shifted symbols on a US keyboard layout
        symbol_map = {
            '~': '`', '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
            '^': '6', '&': '7', '*': '8', '(': '9', ')': '0', '_': '-',
            '+': '=', '{': '[', '}': ']', '|': '\\', ':': ';', '"': "'",
            '<': ',', '>': '.', '?': '/'
        }
        
        key_to_press = symbol_map.get(char, char)

        if key_to_press.upper() in KEY_CODES:
            send_key(key_to_press, modifier)
        elif char == ' ':
            send_key('SPACE')
        
        time.sleep(0.02) # A slightly longer delay can improve reliability

def delay(milliseconds):
    """Wait for a specified number of milliseconds."""
    time.sleep(milliseconds / 1000.0)

def execute_payload(payload_file):
    """Execute a payload file line by line."""
    try:
        with open(payload_file, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Payload file '{payload_file}' not found.")
        sys.exit(1)
    
    print("Executing payload...")
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith("REM"):
            continue

        parts = line.split(' ', 1)
        command = parts[0].upper()
        args = parts[1] if len(parts) > 1 else ""

        try:
            if command == 'DELAY':
                delay(int(args))
            elif command == 'STRING':
                send_string(args)
            elif command in MODIFIER_KEYS: # Handles GUI, CTRL, ALT, SHIFT
                # e.g., "GUI R" or "CTRL C"
                combo_keys = [command] + args.split()
                send_combo(combo_keys)
            elif command == 'WINDOWS': # Alias for GUI
                combo_keys = ['GUI'] + args.split()
                send_combo(combo_keys)
            elif command in KEY_CODES:
                send_key(command)
            else:
                print(f"Line {i+1}: Unknown command '{command}'")

        except Exception as e:
            print(f"Error processing line {i+1} ('{line}'): {e}")
    print("Payload execution finished.")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <payload_file>")
        sys.exit(1)
    
    payload_file = sys.argv[1]
    execute_payload(payload_file)
