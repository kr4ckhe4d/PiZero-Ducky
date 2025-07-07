# Build Your Own USB Rubber Ducky with a Raspberry Pi Zero 2 W

### **Part 1: The Basics - Setting Up Your Pi**

This section covers getting your Raspberry Pi ready with the necessary operating system and basic configuration.

**What You'll Need:**

* **Raspberry Pi Zero 2 W**
* **MicroSD Card** (at least 8GB, Class 10 recommended)
* **USB-A to Micro-USB Cable** (must support data transfer)
* A computer for the initial setup

#### **Step 1: Flash Raspberry Pi OS**

We'll start by installing the lightweight "Lite" version of the Raspberry Pi OS.

1.  **Download and Install:** Get the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) for your computer.
2.  **Open Imager:** Insert your microSD card into your computer and launch the Imager.
3.  **Choose OS:** Select "Raspberry Pi OS Lite (32-bit)."
4.  **Configure:** Click the gear icon to open the advanced settings:
    * **Enable SSH:** Check the box and set a password.
    * **Set Username:** The default is `pi`.
    * **Configure WiFi:** Enter your WiFi network's name (SSID) and password.
    * **Set Locale:** Adjust your language and timezone settings.
5.  **Write:** Select your microSD card and click "Write." Once it's finished, you can eject the card.

#### **Step 2: First Boot and System Update**

Let's boot up the Pi and make sure it's up-to-date.

1.  **Power On:** Insert the microSD card into the Pi Zero and connect it to power.
2.  **Find the Pi's IP Address:** You can find this by checking your router's connected devices list or by using a network scanning tool like `nmap` on your computer (`nmap -sn 192.168.1.0/24`, adjusting the IP range for your network).
3.  **Connect via SSH:** Open a terminal (or PuTTY on Windows) and connect to your Pi:
    ```bash
    ssh pi@[PI_IP_ADDRESS]
    ```
4.  **Update Your System:** It's crucial to run updates to ensure all packages are current.
    ```bash
    sudo apt update && sudo apt upgrade -y
    ```

***

### **Part 2: Enabling USB Gadget Mode**

Now, we'll configure the Pi to act as a USB Human Interface Device (HID), which allows it to be recognized as a keyboard.

#### **Step 3: Configure Boot Files**

1.  **Edit `config.txt`:** Open this file to add the USB driver overlay. On recent OS versions, this is at `/boot/firmware/config.txt`.
    ```bash
    sudo nano /boot/firmware/config.txt
    ```
    Add the following line to the very bottom of the file:
    ```
    dtoverlay=dwc2
    ```
    Save and exit by pressing `Ctrl+X`, then `Y`, then `Enter`.

2.  **Edit `cmdline.txt`:** On recent versions of Raspberry Pi OS, this file is located in the `/boot/firmware` directory.
    ```bash
    sudo nano /boot/firmware/cmdline.txt
    ```
    Find the word `rootwait` and add `modules-load=dwc2,g_hid` right after it, separated by a space. The line should look something like this:
    ```
    ... rootwait modules-load=dwc2,g_hid quiet init=...
    ```

#### **Step 4: Create the HID Gadget Script**

This script sets up the Pi to be recognized as a generic USB keyboard.

1.  **Create the script file:**
    ```bash
    sudo nano /usr/bin/hid-gadget.sh
    ```
