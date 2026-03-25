# Jetson Orin Nano Deployment Guide

## Overview
This guide walks through deploying the Vacuum Bag Gauge Reader application on NVIDIA Jetson Orin Nano with GPU acceleration and auto-start capabilities.

## System Requirements
- **Device**: NVIDIA Jetson Orin Nano
- **JetPack Version**: 5.1.2, 6.0, 6.1, or 6.2 (auto-detected)
- **CUDA**: Auto-configured (11.8 for JetPack 5.x, 12.x for JetPack 6.x)
- **RAM**: 8GB
- **Storage**: 32GB+ microSD card recommended
- **Display**: HDMI or DisplayPort monitor
- **Camera**: USB camera (UVC compatible) or CSI camera
- **Power**: 15W+ power supply

## Compatibility Overview

| Component | Status | Details |
|-----------|--------|---------|
| **OpenCV** | ✅ Full | V4L2 support for Linux cameras |
| **PySide6** | ✅ Full | ARM64 native wheels available |
| **YOLO/ultralytics** | ✅ Full | GPU acceleration via CUDA SM87 |
| **PyTorch** | ✅ Full | Jetson-optimized wheels with CUDA 11.8 |
| **EasyOCR** | ✅ Full | GPU-accelerated inference |
| **Pandas** | ✅ Full | ARM64 wheels |
| **Matplotlib** | ✅ Full | Using Agg backend (non-interactive) |
| **Threading** | ✅ Full | QTimer-based 30fps processing |

## Pre-Deployment Checklist

- [ ] Jetson Orin Nano with JetPack 5.1.2, 6.0, 6.1, or 6.2 installed
- [ ] 32GB+ microSD card with sufficient free space
- [ ] HDMI/DP monitor and keyboard/mouse for initial setup
- [ ] USB camera (or CSI camera + appropriate ribbon cable)
- [ ] Network connection (for package downloads)
- [ ] gauge_epoch-100.pt model file
- [ ] ui_mainwindow.py UI definition file
- [ ] styles.qss Material Design theme file

### Checking Your JetPack Version
```bash
jr@jetson:~$ cat /etc/nv_tegra_release
# NVIDIA Jetson Orin Nano (Developer Kit)
# R35 = JetPack 5.1.x
# R36 = JetPack 6.0/6.1/6.2
```

## Deployment Steps

### Step 1: Prepare Files on Jetson

```bash
# Connect to Jetson via SSH or local terminal
ssh nvidia@jetson-orin-nano.local
# or use direct terminal if connected locally

# Create working directory
mkdir -p ~/VacuumBagGauge
cd ~/VacuumBagGauge
```

### Step 2: Copy Project Files to Jetson

From your development machine, copy all files:

```bash
# From your development PC (Windows/Mac/Linux)
scp main_jetson.py nvidia@jetson:/home/nvidia/VacuumBagGauge/
scp setup_jetson.sh nvidia@jetson:/home/nvidia/VacuumBagGauge/
scp ui_mainwindow.py nvidia@jetson:/home/nvidia/VacuumBagGauge/
scp styles.qss nvidia@jetson:/home/nvidia/VacuumBagGauge/
scp gauge_epoch-100.pt nvidia@jetson:/home/nvidia/VacuumBagGauge/
```

Or use SCP with directory copy:
```bash
scp -r VacuumBagGauge/* nvidia@jetson:/home/nvidia/VacuumBagGauge/
```

### Step 3: Run Setup Script

On the Jetson device:

```bash
# Make setup script executable
chmod +x setup_jetson.sh

# Run the setup script
bash setup_jetson.sh
```

**Expected output:**
```
==========================================
Jetson Orin Nano - Gauge Reader Setup
==========================================

[1/7] Updating system packages...
✓ System packages updated

[2/7] Installing Python development tools...
✓ Python tools installed

[3/7] Creating Python virtual environment...
✓ Virtual environment created

[4/7] Upgrading pip...
✓ pip upgraded

[5/7] Installing Python dependencies (this may take 10-15 minutes)...
✓ Core packages installed

[6/7] Installing PyTorch with CUDA support (this may take 20+ minutes)...
✓ PyTorch with CUDA installed

[6.5/7] Installing YOLOv8...
✓ YOLOv8 installed

[7/7] Creating systemd service for auto-start...
✓ Systemd service created and enabled

==========================================
✓ Setup Complete!
==========================================
```

### Step 4: Verify Installation

```bash
# Test if all dependencies are installed
source gauge_venv/bin/activate
python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
"
```

### Step 5: Connect Camera

Insert USB camera into USB 3.0 port on Jetson Orin Nano, then verify:

```bash
# List connected video devices
ls -la /dev/video*

# Test camera with OpenCV
source gauge_venv/bin/activate
python3 -c "
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, frame = cap.read()
    print(f'Camera OK: {frame.shape}')
    cap.release()
else:
    print('Camera not found')
"
```

## Running the Application

### Option A: Start Immediately

```bash
# Start the service right now
sudo systemctl start gauge-reader

# Check if it's running
sudo systemctl status gauge-reader

# View real-time logs
journalctl -u gauge-reader -f
```

### Option B: Auto-Start on Boot

The setup script already enables auto-start. After reboot, the application will start automatically:

```bash
# Reboot the Jetson
sudo reboot

# Application will start automatically within a few seconds
# Check status after boot
sudo systemctl status gauge-reader
```

