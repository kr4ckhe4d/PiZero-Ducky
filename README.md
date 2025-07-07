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

### **Troubleshooting and Next Steps**

* **Permission Denied on `/dev/hidg0`:** If the script fails, the most common issue is permissions. Run `sudo chmod 666 /dev/hidg0` to grant write access. You can add this command to your `ducky.service` file for a permanent fix.
* **Device Not Recognized:** Ensure you are using a **data-capable** USB cable and have plugged it into the correct USB port on the Pi.
* **Web Interface Not Loading:** Check the service status with `sudo systemctl status ducky-web.service`. Ensure your Pi is connected to WiFi and you are using the correct IP address.
* **Explore Ducky Script:** Experiment with commands like `CTRL`, `ALT`, `SHIFT`, and function keys to build more complex automation scripts.