2.  **Paste the following content:**
    ```bash
    #!/bin/bash
    cd /sys/kernel/config/usb_gadget/
    mkdir -p pi_ducky
    cd pi_ducky
    
    # Device Descriptor
    echo 0x1d6b > idVendor  # Linux Foundation
    echo 0x0104 > idProduct # Multifunction Composite Gadget
    echo 0x0100 > bcdDevice # v1.0.0
    echo 0x0200 > bcdUSB    # USB 2.0
    
    # String Descriptors
    mkdir -p strings/0x409
    echo "pizero" > strings/0x409/serialnumber
    echo "Maker" > strings/0x409/manufacturer
    echo "USB Keyboard" > strings/0x409/product
    
    # Configuration Descriptor
    mkdir -p configs/c.1/strings/0x409
    echo "Keyboard Configuration" > configs/c.1/strings/0x409/configuration
    echo 250 > configs/c.1/MaxPower
    
    # HID Function
    mkdir -p functions/hid.usb0
    echo 1 > functions/hid.usb0/protocol   # Keyboard
    echo 1 > functions/hid.usb0/subclass   # Boot Interface
    echo 8 > functions/hid.usb0/report_length # Report length
    # Standard Keyboard Report Descriptor
    echo -ne \\x05\\x01\\x09\\x06\\xa1\\x01\\x05\\x07\\x19\\xe0\\x29\\xe7\\x15\\x00\\x25\\x01\\x75\\x01\\x95\\x08\\x81\\x02\\x95\\x01\\x75\\x08\\x81\\x03\\x95\\x05\\x75\\x01\\x05\\x08\\x19\\x01\\x29\\x05\\x91\\x02\\x95\\x01\\x75\\x03\\x91\\x03\\x95\\x06\\x75\\x08\\x15\\x00\\x25\\x65\\x05\\x07\\x19\\x00\\x29\\x65\\x81\\x00\\xc0 > functions/hid.usb0/report_desc
    
    # Associate HID function with the configuration
    ln -s functions/hid.usb0 configs/c.1/
    
    # Activate the gadget
    ls /sys/class/udc > UDC
    ```
3.  **Make the script executable:**
    ```bash
    sudo chmod +x /usr/bin/hid-gadget.sh
    ```

***

### **Part 3: The Payload Executor**

Here, we'll set up the Python script that reads Ducky Script-like payloads and "types" them out.

#### **Step 5: Create the Payload Directory and Script**

1.  **Create a directory to store payloads:**
    ```bash
    sudo mkdir -p /opt/payloads
    ```
2.  **Create the Python executor script:**
    ```bash
    sudo nano /opt/payloads/execute.py
    ```
3.  **Paste the Python code for the executor script** into this file.
4.  **Make it executable:**
    ```bash
    sudo chmod +x /opt/payloads/execute.py
    ```

#### **Step 6: Create a Sample Payload**

Let's create a simple payload to test that everything works.

1.  **Create a payload file:**
    ```bash
    sudo nano /opt/payloads/hello-world.txt
    ```
2.  **Add the following Ducky Script commands:** This payload waits 2 seconds, opens Notepad on Windows, and types a message.
    ```
    DELAY 2000
    GUI r
    DELAY 500
    STRING notepad
    ENTER
    DELAY 1000
    STRING Hello from the Pi Ducky!
    ```

***

### **Part 4: Automation and Testing**

This final part makes the payload run automatically when you plug the Pi into a computer.

#### **Step 7: Create an Auto-Run Service**

We'll use `systemd` to create a service that runs our scripts on boot.

1.  **Create the service file:**
    ```bash
    sudo nano /etc/systemd/system/ducky.service
    ```
2.  **Add the service configuration:** This tells the system to run our gadget script and then execute our payload.
    ```ini
    [Unit]
    Description=Rubber Ducky USB HID Service
    After=network.target
    
    [Service]
    Type=oneshot
    ExecStart=/usr/bin/hid-gadget.sh
    ExecStartPost=/bin/sleep 2
    ExecStartPost=/usr/bin/python3 /opt/payloads/execute.py /opt/payloads/hello-world.txt
    RemainAfterExit=yes
    
    [Install]
    WantedBy=multi-user.target
    ```
3.  **Enable the service:** This makes it start automatically on boot.
    ```bash
    sudo systemctl enable ducky.service
    ```

#### **Step 8: Final Test**

1.  **Reboot the Pi:**
    ```bash
    sudo reboot
    ```
2.  **Deploy:** Once the Pi has rebooted, unplug it from power. Now, connect it to your target computer using the **USB data port** on the Pi Zero (the one closer to the center).
3.  **Observe:** The Pi should be detected as a keyboard, and after a few seconds, it should automatically execute the `hello-world.txt` payload.

Congratulations! You've successfully built the core of your Raspberry Pi Rubber Ducky.