### Option C: Manual Start (for debugging)

```bash
cd ~/VacuumBagGauge
source gauge_venv/bin/activate
python3 main_jetson.py
```

## Service Management

### View Application Status
```bash
sudo systemctl status gauge-reader
```

### View Real-Time Logs
```bash
journalctl -u gauge-reader -f
```

### View Last 50 Lines of Logs
```bash
journalctl -u gauge-reader -n 50
```

### Stop Application
```bash
sudo systemctl stop gauge-reader
```

### Restart Application
```bash
sudo systemctl restart gauge-reader
```

### Disable Auto-Start (if needed)
```bash
sudo systemctl disable gauge-reader
```

### Re-Enable Auto-Start
```bash
sudo systemctl enable gauge-reader
```

## Troubleshooting

### Issue: Camera not detected at startup

**Solution 1**: Check USB connection
```bash
# Check if camera is detected
lsusb | grep -i camera

# Check video devices
ls -la /dev/video*
```

**Solution 2**: Verify camera is USB Video Class compatible
```bash
# Test with OpenCV
python3 -c "
import cv2
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f'Camera found at /dev/video{i}')
        cap.release()
"
```

### Issue: CUDA not available

**Check GPU status:**
```bash
# Verify GPU is detected
jetson_clocks --show

# Check CUDA installation
python3 -c "import torch; print(torch.cuda.is_available())"
```

**Solution**: Ensure JetPack 5.1.2+ or 6.x is installed with CUDA support. The setup script auto-detects your version.

### Issue: Application crashes with "Out of Memory"

**Solutions**:
1. Reduce model inference size: edit `main_jetson.py` line with `imgsz=640` to `imgsz=416`
2. Reduce data buffer: edit `self.data_buffer_size = 500` (instead of 1000)
3. Disable plot updates temporarily: change plot timer from 5000ms to 10000ms

### Issue: Slow inference performance

**Check system stats:**
```bash
# Monitor CPU/GPU usage
jtop

# Or use htop
htop
```

**Optimization tips**:
1. Enable GPU frequency scaling: `sudo jetson_clocks`
2. Reduce inference resolution in code
3. Lower confidence threshold if false negatives are acceptable

## Performance Metrics

**Expected Performance on Jetson Orin Nano:**

- **YOLO Inference**: 15-25 fps (GPU accelerated)
- **Data Recording**: 1 Hz (1000ms interval)
- **Plot Generation**: 5 second intervals
- **Memory Usage**: ~800MB - 1.2GB (depending on buffer size)
- **GPU Utilization**: 40-60% during inference

## File Structure on Jetson

```
/home/nvidia/VacuumBagGauge/
├── main_jetson.py              # Main application (GPU-enabled, auto-detect)
├── ui_mainwindow.py            # UI definitions
├── styles.qss                  # Material Design theme
├── gauge_epoch-100.pt          # YOLO model weights
├── setup_jetson.sh             # Setup script
├── gauge-reader.service        # Systemd service file
├── gauge_venv/                 # Python virtual environment
│   ├── bin/
│   │   ├── python3             # Python interpreter
│   │   └── pip                 # Package manager
│   └── lib/
│       └── python3.10/         # Installed packages
├── gauge_data.csv              # Data export file (generated)
├── temp_plot.png               # Temporary plot images (generated)
└── logs/                        # Application logs (if configured)
```

## Key Features Optimized for Jetson

1. **Auto-Device Detection**: Automatically finds first available USB camera - no dialog blocking
2. **GPU Acceleration**: YOLO inference runs on CUDA (Orin Nano SM87)
3. **Non-Interactive Backend**: matplotlib uses 'Agg' backend for headless compatibility
4. **Optimized Camera Settings**: 640x480 @ 30fps
5. **Memory-Efficient**: Rolling buffer prevents excessive RAM usage
6. **Systemd Integration**: Proper service management and auto-restart

## Updating the Application

To update the application on Jetson:

```bash
# Stop the service
sudo systemctl stop gauge-reader

# Get latest files from development machine
scp main_jetson.py nvidia@jetson:/home/nvidia/VacuumBagGauge/
scp styles.qss nvidia@jetson:/home/nvidia/VacuumBagGauge/

# Start the service
sudo systemctl start gauge-reader

# Verify
sudo systemctl status gauge-reader
```

## Uninstalling

To completely remove the application:

```bash
# Stop and disable service
sudo systemctl stop gauge-reader
sudo systemctl disable gauge-reader
sudo rm /etc/systemd/system/gauge-reader.service

# Remove application directory
rm -rf ~/VacuumBagGauge

# Optionally remove virtual environment
rm -rf ~/gauge_venv
```

## Additional Resources

- **Jetson Orin Nano Developer Kit**: https://developer.nvidia.com/embedded/jetson-orin-nano
- **JetPack Documentation**: https://docs.nvidia.com/jetson/jetpack/
- **PyTorch on Jetson**: https://pytorch.org/blog/running-pytorch-models-on-jetson-nano/
- **YOLO on Jetson**: https://docs.ultralytics.com/guides/nvidia-jetson/

## Support

For issues or questions:
1. Check systemd logs: `journalctl -u gauge-reader -n 100`
2. Verify camera: `ls /dev/video* && lsusb`
3. Test GPU: `python3 -c "import torch; print(torch.cuda.is_available())"`
4. Check system resources: `free -h && df -h`
