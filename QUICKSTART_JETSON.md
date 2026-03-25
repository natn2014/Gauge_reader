# Jetson Orin Nano Quick Start Guide

## 3-Step Deployment

### Supported JetPack Versions
✅ **JetPack 5.1.2** (CUDA 11.8)
✅ **JetPack 6.0, 6.1, 6.2** (CUDA 12.1)

**Auto-Detection**: The setup script automatically detects your JetPack version and installs the correct CUDA dependencies!

### Step 1: Copy Files
```bash
# From your PC, copy all files to Jetson
scp -r VacuumBagGauge/* nvidia@jetson:/home/nvidia/VacuumBagGauge/
```

### Step 2: Run Setup (on Jetson)
```bash
cd ~/VacuumBagGauge
bash setup_jetson.sh
```

### Step 3: Start Application
```bash
# Auto-start is already enabled! Just reboot:
sudo reboot

# Or start immediately:
sudo systemctl start gauge-reader
```

## Verify Installation
```bash
# Check service status
sudo systemctl status gauge-reader

# View live logs
journalctl -u gauge-reader -f

# View last 50 lines
journalctl -u gauge-reader -n 50
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Camera not detected | Check USB connection: `lsusb` and `ls /dev/video*` |
| CUDA not available | Ensure JetPack 5.1.2+ installed: `jetson_clocks --show` |
| Out of memory | Reduce `imgsz=640` to `imgsz=416` in main_jetson.py line 142 |
| Slow performance | Run `sudo jetson_clocks` to enable max frequency |

## File Descriptions

| File | Purpose |
|------|---------|
| `main_jetson.py` | GPU-enabled app with auto-camera detection |
| `setup_jetson.sh` | One-command setup script (installs everything) |
| `gauge-reader.service` | Systemd service for auto-start |
| `JETSON_DEPLOYMENT.md` | Complete deployment guide |
| `main.py` | Original version (Windows/desktop) |
| `ui_mainwindow.py` | UI definitions (shared) |
| `styles.qss` | Material Design dark theme (shared) |
| `gauge_epoch-100.pt` | YOLO model weights |

## Command Reference

```bash
# Service Control
sudo systemctl start gauge-reader      # Start now
sudo systemctl stop gauge-reader       # Stop
sudo systemctl restart gauge-reader    # Restart
sudo systemctl status gauge-reader     # Check status

# Logs
journalctl -u gauge-reader -f          # Follow logs
journalctl -u gauge-reader -n 50       # Last 50 lines
journalctl -u gauge-reader --since today  # Since today

# System Info
jtop                                   # Jetson monitoring tool
jetson_clocks --show                   # CPU/GPU frequencies
free -h                                # Memory usage
df -h                                  # Disk usage

# Camera Testing
ls /dev/video*                         # List cameras
v4l2-ctl --list-devices               # List camera details
```

## Key Features Implemented

✅ **GPU Acceleration**: YOLO inference on CUDA (Orin Nano SM87)
✅ **Auto-Camera Detection**: Automatically finds first USB camera
✅ **No Blocking Dialog**: Direct auto-start on boot
✅ **Systemd Service**: Proper service management
✅ **Auto-Restart**: Service restarts if it crashes
✅ **Material Design UI**: Dark theme with modern styling
✅ **Preset Date Filters**: Today/7-30 days/All/Custom ranges
✅ **GPU-Accelerated OCR**: EasyOCR with CUDA support
✅ **Memory Efficient**: Rolling buffer (max 1000 rows)
✅ **Cross-Platform**: Original main.py still works on Windows

## Hardware Requirements

- Jetson Orin Nano with 8GB RAM
- 32GB+ microSD card
- 15W+ USB-C power supply
- USB 3.0 camera (UVC compatible)
- HDMI/DP display monitor

## Network Setup

If accessing Jetson over network:

```bash
# Find Jetson's IP address
ping jetson-orin-nano.local
# or
hostname -I

# SSH access
ssh nvidia@<jetson-ip>
# Default password: nvidia
```

## Advanced Options

### Disable Auto-Start (if needed)
```bash
sudo systemctl disable gauge-reader
sudo systemctl stop gauge-reader
```

### Change Auto-Start User
Edit `/etc/systemd/system/gauge-reader.service`:
```bash
sudo nano /etc/systemd/system/gauge-reader.service
# Change: User=nvidia  ->  User=<your-username>
sudo systemctl daemon-reload
sudo systemctl restart gauge-reader
```

### Reduce Model Size for Faster Inference
Edit `main_jetson.py` line 142:
```python
# Change from:
results = self.model.predict(frame, verbose=False, imgsz=640, conf=0.25, iou=0.45, device=0 if self.use_gpu else 'cpu')

# To (faster inference):
results = self.model.predict(frame, verbose=False, imgsz=416, conf=0.25, iou=0.45, device=0 if self.use_gpu else 'cpu')
```

### Enable High Performance Mode Permanently
Add to `/home/nvidia/.bashrc`:
```bash
# Enable max performance
if [ -f /usr/bin/jetson_clocks ]; then
    sudo jetson_clocks
fi
```

## Performance Tips

1. **CPU Governor**: Set to performance mode for consistent throughput
   ```bash
   echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
   ```

2. **Swap Configuration**: Check available swap if running multiple processes
   ```bash
   free -h
   ```

3. **Temperature Monitoring**: Watch GPU temperature
   ```bash
   watch -n 1 "jtop --non-interactive"
   ```

## Backup & Recovery

### Backup Application Data
```bash
# Backup gauge data and configuration
tar -czf gauge_backup_$(date +%Y%m%d).tar.gz ~/VacuumBagGauge/gauge_data.csv ~/VacuumBagGauge/gauge_venv
```

### Restore After SD Card Flash
```bash
cd ~/
tar -xzf gauge_backup_20240325.tar.gz
cd VacuumBagGauge
bash setup_jetson.sh
sudo systemctl restart gauge-reader
```

## Support & Debugging

1. **Check CUDA availability**:
   ```bash
   python3 -c "import torch; print(torch.cuda.is_available())"
   ```

2. **Test camera**:
   ```bash
   python3 -c "
   import cv2
   cap = cv2.VideoCapture(0)
   print(f'Camera status: {cap.isOpened()}')
   cap.release()
   "
   ```

3. **Test YOLOv8 on GPU**:
   ```bash
   python3 -c "from ultralytics import YOLO; m = YOLO('gauge_epoch-100.pt'); m.to('cuda'); print('GPU OK')"
   ```

4. **Monitor resource usage while running**:
   ```bash
   watch -n 1 'ps aux | grep main_jetson; free -h; nvidia-smi'
   ```
