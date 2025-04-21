# MicroPython Firebase OTA Updater 🔄

A secure **Over-The-Air (OTA)** firmware updater for MicroPython devices (ESP32/RP2040) using **Firebase Realtime Database**. Enables remote updates with fail-safe rollback.

## Key Features ✨
- ♻️ **Fail-Safe Mechanism**: Automatic rollback on update failure  
- 📡 **Firebase Integration**: Real-time version control and update triggers  
- ⚡ **Low Bandwidth**: Delta updates to minimize transfer size  

## Hardware Compatibility 🛠️
- ESP32, ESP8266, Raspberry Pi Pico (RP2040)  
- Supports any MicroPython-enabled device with WiFi  

## Setup Guide 🚀
1. **Configure Firebase**:  
   - Set up a Realtime Database and add your file structures.
     ```json
     {
      "v1_1": {
           "*root*" : "main.py;;test.py",
           "lib"    : "sensor.py"
      }
      }
     ```
   - Add files to Firebase Storage with the same architecture as described in database
     ```
      firmware_bucket/
      ├── v1.1/
      │   ├── main.py
      │   ├── test.py
      │   └── lib/
      │       └── sensor.py
     ```
     

2. **Flash the Bootloader**:  
   - Add ota_updater.py to root directory on micropython device.
  
## Usage 📲
   ```python
  from ota_updater import FirebaseUpdater

  updater = FirebaseUpdater(api_key='API_KEY', auth_email='email', auth_pass='pass', database_url='url1', storage_url='url2')
  updater.download_latest_version()
   ```