***

### **Part 5: Optional - Web Interface for Payload Management**

This advanced section will guide you through setting up a web server on the Pi. This allows you to upload, manage, and select payloads from any device on your network using a web browser, without needing to use SSH.

#### **Step 9: Install Web Server Software**

We'll use Flask, a lightweight and simple web framework for Python.
```bash
sudo apt install python3-flask -y
```

#### **Step 10: Create the Web Interface Script**

This Python script will run our web server.

1.  **Create the file:**
    ```bash
    sudo nano /opt/payloads/web_interface.py
    ```
2.  **Paste the following code:** This app lists payloads, lets you upload new ones, and sets the "active" payload.
    ```python
    #!/usr/bin/env python3
    from flask import Flask, render_template_string, request, redirect, url_for, flash
    import os
    import glob
    
    app = Flask(__name__)
    PAYLOAD_DIR = '/opt/payloads'
    ACTIVE_PAYLOAD_SYMLINK = os.path.join(PAYLOAD_DIR, 'active.txt')
    app.secret_key = 'supersecretkey' # Change this for security
    
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pi Ducky Payload Manager</title>
        <style>
            body { font-family: sans-serif; background: #f4f4f9; color: #333; margin: 2em; }
            .container { max-width: 800px; margin: auto; background: white; padding: 2em; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1, h2 { color: #444; }
            ul { list-style-type: none; padding: 0; }
            li { background: #eee; margin: 0.5em 0; padding: 0.8em; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }
            li.active { background: #d4edda; font-weight: bold; }
            a { text-decoration: none; color: #007bff; }
            .btn { background: #007bff; color: white; padding: 0.5em 1em; border-radius: 4px; }
            .btn-delete { background: #dc3545; }
            form { margin-top: 2em; background: #fdfdfd; padding: 1.5em; border: 1px solid #ddd; border-radius: 4px;}
            input[type=file], input[type=submit] { margin-top: 0.5em; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Pi Ducky Payload Manager</h1>
            {% with messages = get_flashed_messages() %}
              {% if messages %}
                {% for message in messages %}
                  <p><i>{{ message }}</i></p>
                {% endfor %}
              {% endif %}
            {% endwith %}
    
            <h2>Available Payloads</h2>
            <p>Current active payload: <strong>{{ active_payload or 'None' }}</strong></p>
            <ul>
            {% for payload in payloads %}
                <li class="{{ 'active' if payload == active_payload else '' }}">
                    <span>{{ payload }}</span>
                    <div>
                        <a href="/activate/{{ payload }}" class="btn">Activate</a>
                        <a href="/delete/{{ payload }}" class="btn btn-delete" onclick="return confirm('Are you sure you want to delete this payload?');">Delete</a>
                    </div>
                </li>
            {% endfor %}
            </ul>
    
            <h2>Upload New Payload</h2>
            <form method="POST" action="/upload" enctype="multipart/form-data">
                <input type="file" name="payload" accept=".txt" required>
                <br><br>
                <input type="submit" value="Upload Payload">
            </form>
        </div>
    </body>
    </html>
    """
    
    def get_payloads():
        return [os.path.basename(f) for f in glob.glob(f"{PAYLOAD_DIR}/*.txt") if not os.path.basename(f) == 'active.txt']
    
    def get_active_payload():
        if os.path.islink(ACTIVE_PAYLOAD_SYMLINK):
            return os.path.basename(os.readlink(ACTIVE_PAYLOAD_SYMLINK))
        return None
    
    @app.route('/')
    def index():
        return render_template_string(HTML_TEMPLATE, payloads=get_payloads(), active_payload=get_active_payload())
    
    @app.route('/activate/<payload_name>')
    def activate(payload_name):
        target_file = os.path.join(PAYLOAD_DIR, payload_name)
        if os.path.exists(target_file):
            if os.path.exists(ACTIVE_PAYLOAD_SYMLINK):
                os.remove(ACTIVE_PAYLOAD_SYMLINK)
            os.symlink(target_file, ACTIVE_PAYLOAD_SYMLINK)
            flash(f"'{payload_name}' is now the active payload.")
        else:
            flash(f"Error: Payload '{payload_name}' not found.")
        return redirect(url_for('index'))
    
    @app.route('/delete/<payload_name>')
    def delete(payload_name):
        target_file = os.path.join(PAYLOAD_DIR, payload_name)
        if os.path.exists(target_file):
            if get_active_payload() == payload_name:
                os.remove(ACTIVE_PAYLOAD_SYMLINK)
            os.remove(target_file)
            flash(f"Deleted payload '{payload_name}'.")
        else:
            flash(f"Error: Payload '{payload_name}' not found.")
        return redirect(url_for('index'))
    
    @app.route('/upload', methods=['POST'])
    def upload():
        if 'payload' not in request.files:
            flash('No file part')
            return redirect(url_for('index'))
        file = request.files['payload']
        if file.filename == '':
            flash('No selected file')
            return redirect(url_for('index'))
        if file and file.filename.endswith('.txt'):
            filename = os.path.basename(file.filename)
            file.save(os.path.join(PAYLOAD_DIR, filename))
            flash(f"Payload '{filename}' uploaded successfully.")
        else:
            flash("Invalid file type. Please upload a .txt file.")
        return redirect(url_for('index'))
    
    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000)
    ```

