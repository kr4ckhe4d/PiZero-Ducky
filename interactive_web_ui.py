#!/usr/bin/env python3
from flask import Flask, render_template_string
from flask_socketio import SocketIO
import time
import os

app = Flask(__name__)
socketio = SocketIO(app)

# --- Re-using the payload execution logic ---
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
MODIFIER_KEYS = {
    'CTRL': 0x01, 'SHIFT': 0x02, 'ALT': 0x04, 'GUI': 0x08, 'WINDOWS': 0x08
}
HID_DEVICE = '/dev/hidg0'

def send_hid_report(report):
    with open(HID_DEVICE, 'rb+') as hid:
        hid.write(report)

def send_key(key, modifier=0):
    key_code = KEY_CODES.get(key.upper())
    if key_code:
        send_hid_report(bytes([modifier, 0, key_code, 0, 0, 0, 0, 0]))
        time.sleep(0.01)
        send_hid_report(bytes([0, 0, 0, 0, 0, 0, 0, 0])) # Release
        time.sleep(0.01)

def send_combo(keys):
    modifiers = 0
    main_key_code = 0
    for key in keys:
        upper_key = key.upper()
        if upper_key in MODIFIER_KEYS:
            modifiers |= MODIFIER_KEYS[upper_key]
        elif upper_key in KEY_CODES:
            main_key_code = KEY_CODES[upper_key]
    
    if main_key_code:
        send_hid_report(bytes([modifiers, 0, main_key_code, 0, 0, 0, 0, 0]))
        time.sleep(0.01)
        send_hid_report(bytes([0, 0, 0, 0, 0, 0, 0, 0])) # Release
        time.sleep(0.01)

def send_string(text):
    for char in text:
        if char.upper() in KEY_CODES:
            modifier = MODIFIER_KEYS['SHIFT'] if char.isupper() else 0
            send_key(char, modifier)
        elif char == ' ':
            send_key('SPACE')
        # Add more symbol handling here if needed
        time.sleep(0.02)

# --- Web Interface and WebSocket Logic ---

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Interactive Pi Ducky</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { font-family: monospace; background: #1e1e1e; color: #d4d4d4; margin: 2em; }
        #terminal { width: 90%; height: 400px; background: #000; border: 1px solid #888; padding: 1em; overflow-y: scroll; }
        #commandInput { width: 90%; background: #333; color: #d4d4d4; border: 1px solid #888; padding: 0.5em; margin-top: 1em; }
        .log { margin: 0; }
        .log.sent { color: #569cd6; }
        .log.status { color: #4ec9b0; font-style: italic; }
    </style>
</head>
<body>
    <h1>Interactive Ducky Terminal</h1>
    <div id="terminal"></div>
    <input type="text" id="commandInput" placeholder="Type Ducky Script commands and press Enter..." autofocus>
    
    <script>
        const socket = io();
        const terminal = document.getElementById('terminal');
        const commandInput = document.getElementById('commandInput');

        function log(message, type = 'status') {
            const p = document.createElement('p');
            p.className = 'log ' + type;
            p.textContent = message;
            terminal.appendChild(p);
            terminal.scrollTop = terminal.scrollHeight;
        }

        commandInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                const command = commandInput.value;
                if (command) {
                    log(`> ${command}`, 'sent');
                    socket.emit('run_command', { command: command });
                    commandInput.value = '';
                }
            }
        });
        
        socket.on('connect', () => {
            log('Connected to Pi Ducky server.');
        });

        socket.on('status', (data) => {
            log(data.msg);
        });

        log('Welcome to the interactive terminal. Ready for commands.');
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@socketio.on('run_command')
def handle_command(json):
    command_str = json['command'].strip()
    socketio.emit('status', {'msg': f'Executing: {command_str}'})
    
    parts = command_str.split(' ', 1)
    command = parts[0].upper()
    args = parts[1] if len(parts) > 1 else ""

    try:
        if command == 'DELAY':
            time.sleep(int(args) / 1000.0)
        elif command == 'STRING':
            send_string(args)
        elif command in MODIFIER_KEYS:
            send_combo([command] + args.split())
        elif command in KEY_CODES:
            send_key(command)
        else:
            socketio.emit('status', {'msg': f"Unknown command: {command}"})
    except Exception as e:
        socketio.emit('status', {'msg': f"Error: {e}"})

if __name__ == '__main__':
    # Make sure the HID device is ready before starting
    os.system('sudo /usr/bin/hid-gadget.sh')
    time.sleep(2) # Give it a moment
    # Change permissions so the script (running as your user) can write to it
    os.system(f'sudo chown {os.getlogin()}:{os.getlogin()} {HID_DEVICE}')
    
    socketio.run(app, host='0.0.0.0', port=5000)