#### **Step 11: Automate the Web Interface and Ducky Service**

Now we need two services: one for the web interface and an updated one for the ducky script to use the payload selected by the web app.

1.  **Create the Web Interface Service:**
    ```bash
    sudo nano /etc/systemd/system/ducky-web.service
    ```
    Paste the following. This will run the Flask app on boot.
    ```ini
    [Unit]
    Description=Ducky Web Interface
    After=network.target
    
    [Service]
    ExecStart=/usr/bin/python3 /opt/payloads/web_interface.py
    WorkingDirectory=/opt/payloads
    Restart=always
    User=pi
    
    [Install]
    WantedBy=multi-user.target
    ```

2.  **Update the Ducky Service:** Modify the original `ducky.service` to execute the `active.txt` payload.
    ```bash
    sudo nano /etc/systemd/system/ducky.service
    ```
    Change the `ExecStartPost` line that runs the python script. The file should now look like this:
    ```ini
    [Unit]
    Description=Rubber Ducky USB HID Service
    After=network.target
    
    [Service]
    Type=oneshot
    ExecStart=/usr/bin/hid-gadget.sh
    ExecStartPost=/bin/sleep 2
    # This line is changed to execute the active payload
    ExecStartPost=/usr/bin/python3 /opt/payloads/execute.py /opt/payloads/active.txt
    RemainAfterExit=yes
    
    [Install]
    WantedBy=multi-user.target
    ```

3.  **Enable the new service and reload:**
    ```bash
    sudo systemctl enable ducky-web.service
    sudo systemctl daemon-reload
    sudo systemctl restart ducky.service
    sudo systemctl start ducky-web.service
    ```

#### **Step 12: Using the Web Interface**

1.  **Reboot your Pi** to ensure both services start correctly.
2.  From another computer on the same WiFi network, open a web browser and go to `http://[PI_IP_ADDRESS]:5000`.
3.  You should see the payload manager. From here you can:
    * See all available payloads.
    * Click **"Activate"** to choose which payload will run the next time you plug the Pi into a target.
    * **Upload** new `.txt` payload files directly from your browser.

***

### **Troubleshooting and Next Steps**

* **Permission Denied on `/dev/hidg0`:** If the script fails, the most common issue is permissions. Run `sudo chmod 666 /dev/hidg0` to grant write access. You can add this command to your `ducky.service` file for a permanent fix.
* **Device Not Recognized:** Ensure you are using a **data-capable** USB cable and have plugged it into the correct USB port on the Pi.
* **Web Interface Not Loading:** Check the service status with `sudo systemctl status ducky-web.service`. Ensure your Pi is connected to WiFi and you are using the correct IP address.
* **Explore Ducky Script:** Experiment with commands like `CTRL`, `ALT`, `SHIFT`, and function keys to build more complex automation scripts.
